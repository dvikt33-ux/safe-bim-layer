"""Fail-closed 10-GUID runtime smoke test for experimental SomeStuff.SyncGuids.

Requires installed experimental APX and the EXACT existing disposable test PLN.
Never auto-replay after any attempt. Does not save or switch PLN.
Expected evidence: SS-BATCH-02 (2000 walls), SS-LIVE-04 (12 elements).
Run only after confirming API.IsAddOnCommandAvailable(SyncGuids) == true.
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(r"C:\LocalAI\APA\somestuff-live-tests")
BATCH = ROOT / "SS-BATCH-02-20261009-172802-9465e8"
SCENE = ROOT / "SS-LIVE-04-20261009-171312-a66f03"
FIRST = ROOT / "SS-LIVE-02-20261009-165014"
LAST = ROOT / "SS-AB-02-20261009-175447-808203"
URL = "http://127.0.0.1:19723/json"
COUNT = 10

# A prior attempt can have partially modified BIM even without a final report.
if list(ROOT.glob("SS-SYNCGUIDS-SMOKE-*")):
    raise SystemExit("BLOCKED: prior smoke journal exists; inspect before retry")

RUN = ROOT / (
    "SS-SYNCGUIDS-SMOKE-"
    + datetime.now().strftime("%Y%m%d-%H%M%S")
    + "-" + uuid.uuid4().hex[:6]
)
RUN.mkdir(parents=True, exist_ok=False)
phase = "PREFLIGHT"


def save(name, value):
    (RUN / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def check(condition, reason):
    if not condition:
        raise RuntimeError(reason)


def api(command, parameters=None):
    body = json.dumps(
        {"command": command, "parameters": parameters or {}}
    ).encode("utf-8")
    req = Request(
        URL, method="POST", data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
    )
    with urlopen(req, timeout=900) as stream:
        result = json.load(stream)
    check(result.get("succeeded") is True, f"{command}: {result}")
    return result["result"]


def addon(namespace, command, params=None):
    result = api("API.ExecuteAddOnCommand", {
        "addOnCommandId": {
            "commandNamespace": namespace,
            "commandName": command,
        },
        "addOnCommandParameters": params or {},
    })
    out = result.get("addOnCommandResponse")
    check(isinstance(out, dict), f"Missing {namespace}.{command} response")
    return out


def inventory():
    return sorted(
        x["elementId"]["guid"].upper()
        for x in api("API.GetAllElements")["elements"]
    )


def property_values(guids, props):
    out = {}
    for start in range(0, len(guids), 200):
        group = guids[start : start + 200]
        rows = api("API.GetPropertyValuesOfElements", {
            "elements": [{"elementId": {"guid": g}} for g in group],
            "properties": [{"propertyId": p} for p in props],
        })["propertyValuesForElements"]
        check(len(rows) == len(group), "PROPERTY_ROW_COUNT")
        for guid, row in zip(group, rows):
            values = row.get("propertyValues", [])
            check(len(values) == len(props) and all(
                "propertyValue" in v for v in values
            ), "INVALID_PROPERTY_VALUES: " + guid)
            out[guid] = [v["propertyValue"] for v in values]
    return out


def classification_values(guids, systems):
    return api("API.GetClassificationsOfElements", {
        "elements": [{"elementId": {"guid": g}} for g in guids],
        "classificationSystemIds": systems,
    })["elementClassifications"]


try:
    print("=== SYNCGUIDS PREFLIGHT ===", flush=True)
    previous = json.loads((BATCH / "report.json").read_text(encoding="utf-8"))
    last = json.loads((LAST / "report.json").read_text(encoding="utf-8"))
    preflight = json.loads((BATCH / "preflight.json").read_text(encoding="utf-8"))
    all_new = json.loads((BATCH / "created-guids.json").read_text(encoding="utf-8"))
    old_12 = json.loads((SCENE / "created.json").read_text(encoding="utf-8"))
    definitions = json.loads((FIRST / "property-definitions.json").read_text(encoding="utf-8"))
    props = [p["propertyId"] for p in definitions["propertyIds"]]
    check(previous["status"] == last["status"] == "PASS", "BASELINE NOT ACCEPTED")
    check(len(all_new) == 2000 and len(set(all_new)) == 2000, "INVALID GUID EVIDENCE")
    check(len(props) == 3, "PROPERTY IDS MISSING")

    available = api("API.IsAddOnCommandAvailable", {
        "addOnCommandId": {
            "commandNamespace": "SomeStuffCommand",
            "commandName": "SyncGuids",
        }
    })
    check(available.get("available") is True, "EXPERIMENTAL APX NOT INSTALLED")

    project = addon("TapirCommand", "GetProjectInfo")
    for key in ("projectName", "projectPath", "isUntitled", "isTeamwork"):
        check(project.get(key) == preflight["project"].get(key),
              "WRONG PROJECT: " + key)

    original_guids = inventory()
    check(original_guids == sorted(preflight["existingGuids"] + all_new),
          "BIM GUID INVENTORY DRIFT")
    selected = [g.upper() for g in all_new[:COUNT]]
    # Track legacy test walls as well, to detect collateral property changes.
    legacy_walls = ["F3926B48-B165-4F27-91B8-8C1D2F236668"]
    legacy_walls += [entry["guid"].upper() for entry in old_12 if entry["type"] == "Wall"]
    watched = list(dict.fromkeys(
        [g.upper() for g in all_new] + legacy_walls
    ))
    before = property_values(watched, props)
    check(all(before[g][0].get("value") == before[g][1].get("value")
              for g in selected), "SELECTED BASELINE IS NOT SYNCHRONIZED")
    systems = api("API.GetClassificationSystemIds")["classificationSystemIds"]
    classifications_before = classification_values(selected, systems)
    save("preflight.json", {
        "project": project, "targetGuids": selected,
        "initialInventory": original_guids,
        "watchedPropertyCount": len(watched),
    })
    print("PREFLIGHT PASS: 10 selected GUIDs / 2213 total BIM elements", flush=True)

    expected = {
        g: "APA-SG10-" + uuid.uuid4().hex[:16].upper() for g in selected
    }
    changes = [{
        "elementId": {"guid": g},
        "propertyId": props[0],
        "propertyValue": {
            "type": "string",
            "status": "normal",
            "value": expected[g],
        },
    } for g in selected]

    print("=== WRITE 10 SOURCE VALUES ===", flush=True)
    save("write-intent.json", {"elementPropertyValues": changes})
    phase = "WRITE_SOURCE"
    t = time.perf_counter()
    write_response = api("API.SetPropertyValuesOfElements", {
        "elementPropertyValues": changes
    })
    write_seconds = time.perf_counter() - t
    save("write-response.json", write_response)
    rows = write_response.get("executionResults", [])
    check(len(rows) == COUNT and all(r.get("success") is True for r in rows),
          "SOURCE WRITE INCOMPLETE")

    pre_sync = property_values(selected, props)
    check(all(pre_sync[g][0].get("value") == expected[g] for g in selected),
          "SOURCE READBACK FAILED")
    check(all(pre_sync[g][1].get("value") != expected[g] for g in selected),
          "TRACKING IS ACTIVE OR TARGET ALREADY SYNCHRONIZED")

    print("=== CALL SyncGuids(10) ===", flush=True)
    phase = "SYNC_GUIDS"
    save("sync-intent.json", {"elementGuids": selected})
    t = time.perf_counter()
    result = addon("SomeStuffCommand", "SyncGuids", {
        "elementGuids": selected
    })
    sync_seconds = time.perf_counter() - t
    save("sync-response.json", result)
    check(result.get("status") == "returned_unverified", "UNEXPECTED RESPONSE STATUS")
    check(result.get("requestedCount") == COUNT, "REQUEST COUNT MISMATCH")
    check(result.get("requiresReadback") is True, "MISSING READBACK CONTRACT")

    print("=== INDEPENDENT READBACK ===", flush=True)
    phase = "VERIFY"
    after = property_values(watched, props)
    mismatches = [
        g for g in selected
        if after[g][0].get("value") != expected[g]
        or after[g][1].get("value") != expected[g]
    ]
    unselected_changed = [
        g for g in watched if g not in selected and after[g] != before[g]
    ]
    checks = {
        "selectedCorrect": not mismatches,
        "unselectedPropertiesStable": not unselected_changed,
        "guidInventoryStable": inventory() == original_guids,
        "classificationsStable":
            classification_values(selected, systems) == classifications_before,
    }
    report = {
        "test": "SS-SYNCGUIDS-SMOKE",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "requestedCount": COUNT,
        "checks": checks,
        "mismatchCount": len(mismatches),
        "unselectedChangedCount": len(unselected_changed),
        "writeSeconds": write_seconds,
        "syncClientSeconds": sync_seconds,
        "syncResponse": result,
        "evidenceDirectory": str(RUN),
    }
    save("mismatches.json", mismatches)
    save("unselected-changed.json", unselected_changed)
    save("report.json", report)
    print("=== SYNCGUIDS SMOKE REPORT ===", flush=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))

except Exception as error:
    stop = {
        "status": "STOP", "phase": phase,
        "reason": str(error), "evidenceDirectory": str(RUN)
    }
    save("stop.json", stop)
    print("=== SYNCGUIDS SMOKE STOP ===", flush=True)
    print(json.dumps(stop, ensure_ascii=False, indent=2))
    print("DO NOT RERUN. INSPECT JOURNAL AND BIM STATE.")
