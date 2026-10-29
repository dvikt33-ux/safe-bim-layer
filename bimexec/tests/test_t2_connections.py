"""Regression tests for audit T2 connection probe. No Archicad connection."""
from __future__ import annotations

import json
import math
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROBES = os.path.join(ROOT, "probes")
sys.path.insert(0, PROBES)

import probe_t2_connections_v13 as t2c

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


class FakeConnectionsBackend:
    def __init__(self, port=19723, post_join_shift_label=None):
        self.port = port
        self.post_join_shift_label = post_join_shift_label
        self.guids = [t2c.WITNESS]
        self.walls = {t2c.WITNESS}
        self.layer_index = {t2c.WITNESS: t2c.LAYER_INDEX}
        self.layer_name = {t2c.WITNESS: t2c.LAYER_NAME}
        self.element_id = {t2c.WITNESS: "W-WITNESS"}
        self.geometry = {}
        self.label_by_guid = {}
        self.create_calls = 0
        self.layer_calls = 0

    def available(self):
        return True, "fake audit T2 backend"

    def addon_version(self):
        return t2c.ADDON

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
        return sorted(self.walls) if element_type == "Wall" else []

    def count_by_type(self):
        return {
            "Wall": len(self.walls), "Slab": 0, "Window": 0,
            "Door": 0, "Column": 0, "Zone": 0,
        }

    def details_raw(self, guid):
        if guid == t2c.WITNESS:
            return {
                "type": "Wall", "id": self.element_id[guid],
                "floorIndex": t2c.FLOOR, "layerIndex": self.layer_index[guid],
                "details": {
                    "structureType": "Composite",
                    "compositeId": {"guid": "COMP-T2C-FAKE"},
                    "height": t2c.HEIGHT,
                    "begThickness": t2c.THICK, "endThickness": t2c.THICK,
                    "referenceLineLocation": t2c.REFLINE,
                    "offset": t2c.OFFSET, "arcAngle": t2c.ARC,
                },
            }
        if guid not in self.geometry:
            return None
        a, z = self._effective_geometry(guid)
        return {
            "type": "Wall", "id": self.element_id[guid],
            "floorIndex": t2c.FLOOR, "layerIndex": self.layer_index[guid],
            "details": {
                "structureType": "Composite",
                "compositeId": {"guid": "COMP-T2C-FAKE"},
                "height": t2c.HEIGHT,
                "begCoordinate": {"x": a[0], "y": a[1]},
                "endCoordinate": {"x": z[0], "y": z[1]},
                "begThickness": t2c.THICK, "endThickness": t2c.THICK,
                "referenceLineLocation": t2c.REFLINE,
                "offset": t2c.OFFSET, "arcAngle": t2c.ARC,
            },
        }

    def _effective_geometry(self, guid):
        a, z = self.geometry[guid]
        label = self.label_by_guid[guid]
        if self.post_join_shift_label == label and len(self.geometry) == len(t2c.SEGMENTS):
            # Simulate an Archicad join changing the reported endpoint by 0.25 m.
            return a, (z[0] + 0.25, z[1])
        return a, z

    def details(self, guid):
        raw = self.details_raw(guid)
        if not raw:
            return None
        if guid == t2c.WITNESS:
            return {"type": "Wall", "floor_index": t2c.FLOOR,
                    "layer_index": self.layer_index[guid]}
        a, z = self._effective_geometry(guid)
        dx, dy = z[0] - a[0], z[1] - a[1]
        return {
            "type": "Wall", "floor_index": t2c.FLOOR,
            "layer_index": self.layer_index[guid],
            "ref_line": {"from": list(a), "to": list(z)},
            "length": math.hypot(dx, dy), "angle": math.degrees(math.atan2(dy, dx)),
            "height": t2c.HEIGHT, "thickness": t2c.THICK,
        }

    def get_property_values(self, ref, guids):
        if ref.get("id") == "General_ElementID":
            return {g: self.element_id.get(g) for g in guids}
        if ref.get("address") == "ModelView_LayerName":
            return {g: self.layer_name.get(g) for g in guids}
        raise AssertionError(f"unexpected property ref: {ref}")

    def set_property_value(self, guid, ref, value):
        assert ref.get("id") == "General_ElementID"
        self.element_id[guid] = value

    def raw_call(self, command, payload=None):
        assert command == "Get3DBoundingBoxes"
        rows = []
        for item in (payload or {}).get("elements", []):
            guid = item["elementId"]["guid"]
            if guid == t2c.WITNESS:
                box = [100.0, 100.0, 0.0, 101.0, 101.0, 3.0]
            else:
                a, z = self._effective_geometry(guid)
                box = [min(a[0], z[0]) - 0.15, min(a[1], z[1]) - 0.15, 0.0,
                       max(a[0], z[0]) + 0.15, max(a[1], z[1]) + 0.15, 3.0]
            rows.append({"boundingBox3D": {
                "xMin": box[0], "yMin": box[1], "zMin": box[2],
                "xMax": box[3], "yMax": box[4], "zMax": box[5],
            }})
        return {"boundingBoxes3D": rows}


def apply_create(backend, payload):
    backend.create_calls += 1
    assert len(payload["wallsData"]) == 1, "audit T2 must not bulk-create"
    d = payload["wallsData"][0]
    a = (float(d["begCoordinate"]["x"]), float(d["begCoordinate"]["y"]))
    z = (float(d["endCoordinate"]["x"]), float(d["endCoordinate"]["y"]))
    guid = f"T2C-W{backend.create_calls}"
    seg = t2c.abs_segments((20.0, 20.0))[backend.create_calls - 1]
    assert a == seg["from_abs"] and z == seg["to_abs"]
    backend.guids.append(guid)
    backend.walls.add(guid)
    backend.geometry[guid] = (a, z)
    backend.label_by_guid[guid] = seg["label"]
    backend.layer_index[guid] = 1
    backend.layer_name[guid] = "Default Layer"
    backend.element_id[guid] = f"ORIG-{backend.create_calls}"
    return guid


def set_layer(backend, guid):
    backend.layer_calls += 1
    backend.layer_index[guid] = t2c.LAYER_INDEX
    backend.layer_name[guid] = t2c.LAYER_NAME


def run_main(backend, out, report, create_fn):
    old_backend = t2c.TapirBackendV13
    old_create = t2c.create_once
    old_layer = t2c.set_layer_once
    old_argv = sys.argv[:]
    try:
        t2c.TapirBackendV13 = lambda port=19723: backend
        t2c.create_once = create_fn
        t2c.set_layer_once = set_layer
        sys.argv = [
            "probe_t2_connections_v13.py",
            "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
            "--port", "19723",
            "--origin-x", "20", "--origin-y", "20",
            "--out", out, "--report", report,
            "--allow-write", "--i-understand-this-writes-to-archicad",
        ]
        return t2c.main()
    finally:
        t2c.TapirBackendV13 = old_backend
        t2c.create_once = old_create
        t2c.set_layer_once = old_layer
        sys.argv = old_argv


@test
def audit_t2_happy_path_six_single_dispatches():
    backend = FakeConnectionsBackend()
    with tempfile.TemporaryDirectory() as d:
        out, report = os.path.join(d, "receipt.json"), os.path.join(d, "report.json")
        rc = run_main(backend, out, report, lambda b, p: [apply_create(b, p)])
        assert rc == 0
        assert backend.create_calls == 6
        assert backend.layer_calls == 6
        assert len(backend.walls) == 7  # witness + 6 new walls
        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert receipt["status"] == "MACHINE_OK_VISUAL_PENDING"
        assert rep["verdicts"]["audit_t2_machine_go"] is True
        assert rep["results"]["count_delta"] == {"Wall": 6}
        assert rep["results"]["strict_geometry_all_ok"] is True
        assert all(not str(v).startswith(t2c.PREFIX) for v in backend.element_id.values())


@test
def audit_t2_post_join_mismatch_is_f9_not_unknown_and_restores_markers():
    backend = FakeConnectionsBackend(post_join_shift_label="RECT_BOTTOM")
    with tempfile.TemporaryDirectory() as d:
        out, report = os.path.join(d, "receipt.json"), os.path.join(d, "report.json")
        rc = run_main(backend, out, report, lambda b, p: [apply_create(b, p)])
        assert rc == 1
        assert backend.create_calls == 6
        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        with open(report, "r", encoding="utf-8") as f:
            rep = json.load(f)
        assert receipt["status"] == "VERIFY_SPEC_NOT_READY"
        assert rep["verdicts"]["audit_t2_machine_go"] is False
        assert rep["verdicts"]["verify_spec_ready_for_connections"] is False
        bad = [row for row in rep["results"]["walls"] if not row["strict_ok"]]
        assert [row["label"] for row in bad] == ["RECT_BOTTOM"]
        assert all(not str(v).startswith(t2c.PREFIX) for v in backend.element_id.values())


@test
def audit_t2_timeout_on_third_create_is_unknown_and_never_retries():
    backend = FakeConnectionsBackend()
    with tempfile.TemporaryDirectory() as d:
        out, report = os.path.join(d, "receipt.json"), os.path.join(d, "report.json")

        def create_then_timeout_on_third(b, p):
            guid = apply_create(b, p)
            if b.create_calls == 3:
                raise RuntimeError("simulated timeout after apply")
            return [guid]

        rc = run_main(backend, out, report, create_then_timeout_on_third)
        assert rc == 1
        assert backend.create_calls == 3, "must halt immediately; no fourth dispatch"
        assert len(backend.walls) == 4  # witness + three creates; third may have applied
        assert not os.path.exists(report)
        with open(out, "r", encoding="utf-8") as f:
            receipt = json.load(f)
        assert receipt["status"] == "UNKNOWN"
        assert receipt["stopped_at_stage"] == "CREATE_DISPATCH"
        assert receipt["cleanup"]["action"].startswith("DO NOT RETRY")


@test
def audit_t2_live_write_requires_explicit_origin():
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "receipt.json")
        old_argv = sys.argv[:]
        try:
            sys.argv = [
                "probe_t2_connections_v13.py",
                "--expect-project", r"C:\Users\Admin\Downloads\MCP_TEST.pln",
                "--out", out,
                "--allow-write", "--i-understand-this-writes-to-archicad",
            ]
            rc = t2c.main()
        finally:
            sys.argv = old_argv
        assert rc == 1
        assert not os.path.exists(out)
