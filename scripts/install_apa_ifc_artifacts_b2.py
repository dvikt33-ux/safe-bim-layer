"""Explicit new B1+B2 sidecar deployment, dependency lock, no core overwrite."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
TARGET = STABLE / "external-tools/apa-ifc-artifacts-b2"
FILES = ("apa_ifc_reports_b1.py", "apa_ifc_artifacts_b2.py", "apa_ifc_artifacts_factory_b2.py",
         "apa_high_density_readonly_v2.py", "requirements-ifc-artifacts-b2-lock.txt")


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def preflight():
    v2 = STABLE / "external-tools/apa-readonly-v2/apa_high_density_session_factory_v2.py"
    if TARGET.exists() or not v2.is_file() or not all((HERE / name).is_file() for name in FILES):
        raise ValueError("B2_NEW_TARGET_VERIFIED_V2_AND_SOURCES_REQUIRED")
    return {"targetWasAbsent": True, "v2FactorySHA256": sha(v2),
            "sourceSHA256": {name: sha(HERE / name) for name in FILES}}


def check():
    record = json.loads((TARGET / "installation-b2.json").read_text(encoding="utf8"))
    if any(sha(TARGET / name) != digest for name, digest in record["sourceSHA256"].items()):
        raise ValueError("B2_INSTALLED_SOURCE_DRIFT")
    return record


def install():
    record = preflight()
    TARGET.mkdir(exist_ok=False)
    try:
        for name in FILES:
            shutil.copy2(HERE / name, TARGET / name)
        subprocess.run([sys.executable, "-m", "venv", str(TARGET / "venv")], check=True)
        python = TARGET / "venv/Scripts/python.exe"
        subprocess.run([str(python), "-m", "pip", "install", "-r",
                        str(TARGET / "requirements-ifc-artifacts-b2-lock.txt")], check=True)
        doctor = subprocess.run([str(python), "-B", "-c",
            "import importlib.metadata as m,json; print(json.dumps({p:m.version(p) for p in "
            "['ifcopenshell','ifccsv','ifcpatch','bcf-client','ifctester','ezdxf']}))"],
            check=True, capture_output=True, text=True)
        vendors = json.loads(doctor.stdout)
        if vendors != {"ifcopenshell": "0.8.5", "ifccsv": "0.8.5", "ifcpatch": "0.8.5",
                       "bcf-client": "0.8.5", "ifctester": "0.8.5", "ezdxf": "1.4.5"}:
            raise ValueError("B2_VENDOR_DOCTOR_MISMATCH")
        record.update(schema="APA_IFC_ARTIFACTS_INSTALL_B2", status="INSTALLED_OPT_IN",
                      vendors=vendors, nativeCalls=0, plnWrites=0,
                      rollback="Quarantine only this new sidecar; original APA files were not changed")
        with (TARGET / "installation-b2.json").open("x", encoding="utf8") as stream:
            json.dump(record, stream, indent=2)
        return check()
    except Exception:
        # Fresh target only. Preserve failed deployment for diagnosis, deactivate it.
        TARGET.rename(TARGET.with_name(TARGET.name + "-failed-" + uuid.uuid4().hex[:8]))
        raise


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--preflight", action="store_true")
    mode.add_argument("--install", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    print(json.dumps(preflight() if args.preflight else check() if args.check else install(), indent=2))
