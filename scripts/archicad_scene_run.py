"""Guarded one-shot native Archicad scene writer: 12 related BIM elements.

DELIBERATELY NOT a Mailbox recipe; no daemon and no remote activation.
Default is a read-only preflight. --execute requires a matching plan hash
printed by preflight and a unique scene ID. Exactly ONE local saved test PLN.
NO save, switch, retry, delete or rollback. Partial scenes require inspection.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import sys
import traceback

from archicad_guarded_wall_probe import tapir
import archicad_scene_v1 as SCENE

PORT = 19723
EXPECTED_NAME = "Тест MER "
EXPECTED_PATH = r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\Тест MER .pln"
EXPECTED_TAPIR = "1.5.10"
ALLOWED_WRITES = frozenset(("CreateWalls", "CreateSlabs", "CreateColumns",
                           "CreateWindows", "CreateDoors"))
_GUID = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")
_SCENE_ID = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_-]{3,79}$")
_NONSPATIAL_TYPES = frozenset({
    "Dimension", "RadialDimension", "LevelDimension", "AngleDimension",
    "Text", "Label", "Hatch", "Line", "PolyLine", "Arc", "Circle",
    "Spline", "Hotspot", "CutPlane", "Camera", "CamSet", "Group",
    "SectElem", "Drawing", "Picture", "Detail", "Elevation",
    "InteriorElevation", "Worksheet", "ChangeMarker",
})



def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def close(a, b, tolerance=1e-5):
    return (type(a) in (int, float) and type(b) in (int, float)
            and math.isfinite(a) and math.isfinite(b)
            and abs(a-b) <= tolerance)


def guarded_project(api):
    info = api("GetProjectInfo", {})
    if (not isinstance(info, dict) or info.get("projectName") != EXPECTED_NAME
            or info.get("projectPath") != EXPECTED_PATH
            or info.get("isUntitled") is not False
            or info.get("isTeamwork") is not False):
        raise ValueError("WRONG_PROJECT: exact test PLN (including trailing space) required")
    stories = api("GetStories", {})
    floor = next((x for x in stories.get("stories", [])
                  if x.get("index") == 0), None)
    if (stories.get("actStory") != 0 or not isinstance(floor, dict)
            or floor.get("floorId") != 1 or not close(floor.get("level"), 0)):
        raise ValueError("STORY_MISMATCH: require active first story, native index 0 / floorId 1")
    version = api("GetAddOnVersion", {}).get("version")
    if version != EXPECTED_TAPIR:
        raise ValueError(f"TAPIR_VERSION_MISMATCH: {version!r} != {EXPECTED_TAPIR}")
    return {"path": info["projectPath"], "name": info["projectName"],
            "port": PORT, "tapirVersion": version, "storyIndex": 0}


def scan_for_existing_geometry(api, anchor_x, anchor_y):
    """Conservatively refuse if an existing 3D body touches the scene envelope.

    Every existing element is scanned, not just selected Walls. Malformed,
    unsupported or incomplete API responses block all scene writes.
    """
    all_elements = api("GetAllElements", {})
    elements = all_elements.get("elements") if isinstance(all_elements, dict) else None
    if not isinstance(elements, list) or len(elements) > 50000:
        raise ValueError("SPATIAL_SCAN_UNAVAILABLE: missing/oversized native inventory")
    lowx, highx = anchor_x-.35, anchor_x+SCENE.WIDTH+.35
    lowy, highy = anchor_y-.35, anchor_y+SCENE.DEPTH+.35
    lowz, highz = -SCENE.SLAB_THICKNESS-.1, SCENE.HEIGHT+.1
    checked = 0
    nonspatial = 0
    # Batch modestly; do not hold a massive JSON response in memory.
    for i in range(0, len(elements), 100):
        batch = elements[i:i+100]
        if any(not isinstance(v, dict) or not _GUID.fullmatch(str(
               v.get("elementId", {}).get("guid", ""))) for v in batch):
            raise ValueError("SPATIAL_SCAN_UNAVAILABLE: invalid element GUID row")
        boxes = api("Get3DBoundingBoxes", {"elements": batch})
        rows = boxes.get("boundingBoxes3D") if isinstance(boxes, dict) else None
        if not isinstance(rows, list) or len(rows) != len(batch):
            raise ValueError("SPATIAL_SCAN_UNAVAILABLE: incomplete 3D boxes")
        # Some plan annotations have no 3D body. Their explicit native
        # geometry errors can be ignored ONLY after typed native classification;
        # unsupported 3D objects or unknown failures still stop all writes.
        unavailable = []
        keys = ("xMin", "xMax", "yMin", "yMax", "zMin", "zMax")
        for index, item in enumerate(rows):
            b = item.get("boundingBox3D") if isinstance(item, dict) else None
            if b is None and isinstance(item, dict) and "error" in item:
                unavailable.append(batch[index])
                continue
            if (not isinstance(b, dict) or not all(
                    type(b.get(k)) in (int, float) and math.isfinite(b[k])
                    for k in keys)):
                raise ValueError("SPATIAL_SCAN_UNAVAILABLE: invalid 3D bbox")
            if (b["xMin"] > b["xMax"] or b["yMin"] > b["yMax"]
                    or b["zMin"] > b["zMax"]):
                raise ValueError("SPATIAL_SCAN_UNAVAILABLE: inverted 3D bbox")
            if (b["xMin"] <= highx and b["xMax"] >= lowx
                    and b["yMin"] <= highy and b["yMax"] >= lowy
                    and b["zMin"] <= highz and b["zMax"] >= lowz):
                raise ValueError("SPATIAL_COLLISION: existing element inside scene envelope")
            checked += 1
        if unavailable:
            classified = api("GetDetailsOfElements", {"elements": unavailable})
            types = classified.get("detailsOfElements") if isinstance(classified, dict) else None
            if (not isinstance(types, list) or len(types) != len(unavailable)
                    or any(not isinstance(t, dict)
                           or t.get("type") not in _NONSPATIAL_TYPES for t in types)):
                raise ValueError("SPATIAL_SCAN_UNAVAILABLE: unbounded 3D/unknown element")
            nonspatial += len(unavailable)
    return {"nativeElementsInspected": checked+nonspatial,
            "volumetricBodiesChecked": checked,
            "nonSpatialElementsVerified": nonspatial}


def requested_details(api, guid):
    output = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": guid}}]})
    rows = output.get("detailsOfElements") if isinstance(output, dict) else None
    if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict):
        raise ValueError("NATIVE_READBACK: expected one typed detail row")
    return rows[0]


def resolve_params(step, created):
    """Replace ONLY generated parent Wall GUID for Windows or Doors."""
    command = step["command"]
    key = command[6:].lower()+"Data"
    # CreateWalls -> wallsData, CreateWindows -> windowsData, etc.
    params = json.loads(canonical(step["params"]))
    data = params[key]
    if not isinstance(data, list) or len(data) != 1:
        raise ValueError("only one element per native mutation supported")
    item = data[0]
    if command in ("CreateWindows", "CreateDoors"):
        owner = item.get("ownerWallId")
        ref = owner.get("guid") if isinstance(owner, dict) else None
        if not isinstance(ref, dict) or set(ref) != {"$createdGuid"}:
            raise ValueError("hosted opening must reference a generated Wall")
        sid = ref["$createdGuid"]
        if sid not in created or created[sid]["kind"] != "Wall":
            raise ValueError("hosted opening missing verified parent Wall GUID")
        item["ownerWallId"] = {"guid": created[sid]["guid"]}
    return params


def compare_polygon(expected, actual):
    if not isinstance(actual, list) or len(actual) not in (len(expected), len(expected)+1):
        return False
    actual = list(actual)
    if len(actual) == len(expected)+1:
        if not (close(actual[-1].get("x"), actual[0].get("x"))
                and close(actual[-1].get("y"), actual[0].get("y"))):
            return False
        actual.pop()
    want = [(p["x"], p["y"]) for p in expected]
    got = [(p.get("x"), p.get("y")) for p in actual]
    n = len(want)
    return any(all(close(got[(start + direction*i) % n][0], want[i][0])
                   and close(got[(start + direction*i) % n][1], want[i][1])
                   for i in range(n))
               for start in range(n) for direction in (-1, 1))


def verify_readback(command, params, row, owner_guid=None):
    kind = command[6:-1]  # CreateWalls -> Wall, CreateDoors -> Door
    if row.get("type") != kind or row.get("floorIndex") != 0:
        raise ValueError(f"READBACK_TYPE_OR_STORY: expected {kind} on native story 0")
    details = row.get("details")
    if not isinstance(details, dict):
        raise ValueError("READBACK_DETAILS_MISSING")
    k = command[6:].lower()+"Data"
    expected = params[k][0]
    if command == "CreateWalls":
        # Reuse the proven wall's core geometry/type checks.
        for key in ("begCoordinate", "endCoordinate"):
            if any(not close(details.get(key, {}).get(axis), expected[key][axis])
                   for axis in ("x", "y")):
                raise ValueError("WALL_POSITION_READBACK_MISMATCH")
        for source, target in (("height", "height"), ("thickness", "begThickness"),
                               ("thickness", "endThickness"), ("offset", "offset"),
                               ("zCoordinate", "zCoordinate"), ("arcAngle", "arcAngle")):
            if not close(details.get(target), expected[source]):
                raise ValueError("WALL_SIZE_READBACK_MISMATCH")
        if any(details.get(k) != v for k, v in (
            ("structureType", "Basic"), ("referenceLineLocation", "Center"),
            ("geometryType", "Straight"))):
            raise ValueError("WALL_TYPE_READBACK_MISMATCH")
    elif command == "CreateSlabs":
        if (not close(details.get("thickness"), expected["thickness"])
                or not close(details.get("level"), expected["level"])
                or not compare_polygon(expected["polygonCoordinates"],
                                       details.get("polygonOutline"))):
            raise ValueError("SLAB_READBACK_MISMATCH")
    elif command == "CreateColumns":
        point = expected["coordinates"]
        origin = details.get("origin", {})
        if (not all(close(origin.get(axis), point[axis]) for axis in ("x", "y"))
                or not all(close(details.get(key), value) for key, value in (
                    ("zCoordinate", point["z"]), ("height", expected["height"]),
                    ("width", expected["width"]), ("depth", expected["depth"])))):
            raise ValueError("COLUMN_READBACK_MISMATCH")
    else:
        owner = details.get("ownerElementId")
        actual_guid = owner.get("guid") if isinstance(owner, dict) else None
        if not isinstance(actual_guid, str) or actual_guid.lower() != owner_guid.lower():
            raise ValueError("HOST_GUID_READBACK_MISMATCH")
        if details.get("ownerElementType") not in (None, "Wall"):
            raise ValueError("HOST_TYPE_READBACK_MISMATCH")
        for field in ("width", "height", "sillHeight", "centerOffset"):
            if not close(details.get(field), expected[field]):
                raise ValueError(f"OPENING_READBACK_MISMATCH: {field}")
    return kind


def created_guid(raw):
    rows = raw.get("elements") if isinstance(raw, dict) else None
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("AMBIGUOUS_CREATE_RESULT: expected one element")
    entry = rows[0]
    guid = entry.get("elementId", {}).get("guid") if isinstance(entry, dict) else None
    if not isinstance(guid, str) or not _GUID.fullmatch(guid):
        raise ValueError("INVALID_CREATED_GUID")
    return guid


def check_previous_wall(api, graph_step, created):
    key = graph_step["params"]
    data = list(key.values())[0][0]
    wallid = data["ownerWallId"]["guid"]["$createdGuid"]
    parent = created.get(wallid)
    if not parent or parent["kind"] != "Wall":
        raise ValueError("MISSING_APPROVED_PARENT_WALL")
    previous_step = next((s for s in created["__plan__"]["operations"]
                          if s["id"] == wallid), None)
    if previous_step is None:
        raise ValueError("PARENT_PLAN_ROW_MISSING")
    row = requested_details(api, parent["guid"])
    verify_readback("CreateWalls", previous_step["params"], row)
    return parent["guid"]


class SceneWriter:
    def __init__(self, api, journal_path):
        self.api = api
        self.journal_path = Path(journal_path)

    def preflight(self, x, y):
        binding = guarded_project(self.api)
        preview = SCENE.prepare(x, y)
        scan_report = scan_for_existing_geometry(self.api, x, y)
        if guarded_project(self.api) != binding:
            raise ValueError("project binding changed during read-only preflight")
        return {**preview, "status": "READY_FOR_EXPLICIT_TEST_RUN",
                "binding": binding, **scan_report,
                "liveWriteAuthorized": False, "plnChanged": False}

    def execute(self, x, y, scene_id, expected_hash):
        if not isinstance(scene_id, str) or not _SCENE_ID.fullmatch(scene_id):
            raise ValueError("invalid durable scene ID")
        preflight = self.preflight(x, y)
        if preflight["sourcePlanHash"] != expected_hash:
            raise ValueError("PLAN_HASH_MISMATCH: get hash from same-anchor dry-run")
        if not self.journal_path.parent.exists():
            raise ValueError("journal state directory must already exist")
        result = {
            "sceneId": scene_id, "planHash": expected_hash, "status": "BLOCKED",
            "plnSaved": False, "automaticRetry": False, "steps": {},
            "sceneDimensions": preflight["metrics"]["dimensionsMeters"],
        }
        with closing(sqlite3.connect(str(self.journal_path))) as db:
            db.execute("PRAGMA synchronous=FULL")
            db.execute("CREATE TABLE IF NOT EXISTS scenes (scene_id TEXT PRIMARY KEY, plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)")
            db.execute("CREATE TABLE IF NOT EXISTS steps (scene_id TEXT NOT NULL, step_id TEXT NOT NULL, state TEXT NOT NULL, guid TEXT, output TEXT NOT NULL, PRIMARY KEY(scene_id,step_id))")
            db.commit()
            db.execute("BEGIN IMMEDIATE")
            if db.execute("SELECT 1 FROM scenes WHERE scene_id=? OR plan_hash=?",
                          (scene_id, expected_hash)).fetchone():
                raise ValueError("SCENE_ALREADY_RESERVED: never replay ambiguous write")
            db.execute("INSERT INTO scenes VALUES (?,?,?,?)",
                       (scene_id, expected_hash, "STARTED", canonical(result)))
            db.commit()
            created = {"__plan__": preflight["graph"]}
            for step_id in preflight["executionOrder"]:
                step = next(s for s in preflight["graph"]["operations"] if s["id"] == step_id)
                command = step["command"]
                if command not in ALLOWED_WRITES:
                    raise ValueError("UNSUPPORTED_WRITE_RECIPE")
                try:
                    # The FULL project identity is freshly checked at every step.
                    if guarded_project(self.api) != preflight["binding"]:
                        raise ValueError("PROJECT_SWITCHED_DURING_SCENE")
                    parent_guid = None
                    if command in ("CreateWindows", "CreateDoors"):
                        parent_guid = check_previous_wall(self.api, step, created)
                    params = resolve_params(step, created)
                    # Bind each operation to its exact resolved (including GUID)
                    # parameters, approved local test scope, source scene and target.
                    intent = {"sceneId": scene_id, "planHash": expected_hash,
                              "stepId": step_id, "command": command,
                              "parameters": params, "target": preflight["binding"]}
                    approval_record = {
                        "operationHash": digest(intent),
                        "permission": command,
                        "scope": EXPECTED_PATH,
                        "approvedBy": "local-explicit--execute-with-matching-plan-hash",
                        "approvedAt": datetime.now(timezone.utc).isoformat(),
                        "approvalSource": "standing-test-PLN-permission",
                    }
                    if approval_record["permission"] not in ALLOWED_WRITES:
                        raise ValueError("UNREVIEWED_WRITE_SCOPE")
                    db.execute("BEGIN IMMEDIATE")
                    db.execute("INSERT INTO steps VALUES (?,?,?,?,?)",
                               (scene_id, step_id, "ATTEMPTED", None, canonical({
                                   "intent": intent, "localApproval": approval_record
                               })))
                    db.commit()  # Durable per-operation approval and intent BEFORE write.
                    if (guarded_project(self.api) != intent["target"]
                            or digest(intent) != approval_record["operationHash"]
                            or approval_record["scope"] != EXPECTED_PATH):
                        raise ValueError("OPERATION_BOUNDARY_APPROVAL_MISMATCH")
                    raw = self.api(command, params)
                    guid = created_guid(raw)
                    db.execute("UPDATE steps SET state='CREATED_UNVERIFIED',guid=? WHERE scene_id=? AND step_id=?",
                               (guid, scene_id, step_id))
                    db.commit()
                    if guarded_project(self.api) != preflight["binding"]:
                        raise ValueError("PROJECT_CHANGED_AFTER_WRITE")
                    row = requested_details(self.api, guid)
                    kind = verify_readback(command, params, row, parent_guid)
                    created[step_id] = {"guid": guid, "kind": kind}
                    result["steps"][step_id] = {"status": "PASS", "guid": guid, "kind": kind}
                    db.execute("UPDATE steps SET state='PASS',output=? WHERE scene_id=? AND step_id=?",
                               (canonical(result["steps"][step_id]), scene_id, step_id))
                    db.commit()
                except Exception as exc:
                    # A native call can succeed and then time out or read back poorly.
                    # Always stop and never retry, undo, or erase the step ledger.
                    result["status"] = "PARTIAL_OR_UNKNOWN_OUTCOME"
                    result["failedStep"] = step_id
                    result["reason"] = type(exc).__name__ + ": " + str(exc)
                    result["manualReconciliationRequired"] = True
                    db.execute("UPDATE scenes SET state=?,result=? WHERE scene_id=?",
                               (result["status"], canonical(result), scene_id))
                    db.commit()
                    return result
            result["status"] = "COMPLETE_UNSAVED"
            result["createdCount"] = len(result["steps"])
            result["allGuidsReadback"] = True
            db.execute("UPDATE scenes SET state=?,result=? WHERE scene_id=?",
                       (result["status"], canonical(result), scene_id))
            db.commit()
            return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anchor-x", type=float, required=True)
    p.add_argument("--anchor-y", type=float, required=True)
    p.add_argument("--data-dir", type=Path, required=True,
                   help="existing local state directory; separate scene journal is added")
    p.add_argument("--execute", action="store_true",
                   help="actually create scene once inside exact pinned test PLN")
    p.add_argument("--scene-id", help="durable unique name, NEVER reuse")
    p.add_argument("--confirm-plan-hash", help="hash printed by read-only preflight")
    args = p.parse_args(argv)
    try:
        api = lambda command, params: tapir(PORT, command, params)
        runner = SceneWriter(api, args.data_dir / "scene-v1-attempts.sqlite3")
        if args.execute:
            if not args.scene_id or not args.confirm_plan_hash:
                raise ValueError("--execute requires --scene-id and --confirm-plan-hash")
            out = runner.execute(args.anchor_x, args.anchor_y,
                                 args.scene_id, args.confirm_plan_hash)
        else:
            out = runner.preflight(args.anchor_x, args.anchor_y)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0 if out["status"] in ("READY_FOR_EXPLICIT_TEST_RUN", "COMPLETE_UNSAVED") else 2
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "reason": str(exc),
                          "automaticRetry": False, "plnSaved": False},
                         ensure_ascii=False))
        return 2


if __name__ == "__main__":
    sys.exit(main())
