"""Canonical T8 regressions for durable duplicate submission."""
from __future__ import annotations

import json
import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "probes"))
sys.path.insert(0, os.path.join(ROOT, "reference"))

from probe_t8 import (PROJECT, STORIES, T8Stop, executor_for, plan, triple_delivery,
                      write_report_once)
from bimexec.adapters import FakeArchicad, Faults
from bimexec.states import JobState
from bimexec.verify import PlanRejected


TESTS = []
def test(fn): TESTS.append((fn.__name__, fn)); return fn


@test
def triple_same_submit_has_one_dispatch_and_current_status():
    with tempfile.TemporaryDirectory() as workdir:
        result = triple_delivery(workdir)
    assert result["job_ids"] == ["T8_TRIPLE_DELIVERY"] * 3
    assert result["statuses"] == [JobState.COMPLETED.value] * 3
    assert result["create_wall_dispatches"] == 1
    assert result["elements"] == 1
    assert result["second_submit_called_run"] is False
    assert result["third_submit_called_run"] is False


@test
def completed_duplicate_returns_completed_without_redispatch():
    with tempfile.TemporaryDirectory() as workdir:
        archicad = FakeArchicad(PROJECT, STORIES)
        first, first_adapter = executor_for(workdir, archicad)
        first.submit(plan())
        assert first.run() is JobState.COMPLETED
        first.journal.close()
        journal_path = os.path.join(workdir, "t8.journal.jsonl")
        with open(journal_path, "rb") as handle:
            before_duplicate = handle.read()
        duplicate, duplicate_adapter = executor_for(workdir, archicad)
        job = duplicate.submit(plan())
        assert duplicate.job_state is JobState.COMPLETED
        assert job.job_id == "T8_TRIPLE_DELIVERY"
        assert duplicate_adapter.calls.count("create_wall") == 0
        assert first_adapter.calls.count("create_wall") == 1
        duplicate.journal.close()
        with open(journal_path, "rb") as handle:
            assert handle.read() == before_duplicate


@test
def paused_duplicate_returns_paused_and_original_reason():
    with tempfile.TemporaryDirectory() as workdir:
        archicad = FakeArchicad(PROJECT, STORIES)
        first, _ = executor_for(workdir, archicad, faults=Faults(wrong_geometry=True))
        first.submit(plan())
        assert first.run() is JobState.PAUSED
        original_reason = first.paused_reason
        first.journal.close()
        duplicate, duplicate_adapter = executor_for(workdir, archicad)
        duplicate.submit(plan())
        assert duplicate.job_state is JobState.PAUSED
        assert duplicate.paused_reason == original_reason == "VERIFIED_FAILED"
        assert duplicate_adapter.calls.count("create_wall") == 0
        duplicate.journal.close()


@test
def changed_plan_for_same_job_is_rejected_before_mutation():
    with tempfile.TemporaryDirectory() as workdir:
        archicad = FakeArchicad(PROJECT, STORIES)
        first, _ = executor_for(workdir, archicad)
        first.submit(plan())
        first.journal.close()
        duplicate, adapter = executor_for(workdir, archicad)
        try:
            duplicate.submit(plan(x=9.0))
        except PlanRejected:
            pass
        else:
            raise AssertionError("changed plan for the same durable job must be rejected")
        assert adapter.calls.count("create_wall") == 0
        assert len(archicad.elements) == 0
        duplicate.journal.close()


@test
def restart_duplicate_submit_never_redispatches():
    with tempfile.TemporaryDirectory() as workdir:
        archicad = FakeArchicad(PROJECT, STORIES)
        first, first_adapter = executor_for(workdir, archicad)
        first.submit(plan())
        first.run()
        first.journal.close()
        restarted, restarted_adapter = executor_for(workdir, archicad)
        restarted.submit(plan())
        assert restarted_adapter.calls.count("create_wall") == 0
        assert first_adapter.calls.count("create_wall") == 1
        assert len(archicad.elements) == 1
        restarted.journal.close()


@test
def evidence_is_durable_and_not_overwritten():
    with tempfile.TemporaryDirectory() as workdir:
        path = os.path.join(workdir, "t8-report.json")
        report = {"probe": "T8", "result": {"status": "COMPLETED"}}
        write_report_once(path, report)
        try:
            write_report_once(path, {"replacement": True})
        except T8Stop:
            pass
        else:
            raise AssertionError("T8 evidence must not be overwritten")
        with open(path, encoding="utf-8") as handle:
            assert json.load(handle) == report
