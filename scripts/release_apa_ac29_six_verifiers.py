"""Verified single-command release bootstrap for the EXISTING AC29 APA receiver.

Operator must explicitly pass the immutable final Git commit SHA. This script
runs on the user's Windows machine, not GitHub. It uses the existing
install_apa_ac29_autonomous_job_bridge.update_from_checkout, not another
installer/dispatcher. No BIM writes or new native permissions are granted.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")
REPO = "dvikt33-ux/safe-bim-layer"
CURRENT_RELEASE = "9cfe84c42db485a5ad536a38369de0b667e066f0"
WORKING = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
PROTECTED = Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
WORKING_SHA = "9293c799cf4a87792016cc76ca5f2c1d8e569f85d6cbab0b529f82d10a303a34"
PROTECTED_SHA = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
EXPECTED_GUIDS = 298

CORE = {"archicad_project_accelerator.py", "archicad_dynamic_commands.py",
        "archicad_strategy_discovery.py", "apa_ac29_dynamic_write_scopes.py",
        "apa_ac29_dynamic_native_verifiers.py"}
NEW = {"apa_ac29_existing_create_verifiers.py",
       "apa_ac29_existing_modify_verifiers.py"}
HELPERS = {"apa_ac29_reusable_native_copy.py",
           "apa_ac29_multi_prototype_native_copy.py",
           "apa_ac29_scene_reconciliation.py"}


def need(yes, reason):
    if not yes:
        raise ValueError(reason)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(*args, cwd=None, timeout=90):
    p = subprocess.run(args, cwd=cwd, timeout=timeout,
                       check=True, capture_output=True, text=True)
    return p.stdout.strip()


def do_release(revision):
    need(sys.platform == "win32", "WINDOWS_ONLY_NO_REMOTE_APA_EXECUTION")
    need(isinstance(revision, str) and len(revision) == 40 and
         all(x in "0123456789abcdef" for x in revision),
         "REQUIRES_FULL_PINNED_COMMIT_SHA")
    need(WORKING.is_file() and PROTECTED.is_file() and
         sha(WORKING) == WORKING_SHA and sha(PROTECTED) == PROTECTED_SHA,
         "WORKING_OR_PROTECTED_PLN_HASH_MISMATCH_STOP")
    receipt_path = ROOT / "controllers" / "runtime-release.json"
    need(receipt_path.is_file(), "EXISTING_RUNTIME_RECEIPT_REQUIRED")
    old = json.loads(receipt_path.read_text(encoding="utf-8"))
    worker = ROOT / "controllers" / "apa_ac29_autonomous_job_bridge.py"
    require_old_keys = {"schema", "revision", "workerSHA256", "moduleHashes",
                        "controllerHashes", "workingPlnSha256", "expectedGuidCount"}
    need(set(old) == require_old_keys and
         old["schema"] == "APA_AC29_RUNTIME_RELEASE_V1" and
         old["revision"] == CURRENT_RELEASE and
         old["workerSHA256"] == sha(worker) and
         old["workingPlnSha256"] == WORKING_SHA and
         old["expectedGuidCount"] == EXPECTED_GUIDS and
         set(old["moduleHashes"]) == CORE | HELPERS and
         set(old["controllerHashes"]) == HELPERS,
         "INSTALLED_RELEASE_NOT_EXACT_EXPECTED_9CFE84C_STOP")
    for name, digest in old["moduleHashes"].items():
        need(sha(ROOT/"scripts"/name) == digest,
             "INSTALLED_SCRIPT_DRIFT:" + name)
    for name, digest in old["controllerHashes"].items():
        need(sha(ROOT/"controllers"/name) == digest,
             "INSTALLED_CONTROLLER_DRIFT:" + name)
    need(all(not (ROOT/"scripts"/name).exists() for name in NEW),
         "NEW_VERIFIER_ALREADY_INSTALLED_OR_NOT_EMPTY")

    with TemporaryDirectory(prefix="apa-ac29-six-verifier-") as directory:
        checkout = Path(directory) / "repo"
        run("gh", "repo", "clone", REPO, str(checkout),
            "--", "--quiet", "--no-checkout", timeout=180)
        run("git", "fetch", "--quiet", "origin", revision,
            cwd=checkout, timeout=120)
        run("git", "checkout", "--quiet", "--detach", revision,
            cwd=checkout, timeout=120)
        need(run("git", "rev-parse", "HEAD", cwd=checkout) == revision,
             "IMMUTABLE_SOURCE_REVISION_DRIFT")
        updater = checkout / "scripts" / "install_apa_ac29_autonomous_job_bridge.py"
        need(updater.is_file(), "SAME_PROJECT_UPDATER_MISSING")
        targets = {
            **{"scripts/"+n: ROOT/"scripts"/n for n in CORE|NEW|HELPERS},
            **{"controllers/"+n: ROOT/"controllers"/n for n in HELPERS},
            "controllers/"+worker.name: worker,
        }
        # Every existing file already matched the signed current release;
        # absent new verifier files must remain absent until the updater acts.
        known = {key: sha(path) if path.is_file() else None
                 for key, path in targets.items()}
        need(set(known) == {*(("scripts/"+n) for n in CORE|NEW|HELPERS),
                            *(("controllers/"+n) for n in HELPERS),
                            "controllers/"+worker.name},
             "EXACT_APA_RUNTIME_SCOPE_REQUIRED")
        manifest = {
            "schema": "APA_AC29_LOCAL_RUNTIME_UPDATE_V1",
            "revision": revision,
            "oldHashes": known,
            "workingPath": str(WORKING),
            "workingSha256": WORKING_SHA,
            "protectedPath": str(PROTECTED),
            "protectedSha256": PROTECTED_SHA,
            "expectedGuidCount": EXPECTED_GUIDS,
        }
        manifest_path = Path(directory)/"upgrade-manifest.json"
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2)+"\n",
            encoding="utf8")
        spec = importlib.util.spec_from_file_location("existing_apa_installer", updater)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        checked = module.update_from_checkout(checkout, manifest_path, False)
        need(checked.get("status") == "UPDATE_PREFLIGHT_PASS_NO_CHANGES" and
             checked.get("modelWrites") == 0,
             "EXISTING_INSTALLER_DRY_RUN_MISSING")
        print("APA_PREFLIGHT:", checked["status"], flush=True)
        applied = module.update_from_checkout(checkout, manifest_path, True)
        need(applied.get("status") ==
             "UPDATED_RECEIVER_INTEGRITY_IMPORT_PROCESS_AND_SINGLETON_PASS" and
             applied.get("modelWrites") == 0 and
             applied.get("queuePreserved") and
             applied.get("sqlitePreserved") and
             applied.get("projectBytesPreserved"),
             "EXISTING_INSTALLER_FULL_POSTCHECK_INCOMPLETE")
        print("APA_STATUS:", applied["status"], flush=True)
        print("RELEASE:", revision, flush=True)
        print("PID:", applied["receiverPID"], flush=True)
        print("MODEL_WRITES: 0", flush=True)
        print("BACKUP:", applied["backup"], flush=True)


if __name__ == "__main__":
    try:
        need(len(sys.argv) == 2, "ONE_REQUIRED_PINNED_REVISION_ARGUMENT")
        do_release(sys.argv[1])
    except Exception as err:
        print("APA_STATUS: SIX_VERIFIER_RELEASE_BLOCKED", flush=True)
        print("ERROR:", type(err).__name__ + ": " + str(err), flush=True)
        raise SystemExit(2)
