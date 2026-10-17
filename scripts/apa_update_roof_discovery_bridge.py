"""Update ONLY the already-installed Unified Discovery sidecar (PR #132 -> roof bridge).

No native calls, no PLN access, no DynamicCommands/core replacement.
Pinned source blob, expected local file SHA, backup, rollback, import smoke.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

OLD_MODULE_SHA256 = "d3af7643edd3d0af8f966d7ae23b58d7d6f0112f283786621c2300ad4dc1d0bb"
CORE_SHA256 = "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b"
DYNAMIC_SHA256 = "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8"
NEW_GITHUB_BLOB_SHA1 = "2fee289b0be28de5539eeb7a4ae89243058764eb"
SCHEMA = "APA_UNIFIED_DISCOVERY_ROOF_BRIDGE_UPDATE_V1"


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()


def atomic(path, data):
    fd, staging = tempfile.mkstemp(prefix=".apa-roof-bridge-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(staging, path)
    finally:
        if os.path.exists(staging):
            os.unlink(staging)


def rollback(root, receipt_path):
    root = Path(root).resolve()
    receipt_path = Path(receipt_path).resolve()
    require(receipt_path.parent.parent == root / ".apa-discovery-updates",
            "ROLLBACK_RECEIPT_OUTSIDE_TRUSTED_BACKUP_DIRECTORY")
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    require(receipt.get("schema") == SCHEMA, "WRONG_UPDATE_RECEIPT_SCHEMA")
    target = root / "archicad_strategy_discovery.py"
    saved = receipt_path.parent / "archicad_strategy_discovery.py.before"
    require(sha(saved.read_bytes()) == receipt["beforeSHA256"], "BACKUP_HASH_DRIFT")
    require(sha(target.read_bytes()) == receipt["afterSHA256"], "CURRENT_MODULE_CHANGED_NO_BLIND_ROLLBACK")
    require(sha((root / "archicad_project_accelerator.py").read_bytes()) == CORE_SHA256,
            "CORE_CHANGED_NO_BLIND_ROLLBACK")
    atomic(target, saved.read_bytes())
    receipt["status"] = "ROLLED_BACK_PREVIOUS_DISCOVERY_RESTORED"
    atomic(receipt_path, (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode())
    return receipt


def install(root, source, apply=False):
    root, source = Path(root).resolve(), Path(source).resolve()
    target = root / "archicad_strategy_discovery.py"
    old, new = target.read_bytes(), source.read_bytes()
    core = root / "archicad_project_accelerator.py"
    dynamic = root / "archicad_dynamic_commands.py"
    require(sha(old) == OLD_MODULE_SHA256, "LOCAL_DISCOVERY_HASH_CHANGED_OR_ALREADY_UPDATED")
    require(sha(core.read_bytes()) == CORE_SHA256, "LOCAL_APA_CORE_HASH_CHANGED")
    require(sha(dynamic.read_bytes()) == DYNAMIC_SHA256, "LOCAL_DYNAMIC_COMMANDS_HASH_CHANGED")
    require(git_blob_sha(new) == NEW_GITHUB_BLOB_SHA1, "UPDATE_SOURCE_NOT_PINNED_GITHUB_BLOB")
    require(b"AUTO_CATALOG_ROOF_VERIFIED_SOURCE_BINDING_REQUIRED" in new,
            "ROOF_BRIDGE_NOT_PRESENT")
    compile(new, str(target), "exec")
    report = dict(schema=SCHEMA, status="PREFLIGHT_PASS", applied=False,
                  beforeSHA256=sha(old), afterSHA256=sha(new),
                  corePreserved=True, dynamicPreserved=True, nativeCalls=0, modelWrites=0)
    if not apply:
        return report
    folder = root / ".apa-discovery-updates" / (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8])
    folder.mkdir(parents=True, exist_ok=False)
    (folder / "archicad_strategy_discovery.py.before").write_bytes(old)
    receipt = folder / "receipt.json"
    report["receipt"] = str(receipt)
    atomic(receipt, (json.dumps(report, indent=2) + "\n").encode())
    require(target.read_bytes() == old, "LOCAL_MODULE_CHANGED_DURING_BACKUP")
    try:
        atomic(target, new)
        smoke = subprocess.run(
            [sys.executable, "-c",
             "import archicad_strategy_discovery as d; assert callable(d.discover_catalog_task)"],
            cwd=root, capture_output=True, timeout=45)
        require(smoke.returncode == 0, "NEW_MODULE_IMPORT_FAILED:" +
                smoke.stderr.decode(errors="replace")[-400:])
        require(sha(target.read_bytes()) == sha(new), "MODULE_CHANGED_AFTER_UPDATE")
        require(sha(core.read_bytes()) == CORE_SHA256 and
                sha(dynamic.read_bytes()) == DYNAMIC_SHA256,
                "APA_CORE_OR_DYNAMIC_CHANGED_DURING_UPDATE")
    except Exception:
        require(sha(target.read_bytes()) == sha(new), "UPDATE_AMBIGUOUS_NO_BLIND_ROLLBACK")
        atomic(target, old)
        raise
    report.update(status="ROOF_DISCOVERY_BRIDGE_INSTALLED_ORIGINAL_APA_PRESERVED", applied=True)
    atomic(receipt, (json.dumps(report, ensure_ascii=False, indent=2) + "\n").encode())
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts-dir", required=True)
    parser.add_argument("--source-module")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback-receipt")
    args = parser.parse_args()
    if args.rollback_receipt:
        output = rollback(args.scripts_dir, args.rollback_receipt)
    else:
        require(bool(args.source_module), "SOURCE_MODULE_REQUIRED")
        output = install(args.scripts_dir, args.source_module, args.apply)
    print(json.dumps(output, ensure_ascii=False, indent=2))
