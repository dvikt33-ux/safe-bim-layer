"""APA 29: one disposable Hotlink node and one instance via original SceneWriter.

Workflow: --stage -> manually open the *new* scratch PLN in AC29 -> --execute
          -> manually reopen that scratch PLN -> --verify-reopen.

The two native writes have distinct source-qualified SQLite scenes. SaveProject
is separately journaled and guarded. No replay after a dispatch or UNKNOWN.
No main, original PLN, BDD or running project is changed by --stage.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PureWindowsPath
import shutil
import sqlite3
import sys

import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_bim_documentation as DOC
import archicad_connected_components as C
from apa_ac29_dynamic_write_scopes import build_existing_workflow_scopes
from apa_ac29_hotlink_native_verifiers import (
    need, digest, flatten_hotlinks, node_parameters, instance_parameters,
    parse_node_reply, parse_instance_reply, installed_hotlink_verifiers,
    canonical_location,
)
from apa_ac29_reusable_native_copy import GuardedSaveTransport

SOURCE_REF = "https://github.com/dvikt33-ux/safe-bim-layer/pull/169"
AUTH = "USER_APPROVED_AC29_HOTLINK_DISPOSABLE_20261018"
SCHEMA = "APA_AC29_HOTLINK_ONESHOT_V1"
SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schemas/tapir-live-1.5.10/tapir-scene-live.json"
STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
COMMANDS = ("GetHotlinks", "CreateHotlinkNodes", "CreateHotlinkInstances")
SCENES = ("HotlinkNode20261018V1", "HotlinkInstance20261018V1", "HotlinkSave20261018V1")


def utc():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    with Path(path).open("x", encoding="utf8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")


def read(path):
    return json.loads(Path(path).read_text(encoding="utf8"))


def win(path):
    return PureWindowsPath(str(path)).as_posix().casefold()


def stage(source, module, scratch, state, origin, port):
    source, module, scratch, state = [Path(p).resolve() for p in (source, module, scratch, state)]
    need(source.is_file() and module.is_file() and
         source.suffix.lower() == scratch.suffix.lower() == ".pln" and
         module.suffix.lower() in {".pln", ".mod"} and
         source != scratch and module != scratch and
         state != scratch and source != module and
         scratch.parent.is_dir() and state.parent.is_dir() and
         not scratch.exists() and not state.exists() and
         win(STABLE) not in win(scratch) and
         not any(win(scratch).startswith(win(p) + "/")
                 for p in (STABLE, source.parent / "backups")) and
         type(port) is int and 1 <= port <= 65535,
         "HOTLINK_STAGE_REQUIRES_UNIQUE_EXISTING_SOURCES_AND_NEW_SCRATCH")
    # Validate exact native command data even while Archicad is offline.
    node_parameters(module)
    instance_parameters("00000000-0000-4000-8000-000000000001", origin)
    original_sha, module_sha = digest(source), digest(module)
    shutil.copy2(source, scratch)
    need(digest(scratch) == original_sha and digest(module) == module_sha,
         "HOTLINK_STAGE_FILE_COPY_HASH_DRIFT")
    state.mkdir(exist_ok=False)
    receipt = {"schema": SCHEMA, "status": "STAGED_NOT_EXECUTED",
               "source": str(source), "sourceSHA256": original_sha,
               "module": str(module), "moduleSHA256": module_sha,
               "scratch": str(scratch), "scratchInitialSHA256": original_sha,
               "origin": origin, "port": port, "nativeCalls": 0,
               "plnWrites": 0, "automaticReplay": False,
               "requiresOpenScratchManually": True}
    write_new(state / "manifest.json", receipt)
    return receipt


def guard_manifest(state):
    state = Path(state).resolve()
    manifest = read(state / "manifest.json")
    need(manifest.get("schema") == SCHEMA and
         manifest.get("status") == "STAGED_NOT_EXECUTED" and
         set(manifest["origin"]) == {"x", "y", "z"} and
         not (state / "attempted.json").exists(), "HOTLINK_ONCE_ONLY_ATTEMPT_GUARD")
    source, scratch, module = [Path(manifest[x]) for x in ("source", "scratch", "module")]
    need(source.is_file() and module.is_file() and scratch.is_file() and
         source != scratch and module != scratch and
         digest(source) == manifest["sourceSHA256"] and
         digest(module) == manifest["moduleSHA256"] and
         digest(scratch) == manifest["scratchInitialSHA256"] and
         not (state / "scenewriter.sqlite").exists(),
         "HOTLINK_PROTECTED_FILES_OR_LEDGER_CHANGED")
    return manifest


def current_project(api, scratch):
    product = api("API.GetProductInfo", {})
    need(product.get("version") == 29 and product.get("buildNumber") == 5101,
         "HOTLINK_AC29_BUILD_5101_RUNTIME_REQUIRED")
    info = api("GetProjectInfo", {})
    path = info.get("projectPath") or info.get("projectLocation")
    need(path and win(path) == win(scratch) and info.get("isUntitled") is False and
         info.get("isTeamwork") is False, "HOTLINK_ONLY_EXACT_SCRATCH_PLN_MAY_BE_OPEN")
    need(api("GetAddOnVersion", {}).get("version") == "1.5.10",
         "HOTLINK_TAPIR_1510_RUNTIME_REQUIRED")
    return info


def router_for_runtime(api):
    router = APA.native_command_router(SCHEMA_PATH, include_functional_modules=False)
    from archicad_dynamic_commands import DynamicCommands
    need(isinstance(router, DynamicCommands), "HOTLINK_EXISTING_ROUTER_REQUIRED")
    for command in COMMANDS:
        router.probe_runtime(api, command)
    for command in COMMANDS[1:]:
        router.review_policy(command, "CREATE", "MODEL",
                             {"source": SOURCE_REF,
                              "sha256": router.contract_hash(command)})
    router.review_policy("SaveProject", "TRANSACTION", "PROJECT",
                         {"source": SOURCE_REF,
                          "sha256": router.contract_hash("SaveProject")})
    return router


def native_baseline(api):
    ids = sorted(APA.inventory_guids(api))
    need(ids, "HOTLINK_TEST_COPY_MUST_CONTAIN_NATIVE_MODEL_ELEMENTS")
    model = DOC.capture_full_model(api, ids)
    nodes = {x["guid"].lower(): x for x in model["elements"]}
    need(set(nodes) == set(ids), "HOTLINK_NATIVE_FULL_BREP_BASELINE_MISSING")
    signatures = {g: C.ROOF.geometry_signature(nodes[g]) for g in ids}
    return ids, RUN.digest(signatures)


def run_one(router, writer, api, command, params, verifier_id, registry, scene, sha):
    ids, brep_hash = native_baseline(api)
    step_id = "OneHotlinkStep"
    preview = APA.prepare_native_task(router, {
        "schemaVersion": "apa-native-task/1",
        "request": "Only one exact reviewed native Hotlink operation on an isolated PLN",
        "graph": {"operations": [{"id": step_id, "command": command,
                                  "params": params, "after": []}]}
    })
    spec = {
        "schemaVersion": "apa-ac29-dynamic-mutation-scope/1",
        "projectSha256": sha,
        "sourcePlanHash": preview["sourcePlanHash"],
        "authorizationRef": AUTH,
        "sourceEvidenceRef": SOURCE_REF,
        "sceneId": scene,
        "stepId": step_id,
        "command": command, "effect": "CREATE", "impact": "MODEL",
        "commandContractHash": router.contract_hash(command),
        "parametersHash": RUN.digest(params),
        "expectedBeforeGuidSetHash": RUN.digest(ids),
        "expectedBeforeNativeBrepHash": brep_hash,
        "affectedGuids": [],
        "retainedGuids": ids,
        "verifierId": verifier_id,
    }
    scopes = build_existing_workflow_scopes(
        spec=spec, plan=preview["workflow"], router=router,
        registry=registry, writer=writer, api=api,
        capture_model=DOC.capture_full_model, guid_inventory=APA.inventory_guids,
        current_project_sha=lambda: digest(Path(RUN.EXPECTED_PATH)),
        approved_project_sha=sha, local_authorization=AUTH)
    result = APA.run_native_task(router, api, preview, writer, scopes)
    need(result.get("status") == "WORKFLOW_CALLABLE_VERIFIED" and
         len(result.get("trace", [])) == 1, "HOTLINK_NATIVE_RESULT_NOT_CONFIRMED_NO_REPLAY")
    return result["results"][step_id]


def prepare_api(manifest, state, *, for_write):
    scratch, source = Path(manifest["scratch"]), Path(manifest["source"])
    sha = manifest.get("savedSHA256", manifest["scratchInitialSHA256"])
    RUN.bind_authorized_saved_copy(manifest["port"], str(scratch), scratch.stem, sha, AUTH)
    transport = GuardedSaveTransport(
        APA.native_transport, RUN.bind_authorized_saved_copy,
        scratch, source, lambda: digest(scratch), lambda: digest(source),
        scratch.stem, manifest["port"], AUTH)
    evidence = Path(state) / ("trace-live" if for_write else "trace-reopened")
    evidence.mkdir(exist_ok=True)
    api = APA.EvidenceAPI(transport, evidence, execute=for_write)
    # These are exact read-only API requests; never broaden mutation scope.
    api.allowed = api.allowed | frozenset({"GetHotlinks"})
    return api, transport


def execute(state):
    state = Path(state).resolve()
    manifest = guard_manifest(state)
    scratch = Path(manifest["scratch"])
    api, save_guard = prepare_api(manifest, state, for_write=True)
    current_project(api, scratch)
    router = router_for_runtime(api)
    # Read-only preflight finishes before the durable one-shot intent is written.
    need(not any(location == canonical_location(manifest["module"])
                 for location, _ in flatten_hotlinks(api("GetHotlinks", {}))),
         "HOTLINK_SOURCE_ALREADY_LINKED_NO_REUSE_IN_ONESHOT")
    old_ids, old_brep_hash = native_baseline(api)
    sha = manifest["scratchInitialSHA256"]
    need(digest(scratch) == sha, "HOTLINK_SCRATCH_SAVED_BYTES_DRIFT")
    # Immutable, complete saved-copy baseline is essential for reopen proof.
    write_new(state / "baseline.json", {"baselineGuids": old_ids,
             "baselineBrepSHA256": old_brep_hash,
             "scratchInitialSHA256": sha})
    write_new(state / "attempted.json", {
        "status": "ATTEMPT_RESERVED_NO_REPLAY", "at": utc(),
        "scratchSHA256": sha, "sourceSHA256": manifest["sourceSHA256"],
        "moduleSHA256": manifest["moduleSHA256"], "automaticRetry": False
    })
    ledger = state / "scenewriter.sqlite"
    with sqlite3.connect(ledger) as db:
        db.execute("CREATE TABLE scenes (scene_id TEXT PRIMARY KEY, "
                   "plan_hash TEXT NOT NULL, state TEXT NOT NULL, result TEXT NOT NULL)")
        db.execute("CREATE TABLE steps (scene_id TEXT NOT NULL, "
                   "step_id TEXT NOT NULL, state TEXT NOT NULL, guid TEXT, "
                   "output TEXT NOT NULL, PRIMARY KEY(scene_id,step_id))")
        db.commit()
    writer = RUN.SceneWriter(api, journal_path=ledger,
                             schema_path=SCHEMA_PATH,
                             allow_3d_view_for_write=True)
    try:
        registry = installed_hotlink_verifiers(
            manifest["module"], manifest["moduleSHA256"], manifest["origin"])
        reply_node = run_one(router, writer, api, "CreateHotlinkNodes",
                             node_parameters(manifest["module"]),
                             "VerifiedHotlinkNodeOneShot", registry, SCENES[0], sha)
        node = parse_node_reply(reply_node)
        need(digest(scratch) == sha and digest(manifest["source"]) == manifest["sourceSHA256"],
             "HOTLINK_FILES_CHANGED_AFTER_NODE")
        registry = installed_hotlink_verifiers(
            manifest["module"], manifest["moduleSHA256"], manifest["origin"],
            verified_node_guid=node)
        reply_inst = run_one(router, writer, api, "CreateHotlinkInstances",
                             instance_parameters(node, manifest["origin"]),
                             "VerifiedHotlinkInstanceOneShot", registry, SCENES[1], sha)
        instance = parse_instance_reply(reply_inst)
        saved_ids, saved_brep_hash = native_baseline(api)
        need(saved_ids != old_ids and digest(scratch) == sha and
             digest(manifest["source"]) == manifest["sourceSHA256"],
             "HOTLINK_NEW_ELEMENTS_OR_SCRATCH_UNSAVED_STATE_INVALID")
        source_path = canonical_location(manifest["module"])
        need((source_path, node) in flatten_hotlinks(api("GetHotlinks", {})),
             "HOTLINK_SOURCE_NODE_CHANGED_BEFORE_SAVE")
        # Persistence is a THIRD, separate original SceneWriter scene, only
        # after both native readback verifiers have completed with PASS.
        save_guard.enable_after_verified_copy()
        retained = DOC.capture_full_model(api, saved_ids)
        signatures = C.retained_geometry_signatures(retained, saved_ids)
        need(set(signatures) == set(saved_ids), "HOTLINK_PRE_SAVE_BREP_INCOMPLETE")
        def before_save(live):
            current_project(live, scratch)
            need(digest(scratch) == sha and
                 sorted(APA.inventory_guids(live)) == saved_ids and
                 digest(manifest["module"]) == manifest["moduleSHA256"] and
                 (source_path, node) in flatten_hotlinks(live("GetHotlinks", {})),
                 "HOTLINK_SAVE_PRECONDITIONS_CHANGED")
            return {"status": "HOTLINK_BEFORE_SAVE_PASS"}
        def after_save(reply, previous):
            need(reply == {"success": True} and save_guard.new_saved_sha and
                 digest(scratch) == save_guard.new_saved_sha and
                 digest(manifest["source"]) == manifest["sourceSHA256"] and
                 digest(manifest["module"]) == manifest["moduleSHA256"],
                 "HOTLINK_SAVE_NOT_VERIFIED")
            return {"status": "HOTLINK_GUARDED_SAVE_PASS",
                    "savedSHA256": save_guard.new_saved_sha}
        ticket = router.prepare("SaveProject", {})
        save_result = router.execute(
            writer, SCENES[2], ticket, [], signatures, sha,
            AUTH, "PROJECT", after_save, verify_before=before_save)
        need(save_result.get("status") == "PASS" and
             api.write_attempts == 3 and api.calls["SaveProject"] == 1,
             "HOTLINK_THREE_JOURNALED_OPERATIONS_REQUIRED")
        receipt = {
            "schema": SCHEMA, "status": "LIVE_SAVED_PENDING_REOPEN",
            "at": utc(), "nodeGuid": node, "instanceGuid": instance,
            "moduleSHA256": manifest["moduleSHA256"],
            "sourceSHA256": manifest["sourceSHA256"],
            "savedSHA256": save_guard.new_saved_sha,
            "guidCountBefore": len(old_ids), "guidCountAfter": len(saved_ids),
            "beforeBrepSHA256": old_brep_hash, "afterBrepSHA256": saved_brep_hash,
            "afterGuidSetSHA256": RUN.digest(saved_ids),
            "nativeCalls": 2, "saveCalls": 1, "automaticRetry": False,
            "reopenVerified": False, "scratch": str(scratch)
        }
        write_new(state / "saved.json", receipt)
        return receipt
    except Exception as exc:
        # A SceneWriter scene might have reached Archicad even if transport
        # timed out. Never remove or retry the task. Reconcile read-only.
        write_new(state / "failed.json", {
            "schema": SCHEMA, "status": "STOPPED_NO_REPLAY_RECONCILIATION_REQUIRED",
            "at": utc(), "error": type(exc).__name__ + ": " + str(exc)[-1600:],
            "modelWritesMayHaveOccurred": True, "automaticRetry": False,
            "scratch": str(scratch), "ledger": str(ledger)
        })
        raise


def verify_reopen(state):
    state = Path(state).resolve()
    receipt = read(state / "saved.json")
    manifest = read(state / "manifest.json")
    need(receipt["status"] == "LIVE_SAVED_PENDING_REOPEN" and
         not (state / "reopened.json").exists() and
         receipt["sourceSHA256"] == manifest["sourceSHA256"] and
         receipt["moduleSHA256"] == manifest["moduleSHA256"],
         "HOTLINK_SAVED_RECEIPT_REQUIRED")
    scratch = Path(manifest["scratch"])
    need(digest(scratch) == receipt["savedSHA256"] and
         digest(manifest["source"]) == manifest["sourceSHA256"] and
         digest(manifest["module"]) == manifest["moduleSHA256"],
         "HOTLINK_SAVED_OR_ORIGINAL_FILE_DRIFT")
    api, _ = prepare_api({**manifest, "savedSHA256": receipt["savedSHA256"]},
                         state, for_write=False)
    current_project(api, scratch)
    router = APA.native_command_router(SCHEMA_PATH, include_functional_modules=False)
    router.probe_runtime(api, "GetHotlinks")
    node = receipt["nodeGuid"]
    need((canonical_location(manifest["module"]), node) in
         flatten_hotlinks(api("GetHotlinks", {})),
         "HOTLINK_REOPENED_NODE_MISSING")
    ids, brep_hash = native_baseline(api)
    need(RUN.digest(ids) == receipt["afterGuidSetSHA256"] and
         brep_hash == receipt["afterBrepSHA256"] and
         len(ids) == receipt["guidCountAfter"],
         "HOTLINK_REOPENED_GUID_OR_BREP_MISMATCH")
    created = sorted(set(ids) - set(
        # Before exact GUIDs are intentionally recorded separately on disk,
        # not reconstructed from a count or guessed imported identities.
        read(state / "baseline.json")["baselineGuids"]
    ))
    rows = api("GetDetailsOfElements", {
        "elements": [{"elementId": {"guid": g}} for g in created
                     if g != receipt["instanceGuid"]]
    }).get("detailsOfElements")
    need(isinstance(rows, list) and rows and
         all((r.get("hotlinkId") or {}).get("guid", "").lower() ==
             receipt["instanceGuid"] for r in rows),
         "HOTLINK_REOPENED_INSTANCE_OWNERSHIP_UNVERIFIED")
    accepted = dict(receipt, status="LIVE_NATIVE_SAVED_AND_REOPENED_PASS",
                    reopenVerified=True, acceptedAt=utc(),
                    importedElementsVerified=len(rows))
    write_new(state / "reopened.json", accepted)
    return accepted


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--stage", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--verify-reopen", action="store_true")
    parser.add_argument("--source-pln")
    parser.add_argument("--module-pln")
    parser.add_argument("--scratch-pln")
    parser.add_argument("--state-dir", required=True)
    parser.add_argument("--port", type=int, default=19724)
    parser.add_argument("--origin", nargs=3, type=float,
                        metavar=("X", "Y", "Z"), default=None)
    args = parser.parse_args()
    if args.stage:
        need(all((args.source_pln, args.module_pln, args.scratch_pln))
             and args.origin is not None,
             "HOTLINK_STAGE_NEEDS_SOURCE_MODULE_SCRATCH_AND_EXPLICIT_ORIGIN")
        value = stage(args.source_pln, args.module_pln, args.scratch_pln,
                      args.state_dir, dict(zip("xyz", args.origin)), args.port)
    else:
        need(not any((args.source_pln, args.module_pln, args.scratch_pln))
             and args.origin is None,
             "HOTLINK_EXECUTION_USES_ONLY_PINNED_STAGE_MANIFEST")
        value = execute(args.state_dir) if args.execute else verify_reopen(args.state_dir)
    print(json.dumps(value, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
