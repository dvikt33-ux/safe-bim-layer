"""Focused offline regressions for the durable two-read T6 contract."""
from __future__ import annotations

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "probes"))
from probe_t6 import (PAUSED_MODEL_DRIFT, T6Stop, preflight, read_baseline,
                      verify_after_manual_move, write_baseline_once)  # noqa: E402


class BackendStub:
    name = "stub"

    def __init__(self, project_path="C:/MCP_TEST.pln", guids=None, moved=False, details=True):
        self.project_path, self.guids = project_path, set(guids or {"SRC", "DEP"})
        self.moved, self.details_enabled = moved, details

    def available(self): return True, "ok"
    def project_info(self): return {"project_path": self.project_path, "project_name": "MCP_TEST"}
    def all_elements(self): return sorted(self.guids)
    def details(self, guid):
        if not self.details_enabled: return None
        end = [1.5, 0] if self.moved and guid == "SRC" else [1, 0]
        return {"guid": guid, "type": "Wall", "ref_line": {"from": [0, 0], "to": end},
                "height": 3.0, "thickness": 0.3}


TESTS = []
def test(fn): TESTS.append((fn.__name__, fn)); return fn


def baseline(): return preflight(BackendStub(), "SRC", "DEP", "C:/MCP_TEST.pln")


@test
def unchanged_geometry_does_not_false_positive_model_drift():
    calls = []
    result = verify_after_manual_move(BackendStub(), baseline(), lambda: calls.append("dispatch"))
    assert result["status"] == "UNCHANGED_GEOMETRY"
    assert calls == ["dispatch"]


@test
def moved_geometry_pauses_before_dependent_dispatch():
    calls = []
    result = verify_after_manual_move(BackendStub(moved=True), baseline(), lambda: calls.append("dispatch"))
    assert result["status"] == PAUSED_MODEL_DRIFT
    assert result["dependent_dispatch_count"] == 0
    assert calls == []


@test
def project_guid_and_baseline_errors_fail_closed():
    for backend in (BackendStub(project_path="C:/OTHER.pln"), BackendStub(guids={"SRC"}), BackendStub(details=False)):
        try: preflight(backend, "SRC", "DEP", "C:/MCP_TEST.pln")
        except T6Stop: pass
        else: raise AssertionError("invalid preflight must fail closed")
    try: read_baseline("does-not-exist.json")
    except T6Stop: pass
    else: raise AssertionError("missing baseline must fail closed")


@test
def baseline_evidence_is_never_overwritten():
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "baseline.json")
        receipt = baseline()
        write_baseline_once(path, receipt)
        try: write_baseline_once(path, {"replacement": True})
        except T6Stop: pass
        else: raise AssertionError("existing evidence must not be overwritten")
        assert read_baseline(path)["source"]["guid"] == "SRC"
