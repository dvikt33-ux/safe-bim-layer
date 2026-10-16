#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""BDD house: live read-only run THROUGH EXISTING APA DynamicCommands/BIM Graph.

This file is a thin CLI adapter, NOT a new native writer, dispatcher, API
client, ledger or router. It uses:
  archicad_project_accelerator.native_command_router()
  archicad_project_accelerator.prepare_native_task()
  archicad_project_accelerator.run_native_task()
  archicad_project_accelerator.EvidenceAPI()
  archicad_scene_run.bind_authorized_saved_copy()

No existing PLN is saved, changed, opened or closed. Mutations are denied by
EvidenceAPI(execute=False) and the task schema has only five reviewed reads.
--publish uploads a unique evidence file to the PRIVATE mailbox repo.
"""
from __future__ import annotations

import argparse
import base64
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid

import archicad_project_accelerator as APA
import archicad_scene_run as RUN

ROOT = Path(__file__).resolve().parents[1]
INTENT = ROOT / "examples/accelerator/bdd-house-20261016-readonly-native-task.json"
BINDING = ROOT / "docs/research/apa-results/bdd-house/APA_EXISTING_SCENE_WRITER_BASELINE_20261016.json"
SCHEMA = ROOT / "schemas/tapir-live-1.5.10/tapir-scene-live.json"
WORK = Path(tempfile.gettempdir()) / "APA_BDD_Existing_APA_Readback"
PORT = 19727
COMMANDS = frozenset({
    "GetProjectInfo", "GetStories", "GetAllElements",
    "GetDetailsOfElements", "Get3DBoundingBoxes",
})


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def json_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


def exact_model_set(body, expected):
    rows = body.get("elements")
    if not isinstance(rows, list):
        raise ValueError("APA_GET_ALL_ELEMENTS_RESPONSE_MISSING")
    found = []
    for row in rows:
        guid = ((row.get("elementId") or {}).get("guid")
                if isinstance(row, dict) else None)
        if not isinstance(guid, str):
            raise ValueError("APA_ELEMENT_WITHOUT_GUID")
        found.append(guid.lower())
    if len(found) != len(set(found)):
        raise ValueError("APA_DUPLICATE_GUID")
    if len(found) != 261 or set(found) != expected:
        raise ValueError(
            "APA_MODEL_DRIFT: actual %d GUIDs, expected 261, "
            "missing=%d, extra=%d" % (
                len(found), len(expected - set(found)),
                len(set(found) - expected)))
    return found


def baseline_ids(binding):
    roles = binding["roles"]
    originals = {x.lower() for x in roles["originalGuids"]}
    parents = {
        x.lower() for stage in roles["parent"]
        for x in stage["physicalGuids"]
    }
    children = {x.lower() for x in roles["automaticChildGuids"]}
    if not (
        (len(originals), len(parents), len(children)) == (21, 125, 115)
        and not (originals & parents)
        and not (parents & children)
        and not (originals & children)
    ):
        raise ValueError("APA_BASELINE_GUID_CONTRACT_CHANGED")
    return originals | parents | children, parents


def summarize(workflow, intent, parents):
    results = workflow["results"]
    found = exact_model_set(results["read-model-inventory"], intent["_expectedAll"])
    records = []
    for index in range(1, 6):
        suffix = "%02d" % index
        details = results["read-physical-details-" + suffix].get("detailsOfElements")
        bounds = results["read-physical-bounds-" + suffix].get("boundingBoxes3D")
        step = next(x for x in intent["graph"]["operations"]
                    if x["id"] == "read-physical-details-" + suffix)
        assigned = [x["elementId"]["guid"].lower() for x in step["params"]["elements"]]
        if not (isinstance(details, list) and isinstance(bounds, list)
                and len(details) == len(bounds) == len(assigned)):
            raise ValueError("APA_BATCH_READBACK_CARDINALITY_" + suffix)
        for guid, detail, box in zip(assigned, details, bounds):
            bbox = box.get("boundingBox3D") if isinstance(box, dict) else None
            if not isinstance(detail, dict) or not isinstance(bbox, dict):
                raise ValueError("APA_NATIVE_DETAILS_OR_BBOX_NOT_VERIFIED_" + guid)
            records.append({
                "guid": guid,
                "type": detail.get("type"),
                "story": detail.get("floorIndex"),
                "details": detail.get("details"),
                "boundingBox3D": bbox,
            })
    if len(records) != 125 or set(x["guid"] for x in records) != parents:
        raise ValueError("APA_PARENT_READBACK_GUID_MISMATCH")
    counts = dict(Counter(x["type"] for x in records))
    expected = {"Column": 49, "Beam": 66, "Wall": 6, "Slab": 3, "Roof": 1}
    if counts != expected:
        raise ValueError("APA_NATIVE_TYPE_DRIFT: " + repr(counts))
    return {"guidCount": len(found), "nativePhysicalCount": len(records),
            "nativeTypeCounts": counts, "elements": records}


def publish(path):
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remote = "safe-bim-mailbox/gpt-live/results/apa-bdd-existing-router-%s-%s.json" % (
        stamp, uuid.uuid4().hex[:8])
    encoded = base64.b64encode(Path(path).read_bytes()).decode("ascii")
    upload = Path(path).with_suffix(".upload.tmp.json")
    try:
        json_write(upload, {"branch": "main",
                            "message": "Existing APA native router BDD 125 element readback",
                            "content": encoded})
        result = subprocess.run([
            "gh", "api", "--method", "PUT",
            "repos/dvikt33-ux/safe-bim-bridge/contents/" + remote,
            "--input", str(upload)],
            capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError("GitHub report upload: " + result.stderr[-600:])
    finally:
        upload.unlink(missing_ok=True)
    return "https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/" + remote


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--publish", action="store_true")
    args = parser.parse_args()
    WORK.mkdir(parents=True, exist_ok=True)
    target = json.loads(BINDING.read_text(encoding="utf-8"))
    task = json.loads(INTENT.read_text(encoding="utf-8"))
    expected, parents = baseline_ids(target)
    commands = {x["command"] for x in task["graph"]["operations"]}
    if commands != COMMANDS or len(task["graph"]["operations"]) != 13:
        raise ValueError("APA_READONLY_WORKFLOW_CHANGED")
    for step in task["graph"]["operations"]:
        if step["command"] not in COMMANDS:
            raise ValueError("APA_MUTATION_IN_READONLY_GRAPH")
    bind = target["target"]
    path = Path(bind["workingPLN"])
    source = Path(bind["sourcePLN"])
    if not path.is_file() or not source.is_file():
        raise ValueError("APA_WORKING_ORIGINAL_PLN_MISSING")
    if sha256(source) != bind["sourceBaselineSha256"]:
        raise ValueError("APA_ORIGINAL_PLN_CHANGED")
    before_disk = sha256(path)
    # The existing writer identity binder is the only place project binding
    # is configured. This gives NO permission to execute a write.
    RUN.bind_authorized_saved_copy(
        PORT, str(path), path.stem, before_disk,
        authorization_ref="BDD_20261016_USER_GO_EXISTING_APA_READ_ONLY",
    )
    from archicad import ACConnection
    conn = ACConnection.connect(PORT)
    if conn is None:
        raise ValueError("APA_ARCHICAD_19727_UNAVAILABLE")
    product = conn.commands.GetProductInfo()
    if int(product[0]) != 29 or int(product[1]) != 5101:
        raise ValueError("APA_WRONG_ARCHICAD_PRODUCT_BUILD")

    evidence = WORK / ("dispatch-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    evidence.mkdir(parents=True, exist_ok=False)
    api = APA.EvidenceAPI(APA.native_transport, evidence, execute=False)
    binding_before = RUN.guarded_project_for_read(api)
    inventory_before = exact_model_set(api("GetAllElements", {}), expected)

    # Resolve actual provider schema+source file hashes and use the already
    # shipped APA dynamic router and BIM graph, without optional SDK handlers.
    router = APA.native_command_router(SCHEMA, include_functional_modules=False)
    for command in sorted(COMMANDS):
        router.review_policy(
            command, "READ_ONLY", "READ_ONLY",
            {"source": "pinned Tapir 1.5.10 live-export GET operation",
             "sha256": router.contract_hash(command)},
        )
    preview = APA.prepare_native_task(router, task)
    flow = APA.run_native_task(router, api, preview, writer=None, scopes=None)
    if flow.get("status") != "WORKFLOW_CALLABLE_VERIFIED":
        raise ValueError("APA_WORKFLOW_NOT_VERIFIED: " + str(flow.get("status")))
    source_task = dict(task, _expectedAll=expected)
    summary = summarize(flow, source_task, parents)

    inventory_after = exact_model_set(api("GetAllElements", {}), expected)
    if inventory_before != inventory_after or RUN.guarded_project_for_read(api) != binding_before:
        raise ValueError("APA_MODEL_OR_PROJECT_CHANGED_DURING_READBACK")
    if sha256(path) != before_disk or sha256(source) != bind["sourceBaselineSha256"]:
        raise ValueError("APA_SAVED_PLN_BYTES_CHANGED")
    if api.write_attempts != 0:
        raise ValueError("APA_UNEXPECTED_NATIVE_WRITE")

    report = {
        "schema": "apa.bdd.existing-router-live-readback.v1",
        "status": "LIVE_APA_DYNAMIC_ROUTER_AND_BIM_GRAPH_READ_PASS",
        "timestampUTC": datetime.now(timezone.utc).isoformat(),
        "nativeExecuted": True,
        "writeToPLN": False,
        "project": binding_before,
        "currentWorkingPlnSHA256": before_disk,
        "originalPLNUnchanged": True,
        "apiWriteAttempts": api.write_attempts,
        "executor": "existing archicad_project_accelerator.EvidenceAPI and DynamicCommands",
        "sceneWriterMutations": 0,
        "bimGraph": {"sourcePlanHash": preview["sourcePlanHash"],
                     "operationCount": len(task["graph"]["operations"]),
                     "executionOrder": preview["workflow"]["executionOrder"],
                     "workflowStatus": flow["status"],
                     "trace": flow["trace"]},
        "capabilities": {
            "runtimeReads": sorted(router.callable),
            "optionalNativeModulesLoaded": False,
            "SceneWriterAuthorizationForFutureWrites": "NOT_GRANTED",
        },
        "model": summary,
    }
    dest = WORK / ("apa-router-bdd-" +
                   datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".json")
    json_write(dest, report)
    print("APA EXISTING ROUTER LIVE READ PASS")
    print("GUIDS: 261 | PHYSICAL: 125 | GRAPH STEPS: 13")
    print("NATIVE WRITE CALLS:", api.write_attempts)
    print("LOCAL RESULT:", dest)
    if args.publish:
        print("PRIVATE GITHUB APA ROUTER REPORT:", publish(dest))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA ROUTER BLOCKED:", type(exc).__name__, str(exc), file=sys.stderr)
        if "--publish" in sys.argv:
            try:
                WORK.mkdir(parents=True, exist_ok=True)
                failure = WORK / ("blocked-" +
                    datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") +
                    "-" + uuid.uuid4().hex[:6] + ".json")
                json_write(failure, {
                    "schema": "apa.bdd.existing-router-live-readback.v1",
                    "status": "BLOCKED_NO_MODEL_MUTATION_REQUESTED",
                    "atUTC": datetime.now(timezone.utc).isoformat(),
                    "errorType": type(exc).__name__,
                    "error": str(exc)[:1000],
                    "writeRequested": False,
                })
                print("PRIVATE GITHUB APA ROUTER FAILURE:", publish(failure))
            except Exception as upload_exc:
                print("REPORT UPLOAD FAILED:", str(upload_exc)[:300],
                      file=sys.stderr)
        sys.exit(2)
