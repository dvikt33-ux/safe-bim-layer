#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Recover local APA core after incorrect full-file install; additive planner install.

Do NOT overwrite a user-modified local APA core with a GitHub baseline. The
incorrect installer used File.Replace after an explicitly failed hash guard.
Windows File.Replace produced archicad_project_accelerator.py.planner-install.bak
(the real, customized local source). This script verifies the installed GitHub
overwrite matches the exact pinned upstream bytes, then reconstructs the local
core as *original backup bytes + two reviewed planner entrypoints only*.

No Archicad / Tapir / PLN / SceneWriter calls, no saves or retries.
Fail closed if any file has drifted. The original backup is NEVER deleted.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


FUNCTIONS = ("prepare_optimized_native_task", "run_optimized_native_task")
REQUIRED = ("native_command_router", "prepare_native_task", "run_native_task")


def require(ok, text):
    if not ok:
        raise ValueError(text)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def functions(source, filename):
    tree = ast.parse(source, filename=filename)
    return {node.name: node for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def additive_candidate(previous: bytes, upstream: bytes):
    original = previous.decode("utf-8-sig")
    target = upstream.decode("utf-8-sig")
    prev_funcs = functions(original, "local_original_apa.py")
    target_funcs = functions(target, "pinned_github_apa.py")
    require(all(n in prev_funcs for n in REQUIRED),
            "LOCAL_APA_MISSING_EXISTING_BIM_WRITER_ENTRYPOINTS")
    require(all(n not in prev_funcs for n in FUNCTIONS),
            "LOCAL_APA_ALREADY_HAS_PLANNER_WRAPPERS_MANUAL_REVIEW_REQUIRED")
    require(all(n in target_funcs for n in FUNCTIONS),
            "PINNED_GITHUB_UPSTREAM_MISSING_PLANNER_ENTRYPOINTS")
    blocks = [ast.get_source_segment(target, target_funcs[n]) for n in FUNCTIONS]
    require(all(blocks), "FAILED_EXTRACT_REVIEWED_GITHUB_WRAPPERS")
    # Preserve all prior local source bytes: no edits/removal to its functions.
    trailer = ("\n\n# ADDITIVE APA Fast Downward planner entrypoints — original core preserved.\n"
               + "\n\n".join(blocks) + "\n")
    suffix = trailer.encode("utf-8")
    candidate = previous + (b"\n" if not previous.endswith(b"\n") else b"") + suffix
    require(candidate.startswith(previous), "LOCAL_APA_CONTENT_NOT_PRESERVED")
    patched_funcs = functions(candidate.decode("utf-8-sig"), "patched_local_apa.py")
    require(all(n in patched_funcs for n in REQUIRED + FUNCTIONS),
            "PATCHED_APA_MISSING_ENTRYPOINT")
    compile(candidate, "patched_local_apa.py", "exec")
    return candidate


def install(scripts_dir, expected_core, expected_optimizer, *, apply=False,
            smoke_import=True):
    scripts_dir = Path(scripts_dir).resolve()
    core = scripts_dir / "archicad_project_accelerator.py"
    backup = scripts_dir / "archicad_project_accelerator.py.planner-install.bak"
    current_optimizer = scripts_dir / "archicad_execution_optimizer.py"
    expected_core, expected_optimizer = Path(expected_core), Path(expected_optimizer)
    for path in (core, backup, current_optimizer, expected_core, expected_optimizer):
        require(path.is_file(), "REQUIRED_LOCAL_FILE_MISSING:" + str(path))

    # Refuse to run if user/custom automation modified overwritten core since
    # the failed install. The expected GitHub core is downloaded at pinned SHA.
    overwritten_sha = sha(core)
    require(overwritten_sha == sha(expected_core),
            "CURRENT_LOCAL_APA_IS_NOT_EXACT_PINNED_OVERWRITE_DO_NOT_MODIFY")
    require(sha(current_optimizer) == sha(expected_optimizer),
            "INSTALLED_OPTIMIZER_DRIFT_DO_NOT_MODIFY")
    previous_bytes = backup.read_bytes()
    require(len(previous_bytes) > 10000 and sha(backup) != overwritten_sha,
            "ORIGINAL_BACKUP_MISSING_OR_UNEXPECTEDLY_IDENTICAL")
    patched = additive_candidate(previous_bytes, expected_core.read_bytes())
    report = {
        "schema": "apa.planner.additive-recovery.v1",
        "status": "VALIDATED_RESTORE_AND_ADDITIVE_INSTALL" if not apply else "INSTALL_PENDING",
        "originalLocalCoreSHA256": sha(backup),
        "overwrittenCoreSHA256": overwritten_sha,
        "patchedCoreSHA256": hashlib.sha256(patched).hexdigest(),
        "originalLocalCoreBytesPreserved": patched.startswith(previous_bytes),
        "addedOnlyFunctions": list(FUNCTIONS),
        "protectedPLNWriteCount": 0,
        "ArchicadCalls": 0,
        "dryRun": not apply,
    }
    if not apply:
        return report

    # Copies never alter the original local backup. Keep the overwritten
    # GitHub candidate as a separate forensic file before repair.
    evidence = scripts_dir / "archicad_project_accelerator.py.planner-overwrite-before-repair.bak"
    require(not evidence.exists(), "RECOVERY_ALREADY_ATTEMPTED_REQUIRES_REVIEW")
    shutil.copy2(core, evidence)

    # Atomic single-file update. The original local core in .bak stays intact.
    fd, tmp = tempfile.mkstemp(prefix=".apa-planner-additive-", suffix=".py", dir=scripts_dir)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(patched)
            f.flush()
            os.fsync(f.fileno())
        require(sha(core) == overwritten_sha and sha(backup) == report["originalLocalCoreSHA256"],
                "APA_LOCAL_FILES_CHANGED_DURING_PATCH")
        os.replace(tmp, core)
        if smoke_import:
            env = os.environ.copy()
            env["PYTHONPATH"] = str(scripts_dir) + os.pathsep + env.get("PYTHONPATH", "")
            check = subprocess.run(
                [sys.executable, "-c",
                 "import archicad_project_accelerator as a; "
                 "assert callable(a.prepare_optimized_native_task); "
                 "assert callable(a.run_optimized_native_task); "
                 "import archicad_execution_optimizer; "
                 "print('APA ADDITIVE PLANNER IMPORT PASS')"],
                cwd=str(scripts_dir),
                env=env, capture_output=True, text=True,
                encoding="utf-8", errors="replace", timeout=30,
                check=False)
            if check.returncode:
                raise RuntimeError("PLANNER_PATCH_IMPORT_FAILED:" + check.stderr[-1600:])
    except Exception:
        # Fail safe: restore exact local source from the immutable .bak.
        rescue_fd, rescue = tempfile.mkstemp(prefix=".apa-planner-rescue-",suffix=".py",dir=scripts_dir)
        with os.fdopen(rescue_fd, "wb") as f:
            f.write(previous_bytes)
        os.replace(rescue,core)
        raise
    finally:
        if os.path.isfile(tmp):
            os.unlink(tmp)
    require(sha(core) == report["patchedCoreSHA256"],
            "INSTALLED_ADDITIVE_CONTENT_MISMATCH")
    report.update(status="LOCAL_APA_RESTORED_PLUS_PLANNER_WRAPPERS_INSTALLED",
                  dryRun=False,forensicOverwriteBackup=str(evidence),
                  originalBackup=str(backup),
                  overwrittenVersionStillActive=False)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scripts-dir", required=True)
    parser.add_argument("--expected-github-core", required=True)
    parser.add_argument("--expected-github-optimizer", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    try:
        report = install(args.scripts_dir, args.expected_github_core,
                         args.expected_github_optimizer, apply=args.apply)
        print(json.dumps(report, ensure_ascii=False, indent=2))
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED_NO_UNGUARDED_REPLACE",
                          "reason": type(exc).__name__ + ":" + str(exc)},
                         ensure_ascii=False), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
