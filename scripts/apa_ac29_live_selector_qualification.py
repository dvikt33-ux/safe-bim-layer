"""One-shot native AC29 selector runtime qualification for the existing BDD read task.

A production-INTEGRATION check only: refresh the current Tapir export, probe
candidate registrations, prepare the existing APA BIM Graph; NO GetDetails/
Get3DBoundingBoxes dispatch and NO CREATE/MODIFY/SAVE operations.
"""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from uuid import uuid4

STABLE_SCRIPTS = Path(r"C:\LocalAI\APA_AC29_Stable\scripts")
WORKING_PLN = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
PROTECTED_PLN = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
TASK = Path(os.environ.get("TEMP", "")) / "bdd-auto-task-20261017-131105.json"
CORE = "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b"
DYNAMIC = "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8"
BRIDGE_REPO = "dvikt33-ux/safe-bim-bridge"


def require(test, reason):
    if not test:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run():
    require(STABLE_SCRIPTS.is_dir(), "STABLE_INSTALL_NOT_PRESENT")
    require(sha(STABLE_SCRIPTS / "archicad_project_accelerator.py") == CORE,
            "STABLE_APA_CORE_DRIFT")
    require(sha(STABLE_SCRIPTS / "archicad_dynamic_commands.py") == DYNAMIC,
            "STABLE_APA_DYNAMIC_ROUTER_DRIFT")
    require(WORKING_PLN.is_file() and PROTECTED_PLN.is_file() and TASK.is_file(),
            "BDD_WORKING_OR_PROTECTED_PLN_OR_TASK_MISSING")
    saved_sha, protected_sha = sha(WORKING_PLN), sha(PROTECTED_PLN)
    task = json.loads(TASK.read_text(encoding="utf-8-sig"))
    require(task.get("schemaVersion") == "apa-capability-task/1"
            and len(task.get("steps", [])) == 2
            and all(s.get("effect") == s.get("impact") == "READ_ONLY"
                    for s in task["steps"]), "ONLY_EXACT_READ_ONLY_TASK_ALLOWED")
    source_guids = {
        row["elementId"]["guid"].lower()
        for step in task["steps"]
        for row in step["parameters"]["elements"]
    }
    require(len(source_guids) == 6, "SIX_SOURCE_WALL_HOSTS_REQUIRED")

    sys.path.insert(0, str(STABLE_SCRIPTS))
    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_strategy_discovery as DISC

    RUN.bind_authorized_saved_copy(
        19727, str(WORKING_PLN), WORKING_PLN.stem, saved_sha,
        "SOURCE_QUALIFIED_BDD_READ_ONLY_SELECTOR_INTEGRATION_20261017"
    )
    folder = Path(tempfile.mkdtemp(prefix="apa-ac29-live-selector-"))
    export_folder = folder / "current-runtime-export"
    export_result = APA.export_schema(export_folder, APA.native_transport)
    api = APA.EvidenceAPI(APA.native_transport, folder)
    before = APA.inventory_guids(api)
    require(len(before) == 290 and source_guids.issubset(set(before)),
            "BDD_LIVE_INVENTORY_CHANGED_RECONCILE_BEFORE_SELECTOR")
    writer = RUN.SceneWriter(
        api, folder / "unused-read-only-ledger.sqlite",
        schema_path=export_folder / "tapir-scene-live.json"
    )
    router, preview, runtime = DISC.prepare_current_runtime_catalog_task(
        writer, task
    )
    after = APA.inventory_guids(api)
    require(before == after and api.write_attempts == 0,
            "UNEXPECTED_MODEL_MUTATION_OR_INVENTORY_DRIFT")
    require(sha(WORKING_PLN) == saved_sha and sha(PROTECTED_PLN) == protected_sha,
            "WORKING_OR_PROTECTED_SAVED_PLN_CHANGED")
    automatically_selected = (
        preview.get("selectedNativeTaskPreview") is not None
        and runtime.get("automaticReadSelection") ==
            "AUTO_SELECTED_READ_ONLY_BY_RUNTIME_REGISTRATION"
    )
    selection_status = (
        "LIVE_AUTO_SELECTION_PREPARED_NO_NATIVE_WORKFLOW_DISPATCH"
        if automatically_selected
        else "PARTIAL_RUNTIME_SELECTION_UNRESOLVED_NO_MODEL_WRITES"
    )
    report = {
        "schema": "APA_AC29_CURRENT_RUNTIME_AUTO_SELECTOR_READ_ONLY_V1",
        "status": selection_status,
        "project": str(WORKING_PLN),
        "workingPLNSHA256": saved_sha,
        "originalPLNSHA256": protected_sha,
        "guidCount": len(after),
        "sourceWallCount": len(source_guids),
        "taskScopedRegistration": runtime,
        "selectionStatus": preview["status"],
        "selectionMethod": preview.get("selectionMethod"),
        "selectedCommands": runtime["selectedCommands"],
        "currentRuntimeExport": export_result,
        "selectorTaskOperationDispatchCalls": 0,
        "runtimeVerificationAPICalls": dict(api.calls),
        "schemaExportReadCalls": "RECORDED_IN_CURRENT_RUNTIME_EXPORT_LOGS",
        "modelWriteAttempts": api.write_attempts,
        "modelWrites": api.write_attempts,
        "savedPLNUnchanged": True,
        "autoSelected": automatically_selected,
        "sidecar": str(STABLE_SCRIPTS / "archicad_strategy_discovery.py"),
        "noExecutionGrant": True,
    }
    output = folder / "selector-report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print("APA_STATUS:", report["status"])
    print("DISCOVERY:", report["selectionStatus"])
    print("SELECTION_METHOD:", report["selectionMethod"])
    print("SELECTED:", report["selectedCommands"])
    print("TASK_RUNTIME_PROBES:", runtime["taskScopedAvailabilityChecks"])
    print("MODEL_WRITES:", report["modelWrites"])
    print("REPORT:", output)

    # Original working/pln is untouched; publish only a sanitized report to
    # the dedicated bridge repo, never the protected safe-bim-layer main.
    remote = "safe-bim-mailbox/gpt-live/results/apa-ac29-selector-final-" + (
        datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-"
        + uuid4().hex[:8] + ".json"
    )
    payload = {
        "branch": "main",
        "message": "APA AC29 task-scoped automatic read selector native registration evidence",
        "content": base64.b64encode(output.read_bytes()).decode("ascii"),
    }
    request = folder / "upload-request.json"
    request.write_text(json.dumps(payload), encoding="utf-8")
    uploaded = subprocess.run(
        ["gh", "api", "--method", "PUT",
         f"repos/{BRIDGE_REPO}/contents/{remote}",
         "--input", str(request), "--jq", ".content.html_url"],
        capture_output=True, text=True, timeout=50,
    )
    require(uploaded.returncode == 0,
            "LIVE_REPORT_LOCAL_PASS_GITHUB_UPLOAD_FAILED:" + uploaded.stderr[-350:])
    print("PUBLISHED:", uploaded.stdout.strip())
    return 0 if automatically_selected else 2


if __name__ == "__main__":
    try:
        sys.exit(run())
    except Exception as error:
        print("APA_STATUS: BLOCKED_NO_MODEL_WRITES")
        print("ERROR:", type(error).__name__ + ": " + str(error))
        sys.exit(2)
