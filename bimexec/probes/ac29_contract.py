"""Shared AC29 / Tapir 1.5.9 contract, extracted from the T1/T2 live helpers.

No connection on import, no retries, no certification flags. The only write
schema here is the single straight Composite/CoreOutside wall recipe. T0's
mutation denylist is NOT changed. Calling create_wall_once requires the caller's
write gate; this module is a wire contract, not an execution/recovery engine.
"""
from __future__ import annotations

from functools import wraps
import math
import uuid
from typing import Any

import backends as base

ADDON_VERSION = "1.5.9"
ELEMENT_ID_REF = {"kind": "builtin", "id": "General_ElementID"}
LAYER_REF = {"kind": "name", "address": "ModelView_LayerName"}


def backend_boundary(fn):
    """Normalize wire/read failures without converting them to empty results."""
    @wraps(fn)
    def call(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except base.BackendError:
            raise
        except Exception as exc:
            raise base.BackendError(f"{fn.__name__}: {type(exc).__name__}: {exc}") from exc
    return call


def number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise base.BackendError(f"{field}: finite number required")
    return float(value)


def rows(response: Any, key: str, command: str) -> list[Any]:
    """Only an explicit array can prove an empty result. None/error != []."""
    if isinstance(response, list):
        return response
    d = base._to_dict(response)
    if d.get("error") or d.get("success") is False or not isinstance(d.get(key), list):
        raise base.BackendError(f"{command}: unavailable/malformed response: {d!r}")
    return d[key]


def element_guids(response: Any, command: str) -> list[str]:
    result = []
    for item in rows(response, "elements", command):
        row = base._to_dict(item)
        element = base._to_dict(row.get("elementId")) if "elementId" in row else row
        guid = element.get("guid")
        if isinstance(guid, uuid.UUID):
            guid = str(guid)
        if row.get("error") or not isinstance(guid, str) or not guid.strip():
            raise base.BackendError(f"{command}: invalid element row: {row!r}")
        if guid in result:
            raise base.BackendError(f"{command}: duplicate GUID {guid}")
        result.append(guid)
    return result


def story_map(response: Any) -> list[dict[str, Any]]:
    result, indices = [], set()
    for item in rows(response, "stories", "GetStories"):
        s = base._to_dict(item)
        index = s.get("index")
        if s.get("error") or type(index) is not int or index in indices:
            raise base.BackendError("GetStories: missing/duplicate explicit index")
        indices.add(index)
        name = s.get("name")
        if not isinstance(name, str) or not name.strip():
            name = None  # T0 criterion and runtime resolver both fail closed.
        result.append({"index": index, "name": name,
                       "elevation": number(s.get("level"), "story.level")})
    if not result:
        raise base.BackendError("GetStories: no story mapping")
    return result


def resolve_story(stories: list[dict[str, Any]], expected: dict[str, Any]) -> int:
    if not isinstance(expected, dict) or not isinstance(expected.get("name"), str) or not expected["name"].strip():
        raise base.BackendError("story requires a nonblank name and elevation")
    elevation = number(expected.get("elevation"), "story.elevation")
    matches = [s for s in stories if s.get("name") == expected["name"]
               and abs(number(s.get("elevation"), "story.elevation") - elevation) <= 1e-6]
    if len(matches) != 1 or type(matches[0].get("index")) is not int:
        raise base.BackendError("story name+elevation does not resolve to one explicit index")
    return matches[0]["index"]


def wall_payload(start: Any, end: Any, *, floor_index: int, height: float,
                 thickness: float, reference_line: str, structure_type: str,
                 composite_id: str) -> dict[str, Any]:
    """Exactly the T1/T2/T3/T4/T5 recipe; no Basic/profile/arc/top-link guessing."""
    if type(floor_index) is not int:
        raise base.BackendError("explicit resolved floorIndex required")
    for point in (start, end):
        if not isinstance(point, (list, tuple)) or len(point) != 2:
            raise base.BackendError("wall requires two 2D endpoints")
        for v in point:
            number(v, "wall.coordinate")
    if list(start) == list(end):
        raise base.BackendError("zero length wall")
    if (number(height, "height") != 3.0 or number(thickness, "thickness") != 0.30
            or reference_line != "CoreOutside" or structure_type != "Composite"
            or not isinstance(composite_id, str) or not composite_id.strip()):
        raise base.BackendError("outside tested straight Composite/CoreOutside h=3 t=0.30 recipe")
    return {"wallsData": [{
        "begCoordinate": {"x": start[0], "y": start[1]},
        "endCoordinate": {"x": end[0], "y": end[1]},
        "floorIndex": floor_index,
        "zCoordinate": 0.0,
        "height": height,
        "thickness": thickness,
        "offset": 0.0,
        "arcAngle": 0.0,
        "referenceLineLocation": reference_line,
        "structureType": structure_type,
        "compositeId": {"guid": composite_id},
    }]}


def create_wall_once(backend: Any, payload: dict[str, Any]) -> list[str]:
    """One dispatch, never retry. No SetDetails/marker/cleanup side effects."""
    # Reject direct use with an alternate schema or unsupported fields/recipe.
    try:
        walls = payload["wallsData"]
        if not isinstance(walls, list) or len(walls) != 1:
            raise base.BackendError("single wall only")
        w = walls[0]
        expected = wall_payload(
            [w["begCoordinate"]["x"], w["begCoordinate"]["y"]],
            [w["endCoordinate"]["x"], w["endCoordinate"]["y"]],
            floor_index=w["floorIndex"], height=w["height"], thickness=w["thickness"],
            reference_line=w["referenceLineLocation"], structure_type=w["structureType"],
            composite_id=w["compositeId"]["guid"])
        if payload != expected:
            raise base.BackendError("payload differs from tested wall contract")
    except (KeyError, TypeError, IndexError) as exc:
        raise base.BackendError("invalid wall payload") from exc
    backend._connect()
    act = backend.conn.types
    response = backend.conn.commands.ExecuteAddOnCommand(
        act.AddOnCommandId(backend.ns, "CreateWalls"), payload)
    guids = element_guids(response, "CreateWalls")
    if len(guids) != 1:
        raise base.BackendError("CreateWalls outcome unavailable/ambiguous; DO NOT RETRY")
    return guids  # Candidate only, NOT a confirmed mapping.


def observe_wall(backend: Any, guid: str, stories: list[dict[str, Any]]) -> dict[str, Any]:
    """T2 read helper shared by probes and runtime; no guessed geometry fields."""
    raw = backend.details_raw(guid)
    if not isinstance(raw, dict) or not raw or raw.get("error"):
        raise base.BackendError("wall details unavailable")
    norm = base._normalize_tapir_details(raw)
    det = raw.get("details") if isinstance(raw.get("details"), dict) else {}
    out = {k: v for k, v in norm.items() if v is not None}
    out["type"] = norm.get("type") or raw.get("type")
    out["floor_index"] = raw.get("floorIndex")
    matches = [s for s in stories if s.get("index") == raw.get("floorIndex")]
    if type(raw.get("floorIndex")) is not int or len(matches) != 1 or not matches[0].get("name"):
        raise base.BackendError("wall floorIndex has no unique named story mapping")
    st = matches[0]
    out["story"] = {"name": st["name"], "elevation": number(st.get("elevation"), "story.elevation")}
    out["layer_index"] = raw.get("layerIndex")
    values = backend.get_property_values(LAYER_REF, [guid])
    out["layer"] = values.get(guid) if isinstance(values, dict) else None
    if not isinstance(out["layer"], str) or not out["layer"]:
        raise base.BackendError("wall layer name unavailable")
    out["height"] = number(det.get("height"), "wall.height")
    bt, et = number(det.get("begThickness"), "begThickness"), number(det.get("endThickness"), "endThickness")
    if abs(bt - et) > 1e-9:
        raise base.BackendError("nonuniform wall thickness outside tested read contract")
    out["thickness"] = bt
    out["_extra"] = {k: det.get(k) for k in ("referenceLineLocation", "offset", "arcAngle", "structureType")}
    out["_extra"]["compositeId"] = base._to_dict(det.get("compositeId"))
    line = out.get("ref_line") or {}
    for end in ("from", "to"):
        point = line.get(end)
        if not isinstance(point, list) or len(point) != 2:
            raise base.BackendError("wall endpoints unavailable")
        for v in point:
            number(v, "wall.endpoint")
    if out["type"] != "Wall":
        raise base.BackendError("only Wall details covered by this read contract")
    return out
