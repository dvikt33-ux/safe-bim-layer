#!/usr/bin/env python3
"""APA read-only incremental change detector for canonical plan and field snapshots."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from graph import build_index, artifact_impact, field_impact, canonical, fingerprint, configure_stdio


def compact_value(value, cap=100):
    text = canonical(value)
    if len(text) <= cap:
        return value
    return {"sha256": fingerprint(value), "omitted_length": len(text), "value": "TOO_LONG"}


def compare_plans(before, after, limit=20):
    """A diff of authoritative records; outputs possible impact, never status writes."""
    if limit < 1:
        raise ValueError("limit must be positive")
    old = build_index(before)
    new = build_index(after)
    if old["plan_sha256"] == new["plan_sha256"]:
        return {"status": "UNCHANGED", "old_revision": old["plan_revision"],
                "new_revision": new["plan_revision"], "changes": []}
    changes = []
    for kind in ("artifacts", "tasks"):
        old_records, new_records = old[kind], new[kind]
        for rec_id in sorted(old_records.keys() | new_records.keys()):
            a, b = old_records.get(rec_id), new_records.get(rec_id)
            if a == b:
                continue
            if a is None:
                fields = ["ADDED"]
            elif b is None:
                fields = ["REMOVED"]
            else:
                fields = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
            record = {"kind": kind, "id": rec_id, "changed_fields": fields}
            if kind == "artifacts":
                # Include tasks referencing either version: source may have been removed.
                sources = set(old["artifact_to_tasks"].get(rec_id, [])) | set(new["artifact_to_tasks"].get(rec_id, []))
                record["possibly_affected_tasks"] = sorted(sources)
                record["impact_kind"] = "REFERENCE_CANDIDATES_NOT_PROVEN"
            else:
                dep = set(old["task_to_dependents"].get(rec_id, [])) | set(new["task_to_dependents"].get(rec_id, []))
                record["scheduling_dependents"] = sorted(dep)
                record["impact_kind"] = "SCHEDULING_ONLY_NOT_SEMANTIC_IMPACT"
            changes.append(record)
    selected = changes[:limit]
    return {
        "status": "CHANGE_CANDIDATES_ONLY",
        "old_revision": old["plan_revision"], "new_revision": new["plan_revision"],
        "old_plan_hash": old["plan_sha256"], "new_plan_hash": new["plan_sha256"],
        "total_changed_records": len(changes),
        "changes": selected, "omitted": len(changes) - len(selected),
        "warning": "Changes do not automatically invalidate prior approvals, tests or norm compliance"
    }


def compare_field_snapshots(index, lineage, before, after, limit=10):
    """Evaluate changed concrete fields, using only explicitly verified dependency edges."""
    if not isinstance(before, dict) or not isinstance(after, dict):
        raise ValueError("Field snapshots must be JSON objects")
    if before.get("schema") != "APA_FIELD_VALUES_V1" or after.get("schema") != "APA_FIELD_VALUES_V1":
        raise ValueError("Snapshots must be APA_FIELD_VALUES_V1")
    old, new = before.get("values"), after.get("values")
    if not isinstance(old, dict) or not isinstance(new, dict):
        raise ValueError("Snapshot values must be objects")
    if set(old) != set(new):
        return {"status": "COVERAGE_CHANGED", "missing_in_before": sorted(set(new)-set(old)),
                "missing_in_after": sorted(set(old)-set(new)), "impacts": []}
    changed = [k for k in sorted(old) if old[k] != new[k]]
    impacts = []
    for fid in changed[:limit]:
        fld = lineage.get("fields", {}).get(fid)
        if not fld:
            impacts.append({"field_id": fid, "status": "FIELD_NOT_IN_LINEAGE",
                            "decision": "REVIEW_REQUIRED"})
            continue
        change = {"field_id": fid, "project_class": fld["project_class"],
                  "before": old[fid], "after": new[fid]}
        impact = field_impact(index, lineage, change, limit=limit)
        impacts.append({"field_id": fid, "before": compact_value(old[fid]),
                        "after": compact_value(new[fid]), "impact": impact})
    return {"status": "CHANGED" if changed else "UNCHANGED", "total_changed_fields": len(changed),
            "impacts": impacts, "omitted": max(0, len(changed)-limit),
            "warning": "Unregistered or unvalidated dependencies remain UNKNOWN"}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("plan", "fields"))
    p.add_argument("--before", type=Path, required=True)
    p.add_argument("--after", type=Path, required=True)
    p.add_argument("--index", type=Path)
    p.add_argument("--lineage", type=Path)
    p.add_argument("--limit", type=int, default=10)
    a = p.parse_args(argv)
    old = json.loads(a.before.read_text(encoding="utf-8"))
    new = json.loads(a.after.read_text(encoding="utf-8"))
    if a.mode == "plan":
        result = compare_plans(old, new, a.limit)
    else:
        if not a.lineage or not a.index:
            p.error("fields requires --lineage and --index")
        ix = json.loads(a.index.read_text(encoding="utf-8"))
        lineage = json.loads(a.lineage.read_text(encoding="utf-8"))
        result = compare_field_snapshots(ix, lineage, old, new, a.limit)
    print(canonical(result))


if __name__ == "__main__":
    configure_stdio()
    try:
        main()
    except (ValueError, KeyError) as exc:
        print(canonical({"status": "VALIDATION_ERROR", "reason": str(exc)}), file=sys.stderr)
        sys.exit(2)
