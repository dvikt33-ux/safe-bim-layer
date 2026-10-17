"""Pinned one-invocation APA AC29 shared registry upgrade bootstrap.

This is NOT a new installer, receiver, transport or native executor. It builds
the exact local old-hash manifest for the EXISTING source-pinned installer and
delegates all writes, backups, singleton and healthchecks to that installer.
No Archicad commands and no model writes are issued by this script.
"""
from __future__ import annotations
import argparse
from pathlib import Path
from tempfile import TemporaryDirectory
import importlib.util
import hashlib
import json
import subprocess
import sys

REPO = "https://github.com/dvikt33-ux/safe-bim-layer.git"
BRANCH = "fix/apa-ac29-bdd-paired-history-reconciliation-20261018"
BASE_REVISION = "65eb58068f15fb2646e4a5a0464017741441bf6d"
BASE_WORKING_SHA = "9293c799cf4a87792016cc76ca5f2c1d8e569f85d6cbab0b529f82d10a303a34"
BASE_SOURCE_SHA = "33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
BASE_GUIDS = 298
ROOT = Path(r"C:\LocalAI\APA_AC29_Stable")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_source(name, path):
    loader = importlib.util.spec_from_file_location(name, path)
    require(loader is not None and loader.loader is not None,
            "UPGRADE_LOCAL_SOURCE_MODULE_NOT_LOADABLE")
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module


def run(args):
    require(sys.platform == "win32", "AC29_WINDOWS_INSTALL_ONLY")
    require(isinstance(args.revision, str) and len(args.revision) == 40 and
            all(c in "0123456789abcdef" for c in args.revision),
            "NEW_REVISION_MUST_BE_FULL_PINNED_GITHUB_SHA")
    worker = ROOT / "controllers" / "apa_ac29_autonomous_job_bridge.py"
    require(worker.is_file(),
            "APA_EXISTING_RECEIVER_REQUIRED")
    installed = import_source("apa_ac29_installed_worker", worker)
    installed.stable_preflight()
    old = installed.runtime_release()
    require(isinstance(old, dict) and
            old["revision"] == BASE_REVISION and
            old["workingPlnSha256"] == BASE_WORKING_SHA and
            old["expectedGuidCount"] == BASE_GUIDS and
            hash_file(installed.WORKING) == BASE_WORKING_SHA and
            hash_file(installed.ORIGINAL) == BASE_SOURCE_SHA and
            str(installed.ROOT) == str(ROOT),
            "APA_INSTALLED_RELEASE_OR_PLN_NOT_EXPECTED_298_GUID_VERSION")

    # Source checkout is temporary, commit-pinned and never modifies the user's
    # existing dirty checkout. --no-checkout fetches only Git metadata; the
    # original installer reads the exact committed script blobs via git show.
    with TemporaryDirectory(prefix="apa-ac29-pinned-upgrade-") as folder:
        location = Path(folder)
        checkout = location / "safe-bim-layer"
        subprocess.run([
            "git", "clone", "--quiet", "--filter=blob:none", "--no-checkout",
            "--single-branch", "--branch", BRANCH, REPO, str(checkout)
        ], check=True, timeout=180)
        revision = subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=checkout,
            timeout=20).decode().strip()
        require(revision == args.revision,
                "APA_GITHUB_HEAD_DRIFT_PASSED_REVISION_NO_INSTALL")

        # Load audited latest installer definition from EXACT committed Git
        # bytes, not local mutable checkout. Current installed healthcheck
        # already verified the base code and PLN against its release receipt.
        updated_installer = location / "pinned-installer.py"
        source = subprocess.check_output([
            "git", "show",
            revision + ":scripts/install_apa_ac29_autonomous_job_bridge.py"
        ], cwd=checkout, timeout=60)
        compile(source, str(updated_installer), "exec")
        updated_installer.write_bytes(source)
        installer = import_source("apa_ac29_release_installer", updated_installer)

        from_local = ROOT / "scripts"
        helpers = {
            "apa_ac29_reusable_native_copy.py",
            "apa_ac29_multi_prototype_native_copy.py",
            "apa_ac29_scene_reconciliation.py",
        }
        modules = set(installer.KNOWN) | {
            "apa_ac29_dynamic_write_scopes.py",
            "apa_ac29_dynamic_native_verifiers.py",
            "apa_ac29_existing_create_verifiers.py",
            "apa_ac29_existing_modify_verifiers.py",
            "apa_ac29_scoped_native_executor.py",
        } | helpers
        existing_paths = {
            "scripts/" + name: from_local / name
            for name in modules
        }
        existing_paths.update({
            "controllers/" + name: ROOT / "controllers" / name
            for name in helpers | {worker.name}
        })
        # Old target hashes remain authenticated by installed.stable_preflight.
        # New modules must not already exist; never replace unknown code.
        old_hashes = {}
        for label, dest in existing_paths.items():
            require(not dest.exists() or
                    (dest.is_file() and
                     (dest.name in old["moduleHashes"] or
                      (label.startswith("controllers/") and
                       (dest.name in old.get("controllerHashes", {}) or
                        dest.name == worker.name)))),
                    "UNKNOWN_LOCAL_MODULE_REFUSE_OVERWRITE:" + label)
            old_hashes[label] = hash_file(dest) if dest.exists() else None
        require({"apa_ac29_existing_create_verifiers.py",
                 "apa_ac29_existing_modify_verifiers.py"} <=
                set(old["moduleHashes"]),
                "SCOPED_BASE_MUST_HAVE_VERIFIED_SIX_CONTRACT_RELEASE")
        require("apa_ac29_scoped_native_executor.py" in old["moduleHashes"] and
                "apa_ac29_scene_reconciliation.py" in old["moduleHashes"] and
                "apa_ac29_dynamic_write_scopes.py" in old["moduleHashes"],
                "PAIRED_HISTORY_REQUIRES_INSTALLED_SCOPED_EXECUTOR_RELEASE")

        manifest = {
            "schema": "APA_AC29_LOCAL_RUNTIME_UPDATE_V1",
            "revision": revision,
            "oldHashes": old_hashes,
            "workingPath": str(installed.WORKING),
            "workingSha256": BASE_WORKING_SHA,
            "protectedPath": str(installed.ORIGINAL),
            "protectedSha256": BASE_SOURCE_SHA,
            "expectedGuidCount": BASE_GUIDS,
        }
        manifest_path = location / "manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf8")
        report = installer.update_from_checkout(
            checkout, manifest_path, apply=bool(args.apply)
        )
        require(report["modelWrites"] == 0 and
                report["grantsInstalled"] == 0,
                "UPGRADE_MUST_NOT_GRANT_NATIVE_WRITES")
        print("APA_STATUS:", report["status"])
        print("REVISION:", revision)
        print("MODEL_WRITES:", report["modelWrites"])
        print("LOCAL_GRANTS:", report["grantsInstalled"])
        print("UPGRADE_APPLIED:", bool(args.apply))
        if args.apply:
            print("NEW_RECEIVER_PID:", report["receiverPID"])
            print("BACKUP:", report["backup"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--revision", required=True)
    ap.add_argument("--apply", action="store_true")
    run(ap.parse_args())
