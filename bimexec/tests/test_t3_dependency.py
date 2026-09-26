"""Focused regressions for audit T3 dependency probe. No Archicad connection."""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROBES = os.path.join(ROOT, "probes")
sys.path.insert(0, PROBES)

import probe_t3_dependency_v13 as t3
import probe_t2_connections_v13 as t2c

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


class FakeT3Backend:
    def __init__(self, port=19723, wall_bad=False, wrong_owner=False):
        self.port = port
        self.wall_bad = wall_bad
        self.wrong_owner = wrong_owner
        self.origin = (20.0, 20.0)
        self.guids = [t2c.WITNESS]
        self.walls = {t2c.WITNESS}
        self.openings = set()
        self.layer_index = {t2c.WITNESS: t2c.LAYER_INDEX}
        self.layer_name = {t2c.WITNESS: t2c.LAYER_NAME}
        self.element_id = {t2c.WITNESS: "W-WITNESS"}
        self.wall_calls = 0
        self.layer_calls = 0
        self.opening_calls = 0
        self.opening_owner = {}

    def available(self):
        return True, "fake T3 backend"

    def addon_version(self):
        return t3.ADDON

    def project_info(self):
        return {
            "port": self.port,
            "project_path": r"C:\Users\Admin\Downloads\MCP_TEST.pln",
            "project_name": "MCP_TEST",
            "is_untitled": False,
            "is_teamwork": False,
            "archicad_version": "29",
            "archicad_build": "29.3001",
        }

    def stories(self):
        return [{"index": t2c.FLOOR, "name": t2c.STORY, "elevation": t2c.ELEV}]

    def all_elements(self):
        return list(self.guids)

    def elements_by_type(self, element_type):
        if element_type == "Wall":
            return sorted(self.walls)
        if element_type == "Opening":
            return sorted(self.openings)
        return []

    def count_by_type(self):
        return {"Wall": len(self.walls), "Opening": len(self.openings)}

    def details_raw(self, guid):
        if guid == t2c.WITNESS:
            return {
                "type": "Wall",
                "id": self.element_id[guid],
                "floorIndex": t2c.FLOOR,
                "layerIndex": self.layer_index[guid],
                "details": {
                    "structureType": "Composite",
                    "compositeId": {"guid": "COMP-T3-FAKE"},
                    "height": t2c.HEIGHT,
                    "begThickness": t2c.THICK,
                    "endThickness": t2c.THICK,
                    "referenceLineLocation": t2c.REFLINE,
                    "offset": t2c.OFFSET,
                    "arcAngle": t2c.ARC,
                },
            }
        if guid in self.walls:
            ox, oy = self.origin
            return {
                "type": "Wall",
                "id": self.element_id[guid],
                "floorIndex": t2c.FLOOR,
                "layerIndex": self.layer_index[guid],
                "details": {
                    "structureType": "Composite",
                    "compositeId": {"guid": "COMP-T3-FAKE"},
                    "height": 4.0 if self.wall_bad else t2c.HEIGHT,
                    "begCoordinate": {"x": ox, "y": oy},
                    "endCoordinate": {"x": ox + t3.WALL_LENGTH, "y": oy},
                    "begThickness": t2c.THICK,
                    "endThickness": t2c.THICK,
                    "referenceLineLocation": t2c.REFLINE,
                    "offset": t2c.OFFSET,
                    "arcAngle": t2c.ARC,
                },
            }
        if guid in self.openings:
            x, y, z = t3.opening_base(self.origin)
            return {
                "type": "Opening",
                "id": self.element_id[guid],
                "floorIndex": t2c.FLOOR,
                "layerIndex": t2c.LAYER_INDEX,
                "details": {
                    "ownerElementId": {"guid": self.opening_owner[guid]},
                    "basePoint": {"x": x, "y": y, "z": z},
                    "width": t3.OPENING_WIDTH,
                    "height": t3.OPENING_HEIGHT,
                },
            }
        return None

    def details(self, guid):
        if guid not in self.walls:
            return None
        ox, oy = self.origin
        return {
            "type": "Wall",
            "floor_index": t2c.FLOOR,
            "layer_index": self.layer_index[guid],
            "ref_line": {"from": [ox, oy], "to": [ox + t3.WALL_LENGTH, oy]},
            "length": t3.WALL_LENGTH,
            "angle": 0.0,
            "height": 4.0 if self.wall_bad else t2c.HEIGHT,
            "thickness": t2c.THICK,
        }

    def get_property_values(self, ref, guids):
        if ref.get("id") == "General_ElementID":
            return {g: self.element_id.get(g) for g in guids}
        if ref.get("address") == "ModelView_LayerName":
            return {g: self.layer_name.get(g) for g in guids}
        raise AssertionError(f"unexpected property ref: {ref}")

    def set_property_value(self, guid, ref, value):
        assert ref.get("id") == "General_ElementID"
        assert guid in self.guids
        self.element_id[guid] = value

    def raw_call(self, command, payload=None):
        assert command == "Get3DBoundingBoxes"
        rows = []
        for item in (payload or {}).get("elements", []):
            guid = item["elementId"]["guid"]
            assert guid in self.guids
            if guid == t2c.WITNESS:
                box = [100.0, 100.0, 0.0, 101.0, 101.0, 3.0]
            elif guid in self.walls:
                ox, oy = self.origin
                box = [ox, oy - 0.2, 0.0, ox + t3.WALL_LENGTH, oy + 0.2, 3.0]
            else:
                box = [100.0, 100.0, 0.0, 101.0, 101.0, 1.0]
            rows.append({"boundingBox3D": {
                "xMin": box[0], "yMin": box[1], "zMin": box[2],
                "xMax": box[3], "yMax": box[4], "zMax": box[5],
            }})
        return {"boundingBoxes3D": rows}


def _apply_wall(backend: FakeT3Backend, payload):
    backend.wall_calls += 1
    assert backend.wall_calls == 1
    item = payload["wallsData"][0]
    backend.origin = (float(item["begCoordinate"]["x"]), float(item["begCoordinate"]["y"]))
    guid = "T3-HOST-WALL"
    backend.guids.append(guid)
    backend.walls.add(guid)
    backend.layer_index[guid] = 1
    backend.layer_name[guid] = "Default Layer"
    backend.element_id[guid] = "W-T3-ORIGINAL"
    return guid


def _set_layer(backend: FakeT3Backend, guid):
    backend.layer_calls += 1
    assert backend.layer_calls == 1
    backend.layer_index[guid] = t2c.LAYER_INDEX
    backend.layer_name[guid] = t2c.LAYER_NAME


def _apply_opening(backend: FakeT3Backend, payload):
    backend.opening_calls += 1
    assert backend.opening_calls == 1
    item = payload["openingsData"][0]
    requested_owner = item["ownerElementId"]["guid"]
    guid = "T3-OPENING"
    backend.guids.append(guid)
    backend.openings.add(guid)
    backend.element_id[guid] = "O-T3"
    backend.layer_index[guid] = t2c.LAYER_INDEX
    backend.layer_name[guid] = t2c.LAYER_NAME
    backend.opening_owner[guid] = "FOREIGN-WALL" if backend.wrong_owner else requested_owner
    return guid


def _run_main(backend, out, report):
    old_backend = t3.TapirBackendV13
    old_wall = t3.create_wall_once
    old_layer = t3.set_layer_once
    old_open = t3.create_opening_once
    old_argv = sys.argv[:]
    try:
        t3.TapirBackendV13 = lambda port=19723: backend
        t3.create_wall_once = lambda b, p: [_apply_wall(b, p)]
        t3.set_layer_once = _set_layer
        t3.create_opening_once = lambda b, p: [_apply_opening(b, p)]
        sys.argv = [
            "probe_t3_dependency_v13.py",
            "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
            "--port", "19723",
            "--origin-x", "20.0",
            "--origin-y", "20.0",
            "--out", out,
            "--report", report,
            "--allow-write",
            "--i-understand-this-writes-to-archicad",
        ]
        return t3.main()
    finally:
        t3.TapirBackendV13 = old_backend
        t3.create_wall_once = old_wall
        t3.set_layer_once = old_layer
        t3.create_opening_once = old_open
        sys.argv = old_argv


@test
def audit_t3_happy_path_enforces_package_order_and_owner_binding():
    backend = FakeT3Backend()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")
        rc = _run_main(backend, out, report)
        assert rc == 0
        assert backend.wall_calls == 1
        assert backend.opening_calls == 1
        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert receipt["packages"] == {t3.PKG01: "COMPLETED", t3.PKG02: "COMPLETED", t3.PKG04: "COMPLETED"}
        stages = receipt["stages"]
        wall_done = next(i for i, s in enumerate(stages) if s.get("stage") == "PACKAGE_COMPLETED" and s.get("package") == t3.PKG02)
        opening_intent = next(i for i, s in enumerate(stages) if s.get("stage") == "OPENING_CREATE_INTENT")
        assert wall_done < opening_intent
        assert rep["results"]["opening_dispatched_after_wall_completed"] is True
        assert rep["results"]["opening_bound_to_confirmed_wall"] is True
        assert rep["mapping"]["opening"]["owner_wall_guid"] == "T3-HOST-WALL"


@test
def audit_t3_bad_wall_halts_before_opening_dispatch():
    backend = FakeT3Backend(wall_bad=True)
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")
        rc = _run_main(backend, out, report)
        assert rc == 1
        assert backend.wall_calls == 1
        assert backend.opening_calls == 0
        assert not os.path.exists(report)
        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        assert receipt["status"] == "VERIFY_FAILED"
        assert receipt["packages"][t3.PKG02] == "RUNNING"
        assert receipt["packages"][t3.PKG04] == "PENDING"


@test
def audit_t3_wrong_opening_owner_is_verify_failed_not_success():
    backend = FakeT3Backend(wrong_owner=True)
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")
        rc = _run_main(backend, out, report)
        assert rc == 1
        assert backend.wall_calls == 1
        assert backend.opening_calls == 1
        assert not os.path.exists(report)
        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        assert receipt["status"] == "VERIFY_FAILED"
        assert receipt["stopped_at_stage"] == "OPENING_VERIFY"
        assert receipt["packages"][t3.PKG02] == "COMPLETED"
        assert receipt["packages"][t3.PKG04] == "RUNNING"


@test
def audit_t3_live_requires_explicit_origin_before_backend():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        old_argv = sys.argv[:]
        try:
            sys.argv = [
                "probe_t3_dependency_v13.py",
                "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                "--out", out,
                "--allow-write",
                "--i-understand-this-writes-to-archicad",
            ]
            rc = t3.main()
        finally:
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(out)
