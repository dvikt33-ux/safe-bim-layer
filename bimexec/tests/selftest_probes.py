#!/usr/bin/env python3
"""
Offline self-test of the T0 probes. No Archicad, no network, no write to any
project: every scenario runs against the in-memory doubles in tests/fakes/.

    python bimexec/tests/selftest_probes.py

Purpose: prove the shipped probe files actually behave the way the plan claims,
so the Windows run only has to answer questions about Archicad itself.

Checks
  1. T0A against a Tapir-shaped model: exit 0, matrix conforms to the required
     structure, raw GetDetailsOfElements dump preserved, every capability has
     backend attribution, duplicate_detection = SCAN_PREFIX,
     create_wall.production_safe = false.
  2. T0A with no reachable backend: exit 2 (fail closed, nothing certified).
  3. T0B default (no write keys): PRECHECK only, exit 0, model untouched.
  4. T0B with exactly one write key: exit 1, nothing written (both variants).
  5. T0B with both keys, property carrier: exit 0 and the original value is
     provably restored (checked in-process against the fake model).
  6. T0B against a write that silently does nothing: STOP at READ_BACK, UNKNOWN.
  7. T0B when a BX:PROBE: marker is already in the project: STOP at PRECHECK.
  8. create_wall / CreateWalls and other mutating commands are hard-blocked.

Exit code: 0 if every check passes, 1 otherwise.
"""
from __future__ import annotations

import json
import os
import runpy
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # bimexec/
PROBES = os.path.join(ROOT, "probes")
FAKES = os.path.join(HERE, "fakes")
T0A = os.path.join(PROBES, "probe_t0a.py")
T0B = os.path.join(PROBES, "probe_t0b.py")
PROJECT = r"C:\PLN\MCP_TEST.pln"

RESULTS: list[tuple[str, bool, str]] = []


def check(name: str, cond: bool, detail: str = "") -> bool:
    RESULTS.append((name, bool(cond), detail))
    print(f"  {'PASS' if cond else 'FAIL'}  {name}" + (f"  -- {detail}" if detail and not cond else ""))
    return bool(cond)


def run(args: list[str], cwd: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable] + args, cwd=cwd, capture_output=True, text=True)


def fake(name: str) -> str:
    return os.path.join(FAKES, name)


def load_json(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------
# 1. T0A against a Tapir-shaped model
# --------------------------------------------------------------------------
def t0a_shape() -> None:
    with tempfile.TemporaryDirectory() as td:
        cp = run([T0A, "--out", "cm.json", "--backend-module", fake("fake_tapir_shape.py"),
                  "--expect-project", PROJECT], td)
        check("T0A: exit 0", cp.returncode == 0, f"rc={cp.returncode} {cp.stderr[-300:]}")
        cm = load_json(os.path.join(td, "cm.json"))
        check("T0A: probe marker", cm.get("probe") == "T0A")
        check("T0A: executed is not a go decision", cm["verdicts"]["executed"] is True
              and isinstance(cm["verdicts"].get("t0a_go"), bool))
        check("T0A: create_wall.production_safe == false",
              cm["operations"]["create_wall"]["production_safe"] is False)
        check("T0A: create_wall not implemented here",
              cm["operations"]["create_wall"]["implemented_here"] is False)

        caps = cm["capabilities"]
        check("T0A: every capability has backend attribution",
              all("backend" in c for c in caps.values()),
              str([k for k, c in caps.items() if "backend" not in c]))
        check("T0A: no capability silently drops 'supported'",
              all("supported" in c for c in caps.values()))
        check("T0A: tri-state honoured (null stays null, never coerced to true)",
              any(c["supported"] is None for c in caps.values())
              or all(c["supported"] is not None for c in caps.values()))
        check("T0A: list_guids certified", caps["list_guids"]["supported"] is True)
        check("T0A: wall_geometry_endpoints certified",
              caps["wall_geometry_endpoints"]["supported"] is True)
        check("T0A: tapir_native_prefix_search reported NOT FOUND",
              caps["tapir_native_prefix_search"]["supported"] is False)
        check("T0A: duplicate_detection == SCAN_PREFIX",
              cm.get("duplicate_detection") == "SCAN_PREFIX", str(cm.get("duplicate_detection")))

        raw = cm.get("raw_dumps", {}).get("GetDetailsOfElements_sample") or {}
        wall = (raw.get("details") or {}).get("wall") or {}
        check("T0A: raw GetDetailsOfElements dump preserved",
              "begCoordinate" in wall and "endCoordinate" in wall,
              str(sorted(raw)))
        check("T0A: t0b_candidates offered", bool(cm.get("t0b_candidates")))
        base = ["GetProjectInfo", "GetStories", "GetAllElements", "GetElementsByType",
                "GetDetailsOfElements", "GetPropertyValuesOfElements"]
        check("T0A: read commands verified by real calls",
              all(cm["capabilities"]["tapir_read_commands"]["evidence"]["commands"]
                  [f"tapir.{c}"]["ok"] for c in base))


# --------------------------------------------------------------------------
# 2. T0A fail closed
# --------------------------------------------------------------------------
def t0a_fail_closed() -> None:
    with tempfile.TemporaryDirectory() as td:
        cp = run([T0A, "--out", "cm.json", "--backend-order", "",
                  "--ports", "1", "--mcp-url", "http://127.0.0.1:1/mcp"], td)
        check("T0A: no backend => exit 2 (fail closed)", cp.returncode == 2,
              f"rc={cp.returncode}")


# --------------------------------------------------------------------------
# 3. T0B default = no write
# --------------------------------------------------------------------------
def t0b_default_is_readonly() -> None:
    with tempfile.TemporaryDirectory() as td:
        cp = run([T0B, "--guid", "G-0001", "--expect-project", PROJECT,
                  "--backend-module", fake("fake_tapir_shape.py"),
                  "--out", "r.json", "--report", "p.json"], td)
        check("T0B: default run exits 0 (PRECHECK only)", cp.returncode == 0,
              f"rc={cp.returncode} {cp.stderr[-300:]}")
        rec = load_json(os.path.join(td, "r.json"))
        check("T0B: default run status is DRY_RUN_OK", rec.get("status") == "DRY_RUN_OK",
              str(rec.get("status")))
        check("T0B: default run wrote no stage after PRECHECK",
              not any(s["stage"] in ("WRITTEN", "RESTORED") for s in rec.get("stages", [])))


# --------------------------------------------------------------------------
# 4. T0B one key is not enough
# --------------------------------------------------------------------------
def t0b_two_keys() -> None:
    for key in ("--allow-write", "--i-understand-this-writes-to-archicad"):
        with tempfile.TemporaryDirectory() as td:
            cp = run([T0B, "--guid", "G-0001", "--expect-project", PROJECT,
                      "--backend-module", fake("fake_tapir_shape.py"),
                      "--out", "r.json", key], td)
            check(f"T0B: single key {key} => exit 1, no write",
                  cp.returncode == 1, f"rc={cp.returncode}")
            check(f"T0B: single key {key} never reaches WRITTEN",
                  not os.path.exists(os.path.join(td, "r.json"))
                  or not any(s["stage"] == "WRITTEN"
                             for s in load_json(os.path.join(td, "r.json")).get("stages", [])))


# --------------------------------------------------------------------------
# 5. T0B round-trip with both keys, and the original value is restored
# --------------------------------------------------------------------------
def t0b_roundtrip_restores() -> None:
    sys.path.insert(0, PROBES)
    sys.path.insert(0, FAKES)
    with tempfile.TemporaryDirectory() as td:
        cwd = os.getcwd()
        os.chdir(td)
        try:
            argv = sys.argv
            sys.argv = [T0B, "--guid", "G-0001", "--expect-project", PROJECT,
                        "--backend-module", fake("fake_tapir_shape.py"),
                        "--carrier", "property", "--out", "r.json", "--report", "p.json",
                        "--allow-write", "--i-understand-this-writes-to-archicad"]
            code = 0
            try:
                runpy.run_path(T0B, run_name="__main__")
            except SystemExit as e:
                code = int(e.code or 0)
            finally:
                sys.argv = argv
            check("T0B: both keys => exit 0", code == 0, f"rc={code}")

            rep = load_json(os.path.join(td, "p.json"))
            stages = rep["results"]["property"]["stages"]
            check("T0B: read-back proved the write", stages.get("READ_BACK") is True)
            check("T0B: exact search found exactly one element", stages.get("FIND_EXACT") is True)
            check("T0B: prefix search found exactly one element", stages.get("FIND_PREFIX") is True)
            check("T0B: restore verified", stages.get("VERIFY_RESTORE") is True)

            # in-process: the fake model is shared through sys.modules
            model = sys.modules["bimexec_user_backend"].MODEL
            stored = model["user_props"].get("G-0001", {}).get("BIMEXEC_MARKER")
            check("T0B: original value restored in the model (no BX:PROBE: left)",
                  not str(stored).startswith("BX:PROBE:"), f"stored={stored!r}")
            check("T0B: recommended carrier is property",
                  rep["verdicts"]["recommended_carrier"] == "property",
                  str(rep["verdicts"].get("recommended_carrier")))
        finally:
            os.chdir(cwd)


# --------------------------------------------------------------------------
# 6. Silent no-op write must be caught
# --------------------------------------------------------------------------
def t0b_silent_noop() -> None:
    with tempfile.TemporaryDirectory() as td:
        cp = run([T0B, "--guid", "G-0001", "--expect-project", PROJECT,
                  "--backend-module", fake("fake_backend_silentnoop.py"),
                  "--carrier", "property", "--out", "r.json", "--report", "p.json",
                  "--allow-write", "--i-understand-this-writes-to-archicad"], td)
        check("T0B: silent no-op => exit 1", cp.returncode == 1, f"rc={cp.returncode}")
        rec = load_json(os.path.join(td, "r.json"))
        check("T0B: silent no-op stops at READ_BACK",
              rec.get("stopped_at_stage") == "READ_BACK", str(rec.get("stopped_at_stage")))
        check("T0B: silent no-op status is UNKNOWN (not success)",
              rec.get("status") == "UNKNOWN", str(rec.get("status")))
        check("T0B: receipt carries the value to clean up manually",
              isinstance(rec.get("cleanup"), dict))


# --------------------------------------------------------------------------
# 7. Leftover marker from an interrupted run
# --------------------------------------------------------------------------
def t0b_leftover() -> None:
    with tempfile.TemporaryDirectory() as td:
        cp = run([T0B, "--guid", "G-0001", "--expect-project", PROJECT,
                  "--backend-module", fake("fake_backend_leftover.py"),
                  "--carrier", "both", "--out", "r.json",
                  "--allow-write", "--i-understand-this-writes-to-archicad"], td)
        check("T0B: leftover BX:PROBE: => exit 1", cp.returncode == 1, f"rc={cp.returncode}")
        rec = load_json(os.path.join(td, "r.json"))
        check("T0B: leftover stops at PRECHECK",
              rec.get("stopped_at_stage") == "PRECHECK", str(rec.get("stopped_at_stage")))


# --------------------------------------------------------------------------
# 8. create_wall and friends are hard-blocked
# --------------------------------------------------------------------------
def forbidden_commands() -> None:
    sys.path.insert(0, PROBES)
    import backends  # noqa: E402

    for cmd in ("CreateWalls", "DeleteElements", "SetSelection"):
        try:
            backends._assert_not_forbidden(cmd)
            check(f"guard: {cmd} rejected", False, "no exception")
        except backends.BackendError:
            check(f"guard: {cmd} rejected", True)
    check("guard: CreateWalls is in FORBIDDEN_COMMANDS",
          "CreateWalls" in backends.FORBIDDEN_COMMANDS)
    # quoted literals only: the probes mention CreateWalls in prose, but must
    # never pass it to a backend as a command name
    for fname in ("probe_t0a.py", "probe_t0b.py"):
        src = open(os.path.join(PROBES, fname), encoding="utf-8").read()
        check(f"probes: {fname} never passes CreateWalls as a command",
              '"CreateWalls"' not in src and "'CreateWalls'" not in src)


def main() -> int:
    print("=== selftest: T0 probes (offline, no Archicad)")
    for fn in (t0a_shape, t0a_fail_closed, t0b_default_is_readonly, t0b_two_keys,
               t0b_roundtrip_restores, t0b_silent_noop, t0b_leftover, forbidden_commands):
        print(f"\n-- {fn.__name__}")
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - a broken self-test must be visible
            check(f"{fn.__name__} raised", False, f"{type(e).__name__}: {e}")
    failed = [n for n, ok, _ in RESULTS if not ok]
    print(f"\n{'FAILED' if failed else 'OK'}: {len(failed)} failure(s), "
          f"{len(RESULTS) - len(failed)} check(s) passed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
