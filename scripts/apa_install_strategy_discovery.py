#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Strictly additive installation of APA's auto-strategy discovery.

Intended local APA core is the user-confirmed recovered+planner patched version
SHA256 e7d9ae310f7a7022a2262b8d7c3944a1b23c8feed49c20ec933190ba583ff727.
Never replace this source with an upstream GitHub version; append exactly two
new wrapper functions to the existing bytes and preserve the entire old file.
No Archicad, Tapir, PLN, or SceneWriter calls; no auto native execution.

Default is read-only preflight. --apply is required. If any original local
code or module changes between preflight and write, abort without modification.
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


PINNED_RECOVERED_CORE_SHA256 = "e7d9ae310f7a7022a2262b8d7c3944a1b23c8feed49c20ec933190ba583ff727"

WRAPPERS = r'''

# BEGIN APA source-qualified native strategy auto-discovery adapter.
def prepare_auto_optimized_native_task(router, intent, planner_python=None):
    """Discover reviewed source-qualified strategies; prepare, never execute."""
    from archicad_strategy_discovery import discover_native_execution_plan
    return discover_native_execution_plan(router, intent, planner_python)


def run_auto_optimized_native_task(router, api, auto_preview, writer, scopes, checkpoint=None):
    """Explicitly authorized route ONLY through existing APA run_native_task."""
    if (not isinstance(auto_preview, dict)
            or auto_preview.get("schema") != "APA_AUTO_NATIVE_TASK_V1"
            or auto_preview.get("nativeWritePermission") is not False
            or auto_preview.get("automaticNativeExecution") is not False
            or auto_preview.get("status") not in {
                "ONE_SOURCE_QUALIFIED_STRATEGY_PREPARED",
                "COST_OPTIMAL_SOURCE_QUALIFIED_STRATEGY_PREPARED"
            }):
        raise ValueError("APA_AUTO_DISCOVERY_NOT_READY_FOR_EXPLICIT_EXECUTION")
    preview = auto_preview.get("selectedNativeTaskPreview")
    if (not isinstance(preview, dict)
            or preview.get("schema") != "APA_NATIVE_TASK_PREVIEW_V1"
            or preview.get("executionPermission") is not False):
        raise ValueError("APA_AUTO_DISCOVERY_INVALID_NATIVE_PREVIEW")
    # All step-level SceneWriter scopes and pre/post verifiers remain mandatory.
    return run_native_task(router, api, preview, writer, scopes, checkpoint)
# END APA source-qualified native strategy auto-discovery adapter.
'''


def need(ok, why):
    if not ok:
        raise ValueError(why)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def names(data, label):
    tree = ast.parse(data, filename=label)
    return {x.name for x in tree.body if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))}


def stage(root, module, expected_sha=PINNED_RECOVERED_CORE_SHA256):
    root = Path(root).resolve()
    module = Path(module).resolve()
    core = root / "archicad_project_accelerator.py"
    deployed = root / "archicad_strategy_discovery.py"
    adapter = root / "archicad_execution_optimizer.py"
    original = root / "archicad_project_accelerator.py.planner-install.bak"
    backup = root / "archicad_project_accelerator.py.before-auto-discovery.bak"
    need(core.is_file() and adapter.is_file() and original.is_file(),
         "LOCAL_RECOVERED_APA_AND_SOLVER_ADAPTER_REQUIRED")
    need(module.is_file(), "STAGED_AUTO_DISCOVERY_MODULE_MISSING")
    need(not deployed.exists() and not backup.exists(),
         "AUTO_DISCOVERY_ALREADY_INSTALLED_OR_PREVIOUS_ATTEMPT_REQUIRES_MANUAL_RECONCILIATION")
    current = core.read_bytes()
    need(hashlib.sha256(current).hexdigest() == expected_sha,
         "LOCAL_APA_HASH_DRIFT_NO_OVERWRITE")
    need("prepare_optimized_native_task" in names(current, "local_apa.py"),
         "LOCAL_APA_FIRST_STAGE_PLANNER_NOT_INSTALLED")
    need("prepare_auto_optimized_native_task" not in names(current, "local_apa.py")
         and "run_auto_optimized_native_task" not in names(current, "local_apa.py"),
         "AUTO_DISCOVERY_WRAPPERS_ALREADY_EXIST")
    module_bytes = module.read_bytes()
    need(len(module_bytes) > 5000
         and "def discover_native_execution_plan(" in module_bytes.decode("utf-8-sig"),
         "INVALID_AUTO_DISCOVERY_ADAPTER")
    compile(module_bytes, str(module), "exec")
    patched = current + (b"\n" if not current.endswith(b"\n") else b"") + WRAPPERS.encode("utf-8")
    compile(patched, str(core), "exec")
    need(patched.startswith(current), "BASELINE_NOT_PRESERVED_PREFIX")
    return {
        "core": core, "adapter": adapter, "original": original,
        "module": module, "deployed": deployed, "backup": backup,
        "current": current, "module_bytes": module_bytes, "patched": patched,
        "sha": hashlib.sha256(current).hexdigest(),
    }


def install(root, module, expected_sha=PINNED_RECOVERED_CORE_SHA256, *, apply=False, smoke=True):
    s = stage(root,module,expected_sha)
    report = {
        "schema": "APA_AUTO_DISCOVERY_ADDITIVE_INSTALL_V1",
        "status": "AUTO_DISCOVERY_ADDITIVE_PREFLIGHT_PASS" if not apply else "INSTALL_PENDING",
        "originalLocalSHA256": s["sha"],
        "newLocalSHA256": hashlib.sha256(s["patched"]).hexdigest(),
        "sourcePreservedByteForByte": s["patched"].startswith(s["current"]),
        "newModuleSHA256": hashlib.sha256(s["module_bytes"]).hexdigest(),
        "installedFunctions": ["prepare_auto_optimized_native_task",
                               "run_auto_optimized_native_task"],
        "modelWrites":0,"archicadCalls":0,"dryRun":not apply,
    }
    if not apply:
        return report

    core = s["core"]
    deployed = s["deployed"]
    backup = s["backup"]
    first_fd, first_temp = tempfile.mkstemp(prefix=".apa-auto-stage-core-",suffix=".py",dir=core.parent)
    second_fd, second_temp = tempfile.mkstemp(prefix=".apa-auto-stage-module-",suffix=".py",dir=core.parent)
    installed_module = False
    installed_core = False
    try:
        with os.fdopen(first_fd,"wb") as file:
            file.write(s["patched"])
            file.flush()
            os.fsync(file.fileno())
        with os.fdopen(second_fd,"wb") as file:
            file.write(s["module_bytes"])
            file.flush()
            os.fsync(file.fileno())
        need(sha(core)==s["sha"] and not deployed.exists() and not backup.exists(),
             "LOCAL_APA_CHANGED_DURING_INSTALL")
        # Old code is copied without modifying or deleting prior rescue files.
        shutil.copy2(core,backup)
        need(sha(backup)==s["sha"],"NEW_BACKUP_MISMATCH")
        os.replace(second_temp,deployed)
        installed_module = True
        os.replace(first_temp,core)
        installed_core = True
        if smoke:
            env=os.environ.copy()
            env["PYTHONPATH"]=str(core.parent)+os.pathsep+env.get("PYTHONPATH","")
            process=subprocess.run([
                sys.executable,"-c",
                "import archicad_project_accelerator as a; "
                "assert callable(a.prepare_auto_optimized_native_task); "
                "assert callable(a.run_auto_optimized_native_task); "
                "import archicad_strategy_discovery as s; "
                "assert callable(s.discover_native_execution_plan); "
                "print('APA AUTO DISCOVERY IMPORT PASS')",
            ],cwd=str(core.parent),env=env,capture_output=True,text=True,
                encoding="utf-8",errors="replace",timeout=45,check=False)
            need(process.returncode==0,
                 "AUTO_DISCOVERY_IMPORT_FAILED:" + process.stderr[-1200:])
        need(sha(core)==report["newLocalSHA256"] and
             sha(deployed)==report["newModuleSHA256"],
             "NEW_AUTO_DISCOVERY_INSTALL_HASH_MISMATCH")
    except Exception:
        # The original source stays immutable in backup; rollback is possible
        # even when the smoke import fails.
        if installed_core:
            fd, tmp=tempfile.mkstemp(prefix=".apa-auto-rollback-",suffix=".py",dir=core.parent)
            with os.fdopen(fd,"wb") as file:
                file.write(s["current"])
            os.replace(tmp,core)
        if installed_module and deployed.is_file() and sha(deployed)==report["newModuleSHA256"]:
            deployed.unlink()
        # Keep the backup to facilitate auditing any failure.
        raise
    finally:
        for temp in (first_temp,second_temp):
            if os.path.exists(temp):
                os.unlink(temp)
    report.update(status="AUTO_DISCOVERY_INSTALLED_WITH_ORIGINAL_APA_PRESERVED",
                  dryRun=False,backup=str(backup))
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--scripts-dir",required=True)
    p.add_argument("--module",required=True)
    p.add_argument("--apply",action="store_true")
    args=p.parse_args()
    try:
        print(json.dumps(install(args.scripts_dir,args.module,apply=args.apply),
                         ensure_ascii=False,indent=2))
        return 0
    except Exception as e:
        print(json.dumps({"status":"INSTALL_BLOCKED_NO_DESTRUCTIVE_REPLACEMENT",
                          "reason":type(e).__name__+":"+str(e)},
                         ensure_ascii=False),file=sys.stderr)
        return 2


if __name__=="__main__":
    sys.exit(main())
