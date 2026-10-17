"""One production preflight of existing BDD timber studs using stable APA.

Read-only: one complete native inventory, one native model dump and one typed
batched column Details call. Does not replay earlier source-wall read, test
CreateColumns, modify/save a PLN, or authorize output placement of block 1.14.
"""
from __future__ import annotations

import base64
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
WORKING = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
ORIGINAL = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
WORKING_SHA = "e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
ORIGINAL_SHA = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
CORE_SHA = "5ce7cbb91c8f799265a541f79922b50455fecf661ed9278a1cc4ffaff766ba4b"
DYNAMIC_SHA = "8effd2f294197179b4b18b785de80f7f78091649e7f105ee4cf66877dbe0e6f8"
SELECTOR_SHA = "32b7f1c161c545695b6db20aa87003d08cbd86916bc880f9eba1434f3a0801ce"
KNOWN_PROTOTYPE = "b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
WOOD_GUID = "e7ef3819-b3e8-419f-b313-5172e6b0412c"
BRIDGE = "dvikt33-ux/safe-bim-bridge"
TOL = 0.0005


def require(test, reason):
    if not test:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def close(a, b):
    return type(a) in (float, int) and math.isfinite(a) and abs(a-b) < TOL


def bounds(row):
    xyz = [v for body in row.get("bodies", []) for v in body.get("vertices", [])]
    if not xyz:
        return None
    return [
        [min(float(v[i]) for v in xyz), max(float(v[i]) for v in xyz)]
        for i in range(3)
    ]


def run():
    scripts = STABLE / "scripts"
    for name, expected in [
        ("archicad_project_accelerator.py", CORE_SHA),
        ("archicad_dynamic_commands.py", DYNAMIC_SHA),
        ("archicad_strategy_discovery.py", SELECTOR_SHA),
    ]:
        require(sha(scripts / name) == expected,
                "STABLE_APA_ORIGINAL_CHANGED:" + name)
    require(sha(WORKING) == WORKING_SHA, "SAVED_BDD_PLN_BASELINE_CHANGED")
    require(sha(ORIGINAL) == ORIGINAL_SHA, "PROTECTED_BDD_PLN_CHANGED")
    sys.path.insert(0, str(scripts))
    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_connected_components as C

    RUN.bind_authorized_saved_copy(
        19727, str(WORKING), WORKING.stem, WORKING_SHA,
        "BDD_20261017_SOURCE_STUD_PROTOTYPE_READ_ONLY_NO_WRITE"
    )
    folder = Path(tempfile.mkdtemp(prefix="apa-bdd-stud-read-"))
    raw = folder / "raw"
    raw.mkdir()
    api = APA.EvidenceAPI(APA.native_transport, raw, execute=False)
    RUN.guarded_project_for_read(api)
    product = APA.archicad29(api)
    require(product.get("buildNumber") == 5101, "AC29_BUILD_NOT_PINNED")
    known = set(APA.inventory_guids(api))
    require(len(known) == 290, "LIVE_BDD_GUID_BASELINE_NOT_290")
    model = C.G.normalize_dump(api("GetModelDumpV1", {}))
    native = {el["guid"].lower(): el for el in model["elements"]}
    require(set(native) == known, "LIVE_MODEL_DUMP_INVENTORY_DIFFERENCE")
    parents = sorted(g for g, row in native.items() if row["type"] == "Column")
    require(KNOWN_PROTOTYPE in parents, "KNOWN_STUD_PROTOTYPE_NOT_IN_MODEL")

    response = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": g}} for g in parents]
    })
    details = response.get("detailsOfElements")
    require(isinstance(details, list) and len(details) == len(parents),
            "LIVE_COLUMNS_DETAILS_INCOMPLETE")

    identified = []
    for guid, row in zip(parents, details):
        if row.get("type") != "Column" or row.get("floorIndex") != 0:
            continue
        d = row.get("details") or {}
        if not all(close(d.get(k), val) for k, val in (
            ("height", 2.9), ("width", 0.1), ("depth", 0.05)
        )):
            continue
        org = d.get("origin") or {}
        if not all(type(org.get(axis)) in (int, float)
                   and math.isfinite(org[axis]) for axis in ("x", "y")):
            continue
        children = [
            (subguid, obj) for subguid, obj in native.items()
            if obj.get("type") == "ColumnSegment"
            and (obj.get("relationships", {}).get("hostGuid", "") or "").lower() == guid
        ]
        require(len(children) == 1, "STUD_COLUMN_SEGMENT_NOT_UNIQUE:" + guid)
        segment_guid, segment = children[0]
        material = (
            segment.get("materialBindings", {}).get("buildingMaterial", {})
            .get("guid", "").lower()
        )
        if material != WOOD_GUID:
            continue
        bb = bounds(segment)
        require(bb is not None and close(bb[2][1]-bb[2][0], 2.9),
                "STUD_SEGMENT_BREP_MISSING_OR_HEIGHT_DRIFT:" + guid)
        identified.append({
            "guid": guid,
            "segmentGuid": segment_guid,
            "originXY": {"x": org["x"], "y": org["y"]},
            "zCoordinate": d.get("zCoordinate"),
            "height": d["height"],
            "width": d["width"],
            "depth": d["depth"],
            "axisRotationAngle": d.get("axisRotationAngle"),
            "materialGuid": material,
            "segmentBounds3D": bb,
            "type": "Column",
        })
    prototype = next((x for x in identified
                      if x["guid"] == KNOWN_PROTOTYPE), None)
    require(prototype is not None, "EXISTING_LIVE_STUD_PROTOTYPE_BREP_OR_MATERIAL_DRIFT")
    require(close(prototype["originXY"]["x"], 3.53)
            and close(prototype["originXY"]["y"], 9.255),
            "STUD_PROTOTYPE_SOURCE_COORDINATE_DRIFT")
    require(len(identified) >= 13, "LESS_THAN_THIRTEEN_PREVIOUSLY_CREATED_STUDS")
    after = set(APA.inventory_guids(api))
    require(after == known and api.write_attempts == 0,
            "READ_ATTEMPT_MUTATED_NATIVE_INVENTORY")
    require(sha(WORKING) == WORKING_SHA and sha(ORIGINAL) == ORIGINAL_SHA,
            "READ_CHANGED_SAVED_PLN")

    report = {
        "schema": "APA_BDD_BLOCK114_EXISTING_STUD_PROTOTYPE_V1",
        "status": "NATIVE_STUD_PROTOTYPE_READBACK_PASS",
        "workingPlnSHA256": WORKING_SHA,
        "guidCount": len(after),
        "studFamilyCount": len(identified),
        "studPrototypes": identified,
        "preferredSourcePrototype": prototype,
        "relativeCentersMm": [25, 442, 860, 1272, 1685, 2285, 2885],
        "block114GlobalXY": "NOT_NUMERICALLY_VERIFIED",
        "nativeReadCommands": [
            "GetProjectInfo", "GetStories", "API.GetProductInfo",
            "GetAllElements", "GetModelDumpV1", "GetDetailsOfElements"
        ],
        "modelWrites": api.write_attempts,
        "sourceOrWorkingPlnSaved": False,
        "nativeWritePermission": False,
        "next": "Source-verify global XY and axis/orientation for block 1.14 before one guarded copy batch",
    }
    local = folder / "summary.json"
    local.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                     encoding="utf-8")
    print("APA_STATUS:", report["status"])
    print("GUIDS:", report["guidCount"])
    print("WOOD_STUDS:", len(identified))
    print("PROTOTYPE:", prototype["guid"], prototype["originXY"])
    print("MODEL_WRITES: 0")
    print("REPORT:", local)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    remote = "safe-bim-mailbox/gpt-live/results/apa-bdd-block114-prototype-" + stamp + "-" + uuid4().hex[:8] + ".json"
    payload = {
        "branch": "main",
        "message": "BDD block 1.14 verified existing native timber prototype (read only)",
        "content": base64.b64encode(local.read_bytes()).decode("ascii"),
    }
    body = folder / "upload.json"
    body.write_text(json.dumps(payload), encoding="utf-8")
    result = subprocess.run(
        ["gh", "api", "--method", "PUT",
         f"repos/{BRIDGE}/contents/{remote}",
         "--input", str(body), "--jq", ".content.html_url"],
        capture_output=True, timeout=50
    )
    require(result.returncode == 0,
            "PREVIEW_READY_BUT_REPORT_UPLOAD_FAILED")
    print("PUBLISHED:", result.stdout.decode("utf-8").strip())


if __name__ == "__main__":
    try:
        run()
    except Exception as exc:
        print("APA_STATUS: BLOCKED_NO_MODEL_CHANGES")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
