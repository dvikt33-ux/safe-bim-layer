"""Focused offline regressions for the T6 preflight contract."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "probes"))
from probe_t6 import preflight  # noqa: E402


class BackendStub:
    name = "stub"

    def __init__(self, project_path="C:/MCP_TEST.pln", guids=None):
        self.project_path = project_path
        self.guids = set(guids or {"SRC", "DEP"})
        self.detail_calls = []

    def available(self):
        return True, "ok"

    def project_info(self):
        return {"project_path": self.project_path, "project_name": "MCP_TEST"}

    def all_elements(self):
        return sorted(self.guids)

    def details(self, guid):
        self.detail_calls.append(guid)
        return {"guid": guid, "type": "Wall", "ref_line": {"from": [0, 0], "to": [1, 0]}}


TESTS = []


def test(fn):
    TESTS.append((fn.__name__, fn))
    return fn


@test
def preflight_is_read_only_and_records_contract():
    b = BackendStub()
    receipt = preflight(b, "SRC", "DEP", "C:/MCP_TEST.pln")
    assert receipt["mode"] == "preflight-read-only"
    assert receipt["contract"]["expected_pause"] == "PAUSED(MODEL_DRIFT)"
    assert receipt["contract"]["dependent_mutation_allowed_after_drift"] is False
    assert b.detail_calls == ["SRC"]


@test
def preflight_rejects_wrong_project_before_snapshots():
    b = BackendStub(project_path="C:/OTHER.pln")
    try:
        preflight(b, "SRC", "DEP", "C:/MCP_TEST.pln")
    except RuntimeError as exc:
        assert "project mismatch" in str(exc)
    else:
        raise AssertionError("project mismatch must fail closed")
