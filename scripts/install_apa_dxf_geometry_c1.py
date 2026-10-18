"""Source-only C1 sidecar install; existing vendors/core remain in place."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
EXTERNAL = Path(r"C:\LocalAI\APA_AC29_Stable\external-tools")
TARGET = EXTERNAL / "apa-dxf-geometry-c1"
FILES = ("apa_dxf_geometry_c1.py", "apa_dxf_geometry_factory_c1.py", "apa_high_density_readonly_v2.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preflight():
    base = EXTERNAL / "apa-ifc-artifacts-b2/apa_ifc_artifacts_factory_b2.py"
    if TARGET.exists() or not base.is_file() or not all((HERE / name).is_file() for name in FILES):
        raise ValueError("C1_NEW_TARGET_INSTALLED_B2_AND_SOURCE_REQUIRED")
    return {"schema": "APA_DXF_GEOMETRY_INSTALL_C1", "targetWasAbsent": True,
            "baseFactorySHA256": sha(base), "sourceSHA256": {name: sha(HERE / name) for name in FILES},
            "rollback": "Quarantine only the new C1 folder; no existing files are changed",
            "nativeCalls": 0, "plnWrites": 0}


def check():
    record = json.loads((TARGET / "installation-c1.json").read_text(encoding="utf8"))
    if any(sha(TARGET / name) != digest for name, digest in record["sourceSHA256"].items()):
        raise ValueError("C1_INSTALLED_SOURCE_DRIFT")
    return record


def install():
    record = preflight()
    with tempfile.TemporaryDirectory(prefix=".c1-stage-", dir=EXTERNAL) as temp:
        stage = Path(temp)
        for name in FILES:
            shutil.copy2(HERE / name, stage / name)
        if any(sha(stage / name) != digest for name, digest in record["sourceSHA256"].items()):
            raise ValueError("C1_STAGED_SOURCE_DRIFT")
        record["status"] = "INSTALLED_OPT_IN"
        (stage / "installation-c1.json").write_text(json.dumps(record, indent=2), encoding="utf8")
        if TARGET.exists():
            raise ValueError("C1_TARGET_CONFLICT")
        stage.rename(TARGET)
    return check()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--preflight", action="store_true")
    group.add_argument("--install", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(preflight() if args.preflight else check() if args.check else install(), indent=2))
