"""CLI entry point for the localhost Safe BIM runtime/palette service."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_bim_ipc import serve, strict_json
from safe_bim_layer import TapirClient
from safe_bim_operations import SafeBIMOperations, normalized_params
from safe_bim_runtime import ExecutorError, ResumableExecutor, SQLiteCheckpointStore, StepSpec, valid_job_id


def load_plan(path: str | Path):
    data = strict_json(Path(path).read_text(encoding="utf-8"))
    allowed = {"job_id", "task_name", "project_path", "steps"}
    if not isinstance(data, dict) or set(data) != allowed:
        raise ValueError(f"plan fields must be exactly {sorted(allowed)}")
    if not valid_job_id(data['job_id']) or not isinstance(data['task_name'], str) or not data['task_name'].strip() or not isinstance(data['project_path'], str) or not data['project_path'].strip():
        raise ValueError('invalid plan identity/task')
    if not isinstance(data['steps'], list) or not data['steps']:
        raise ValueError('nonempty steps array required')
    steps = []
    for raw in data["steps"]:
        step_allowed = {"name", "operation", "params", "floor_index"}
        if not isinstance(raw, dict) or set(raw) - step_allowed or not {"name", "operation", "params"} <= set(raw):
            raise ValueError("invalid step fields")
        if not isinstance(raw['name'], str) or not raw['name']:
            raise ValueError('step name required')
        clean = normalized_params(raw['operation'], raw['params'])
        floor = raw.get('floor_index')
        if floor is not None and (type(floor) is not int or ('floor_index' in clean and clean['floor_index'] != floor)):
            raise ValueError('step floor_index contradicts operation')
        steps.append(StepSpec(raw["name"], raw["operation"], raw["params"],
                              raw.get("floor_index")))
    return data, steps


def main():
    parser = argparse.ArgumentParser(description="Safe BIM resumable runtime")
    parser.add_argument("--db", default="safe_bim_runtime.sqlite3")
    parser.add_argument("--schema", default=str(Path(__file__).with_name("tapir-1.5.8.json")))
    parser.add_argument("--bridge", default="http://127.0.0.1:19723")
    parser.add_argument("--port", type=int, default=19731)
    parser.add_argument("--plan", help="strict JSON plan to create if job_id is new")
    args = parser.parse_args()

    store = SQLiteCheckpointStore(args.db)
    if args.plan:
        plan, steps = load_plan(args.plan)
        try:
            store.job(plan["job_id"])
        except ExecutorError:
            store.create_job(plan["job_id"], plan["task_name"],
                             plan["project_path"], steps)
    client = TapirClient(args.bridge, args.schema)
    operations = SafeBIMOperations(client)
    executor = ResumableExecutor(store, operations.execute,
                                 operations.reconcile, operations.current_project)
    print(f"Safe BIM IPC: http://127.0.0.1:{args.port}")
    serve(executor, args.port)


if __name__ == "__main__":
    main()
