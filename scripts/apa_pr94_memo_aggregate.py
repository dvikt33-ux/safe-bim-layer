"""Cross-shard accounting: reject missing/duplicated/uncovered tests.

Reads Windows CI artifacts, not user workstation files. Reports failure even
when a suite shard failed, so all discovered tests have auditable results.
"""
from __future__ import annotations
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--reports-dir",type=Path,required=True)
    p.add_argument("--shards",type=int,required=True)
    args=p.parse_args()
    reports=[]
    issues=[]
    for idx in range(args.shards):
        f=args.reports_dir/f"shard-{idx}.json"
        if not f.exists():
            issues.append(f"missing artifact {f}")
            continue
        try: reports.append(json.loads(f.read_text(encoding="utf8")))
        except Exception as exc: issues.append(f"invalid artifact {f}: {exc!r}")
    if reports:
        discovered={r.get("totalDiscovered") for r in reports}
        fingerprints={r.get("suiteSHA256") for r in reports}
        if len(discovered)!=1 or len(fingerprints)!=1:
            issues.append(f"inconsistent discovery counts/hashes: {discovered} / {fingerprints}")
        all_ids=[x for r in reports for x in r.get("assignedTestIDs",[])]
        dup=[tid for tid,n in Counter(all_ids).items() if n!=1]
        if dup:issues.append(f"duplicate test executions: {dup[:30]}")
        if len(discovered)==1 and len(all_ids)!=next(iter(discovered)):
            issues.append(f"coverage mismatch: executed IDs={len(all_ids)}, discovered={next(iter(discovered))}")
        if any(r.get("testsRun")!=r.get("assigned") for r in reports):
            issues.append("assigned test count differs from runner results")
        if any(not r.get("successful") for r in reports):issues.append("one or more unittest shards FAILED")
    metrics={k:sum((len(r.get(k,[])) if isinstance(r.get(k),list) else r.get(k,0)) for r in reports) for k in ("testsRun","failures","errors","skipped","expectedFailures","unexpectedSuccesses")}
    output={"schema":"APA_PARALLEL_OFFLINE_AGGREGATE_V1","shardsExpected":args.shards,"shardsFound":len(reports),"suiteSHA256":reports[0].get("suiteSHA256") if reports else None,"discoveredTests":reports[0].get("totalDiscovered") if reports else None,"metrics":metrics,"issues":issues,"shards":[{"id":r.get("shard"),"testsRun":r.get("testsRun"),"failures":len(r.get("failures",[])),"errors":len(r.get("errors",[])),"skipped":len(r.get("skipped",[])),"expectedFailures":len(r.get("expectedFailures",[])),"unexpectedSuccesses":len(r.get("unexpectedSuccesses",[])),"success":r.get("successful")} for r in reports]}
    out=Path("reports/full-offline-aggregate.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,indent=2,ensure_ascii=False),encoding="utf8")
    print("APA_PARALLEL_AGGREGATE " + json.dumps(output,ensure_ascii=False))
    return 0 if not issues else 1

if __name__=="__main__":sys.exit(main())
