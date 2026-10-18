"""Explicit source-only geometry sidecar; reuses existing tested B2 runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

HERE = Path(__file__).resolve().parent
EXTERNAL = Path(r"C:\LocalAI\APA_AC29_Stable\external-tools")
TARGET = EXTERNAL / "apa-ifc-geometry-b3"
FILES = ("apa_ifc_geometry_b3.py", "apa_ifc_geometry_factory_b3.py",
         "apa_ifc_artifacts_b2.py", "apa_high_density_readonly_v2.py")


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def preflight():
    base = EXTERNAL / "apa-dxf-geometry-c1/apa_dxf_geometry_factory_c1.py"
    if TARGET.exists() or not base.is_file() or not all((HERE / name).is_file() for name in FILES):
        raise ValueError("B3_NEW_TARGET_INSTALLED_C1_AND_SOURCES_REQUIRED")
    return {"schema": "APA_IFC_GEOMETRY_INSTALL_B3", "targetWasAbsent": True,
            "baseFactorySHA256": sha(base), "sourceSHA256": {name: sha(HERE / name) for name in FILES},
            "nativeCalls": 0, "plnWrites": 0,
            "rollback": "Quarantine only the new B3 directory; existing files are untouched"}


def check():
    record = json.loads((TARGET / "installation-b3.json").read_text(encoding="utf8"))
    if any(sha(TARGET / name) != digest for name, digest in record["sourceSHA256"].items()):
        raise ValueError("B3_INSTALLED_SOURCE_DRIFT")
    return record


def install():
    record = preflight()
    with tempfile.TemporaryDirectory(prefix=".b3-stage-", dir=EXTERNAL) as tmp:
        stage = Path(tmp)
        for name in FILES:
            shutil.copy2(HERE / name, stage / name)
        if any(sha(stage / name) != digest for name, digest in record["sourceSHA256"].items()):
            raise ValueError("B3_STAGE_SOURCE_DRIFT")
        record["status"] = "INSTALLED_OPT_IN"
        (stage / "installation-b3.json").write_text(json.dumps(record, indent=2), encoding="utf8")
        if TARGET.exists():
            raise ValueError("B3_TARGET_CONFLICT")
        stage.rename(TARGET)
    return check()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(preflight() if args.preflight else check() if args.check else install(), indent=2))
