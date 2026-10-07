"""Focused regressions for read-only T3 dependency reconciliation."""
from __future__ import annotations

import copy
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PROBES = os.path.join(ROOT, "probes")
sys.path.insert(0, PROBES)

import reconcile_t3_dependency_v13 as rec
import probe_t3_dependency_v13 as t3
import probe_t2_connections_v13 as t2c
import tests.test_t3_dependency as base_t3

TESTS: list[tuple[str, object]] = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


WALL = "T3-HOST-WALL"
OPENING = "T3-OPENING"


def source_receipt():
    return {
        "probe": "AUDIT_T3_DEPENDENCY",
        "status": "VERIFY_UNAVAILABLE",
        "stopped_at_stage": "OPENING_READBACK",
        "packages": {
            t3.PKG01: "COMPLETED",
            t3.PKG02: "COMPLETED",
            t3.PKG04: "RUNNING",
        },
        "mapping": {
            "host_wall": {
                "state": "CONFIRMED",
                "guid": WALL,
            }
        },
        "artifacts": [
            {"kind": "Wall", "guid": WALL},
            {"kind": "Opening", "guid": OPENING, "host_wall_guid": WALL},
        ],
        "stages": [
            {"stage": "PRECHECK", "origin": [20.0, 20.0]},
            {"stage": "PACKAGE_COMPLETED", "package": t3.PKG02},
            {"stage": "OPENING_CREATE_INTENT", "package": t3.PKG04},
        ],
    }


class FakeReconcileBackend(base_t3.FakeT3Backend):
    def __init__(self, connected=None):
        super().__init__()
        self.origin = (20.0, 20.0)
        self.guids.extend([WALL, OPENING])
        self.walls.add(WALL)
        self.openings.add(OPENING)
        self.layer_index[WALL] = t2c.LAYER_INDEX
        self.layer_name[WALL] = t2c.LAYER_NAME
        self.element_id[WALL] = "W-T3-ORIGINAL"
        self.element_id[OPENING] = "O-T3"
        self.opening_owner[OPENING] = WALL
        self.connected = [OPENING] if connected is None else list(connected)
        self.mutations = 0

    def addon_version(self):
        return t3.ADDON

    def set_property_value(self, guid, ref, value):
        self.mutations += 1
        raise AssertionError("reconcile must never mutate")

    def raw_call(self, command, payload=None):
        if command == "GetConnectedElements":
            assert (payload or {}).get("connectedElementType") == "Opening"
            requested = (payload or {}).get("elements") or []
            assert requested == [{"elementId": {"guid": WALL}}]
            return {
                "connectedElements": [{
                    "elements": [{"elementId": {"guid": g}} for g in self.connected]
                }]
            }
        if command == "Get3DBoundingBoxes":
            rows = []
            for item in (payload or {}).get("elements", []):
                guid = item["elementId"]["guid"]
                if guid == WALL:
                    box = [20.0, 19.95, 0.0, 26.0, 20.25, 3.0]
                elif guid == OPENING:
                    box = [22.0, 19.95, 0.0, 23.0, 20.25, 0.0]
                else:
                    box = [100.0, 100.0, 0.0, 101.0, 101.0, 1.0]
                rows.append({"boundingBox3D": {
                    "xMin": box[0], "yMin": box[1], "zMin": box[2],
                    "xMax": box[3], "yMax": box[4], "zMax": box[5],
                }})
            return {"boundingBoxes3D": rows}
        raise AssertionError(f"unexpected raw_call {command}")


@test
def audit_t3_reconcile_adopts_existing_binding_readonly():
    b = FakeReconcileBackend()
    report = rec.reconcile(b, source_receipt(), r"C:\Users\Admin\Downloads\MCP_TEST.pln")
    assert report["verdicts"]["audit_t3_dependency_machine_go"] is True
    assert report["verdicts"]["owner_binding_reconciled"] is True
    assert report["results"]["connected_openings_from_host_wall"] == [OPENING]
    assert report["results"]["mutations"] == 0
    assert report["limitations"]["opening_size_machine_certified"] is False
    assert b.mutations == 0


@test
def audit_t3_reconcile_rejects_wrong_or_ambiguous_relation():
    for connected in ([], ["FOREIGN"], [OPENING, "FOREIGN"]):
        b = FakeReconcileBackend(connected=connected)
        try:
            rec.reconcile(b, source_receipt(), r"C:\Users\Admin\Downloads\MCP_TEST.pln")
        except rec.ReconcileError as e:
            assert "owner relation mismatch/ambiguous" in str(e)
        else:
            raise AssertionError(f"reconcile unexpectedly accepted {connected}")
        assert b.mutations == 0


@test
def audit_t3_reconcile_only_accepts_specific_fail_closed_receipt():
    for status, stage in (("UNKNOWN", "OPENING_CREATE_DISPATCH"), ("VERIFY_FAILED", "OPENING_VERIFY"), ("MACHINE_OK_VISUAL_PENDING", None)):
        r = copy.deepcopy(source_receipt())
        r["status"] = status
        r["stopped_at_stage"] = stage
        b = FakeReconcileBackend()
        try:
            rec.reconcile(b, r, r"C:\Users\Admin\Downloads\MCP_TEST.pln")
        except rec.ReconcileError as e:
            assert "only valid for VERIFY_UNAVAILABLE" in str(e)
        else:
            raise AssertionError(f"reconcile unexpectedly accepted {status}/{stage}")
        assert b.mutations == 0
