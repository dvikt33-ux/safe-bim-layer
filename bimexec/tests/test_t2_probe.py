"""Focused regression tests for the guarded live T2 wall probe.

These tests never import/connect to Archicad. They exercise the orchestration
contract around the first geometry write: exactly one create attempt, independent
set-diff identification, layer/marker round-trips, and fail-closed UNKNOWN when a
create may have applied before an exception.
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROBES = os.path.join(ROOT, "probes")
sys.path.insert(0, PROBES)

import probe_t2_live_v13 as t2

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


class FakeT2Backend:
    def __init__(self, port=19723):
        self.port = port
        self.guids = [t2.WITNESS]
        self.walls = {t2.WITNESS}
        self.layer_index = {t2.WITNESS: t2.LAYER_INDEX}
        self.layer_name = {t2.WITNESS: t2.LAYER_NAME}
        self.element_id = {t2.WITNESS: "W-WITNESS"}
        self.created_payload = None
        self.create_calls = 0
        self.layer_calls = 0

    def available(self):
        return True, "fake T2 backend"

    def addon_version(self):
        return t2.ADDON

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
        return [{"index": t2.FLOOR, "name": t2.STORY, "elevation": t2.ELEV}]

    def all_elements(self):
        return list(self.guids)

    def elements_by_type(self, element_type):
        return sorted(self.walls) if element_type == "Wall" else []

    def count_by_type(self):
        return {
            "Wall": len(self.walls),
            "Slab": 0,
            "Window": 0,
            "Door": 0,
            "Column": 0,
            "Zone": 0,
        }

    def details_raw(self, guid):
        if guid == t2.WITNESS:
            return {
                "type": "Wall",
                "id": self.element_id[guid],
                "floorIndex": t2.FLOOR,
                "layerIndex": self.layer_index[guid],
                "details": {
                    "structureType": "Composite",
                    "compositeId": {"guid": "COMP-T2-FAKE"},
                    "height": t2.HEIGHT,
                    "begThickness": t2.THICK,
                    "endThickness": t2.THICK,
                    "referenceLineLocation": t2.REFLINE,
                    "offset": t2.OFFSET,
                    "arcAngle": t2.ARC,
                },
            }
        if guid not in self.guids:
            return None
        return {
            "type": "Wall",
            "id": self.element_id[guid],
            "floorIndex": t2.FLOOR,
            "layerIndex": self.layer_index[guid],
            "details": {
                "height": t2.HEIGHT,
                "begCoordinate": {"x": t2.P0[0], "y": t2.P0[1]},
                "endCoordinate": {"x": t2.P1[0], "y": t2.P1[1]},
                "begThickness": t2.THICK,
                "endThickness": t2.THICK,
                "referenceLineLocation": t2.REFLINE,
                "offset": t2.OFFSET,
                "arcAngle": t2.ARC,
            },
        }

    def details(self, guid):
        raw = self.details_raw(guid)
        if not raw:
            return None
        if guid == t2.WITNESS:
            return {
                "type": "Wall",
                "floor_index": t2.FLOOR,
                "layer_index": self.layer_index[guid],
            }
        return {
            "type": "Wall",
            "floor_index": t2.FLOOR,
            "layer_index": self.layer_index[guid],
            "ref_line": {"from": list(t2.P0), "to": list(t2.P1)},
            "length": 5.0,
            "angle": 0.0,
            "height": t2.HEIGHT,
            "thickness": t2.THICK,
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
            rows.append({
                "boundingBox3D": {
                    "xMin": 100.0, "yMin": 100.0, "zMin": 0.0,
                    "xMax": 101.0, "yMax": 101.0, "zMax": 3.0,
                }
            })
        return {"boundingBoxes3D": rows}


def _apply_create(backend: FakeT2Backend, payload):
    backend.create_calls += 1
    assert backend.create_calls == 1, "T2 must never retry CreateWalls"
    assert payload["wallsData"][0]["begCoordinate"] == {"x": 1.5, "y": 2.5}
    assert payload["wallsData"][0]["endCoordinate"] == {"x": 6.5, "y": 2.5}
    guid = "T2-NEW-WALL"
    backend.created_payload = payload
    backend.guids.append(guid)
    backend.walls.add(guid)
    backend.layer_index[guid] = 1
    backend.layer_name[guid] = "Default Layer"
    backend.element_id[guid] = "W-T2-ORIGINAL"
    return guid


def _set_layer(backend: FakeT2Backend, guid):
    backend.layer_calls += 1
    assert backend.layer_calls == 1
    backend.layer_index[guid] = t2.LAYER_INDEX
    backend.layer_name[guid] = t2.LAYER_NAME


def _run_main(backend, out, report, create_fn):
    old_backend = t2.TapirBackendV13
    old_create = t2.create_once
    old_layer = t2.set_layer_once
    old_argv = sys.argv[:]
    try:
        t2.TapirBackendV13 = lambda port=19723: backend
        t2.create_once = create_fn
        t2.set_layer_once = _set_layer
        sys.argv = [
            "probe_t2_live_v13.py",
            "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
            "--port", "19723",
            "--out", out,
            "--report", report,
            "--allow-write",
            "--i-understand-this-writes-to-archicad",
        ]
        return t2.main()
    finally:
        t2.TapirBackendV13 = old_backend
        t2.create_once = old_create
        t2.set_layer_once = old_layer
        sys.argv = old_argv


@test
def t2_happy_path_is_single_attempt_and_machine_go():
    backend = FakeT2Backend()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")

        def create_once(b, payload):
            return [_apply_create(b, payload)]

        rc = _run_main(backend, out, report, create_once)
        assert rc == 0
        assert backend.create_calls == 1
        assert backend.layer_calls == 1
        assert len(backend.walls) == 2

        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)

        assert receipt["status"] == "MACHINE_OK_VISUAL_PENDING"
        assert receipt["artifact"]["guid"] == "T2-NEW-WALL"
        assert receipt["cleanup"] is None
        assert rep["verdicts"]["t2_machine_go"] is True
        assert rep["verdicts"]["production_integration_ready"] is False
        assert rep["capabilities"]["create_wall"]["production_safe"] is False
        assert rep["capabilities"]["create_wall"]["probe_certified"] is False
        assert rep["results"]["wrong_height_rejected"] is True
        assert backend.element_id["T2-NEW-WALL"] == "W-T2-ORIGINAL"
        assert not any(v.startswith(t2.PREFIX) for v in backend.element_id.values())


@test
def t2_create_applied_then_exception_is_unknown_and_never_retried():
    backend = FakeT2Backend()
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        report = os.path.join(d, "report.json")

        def create_then_timeout(b, payload):
            _apply_create(b, payload)
            raise RuntimeError("simulated timeout after apply")

        rc = _run_main(backend, out, report, create_then_timeout)
        assert rc == 1
        assert backend.create_calls == 1
        assert len(backend.walls) == 2, "simulated create applied before timeout"
        assert not os.path.exists(report)

        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        assert receipt["status"] == "UNKNOWN"
        assert receipt["stopped_at_stage"] == "CREATE_DISPATCH"
        assert receipt["cleanup"]["action"].startswith("DO NOT RETRY")


@test
def t2_one_write_flag_refuses_before_any_backend_or_receipt():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        old_argv = sys.argv[:]
        try:
            sys.argv = [
                "probe_t2_live_v13.py",
                "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                "--out", out,
                "--allow-write",
            ]
            rc = t2.main()
        finally:
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(out)
