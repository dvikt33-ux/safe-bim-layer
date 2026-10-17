"""One-time, fail-closed upgrade of ONLY installed external read-only IFC adapter.

No changes to core APA, model, PLN, SDK, dispatcher, packages or venv.
Enforces precisely the one reviewed IfcClash mode/tolerance fix, verifies the
installed hashes, leaves an audit backup, and refuses blind retries.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
FOLDER = ROOT / "external-tools" / "apa-readonly-v1"
SRC = Path(__file__).resolve().with_name("apa_external_readonly.py")
BACKUP = FOLDER / "upgrade-ifcclash-intersection-v1"
OLD = '''spec = [{"name": "APA_SOURCE_QUALIFIED_CLASH_SET",
                 "a": [{"file": str(a)}]}]'''
NEW = '''spec = [{"name": "APA_SOURCE_QUALIFIED_CLASH_SET",
                 "mode": "intersection", "tolerance": 0.001,
                 "check_all": False, "a": [{"file": str(a)}]}]'''


def require(value, reason):
    if not value:
        raise ValueError(reason)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def review():
    installed = FOLDER / "apa_external_readonly.py"
    manifest_path = FOLDER / "installation.json"
    require(installed.is_file() and manifest_path.is_file() and SRC.is_file(),
            "SOURCE_OR_ISOLATED_INSTALL_NOT_FOUND")
    old_bytes = installed.read_bytes()
    new_bytes = SRC.read_bytes()
    receipt_bytes = manifest_path.read_bytes()
    manifest = json.loads(receipt_bytes.decode("utf-8"))
    require(manifest.get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1"
            and manifest.get("status") == "EXTERNAL_READONLY_INSTALLED_READY"
            and manifest.get("adapterSHA256") == sha(old_bytes),
            "INSTALLED_ADAPTER_HASH_OR_RECEIPT_DRIFT")
    for name, key in (("apa_external_catalog.py", "catalogSHA256"),
                      ("requirements-external-readonly.txt", "requirementsSHA256")):
        p = FOLDER / name
        require(p.is_file() and sha(p.read_bytes()) == manifest[key],
                "INSTALLED_SIDECAR_DRIFT:" + name)
    require(old_bytes != new_bytes, "ALREADY_UPGRADED_RUN_CHECK")
    new_text = new_bytes.decode("utf-8")
    old_text = old_bytes.decode("utf-8")
    require(new_text.count(NEW) == 1 and
            new_text.replace(NEW, OLD, 1) == old_text,
            "SOURCE_DIFF_OUTSIDE_REVIEWED_IFCCLASH_FIX")
    require(not BACKUP.exists(), "UPGRADE_BACKUP_ALREADY_EXISTS_AUDIT_REQUIRED")
    require((FOLDER / "venv" / "Scripts" / "python.exe").is_file(),
            "ISOLATED_PYTHON_MISSING")
    return dict(installed=installed, manifest_path=manifest_path,
                old_bytes=old_bytes, new_bytes=new_bytes,
                receipt_bytes=receipt_bytes, receipt=manifest)


def upgrade():
    state = review()
    BACKUP.mkdir(exist_ok=False)
    saved_old = BACKUP / "apa_external_readonly.py.original"
    saved_receipt = BACKUP / "installation.json.original"
    with saved_old.open("xb") as f:
        f.write(state["old_bytes"])
    with saved_receipt.open("xb") as f:
        f.write(state["receipt_bytes"])
    updated = dict(state["receipt"])
    updated["adapterSHA256"] = sha(state["new_bytes"])
    updated["clashIntersectionUpgrade"] = {
        "status": "APPLIED_READ_ONLY_ADAPTER_PATCH",
        "originalAdapterSHA256": sha(state["old_bytes"]),
        "updatedAdapterSHA256": sha(state["new_bytes"]),
        "nativeCalls": 0,
        "plnWrites": 0
    }
    stage_py = FOLDER / "apa_external_readonly.py.upgrade-next"
    stage_receipt = FOLDER / "installation.json.upgrade-next"
    require(not stage_py.exists() and not stage_receipt.exists(),
            "PENDING_UPGRADE_STAGE_ALREADY_EXISTS")
    try:
        with stage_py.open("xb") as f:
            f.write(state["new_bytes"])
        with stage_receipt.open("x", encoding="utf-8") as f:
            json.dump(updated, f, indent=2, ensure_ascii=False)
            f.write("\n")
        compile(state["new_bytes"], str(state["installed"]), "exec")
        os.replace(stage_py, state["installed"])
        os.replace(stage_receipt, state["manifest_path"])
        py = FOLDER / "venv" / "Scripts" / "python.exe"
        check = subprocess.run([str(py), str(state["installed"]), "doctor"],
                               capture_output=True, text=True, timeout=90)
        require(check.returncode == 0, "UPDATED_ADAPTER_DOCTOR_BLOCKED:"
                + check.stderr[-300:])
        require(sha(state["installed"].read_bytes()) == updated["adapterSHA256"],
                "UPDATED_ADAPTER_HASH_DRIFT")
    except BaseException:
        # Roll back from untouched byte snapshots, not from external code.
        rollback_py = FOLDER / "apa_external_readonly.py.rollback-next"
        rollback_receipt = FOLDER / "installation.json.rollback-next"
        rollback_py.write_bytes(state["old_bytes"])
        rollback_receipt.write_bytes(state["receipt_bytes"])
        os.replace(rollback_py, state["installed"])
        os.replace(rollback_receipt, state["manifest_path"])
        raise
    finally:
        for temp in (stage_py, stage_receipt):
            if temp.exists():
                temp.unlink()
    return {
        "status": "EXTERNAL_READONLY_IFCCLASH_ADAPTER_UPGRADED",
        "installedSHA256": updated["adapterSHA256"],
        "backupDirectory": str(BACKUP),
        "pythonPackagesChanged": False,
        "coreFilesChanged": False,
        "modelWrites": 0,
        "archicadNativeCalls": 0}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--apply", action="store_true")
    opts = p.parse_args(argv)
    if opts.apply:
        print(json.dumps(upgrade(), ensure_ascii=False, indent=2))
    else:
        s = review()
        print(json.dumps({"status": "UPGRADE_PREFLIGHT_PASS_NO_CHANGES",
                          "originalSHA256": sha(s["old_bytes"]),
                          "targetSHA256": sha(s["new_bytes"]),
                          "modelWrites": 0}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_STATUS: EXTERNAL_READONLY_UPGRADE_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
