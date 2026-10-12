#!/usr/bin/env python3
"""APA read-only knowledge graph: exact task/artifact search and bounded change impact.

Stdlib only. Derived indexes are disposable; PROJECT_PLAN.json remains sole task authority.
No GitHub writes, model calls, Archicad writes or inferred normative compliance.
"""
from __future__ import annotations

import argparse
from collections import defaultdict, deque
import hashlib
import json
import re
from pathlib import Path
import sys

PROPAGATING = frozenset({"DERIVED_FROM", "USES_PARAMETER", "CONSTRAINED_BY"})
REVIEWS = frozenset({"PROPOSED", "UNVERIFIED", "REVIEW_REQUIRED"})
READY = frozenset({"READY", "PARTIAL"})


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def sorted_unique(values):
    return sorted(set(values))


def validate_plan(plan):
    if not isinstance(plan, dict) or not isinstance(plan.get("tasks"), dict) or not isinstance(plan.get("artifacts"), dict):
        raise ValueError("Expected a canonical APA plan with tasks and artifacts")
    tasks, artifacts = plan["tasks"], plan["artifacts"]
    for key, task in tasks.items():
        if key != task.get("id"):
            raise ValueError("Task key/id mismatch: " + key)
        for field in ("depends_on", "related"):
            for ref in task.get(field, []):
                if ref not in tasks:
                    raise ValueError("Dangling task reference: " + key + " -> " + ref)
        for field in ("inputs", "evidence"):
            for ref in task.get(field, []):
                if ref not in artifacts:
                    raise ValueError("Dangling artifact reference: " + key + " -> " + ref)
    return True


def build_index(plan):
    """Emit only a derived compact read-only index, with stable explicit relationships."""
    validate_plan(plan)
    tasks, artifacts = plan["tasks"], plan["artifacts"]
    output_tasks = {}
    by_artifact = defaultdict(set)
    downstream = defaultdict(set)
    for task_id, item in tasks.items():
        refs = sorted_unique(item.get("inputs", []) + item.get("evidence", []))
        for art in refs:
            by_artifact[art].add(task_id)
        for dep in item.get("depends_on", []):
            downstream[dep].add(task_id)
        output_tasks[task_id] = {
            "title": item.get("title", ""), "status": item.get("status"),
            "priority": item.get("priority", 99),
            "depends_on": sorted_unique(item.get("depends_on", [])),
            "related": sorted_unique(item.get("related", [])),
            "artifacts": refs,
            "owner": item.get("owner"), "claim_ref": item.get("claim_ref"),
            "requires_approval": bool(item.get("requires_approval", False))
        }
    return {
        "schema": "APA_KNOWLEDGE_GRAPH_INDEX_V1",
        "authority": "DERIVED_READ_ONLY",
        "plan_revision": plan.get("revision"),
        "plan_sha256": fingerprint(plan),
        "tasks": output_tasks,
        "artifacts": {key: {
            "uri": art.get("uri"), "kind": art.get("kind"),
            "verification": art.get("verification")
        } for key, art in sorted(artifacts.items())},
        "artifact_to_tasks": {key: sorted(v) for key, v in sorted(by_artifact.items())},
        "task_to_dependents": {key: sorted(v) for key, v in sorted(downstream.items())}
    }


def assert_index(index):
    if index.get("schema") != "APA_KNOWLEDGE_GRAPH_INDEX_V1" or index.get("authority") != "DERIVED_READ_ONLY":
        raise ValueError("Invalid or non-read-only derived index")


def bounded(items, maximum):
    if not isinstance(maximum, int) or maximum < 1:
        raise ValueError("limit must be positive")
    values = list(items)
    return values[:maximum], max(0, len(values) - maximum)


def task_card(index, task_id, include_artifacts=False):
    assert_index(index)
    task = index["tasks"].get(task_id)
    if task is None:
        return {"status": "NOT_FOUND", "id": task_id}
    out = {
        "id": task_id, "status": task["status"], "title": task["title"],
        "priority": task["priority"], "depends_on": task["depends_on"],
        "artifact_count": len(task["artifacts"])
    }
    if include_artifacts:
        out["artifacts"] = task["artifacts"]
    return out


def task_descendants(index, start, limit=50):
    assert_index(index)
    if start not in index["tasks"]:
        return {"status": "NOT_FOUND", "id": start}
    queue = deque([(start, 0)])
    seen = {start}
    found = []
    while queue:
        current, depth = queue.popleft()
        for dependent in index["task_to_dependents"].get(current, []):
            if dependent not in seen:
                seen.add(dependent)
                found.append({"id": dependent, "depth": depth + 1})
                queue.append((dependent, depth + 1))
    found.sort(key=lambda x: (x["depth"], x["id"]))
    selected, omitted = bounded(found, limit)
    return {"status": "OK", "source_task": start, "count": len(found), "results": selected,
            "omitted": omitted, "relation_kind": "SCHEDULING_ONLY_NOT_PROVEN_DATA_IMPACT"}


def artifact_impact(index, artifact_id, limit=20):
    """Document citation is a candidate ONLY, not proof that a changed value affects it."""
    assert_index(index)
    if artifact_id not in index["artifacts"]:
        return {"status": "NOT_FOUND", "artifact_id": artifact_id}
    targets = index["artifact_to_tasks"].get(artifact_id, [])
    results = [{"task_id": t, "title": index["tasks"][t]["title"],
                "status": index["tasks"][t]["status"],
                "impact": "POSSIBLE_IMPACT", "reason": "ARTIFACT_REFERENCE_ONLY"}
               for t in targets]
    selected, omitted = bounded(results, limit)
    return {"status": "OK", "artifact_id": artifact_id, "total_candidates": len(results),
            "results": selected, "omitted": omitted,
            "field_lineage_coverage": "UNKNOWN",
            "warning": "Artifact references and scheduling edges do not prove field-level impact"}


def validate_lineage(lineage, index):
    if not isinstance(lineage, dict) or lineage.get("schema") != "APA_FIELD_LINEAGE_V1":
        raise ValueError("Expected APA_FIELD_LINEAGE_V1")
    fields, edges = lineage.get("fields"), lineage.get("edges")
    if not isinstance(fields, dict) or not isinstance(edges, list):
        raise ValueError("Lineage requires fields object and edges array")
    seen = set()
    for field_id, field in fields.items():
        if not isinstance(field, dict) or not isinstance(field_id, str):
            raise ValueError("Invalid field")
        if not isinstance(field.get("project_class"), str) or not field["project_class"]:
            raise ValueError("Field requires explicit project_class: " + field_id)
        if field.get("task_id") and field["task_id"] not in index["tasks"]:
            raise ValueError("Unknown task in field: " + field_id)
    for edge in edges:
        if not isinstance(edge, dict) or not {"from", "to", "kind", "verification", "project_class"} <= edge.keys():
            raise ValueError("Incomplete edge")
        src, dst = edge["from"], edge["to"]
        if src not in fields or dst not in fields:
            raise ValueError("Edge refers to absent field")
        if edge["kind"] not in PROPAGATING | {"REFERENCES", "MENTIONS", "SUPERSEDES"}:
            raise ValueError("Unknown relation type")
        if edge["verification"] not in {"SOURCE_VERIFIED", "PROPOSED", "UNVERIFIED", "REVIEW_REQUIRED"}:
            raise ValueError("Unknown verification state")
        if edge["project_class"] != fields[src]["project_class"] or edge["project_class"] != fields[dst]["project_class"]:
            raise ValueError("Cross-class propagation prohibited without independently scoped rule")
        identity = (src, dst, edge["kind"])
        if identity in seen:
            raise ValueError("Duplicate lineage edge")
        seen.add(identity)
        if edge["verification"] == "SOURCE_VERIFIED":
            if not edge.get("source_revision") or not edge.get("evidence_uri"):
                raise ValueError("A verified edge requires source_revision and evidence_uri")
            if not isinstance(edge["source_revision"], str) or not re.fullmatch(r"(?:[a-f0-9]{40}|[a-f0-9]{64})", edge["source_revision"]):
                raise ValueError("Verified edge source_revision must be a pinned 40/64 hexadecimal digest")
    return True


def field_impact(index, lineage, change, limit=20):
    """Compare explicit values and traverse only verified, scope-matched typed edges.

    Never claims source correctness based on index text. No PLAN/PLN writes.
    """
    assert_index(index)
    validate_lineage(lineage, index)
    source = change.get("field_id")
    project_class = change.get("project_class")
    if not project_class:
        raise ValueError("Change must specify project_class")
    fields = lineage["fields"]
    if source not in fields:
        return {"status": "NOT_FOUND", "field_id": source}
    if fields[source]["project_class"] != project_class:
        return {"status": "SCOPE_MISMATCH", "field_id": source}
    if not ("before" in change and "after" in change):
        raise ValueError("Change must contain before and after")
    if change["before"] == change["after"]:
        return {"status": "NO_VALUE_CHANGE", "field_id": source, "verified_impacts": [],
                "review_required": []}
    adjacency = defaultdict(list)
    for e in lineage["edges"]:
        if e["project_class"] == project_class:
            adjacency[e["from"]].append(e)
    visited = {source}
    queue = deque([source])
    proven = []
    review = []
    review_ids = set()
    while queue:
        current = queue.popleft()
        for edge in sorted(adjacency.get(current, []), key=lambda e: (e["to"], e["kind"])):
            dest = edge["to"]
            if edge["kind"] in PROPAGATING and edge["verification"] == "SOURCE_VERIFIED":
                if dest not in visited:
                    visited.add(dest)
                    proven.append({"field_id": dest, "via": current,
                                   "kind": edge["kind"], "task_id": fields[dest].get("task_id"),
                                   "decision": "RECHECK_OR_RECOMPUTE",
                                   "evidence_uri": edge["evidence_uri"]})
                    queue.append(dest)
            else:
                token = (current, dest, edge["kind"])
                if token not in review_ids:
                    review_ids.add(token)
                    review.append({"field_id": dest, "via": current, "kind": edge["kind"],
                                   "task_id": fields[dest].get("task_id"),
                                   "decision": "REVIEW_REQUIRED"})
    proven.sort(key=lambda r: (r["field_id"], r["via"]))
    review.sort(key=lambda r: (r["field_id"], r["via"]))
    selected, omitted = bounded(proven, limit)
    review_selected, review_omitted = bounded(review, limit)
    eligible = []
    for item in proven:
        sid = item["task_id"]
        if not sid:
            continue
        task = index["tasks"][sid]
        if (task["status"] in READY and not task["owner"] and not task["claim_ref"]
                and not task["requires_approval"]
                and all(index["tasks"][d]["status"] == "DONE_PUBLISHED" for d in task["depends_on"])):
            eligible.append(sid)
    return {
        "status": "IMPACT_REVIEW_REQUIRED",
        "changed_field": source, "project_class": project_class,
        "verified_relation_count": len(proven),
        "verified_impacts": selected, "omitted_verified": omitted,
        "review_required_count": len(review), "review_required": review_selected,
        "omitted_review": review_omitted,
        "potential_next_tasks_not_claimed": sorted_unique(eligible),
        "no_impact_proven": False,
        "runtime_evidence_readback": "NOT_PERFORMED",
        "warning": "Edges are declared verified by input, NOT independently read back during this query; unregistered dependencies remain UNKNOWN"
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "task", "artifact", "descendants", "field-impact"))
    parser.add_argument("--plan", type=Path)
    parser.add_argument("--index", type=Path)
    parser.add_argument("--verify-plan", type=Path,
                        help="Reject query if index hash differs from current canonical plan")
    parser.add_argument("--out", type=Path)
    parser.add_argument("--id")
    parser.add_argument("--lineage", type=Path)
    parser.add_argument("--change", type=Path)
    parser.add_argument("--limit", type=int, default=20)
    args = parser.parse_args(argv)
    if args.command == "build":
        if not args.plan:
            parser.error("build requires --plan")
        plan = json.loads(args.plan.read_text(encoding="utf-8"))
        result = build_index(plan)
        # Only explicit --out writes a disposable derived file, never the source plan.
        if args.out:
            target = args.out.resolve()
            if target == args.plan.resolve():
                parser.error("--out may not overwrite --plan")
            if target.exists():
                parser.error("--out must be a fresh disposable file (refusing overwrite)")
            target.write_text(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
            print(canonical({"status": "DERIVED_INDEX_WRITTEN", "path": str(target),
                             "tasks": len(result["tasks"]), "artifacts": len(result["artifacts"]),
                             "plan_revision": result["plan_revision"], "plan_sha256": result["plan_sha256"]}))
            return 0
    else:
        if not args.index:
            parser.error("query requires --index")
        index = json.loads(args.index.read_text(encoding="utf-8"))
        assert_index(index)
        if args.verify_plan:
            latest_plan = json.loads(args.verify_plan.read_text(encoding="utf-8"))
            if fingerprint(latest_plan) != index["plan_sha256"]:
                raise ValueError("STALE_INDEX: plan changed; rebuild before querying")
        if args.command == "task":
            result = task_card(index, args.id)
        elif args.command == "artifact":
            result = artifact_impact(index, args.id, args.limit)
        elif args.command == "descendants":
            result = task_descendants(index, args.id, args.limit)
        else:
            if not args.lineage or not args.change:
                parser.error("field-impact requires --lineage and --change")
            result = field_impact(index, json.loads(args.lineage.read_text(encoding="utf-8")),
                                  json.loads(args.change.read_text(encoding="utf-8")), args.limit)
    print(canonical(result))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        print(canonical({"status": "VALIDATION_ERROR", "reason": str(exc)}), file=sys.stderr)
        sys.exit(2)
