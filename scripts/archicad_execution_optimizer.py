"""APA cost-based native execution strategy selection (NO model-write access).

The caller provides source-qualified alternatives as normal existing BIM
workflow graphs, and explicit, independently reviewable COST evidence.
Only existing DynamicCommands.prepare_workflow validates those graphs.
Fast Downward chooses the least-cost qualified alternative. It never calls
Archicad, the MCP transport, SceneWriter or filesystem mutation APIs.

The selected graph is rewrapped by APA.prepare_native_task into an original
v1 preview and must go through unchanged APA.run_native_task -> SceneWriter.
This is not natural-language-to-BIM inference or a replacement writer.

The optional engine runs in the user's isolated APA/planner-venv; the host APA
Python interpreter need not (and should not) install solver dependencies.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import subprocess
import sys


ENGINE = "fast-downward-opt"
MAX_ALTERNATIVES = 32
MAX_COST_MS = 10_000_000
SAFE_EFFECTS = frozenset({"READ_ONLY", "CREATE", "MODIFY", "DELETE", "TRANSACTION", "SERVICE"})


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _canonical(payload):
    return json.loads(json.dumps(payload, sort_keys=True, ensure_ascii=False, allow_nan=False))


def _planner_python(override=None):
    if override is not None:
        path = Path(override)
    elif os.environ.get("APA_PLANNER_PYTHON"):
        path = Path(os.environ["APA_PLANNER_PYTHON"])
    elif sys.platform == "win32":
        path = Path(os.environ.get("LOCALAPPDATA", "")) / "APA" / "planner-venv" / "Scripts" / "python.exe"
    else:
        path = Path(sys.executable)
    _require(path.is_file(), "APA_FAST_DOWNWARD_ENV_NOT_INSTALLED:" + str(path))
    return path


def _validate_strategies(router, strategies):
    _require(isinstance(strategies, list) and 2 <= len(strategies) <= MAX_ALTERNATIVES,
             "APA_PLANNER_REQUIRES_2_TO_32_ALTERNATIVE_STRATEGIES")
    ids = set()
    validated = []
    for row in strategies:
        _require(isinstance(row, dict) and set(row) == {
            "id", "graph", "estimatedCostMs", "nativeCallCount", "costEvidenceRef"
        }, "APA_PLANNER_EXACT_STRATEGY_FIELDS_REQUIRED")
        key = row["id"]
        _require(isinstance(key, str) and 1 <= len(key) <= 64
                 and all(c.isalnum() or c in "_-" for c in key) and key not in ids,
                 "APA_PLANNER_UNIQUE_SAFE_STRATEGY_ID_REQUIRED")
        ids.add(key)
        cost, calls, evidence = row["estimatedCostMs"], row["nativeCallCount"], row["costEvidenceRef"]
        _require(type(cost) is int and 1 <= cost <= MAX_COST_MS,
                 "APA_PLANNER_EXPLICIT_FINITE_POSITIVE_COST_MS_REQUIRED")
        _require(type(calls) is int and 0 <= calls <= 200,
                 "APA_PLANNER_EXPLICIT_NATIVE_CALL_COUNT_REQUIRED")
        _require(isinstance(evidence, str) and len(evidence.strip()) >= 8,
                 "APA_PLANNER_REVIEWABLE_COST_EVIDENCE_REQUIRED")
        graph = _canonical(row["graph"])
        # No second graph validator or native schema catalog.
        prepared = router.prepare_workflow(graph)
        ops = graph["operations"]
        _require(isinstance(ops, list) and bool(ops),
                 "APA_PLANNER_NONEMPTY_VALIDATED_GRAPH_REQUIRED")
        for step in ops:
            effect = router.operation_kind(step["command"])
            _require(effect in SAFE_EFFECTS,
                     "APA_PLANNER_UNREVIEWED_COMMAND_EFFECT:" + step["command"])
        validated.append({
            "id": key, "graph": graph, "preparedWorkflow": prepared,
            "estimatedCostMs": cost, "nativeCallCount": calls,
            "costEvidenceRef": evidence,
        })
    return validated


def _solve(choices, python_path=None):
    python = _planner_python(python_path)
    data = {"alternatives": [
        {"id": row["id"],
         # Primary objective: estimated total time; secondary: native writes,
         # third: stable input order. 1ms dominates <=200-call tie break.
         "cost": row["estimatedCostMs"] * 10000 + row["nativeCallCount"] * 40 + i}
        for i, row in enumerate(choices)
    ]}
    request = json.dumps(data, ensure_ascii=False, sort_keys=True, allow_nan=False)
    process = subprocess.run(
        [str(python), str(Path(__file__).resolve()), "--worker"],
        input=request, text=True, capture_output=True, timeout=30,
        check=False, encoding="utf-8",
    )
    if process.returncode != 0:
        raise RuntimeError("APA_FAST_DOWNWARD_SOLVE_FAILED:" + process.stderr[-2000:])
    try:
        result = json.loads(process.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("APA_FAST_DOWNWARD_INVALID_REPLY") from exc
    _require(result.get("engine") == ENGINE and result.get("status") == "SOLVED",
             "APA_FAST_DOWNWARD_NOT_OPTIMAL_SOLUTION")
    choice = result.get("selected")
    _require(choice in {row["id"] for row in choices},
             "APA_FAST_DOWNWARD_UNKNOWN_ACTION_SELECTED")
    return choice


def prepare_optimized_native_task(router, request, strategies, planner_python=None):
    """Produce a no-permission APA v1 preview chosen by the real solver.

    Caller must provide source-qualified graphs and evidence-based, total
    end-to-end time estimates. No guessed geometry, guessed cost or native call.
    """
    _require(isinstance(request, str) and request.strip(),
             "APA_PLANNER_NONEMPTY_USER_REQUEST_REQUIRED")
    choices = _validate_strategies(router, strategies)
    selected_id = _solve(choices, planner_python)
    winner = next(row for row in choices if row["id"] == selected_id)
    # Uses original APA preview/compiler; no new authorization path.
    import archicad_project_accelerator as APA
    child = APA.prepare_native_task(router, {
        "schemaVersion": "apa-native-task/1", "request": request,
        "graph": winner["graph"]
    })
    # Selection does NOT enable run or SceneWriter. Native execution still
    # requires an explicit authorized existing run_native_task(...) call.
    return {
        "schema": "APA_FAST_DOWNWARD_OPTIMIZED_NATIVE_TASK_V1",
        "status": "OPTIMAL_EVIDENCE_QUALIFIED_PLAN_PREPARED",
        "engine": ENGINE,
        "request": request,
        "alternativesExamined": len(choices),
        "selectedStrategyId": selected_id,
        "estimatedCostMs": winner["estimatedCostMs"],
        "costEvidenceRef": winner["costEvidenceRef"],
        "compared": [
            {"id": x["id"], "estimatedCostMs": x["estimatedCostMs"],
             "nativeCallCount": x["nativeCallCount"],
             "costEvidenceRef": x["costEvidenceRef"]}
            for x in choices
        ],
        "selectedNativeTaskPreview": child,
        "executor": "EXISTING_APA_SCENEWRITER_ONLY",
        "automaticNativeExecution": False,
        "nativeWritePermission": False,
        "note": "The engine optimizes among qualified alternatives; it does not invent missing capabilities or geometry.",
    }


def _worker():
    try:
        from unified_planning.shortcuts import (
            Problem, Fluent, InstantaneousAction, MinimizeActionCosts,
            OneshotPlanner, Int, get_environment,
        )
        get_environment().credits_stream = None
        data = json.loads(sys.stdin.read())
        candidates = data["alternatives"]
        _require(isinstance(candidates, list) and 2 <= len(candidates) <= MAX_ALTERNATIVES,
                 "APA_PLANNER_WORKER_ALTERNATIVES_INVALID")
        problem = Problem("APA_select_verified_native_strategy")
        complete = Fluent("task_complete")
        problem.add_fluent(complete, default_initial_value=False)
        costs = {}
        lookup = {}
        for idx, choice in enumerate(candidates):
            _require(isinstance(choice, dict) and
                     set(choice) == {"id", "cost"} and
                     isinstance(choice["id"], str) and
                     type(choice["cost"]) is int and choice["cost"] > 0,
                     "APA_PLANNER_WORKER_INVALID_CHOICE")
            action = InstantaneousAction("strategy_" + str(idx))
            action.add_effect(complete, True)
            problem.add_action(action)
            costs[action] = Int(choice["cost"])
            lookup[action.name] = choice["id"]
        problem.add_goal(complete)
        problem.add_quality_metric(MinimizeActionCosts(costs))
        with OneshotPlanner(name=ENGINE) as planner:
            outcome = planner.solve(problem)
        _require(outcome.plan is not None and len(outcome.plan.actions) == 1,
                 "APA_PLANNER_WORKER_NO_PLAN")
        selected = lookup[outcome.plan.actions[0].action.name]
        # Independently validate the solver result against this small one-step
        # model; report OPTIMAL only when it attained the minimum cost.
        c = next(x["cost"] for x in candidates if x["id"] == selected)
        _require(c == min(x["cost"] for x in candidates),
                 "APA_PLANNER_WORKER_NOT_MINIMAL")
        print(json.dumps({"engine": ENGINE, "status": "SOLVED", "selected": selected}))
    except Exception as exc:
        print("APA_PLANNER_WORKER_ERROR:" + type(exc).__name__ + ":" + str(exc),
              file=sys.stderr)
        raise SystemExit(2)


if __name__ == "__main__":
    _require(sys.argv[1:] == ["--worker"], "APA_PLANNER_WORKER_ONLY")
    _worker()
