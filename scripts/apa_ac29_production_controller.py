"""Minimal separate AC29 APA production controller / GPT bridge.

Uses the EXISTING stable APA release, without patching the UI AI Dispatcher.
One-shot and read-only by default. Does not connect to native Archicad or
dispatch any model writes. BDD source layout is only a preflight plan.
"""
from __future__ import annotations

import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
SCRIPTS = STABLE / "scripts"
MODEL = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
PROTECTED = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
CORE_SHA256 = "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b"
DYNAMIC_SHA256 = "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8"
SELECTOR_SHA256 = "32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce"
BDD_BASELINE_SHA256 = "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
BLOCK_REPO = "dvikt33-ux/safe-bim-layer"
BLOCK_REF = "8b3bf90d676d6b837312e544d22f289e8dc17991"
BLOCK_PATH = "examples/accelerator/bdd-house-block-114-local-stud-layout.json"
BLOCK_BLOB_SHA1 = "15e09eb2216f4523c9f68e7922a2a5cb508199c2"
BRIDGE_REPO = "dvikt33-ux/safe-bim-bridge"


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def sha_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def gh_pinned(repo, ref, path, expected_sha):
    url = f"repos/{repo}/contents/{path}?ref={ref}"
    response = subprocess.run(
        ["gh", "api", url], capture_output=True, timeout=45
    )
    require(response.returncode == 0, "AUTHENTICATED_SOURCE_FETCH_FAILED")
    item = json.loads(response.stdout.decode("utf-8"))
    data = base64.b64decode(item["content"])
    calc = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    require(calc == expected_sha == item["sha"], "SOURCE_BLOB_SHA_CHANGED")
    return json.loads(data.decode("utf-8-sig"))


def preflight():
    require(STABLE.is_dir() and SCRIPTS.is_dir(), "APA_STABLE_ROOT_MISSING")
    expected = {
        "archicad_project_accelerator.py": CORE_SHA256,
        "archicad_dynamic_commands.py": DYNAMIC_SHA256,
        "archicad_strategy_discovery.py": SELECTOR_SHA256,
    }
    for name, sha in expected.items():
        require(sha_file(SCRIPTS / name) == sha, "APA_STABLE_MODULE_CHANGED:" + name)
    receipt = STABLE / "apa-selector-install-receipt.json"
    require(receipt.is_file(), "APA_STABLE_RECEIPT_MISSING")
    installed = json.loads(receipt.read_text(encoding="utf-8"))
    require(installed.get("applied") is True and
            installed.get("status") == "STABLE_SELECTOR_DEPLOYED_IMPORT_VERIFIED_NO_NATIVE_CALLS",
            "APA_STABLE_INSTALL_NOT_CONFIRMED")
    require(MODEL.is_file() and PROTECTED.is_file(), "BDD_WORKING_OR_SOURCE_PLN_MISSING")
    current_sha = sha_file(MODEL)
    base_matches = current_sha == BDD_BASELINE_SHA256
    # Check installed modules resolve from this stable release, not a temporary
    # checkout. Imports are read-only; no native Archicad connection.
    probe = (
        "import sys;"
        "sys.path.insert(0,sys.argv[1]);"
        "import archicad_project_accelerator as a;"
        "import archicad_dynamic_commands as d;"
        "import archicad_strategy_discovery as s;"
        "assert a.__file__.lower().startswith(sys.argv[1].lower());"
        "assert d.__file__.lower().startswith(sys.argv[1].lower());"
        "assert s.__file__.lower().startswith(sys.argv[1].lower());"
        "assert callable(s.prepare_current_runtime_catalog_task)"
    )
    p = subprocess.run(
        [sys.executable, "-c", probe, str(SCRIPTS)],
        cwd=STABLE, capture_output=True, timeout=45
    )
    require(p.returncode == 0, "APA_STABLE_IMPORT_OR_SOURCE_DRIFT:" +
            p.stderr.decode(errors="replace")[-350:])
    # This is the already running UI messaging dispatcher, NOT an APA executor.
    dispatcher = Path.home() / "dispatcher.py"
    dispatcher_core = Path.home() / "dispatcher_core.py"
    return {
        "schema": "APA_AC29_SEPARATE_PRODUCTION_CONTROLLER_STATUS_V1",
        "status": "APA_STABLE_CONTROLLER_AVAILABLE",
        "stableRoot": str(STABLE),
        "stableModulesValidated": sorted(expected),
        "workingProject": str(MODEL),
        "workingPlnSha256": current_sha,
        "expectedSavedBaselineMatched": base_matches,
        "modelInventoryLiveVerifiedNow": False,
        "protectedSourcePresent": True,
        "uiDispatcherFilesPresent": dispatcher.is_file() and dispatcher_core.is_file(),
        "uiDispatcherAPAExecutionTarget": "NOT_INSTALLED_BY_THIS_CONTROLLER",
        "currentGPTCommunication": "SAFE_BIM_BRIDGE_EXPLICIT_ONE_SHOT_RESULTS",
        "nativeCalls": 0,
        "modelWrites": 0,
        "automaticModelWriteAuthorization": False,
    }


def prepare_block114(status):
    block = gh_pinned(BLOCK_REPO, BLOCK_REF, BLOCK_PATH, BLOCK_BLOB_SHA1)
    frame = block["localFrame"]
    positions = frame["centerOffsetsFromLeftEndMm"]
    require(frame["studCount"] == 7 and len(positions) == 7 and
            frame["lengthOverallMm"] == 2910 and
            sum(frame["studAxisPitchesMm"]) + 50 == 2910,
            "FRAME_114_SOURCE_LAYOUT_MISMATCH")
    # Absolute XY cannot be created from the PDF elevation dimensions alone.
    require(block["execution"]["eligibleForNativeWrite"] is False and
            block["plan"]["exactStartXY"] == "NOT_NUMERICALLY_DIMENSIONED",
            "BLOCK_114_EXACT_ORIGIN_SOURCE_CHANGED")
    return {
        "schema": "APA_BDD_BLOCK_114_PRODUCTION_HANDOFF_V1",
        "status": "PENDING_EXACT_GLOBAL_XY_AND_PROTOTYPE_READBACK",
        "sourceBlockId": "1.14",
        "sourceBlockBlobSHA1": BLOCK_BLOB_SHA1,
        "workingPLN": status["workingProject"],
        "workingPLNMatchesAccepted290GUIDSave": status["expectedSavedBaselineMatched"],
        "relativeStudCentersMillimeters": positions,
        "studSectionMillimeters": frame["studSectionMm"],
        "studHeightMillimeters": frame["studHeightMm"],
        "numberOfStuds": 7,
        "absolutePlacement": "NOT_APPROVED_DO_NOT_INFER_FROM_PICTURE",
        "requireBeforeWrite": block["execution"]["requiredBeforeCreate"],
        "router": "EXISTING_APA_DYNAMIC_COMMANDS_TO_SCENE_WRITER_ONLY",
        "nativeCalls": 0,
        "modelWrites": 0,
        "automaticExecution": False,
    }


def output_report(document, publish):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    path = Path(tempfile.gettempdir()) / (
        "apa-ac29-local-controller-" + stamp + "-" + uuid.uuid4().hex[:8] + ".json"
    )
    path.write_text(json.dumps(document, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    print("APA_STATUS:", document["status"])
    print("MODEL_WRITES: 0")
    print("REPORT:", path)
    if not publish:
        return
    remote = ("safe-bim-mailbox/gpt-live/results/apa-ac29-local-controller-"
              + stamp + "-" + uuid.uuid4().hex[:8] + ".json")
    payload = {
        "branch": "main",
        "message": "APA AC29 stable controller and BDD production readiness",
        "content": base64.b64encode(path.read_bytes()).decode("ascii"),
    }
    envelope = path.with_suffix(".upload.json")
    envelope.write_text(json.dumps(payload), encoding="utf-8")
    proc = subprocess.run(
        ["gh", "api", "--method", "PUT",
         f"repos/{BRIDGE_REPO}/contents/{remote}",
         "--input", str(envelope), "--jq", ".content.html_url"],
        capture_output=True, timeout=45
    )
    require(proc.returncode == 0, "BRIDGE_REPORT_UPLOAD_FAILED")
    print("PUBLISHED:", proc.stdout.decode("utf-8", errors="replace").strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare-block114", action="store_true")
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    try:
        current = preflight()
        result = prepare_block114(current) if args.prepare_block114 else current
        output_report(result, args.publish)
        return 0
    except Exception as exc:
        print("APA_STATUS: BLOCKED_NO_MODEL_CHANGES")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        return 2


if __name__ == "__main__":
    sys.exit(main())
