"""Deterministic bounded shard execution; no Archicad connection or PLN writes."""
from __future__ import annotations
import argparse
import ast
import json
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def modules():
    return sorted((ROOT / "tests").glob("test_*.py")) + sorted((ROOT / "scripts").glob("test_*.py"))


def weight(path):
    if path.name.startswith("test_apa_graph_matrix_"):
        return 128  # Two parametrized functions * 64 distinct topology masks.
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    return max(1, sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                      and n.name.startswith("test_") for n in ast.walk(tree)))


def partition(files, shards):
    bins = [[] for _ in range(shards)]
    totals = [0] * shards
    for path in sorted(files, key=lambda p: (-weight(p), str(p))):
        idx = min(range(shards), key=lambda k: (totals[k], len(bins[k]), k))
        bins[idx].append(path)
        totals[idx] += weight(path)
    return bins, totals


def run(args):
    files = modules()
    if not files:
        raise SystemExit("No offline tests discovered")
    bins, totals = partition(files, args.shards)
    if not (0 <= args.shard < args.shards):
        raise SystemExit("Invalid shard")
    selected = bins[args.shard]
    if not selected:
        raise SystemExit("Empty shard: decrease --shards")
    out = Path(args.artifacts) / ("shard-" + str(args.shard))
    out.mkdir(parents=True, exist_ok=True)
    junit = out / "junit.xml"
    cmd = [sys.executable, "-m", "pytest", "-q", "--tb=short",
           "-p", "no:cacheprovider", "-n", str(args.workers),
           "--dist=loadfile", "--junitxml=" + str(junit)]
    cmd += [str(p.relative_to(ROOT)) for p in selected]
    manifest = {"shard": args.shard, "shards": args.shards,
                "workers": args.workers,
                "moduleCount": len(selected),
                "weightEstimate": totals[args.shard],
                "modules": [str(p.relative_to(ROOT)) for p in selected],
                "command": cmd, "status": "STARTED"}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    started = time.monotonic()
    try:
        process = subprocess.run(cmd, cwd=ROOT, check=False)
        code = process.returncode
    except OSError as exc:
        code = 127
        manifest["launchError"] = repr(exc)
    manifest.update(status="PASS" if code == 0 and junit.is_file() else "FAIL_OR_NO_REPORT",
                    exitCode=code, elapsedSeconds=round(time.monotonic() - started, 3),
                    junitExists=junit.is_file())
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return code or (0 if junit.is_file() else 2)


def summarize(args):
    root = Path(args.artifacts)
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0, "time": 0.0}
    rows, missing = [], []
    for shard in range(args.shards):
        folder = root / ("apa-offline-shard-" + str(shard))
        report = folder / "junit.xml"
        manifest = folder / "manifest.json"
        if not report.is_file() or not manifest.is_file():
            missing.append(shard)
            continue
        info = json.loads(manifest.read_text(encoding="utf-8"))
        tree = ET.parse(report)
        xml = tree.getroot()
        suite = xml if xml.tag == "testsuite" else xml.find("testsuite")
        if suite is None:
            missing.append(shard)
            continue
        counts = {k: float(suite.attrib.get(k, 0)) if k == "time"
                  else int(suite.attrib.get(k, 0)) for k in totals}
        for k in totals:
            totals[k] += counts[k]
        rows.append({"shard": shard, "exitCode": info["exitCode"],
                     "status": info["status"], **counts})
    totals["tests"] = int(totals["tests"])
    summary = {"schema": "APA_OFFLINE_MATRIX_RESULT_V1",
               "expectedShards": args.shards, "collectedShards": len(rows),
               "missingShards": missing, "totals": totals, "shards": rows,
               "status": "PASS" if not missing and all(r["exitCode"] == 0 for r in rows)
               and totals["failures"] == totals["errors"] == 0 else "FAIL_OR_INCOMPLETE",
               "evidence": "GitHub Actions JUnit + per-shard manifests; no Archicad LIVE assertions"}
    Path("apa-offline-summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0 if summary["status"] == "PASS" else 1


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--shard", type=int, default=-1)
    parser.add_argument("--shards", type=int, default=12)
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--artifacts", default="offline-artifacts")
    parser.add_argument("--summarize", action="store_true")
    args = parser.parse_args()
    if not (1 <= args.shards <= 32 and 1 <= args.workers <= 4):
        parser.error("Bound concurrency: 1..32 shards, 1..4 workers")
    return summarize(args) if args.summarize else run(args)


if __name__ == "__main__":
    sys.exit(main())
