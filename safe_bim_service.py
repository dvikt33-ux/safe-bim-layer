"""CLI entry point for the localhost Safe BIM runtime/palette service."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from safe_bim_ipc import serve
from safe_bim_layer import TapirClient
from safe_bim_operations import SafeBIMOperations
from safe_bim_runtime import ExecutorError, ResumableExecutor, SQLiteCheckpointStore, StepSpec


def load_plan(path: str | Path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    allowed = {"job_id", "task_name", "project_path", "steps"}
    if set(data) != allowed:
        raise ValueError(f"plan fields must be exactly {sorted(allowed)}")
    steps = []
    for raw in data["steps"]:
        step_allowed = {"name", "operation", "params", "floor_index"}
        if set(raw) - step_allowed or not {"name", "operation", "params"} <= set(raw):
            raise ValueError(f"invalid step fields: {sorted(raw)}")
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
