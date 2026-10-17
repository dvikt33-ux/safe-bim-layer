"""Install the completed AC29 selector as an isolated, permanent APA copy.

Local defaults:
  source: the previously confirmed, still-working temporary APA checkout
  destination: C:\LocalAI\APA_AC29_Stable (MUST NOT exist)
No code is executed against Archicad; no PLN/API writes; no in-place changes to
the known temporary checkout or an existing permanent APA installation.

This is an opt-in promotion, not evidence of a native runtime LIVE_PASS.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from uuid import uuid4

EXPECTED_LOCAL_DISCOVERY = "e2afc6fe156dbe0ccbc295d00a447546be3fc90a7c92a20e1030b9f0bce54afe"
EXPECTED_CORE = "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b"
EXPECTED_DYNAMIC = "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8"
# SHA1 of content retrieved from this exact approved commit
NEW_DISCOVERY_BLOB = "2fa0897bf7ca4fcf16a9c5942e87381bf6bc11d5"
SOURCE_REVISION = "921ae63e9923a4a7ccc13d76bf09e429c012af12"
SOURCE_PATH = "scripts/archicad_strategy_discovery.py"
REPO = "dvikt33-ux/safe-bim-layer"
REQUIRED_FOLDERS = ("scripts", "schemas", "archicad-addon")


def require(value, error):
    if not value:
        raise ValueError(error)


def digest(blob):
    return hashlib.sha256(blob).hexdigest()


def git_blob(blob):
    return hashlib.sha1(b"blob " + str(len(blob)).encode() + b"\0" + blob).hexdigest()


def get_release_sidecar():
    endpoint = f"repos/{REPO}/contents/{SOURCE_PATH}?ref={SOURCE_REVISION}"
    raw = subprocess.check_output(
        ["gh", "api", endpoint], timeout=45, stderr=subprocess.PIPE
    )
    payload = json.loads(raw.decode("utf-8"))
    data = base64.b64decode(payload["content"])
    require(git_blob(data) == NEW_DISCOVERY_BLOB == payload["sha"],
            "RELEASE_DISCOVERY_SOURCE_HASH_DRIFT")
    compile(data, SOURCE_PATH, "exec")
    require(b"def select_uniquely_registered_read_alternative(" in data and
            b"def prepare_current_runtime_catalog_task(" in data,
            "RELEASE_MISSING_LIVE_SELECTOR_OR_READ_TIEBREAK")
    return data


def source_preflight(source_scripts):
    root = source_scripts.resolve().parent
    require(source_scripts.name.lower() == "scripts", "SOURCE_MUST_BE_SCRIPTS_DIRECTORY")
    require(all((root / name).is_dir() for name in REQUIRED_FOLDERS),
            "LOCAL_APA_CHECKOUT_INCOMPLETE_REQUIRED_SCRIPTS_SCHEMAS_ADDON")
    hashes = {}
    for filename, expected in (
        ("archicad_strategy_discovery.py", EXPECTED_LOCAL_DISCOVERY),
        ("archicad_project_accelerator.py", EXPECTED_CORE),
        ("archicad_dynamic_commands.py", EXPECTED_DYNAMIC),
    ):
        path = source_scripts / filename
        hashes[filename] = digest(path.read_bytes())
        require(hashes[filename] == expected, "LOCAL_APA_CHANGED_FAIL_CLOSED:" + filename)
    require(
        (root / "schemas/accelerator/mass-capabilities/operation-effects.json").is_file()
        and (root / "schemas/accelerator/functional-modules.json").is_file()
        and (root / "archicad-addon/Sources/NativeModuleCommands.cpp").is_file(),
        "SOURCE_REQUIRED_DISCOVERY_ASSETS_MISSING"
    )
    return root, hashes


def smoke(scripts):
    code = (
        "import sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "import archicad_project_accelerator as apa;"
        "import archicad_dynamic_commands as dynamic;"
        "import archicad_strategy_discovery as discovery;"
        "assert callable(discovery.prepare_current_runtime_catalog_task);"
        "assert callable(discovery.select_uniquely_registered_read_alternative);"
        "assert callable(apa.native_command_router)"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, str(scripts)],
        cwd=scripts.parent, capture_output=True, text=True, timeout=45
    )
    require(result.returncode == 0, "STABLE_SELECTOR_IMPORT_FAILED:" +
            result.stderr[-1400:])


def install(source_scripts, destination, apply):
    source_scripts, destination = Path(source_scripts), Path(destination)
    source_root, hashes = source_preflight(source_scripts)
    data = get_release_sidecar()
    require(destination.is_absolute() and destination != source_root and
            destination.resolve() != source_root and
            source_root not in destination.resolve().parents and
            destination.resolve() not in source_root.parents,
            "DESTINATION_MUST_BE_AN_INDEPENDENT_ABSOLUTE_INSTALL")
    require(not destination.exists(), "STABLE_TARGET_ALREADY_EXISTS_NO_OVERWRITE")
    require(destination.parent.is_dir(), "DESTINATION_PARENT_MUST_ALREADY_EXIST")
    report = dict(
        schema="APA_AC29_PERMANENT_SELECTOR_DEPLOY_V1",
        status="PREFLIGHT_PASS_NO_CHANGES",
        source=str(source_root),
        destination=str(destination),
        releaseRevision=SOURCE_REVISION,
        localDigests=hashes,
        newDiscoverySHA256=digest(data),
        originalCorePreserved=True,
        originalDynamicPreserved=True,
        originalWorkingCheckoutUntouched=True,
        liveNativeCommandsThisRun=0,
        modelWritesThisRun=0,
        currentRuntimeAvailability="NOT_PROBED",
        nativeOptimality="NOT_MEASURED",
        applied=False,
    )
    if not apply:
        return report
    temporary = destination.with_name(destination.name + ".stage-" + uuid4().hex[:10])
    require(not temporary.exists(), "STAGING_INSTALL_EXISTS")
    ignore = shutil.ignore_patterns(
        "__pycache__", ".git", ".apa-discovery-updates",
        "*.pln", "*.pla", "*.ifc", "*.sqlite", "*.db",
        "*.log", "*.jsonl", "*.bak", "*.before", "*.tmp",
        "*.pyc", ".env", ".env.*",
    )
    try:
        temporary.mkdir()
        for name in REQUIRED_FOLDERS:
            shutil.copytree(source_root / name, temporary / name, ignore=ignore)
        target = temporary / "scripts" / "archicad_strategy_discovery.py"
        require(digest(target.read_bytes()) == EXPECTED_LOCAL_DISCOVERY,
                "STAGING_INITIAL_MODULE_DRIFT")
        target.write_bytes(data)
        smoke(temporary / "scripts")
        # Verify exact core/router copies and original checkout still pinned.
        require(digest((temporary / "scripts/archicad_project_accelerator.py").read_bytes())
                == EXPECTED_CORE, "STAGING_CORE_CHANGED")
        require(digest((temporary / "scripts/archicad_dynamic_commands.py").read_bytes())
                == EXPECTED_DYNAMIC, "STAGING_ROUTER_CHANGED")
        require(all(digest((source_scripts / file).read_bytes()) == value
                    for file, value in hashes.items()),
                "SOURCE_CHECKOUT_CHANGED_DURING_INSTALL")
        require(not destination.exists(), "DESTINATION_APPEARED_DURING_INSTALL")
        report.update(status="STABLE_SELECTOR_DEPLOYED_IMPORT_VERIFIED_NO_NATIVE_CALLS",
                      applied=True)
        (temporary / "apa-selector-install-receipt.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.rename(destination)
        return report
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)


def main():
    root = os.environ.get("TEMP")
    require(isinstance(root, str) and root, "WINDOWS_TEMP_REQUIRED")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source-scripts",
        default=str(Path(root) / "APA_BDD_NorthPair_20261016_174054" / "scripts"),
    )
    parser.add_argument("--destination", default=r"C:\LocalAI\APA_AC29_Stable")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        result = install(args.source_scripts, args.destination, args.apply)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        print("APA_STATUS:", result["status"])
        print("NATIVE_CALLS: 0 | MODEL_WRITES: 0")
        return 0
    except Exception as exc:
        print("APA_STATUS: BLOCKED_NO_CHANGES")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
