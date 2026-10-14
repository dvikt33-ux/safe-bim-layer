"""Offline audit of all tracked Python and JSON source files (no Archicad runtime).

Runs entirely on GitHub's isolated runner. Malformed tracked files are reported
as failures with paths, never silently excluded or counted as parsed.
"""
from __future__ import annotations
import ast
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

def tracked(pattern):
    proc = subprocess.run(["git", "ls-files", "-z", "--", pattern], check=True, stdout=subprocess.PIPE)
    return [Path(p.decode("utf8")) for p in proc.stdout.split(b"\x00") if p]

def main():
    counts = Counter()
    issues = []
    digests = {}
    for suffix, syntax in [("*.py","python"),("*.json","json")]:
        for file in tracked(suffix):
            counts[syntax + ".tracked"] += 1
            try:
                payload = file.read_text(encoding="utf-8-sig")
                if syntax == "python":
                    ast.parse(payload, filename=str(file))
                else:
                    json.loads(payload)
                counts[syntax + ".parsed"] += 1
            except Exception as exc:
                issues.append({"path":str(file), "kind":syntax, "error":repr(exc)})
    # Audit test coverage inventory independently of any test result claims.
    paths = tracked("tests/test_*.py")
    counts["test_files.tracked"] = len(paths)
    print("APA_STATIC_AUDIT " + json.dumps({"counts":counts, "issues":issues[:100]},ensure_ascii=False))
    out = Path("reports/static-tracked-file-audit.json")
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps({"schema":"APA_REPO_STATIC_V1","counts":counts,"issues":issues},ensure_ascii=False,indent=2),encoding="utf8")
    return 1 if issues else 0

if __name__=="__main__":
    sys.exit(main())
