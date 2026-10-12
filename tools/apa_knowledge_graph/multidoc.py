#!/usr/bin/env python3
"""APA token-bounded multi-document join over authoritative artifact/task references.

This joins existing artifact IDs to their citing tasks. It never pretends those
references are semantic field-level dependencies or norm compliance evidence.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from graph import assert_index, canonical


def document_bundle(index, artifact_ids, max_tasks=12):
    assert_index(index)
    if not isinstance(artifact_ids, list) or not 1 <= len(artifact_ids) <= 16:
        raise ValueError("Supply 1-16 artifact IDs")
    if not isinstance(max_tasks, int) or max_tasks < 1:
        raise ValueError("max_tasks must be positive")
    ids = sorted(set(artifact_ids))
    missing = [aid for aid in ids if aid not in index["artifacts"]]
    if missing:
        return {"status": "NOT_FOUND", "missing": missing}
    membership = {}
    for aid in ids:
        for tid in index["artifact_to_tasks"].get(aid, []):
            membership.setdefault(tid, set()).add(aid)
    joined = sorted(membership.items(), key=lambda kv: (-len(kv[1]), kv[0]))
    hit_cards = []
    for tid, referenced in joined[:max_tasks]:
        task = index["tasks"][tid]
        hit_cards.append({
            "task_id": tid, "title": task["title"], "status": task["status"],
            "shared_artifact_count": len(referenced),
            "artifacts": sorted(referenced), "relationship": "CITES_ARTIFACT_ONLY"
        })
    missing_revisions = []
    source_cards = []
    for aid in ids:
        art = index["artifacts"][aid]
        uri = art.get("uri") or ""
        # No guarantee that a link to a branch or file is immutable.
        immutable = bool(("blob/" in uri and "/blob/" in uri and
                          any(len(part) == 40 and all(c in "0123456789abcdef" for c in part.lower())
                              for part in uri.split("/")))
                         or uri.startswith("sha256:"))
        if not immutable:
            missing_revisions.append(aid)
        source_cards.append({"id": aid, "uri": uri, "verification": art.get("verification"),
                             "revision": "PINNED_URI" if immutable else "UNPINNED_OR_UNVERIFIED_URI"})
    return {
        "status": "OK",
        "source_artifacts": source_cards,
        "tasks_with_any_reference": len(joined),
        "tasks_referencing_all": sum(len(s) == len(ids) for _, s in joined),
        "tasks": hit_cards,
        "omitted_task_count": max(0, len(joined) - max_tasks),
        "source_revision_warnings": missing_revisions,
        "verification": "REFERENCES_ONLY_NOT_FIELD_LINEAGE",
        "next_action": "Check exact clauses/fields and independently validated lineage before declaring impact"
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--index", type=Path, required=True)
    p.add_argument("--artifacts", nargs="+", required=True)
    p.add_argument("--max-tasks", type=int, default=12)
    args = p.parse_args(argv)
    index = json.loads(args.index.read_text(encoding="utf-8"))
    print(canonical(document_bundle(index, args.artifacts, args.max_tasks)))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError) as exc:
        print(canonical({"status": "VALIDATION_ERROR", "reason": str(exc)}), file=sys.stderr)
        sys.exit(2)
