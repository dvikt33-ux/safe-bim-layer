"""TRC-SAD Archicad 29 port 19727: strict read-only identity and story probe.

Reuses the accepted Tapir UTF-8 transport. Never calls Create/Modify/Save,
SceneWriter, ChangeWindow or modifies any existing configuration/PLN.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path, PureWindowsPath
from archicad_guarded_wall_probe import tapir
import trc_sad_plan as PLAN

PORT = 19727
DIRECTORY = PureWindowsPath(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects")
READS = frozenset(("GetProjectInfo", "GetAddOnVersion", "GetStories"))
TAPIR_VERSION = "1.5.10"


def accepted_project(info):
    if not isinstance(info, dict) or info.get("isUntitled") or info.get("isTeamwork"):
        return False
    name, filename = info.get("projectName"), info.get("projectPath")
    if not isinstance(name, str) or not isinstance(filename, str):
        return False
    path = PureWindowsPath(filename)
    return (path.is_absolute() and path.suffix.casefold() == ".pln"
            and path.parent.as_posix().casefold() == DIRECTORY.as_posix().casefold()
            and path.stem.casefold().startswith("трц")
            and "gp" in path.stem.casefold()
            and name.casefold() == path.stem.casefold())


def native_levels(response):
    rows = response.get("stories") if isinstance(response, dict) else None
    if not isinstance(rows, list):
        raise ValueError("INVALID_GETSTORIES")
    result = {}
    for row in rows:
        if not isinstance(row, dict) or type(row.get("index")) is not int:
            raise ValueError("INVALID_STORY_INDEX")
        index, value = row["index"], row.get("level")
        if (index in result or type(value) not in (int, float)
                or not math.isfinite(value)):
            raise ValueError("INVALID_OR_DUPLICATE_NATIVE_LEVEL")
        result[index] = {"nativeIndex": index, "floorId": row.get("floorId"),
                         "elevation": float(value), "height": row.get("height"),
                         "name": row.get("name", "")}
    return result


def inspect(read_api, spec, port=PORT):
    if type(port) is not int or port != PORT:
        raise ValueError("PORT_19727_ONLY")
    if not callable(read_api):
        raise ValueError("READ_ONLY_TRANSPORT_REQUIRED")
    PLAN.validate_spec(spec)
    calls = []

    def read(command):
        if command not in READS:
            raise ValueError("READ_ONLY_COMMAND_REQUIRED")
        calls.append(command)
        result = read_api(command)
        if not isinstance(result, dict):
            raise ValueError("INVALID_TAPIR_RESULT")
        return result

    before = read("GetProjectInfo")
    report = {
        "status": "BLOCKED_WRONG_PROJECT",
        "port": port,
        "projectName": before.get("projectName"),
        "projectPath": before.get("projectPath"),
        "nativeStoryBindings": None,
        "liveWriteAuthorized": False,
        "nativeWrites": 0,
        "plnChanged": False,
        "sceneWriterCalled": False,
    }
    if not accepted_project(before):
        report["readCommands"] = calls
        return report

    addon = read("GetAddOnVersion")
    floors = read("GetStories")
    after = read("GetProjectInfo")
    if before != after:
        raise ValueError("PROJECT_CHANGED_DURING_PROBE")

    actual = native_levels(floors)
    expected = {str(x["id"]): float(x["elevation"]) for x in spec["floors"]}
    mismatches = []
    bindings = {}
    for sid in PLAN.ABOVE_STORIES:
        row = actual.get(int(sid) - 1)
        if row is None or abs(row["elevation"] - expected[sid]) > 1e-6:
            mismatches.append({
                "story": sid, "expected": expected[sid],
                "actual": row["elevation"] if row else None})
        else:
            bindings[sid] = {"nativeIndex": row["nativeIndex"],
                             "elevation": row["elevation"]}
    if not any(abs(x["elevation"] - expected["-1"]) < 1e-6 for x in actual.values()):
        mismatches.append({"story": "-1", "expected": -4.5,
                           "actual": None, "reason": "No basement at -4.5m"})
    report.update(
        status="READ_ONLY_STORY_MAPPING_READY",
        tapirVersion=addon.get("version"),
        actualStories=[actual[i] for i in sorted(actual)],
        targetElevationsMeters=expected,
        discrepancies=mismatches,
        readCommands=calls)
    if addon.get("version") != TAPIR_VERSION:
        report["status"] = "BLOCKED_TAPIR_VERSION_MISMATCH"
    elif mismatches:
        report["status"] = "BLOCKED_STORY_ELEVATIONS_MISMATCH"
    else:
        # Safe for an OFFLINE compiler only; never authorize a native write.
        report["nativeStoryBindings"] = bindings
    return report


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--spec", type=Path, default=PLAN.DEFAULT_SPEC)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args(argv)
    if args.port != PORT:
        raise ValueError("PORT_19727_ONLY")
    if args.output.exists():
        raise FileExistsError("EVIDENCE_ALREADY_EXISTS_USE_NEW_OUTPUT_FILENAME")
    spec = json.loads(args.spec.read_text(encoding="utf-8"))
    report = inspect(lambda c: tapir(args.port, c, {}, timeout=6), spec, args.port)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
    print(json.dumps({"status": report["status"], "port": args.port,
                      "projectName": report["projectName"],
                      "projectPath": report["projectPath"],
                      "discrepancies": report.get("discrepancies", []),
                      "evidence": str(args.output), "nativeWrites": 0},
                     ensure_ascii=False, indent=2))
    return 0 if report["status"] == "READ_ONLY_STORY_MAPPING_READY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
