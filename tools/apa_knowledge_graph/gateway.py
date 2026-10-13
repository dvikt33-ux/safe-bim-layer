#!/usr/bin/env python3
"""APA read-only, compact GPT evidence gateway: exact IDs -> graph -> scoped snippets.

The current PLAN is the only task authority. The FTS and graph index are caches.
The gateway never asserts engineering compliance, rewrites evidence or issues claims.
All text from documents is untrusted DATA, not an instruction to the LLM.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlparse

from graph import assert_index, canonical, fingerprint, task_card
from sections import search as search_sections

SID = re.compile(r"\bAPA-P\d{2}\.A\d{2}\.S\d{2}\b", re.I)
ART = re.compile(r"\bART-[A-Z0-9][A-Z0-9._-]+\b")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
MAX_QUERY_CHARS = 280
MIN_BUDGET = 400
MAX_BUDGET = 12000


def verify_plan(index, plan):
    assert_index(index)
    if fingerprint(plan) != index.get("plan_sha256"):
        raise ValueError("STALE_INDEX: rebuild read-only graph from current source plan")
    return True


def stable_relative(repo_root, absolute_path):
    """Never reveal or link arbitrary host paths outside the checkout."""
    root = Path(repo_root).resolve(strict=True)
    target = Path(absolute_path).resolve(strict=True)
    if not target.is_relative_to(root):
        raise ValueError("SOURCE_PATH_OUTSIDE_REPOSITORY")
    return target.relative_to(root).as_posix()


def artifact_source_path(uri, repo):
    """Only associate GitHub blob URLs with an explicit path; no repo broadening."""
    if not isinstance(uri, str) or not uri:
        return None, "MISSING_URI"
    if uri.startswith("sha256:"):
        return None, "HASH_ONLY"
    if "://" not in uri:
        p = Path(uri)
        if p.is_absolute() or ".." in p.parts:
            return None, "UNSAFE_OR_EXTERNAL_URI"
        return p.as_posix(), "RELATIVE_NOT_COMMIT_PINNED"
    parsed = urlparse(uri)
    if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
        return None, "EXTERNAL_URI"
    prefix = "/" + repo + "/blob/"
    if not parsed.path.startswith(prefix):
        return None, "NOT_REPO_BLOB_URI"
    suffix = unquote(parsed.path[len(prefix):])
    # SHA-pinned revision. A branch with slash is intentionally not guessed.
    if len(suffix) > 41 and HEX40.fullmatch(suffix[:40]) and suffix[40] == "/":
        return suffix[41:], "COMMIT_PINNED_URI"
    return None, "MOVING_OR_UNRESOLVED_REF"


def source_artifacts(index, repo):
    """Build exact, no-LLM artifact-to-repo-path map."""
    mapping = {}
    for aid, art in index["artifacts"].items():
        path, provenance = artifact_source_path(art.get("uri"), repo)
        if path and path.startswith(("docs/", "tools/", "tests/", "examples/")):
            mapping.setdefault(path, []).append((aid, provenance))
    return mapping


def ready_to_suggest(index, task_id):
    task = index["tasks"][task_id]
    if task["status"] not in ("READY", "PARTIAL"):
        return False
    if task["owner"] or task["claim_ref"] or task["requires_approval"]:
        return False
    return all(index["tasks"][dep]["status"] == "DONE_PUBLISHED"
               for dep in task["depends_on"])


def compact_fit(base, proposals, budget):
    """Never truncate a source identity, status, hash or section citation."""
    if not isinstance(budget, int) or not MIN_BUDGET <= budget <= MAX_BUDGET:
        raise ValueError("max_chars outside secure 400..12000 range")
    base = dict(base)
    base["items"] = []
    base["total_candidates"] = len(proposals)
    base["omitted"] = len(proposals)
    if len(canonical(base)) > budget:
        return {"status": "BUDGET_TOO_SMALL", "minimum_chars": len(canonical(base)),
                "requested_max_chars": budget, "items": []}
    for item in proposals:
        attempt = dict(base)
        attempt["items"] = base["items"] + [item]
        attempt["omitted"] = len(proposals) - len(attempt["items"])
        if len(canonical(attempt)) > budget:
            break
        base = attempt
    if not base["items"] and proposals:
        return {"status": "BUDGET_TOO_SMALL", "minimum_chars": len(canonical({**base, "items": [proposals[0]],
                         "omitted": len(proposals)-1})), "requested_max_chars": budget,
                "items": [], "total_candidates": len(proposals)}
    return base


def retrieve(index, plan, section_db, repo_root, repo, query, mode="research",
             source_class=None, limit=4, max_chars=2500):
    verify_plan(index, plan)
    if not isinstance(query, str) or not 1 <= len(query.strip()) <= MAX_QUERY_CHARS:
        raise ValueError("Query length must be 1..280 characters")
    if mode not in ("research", "next", "normative"):
        raise ValueError("Allowed modes: research, next, normative")
    if not isinstance(limit, int) or not 1 <= limit <= 10:
        raise ValueError("limit 1..10")
    ids = SID.findall(query.upper())
    aids = ART.findall(query.upper())
    base = {
        "schema": "APA_COMPACT_RETRIEVAL_V1",
        "status": "OK", "mode": mode, "query": query,
        "authority": "GITHUB_PROJECT_PLAN_ONLY",
        "plan_revision": index.get("plan_revision"),
        "plan_sha256": index["plan_sha256"],
        "normative_authority": False,
        "limitations": "Cross-document mentions are NOT proven field lineage; verify source edition and rule gates."
    }
    if ids:
        cards = [task_card(index, sid, include_artifacts=False) for sid in dict.fromkeys(ids)]
        return compact_fit({**base, "retrieval": "EXACT_TASK", "task_claim": "NEVER_AUTOMATIC"},
                           cards[:limit], max_chars)
    if aids:
        cards = []
        for aid in dict.fromkeys(aids):
            art = index["artifacts"].get(aid)
            if not art:
                cards.append({"id": aid, "status": "NOT_FOUND"})
            else:
                hit_tasks = index["artifact_to_tasks"].get(aid, [])
                cards.append({"id": aid, "kind": art["kind"], "uri": art["uri"],
                              "verification": art["verification"],
                              "task_reference_count": len(hit_tasks),
                              "task_ids": hit_tasks[:4],
                              "relation": "REFERENCE_ONLY"})
        return compact_fit({**base, "retrieval": "EXACT_ARTIFACT"}, cards[:limit], max_chars)

    # A legal/normative engineering decision must NOT be sourced from an
    # arbitrary Markdown path label. Expose search leads, but never authority.
    selected_class = source_class
    if mode == "normative" and selected_class is None:
        selected_class = "PROJECT_CONTROL"
    result = search_sections(section_db, query, limit=min(20, limit * 4),
                             max_snippet=160, selected_class=selected_class)
    if result["status"] == "STALE_INDEX":
        return {"status": "STALE_INDEX", "items": [],
                "warning": "Stale top results: rebuild index before retrieval"}
    if result["status"] != "OK":
        return {"status": result["status"], "items": []}

    mapped = source_artifacts(index, repo)
    cards = []
    seen = set()
    for hit in result["results"]:
        relative = stable_relative(repo_root, hit["path"])
        if relative in seen:
            continue  # diversify documents, not a flood of headings from one doc
        seen.add(relative)
        provenance = mapped.get(relative, [])
        art_ids = sorted(x[0] for x in provenance)
        tasks = sorted(set(t for aid in art_ids for t in index["artifact_to_tasks"].get(aid, [])))
        eligible = [t for t in tasks if ready_to_suggest(index, t)]
        card = {
            "source": relative, "line": hit["line"], "heading": hit["heading"],
            "sha256": hit["source_sha256"], "class": hit["source_class"],
            "excerpt": hit["excerpt"], "artifact_ids": art_ids[:3],
            "task_ids": tasks[:3], "unshown_task_refs": max(0, len(tasks)-3),
            "relationship": "LEXICAL_AND_EXPLICIT_REFERENCES_ONLY",
            "source_legal_authority": "NOT_VERIFIED"
        }
        if mode == "next":
            card["eligible_tasks_not_claimed"] = eligible[:3]
        cards.append(card)
    status = "NOT_VERIFIED_OFFICIAL_SOURCE" if mode == "normative" else "OK"
    base.update({"status": status, "retrieval": "SECTION_SEARCH_PLUS_TASK_GRAPH",
                 "search_mode": "FTS5_LEXICAL", "source_class_filter": selected_class,
                 "bytes_verified": result.get("source_byte_readback"),
                 "candidate_docs": len(cards),
                 "note": ("Documents returned as research leads only, not official normative evidence."
                          if mode == "normative" else
                          "Citation and task edges are preliminary; NO task claimed.")})
    return compact_fit(base, cards[:limit], max_chars)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--index", type=Path, required=True)
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--sections", type=Path)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--repo", default="dvikt33-ux/safe-bim-layer")
    parser.add_argument("--query", required=True)
    parser.add_argument("--mode", choices=("research", "next", "normative"), default="research")
    parser.add_argument("--source-class", choices=("ARCHIVED_SOURCE", "RESEARCH_RUN",
                                                   "PROJECT_CONTROL", "OTHER_DOCUMENT"))
    parser.add_argument("--limit", type=int, default=4)
    parser.add_argument("--max-chars", type=int, default=2500)
    a = parser.parse_args(argv)
    plan = json.loads(a.plan.read_text(encoding="utf-8"))
    index = json.loads(a.index.read_text(encoding="utf-8"))
    if not SID.search(a.query.upper()) and not ART.search(a.query.upper()):
        if a.sections is None or a.repo_root is None:
            parser.error("Free-text query requires --sections and --repo-root")
    result = retrieve(index, plan, a.sections, a.repo_root, a.repo, a.query,
                      a.mode, a.source_class, a.limit, a.max_chars)
    print(canonical(result))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(canonical({"status": "VALIDATION_ERROR", "reason": str(exc)}), file=sys.stderr)
        sys.exit(2)
