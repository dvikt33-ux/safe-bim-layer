"""Bridge source-qualified CREATE/MODIFY into EXISTING APA DynamicCommands.

Provides a reviewed, one-mutation scope for the existing run_workflow.
It never replaces the BIM Graph, SceneWriter, catalog or native transport.
An installed code-owned pre/post verifier is mandatory. Untrusted GitHub
tasks may describe native data, but cannot submit executable callbacks.
"""
from __future__ import annotations
import copy
from contextlib import closing
import re
import sqlite3
from pathlib import Path
from dataclasses import dataclass

_HASH = re.compile(r"^[a-f0-9]{64}$")
_GUID = re.compile(r"^[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}$")
_ID = re.compile(r"^[A-Za-z][A-Za-z0-9_-]{3,79}$")
_MUTATE = frozenset({"CREATE", "MODIFY"})


def need(condition, reason):
    if not condition:
        raise ValueError(reason)


@dataclass(frozen=True)
class NativeVerifier:
    verifier_id: str
    command: str
    effect: str
    before: object
    after: object

    def __post_init__(self):
        need(_ID.fullmatch(self.verifier_id) and
             isinstance(self.command, str) and
             self.effect in _MUTATE and
             callable(self.before) and callable(self.after),
             "DYNAMIC_VERIFIER_MUST_BE_INSTALLED_CODE")


def verify_contract(spec, plan, router, registry, *,
                    approved_project_sha, local_authorization):
    """No native calls, no authorization inferred from command prefixes."""
    need(isinstance(spec, dict) and set(spec) == {
        "schemaVersion", "projectSha256", "sourcePlanHash",
        "authorizationRef", "sourceEvidenceRef", "sceneId",
        "stepId", "command", "effect", "impact",
        "commandContractHash", "parametersHash",
        "expectedBeforeGuidSetHash", "expectedBeforeNativeBrepHash",
        "affectedGuids", "retainedGuids", "verifierId"},
        "DYNAMIC_WRITE_EXACT_SCOPE_SCHEMA")
    need(spec["schemaVersion"] == "apa-ac29-dynamic-mutation-scope/1" and
         plan.get("schema") == "APA_DYNAMIC_BIM_WORKFLOW_V1" and
         plan.get("executionPermission") is False and
         spec["sourcePlanHash"] == plan["sourcePlanHash"],
         "DYNAMIC_WRITE_EXISTING_BIM_GRAPH_NOT_BOUND")
    need(isinstance(approved_project_sha, str) and
         _HASH.fullmatch(approved_project_sha) and
         spec["projectSha256"] == approved_project_sha and
         isinstance(local_authorization, str) and
         local_authorization.startswith("USER_APPROVED_") and
         spec["authorizationRef"] == local_authorization and
         isinstance(spec["sourceEvidenceRef"], str) and
         spec["sourceEvidenceRef"].startswith("https://github.com/"),
         "DYNAMIC_WRITE_LOCAL_APPROVAL_AND_SOURCE_REQUIRED")
    need(isinstance(spec["sceneId"], str) and
         _ID.fullmatch(spec["sceneId"]),
         "DYNAMIC_WRITE_FRESH_SCENE_NAME_REQUIRED")
    operations = plan["graph"]["operations"]
    need(isinstance(operations, list) and
         len(operations) <= 20 and
         len({row["id"] for row in operations}) == len(operations),
         "DYNAMIC_WRITE_BOUNDED_UNIQUE_GRAPH_REQUIRED")
    writes = [step for step in operations
              if router.operation_kind(step["command"]) != "READ_ONLY"]
    need(len(writes) == 1 and
         spec["stepId"] == writes[0]["id"] and
         spec["command"] == writes[0]["command"] and
         spec["effect"] in _MUTATE and
         router.operation_kind(spec["command"]) == spec["effect"] and
         spec["impact"] == "MODEL" and
         router.policies[spec["command"]]["impact"] == "MODEL" and
         spec["commandContractHash"] ==
         router.contract_hash(spec["command"]) and
         spec["parametersHash"] == router.A.RUN.digest(writes[0]["params"]),
         "DYNAMIC_WRITE_SINGLE_REVIEWED_NATIVE_MUTATION_REQUIRED")
    need(all(router.operation_kind(row["command"]) == "READ_ONLY"
             for row in operations if row["id"] != spec["stepId"]),
         "DYNAMIC_WRITE_UNREVIEWED_SECOND_MUTATION")
    need(all(isinstance(spec[key], str) and _HASH.fullmatch(spec[key])
             for key in ("expectedBeforeGuidSetHash",
                         "expectedBeforeNativeBrepHash")),
         "DYNAMIC_WRITE_LIVE_MODEL_FINGERPRINT_REQUIRED")
    affected, retained = spec["affectedGuids"], spec["retainedGuids"]
    need(isinstance(affected, list) and isinstance(retained, list) and
         all(isinstance(g, str) and _GUID.fullmatch(g) and g == g.lower()
             for g in affected + retained) and
         len(affected) == len(set(affected)) and
         len(retained) == len(set(retained)) and
         not set(affected).intersection(retained) and
         (bool(affected) if spec["effect"] == "MODIFY" else not affected),
         "DYNAMIC_WRITE_COMPLETE_OWNED_GUID_SCOPE_REQUIRED")
    verifier = registry.get(spec["verifierId"])
    need(isinstance(verifier, NativeVerifier) and
         verifier.verifier_id == spec["verifierId"] and
         verifier.command == spec["command"] and
         verifier.effect == spec["effect"],
         "DYNAMIC_WRITE_UNQUALIFIED_CODE_OWNED_VERIFIER")
    return verifier


def validate_existing_ledger(journal, scene_id, reconciliation=None):
    """No SQL mutations. No automatic replay or quiet UNKNOWN removal."""
    journal = Path(journal)
    need(journal.is_file(), "DYNAMIC_WRITE_ORIGINAL_SCENEWRITER_SQLITE_REQUIRED")
    with closing(sqlite3.connect(f"file:{journal.as_posix()}?mode=ro", uri=True)) as db:
        old = db.execute("SELECT scene_id,state FROM scenes").fetchall()
    need(scene_id not in {r[0] for r in old},
         "DYNAMIC_WRITE_SCENE_ID_ALREADY_USED_NEVER_RETRY")
    pending = [(name, status) for name, status in old if status != "PASS"]
    if pending:
        need(isinstance(reconciliation, dict) and
             reconciliation.get("status") ==
             "PREVIOUS_UNKNOWN_EFFECT_ABSENT_FROM_CURRENT_MODEL_PASS" and
             {r[0] for r in pending} == {reconciliation.get("sceneId")},
             "DYNAMIC_WRITE_UNRECONCILED_PREVIOUS_NATIVE_OPERATION")
    return pending


def build_existing_workflow_scopes(*, spec, plan, router, registry,
                                   writer, api, capture_model, guid_inventory,
                                   current_project_sha, approved_project_sha,
                                   local_authorization,
                                   reconciliation=None):
    """Scope factory for DynamicCommands.run_workflow(..., scopes=factory).

    Does not execute; initial matching is read-only. The same original
    DynamicCommands.execute handles native registration, identity, SQLite
    durable intent, full retained BREP and independent verifier callbacks.
    """
    spec, plan = copy.deepcopy(spec), copy.deepcopy(plan)
    verifier = verify_contract(spec, plan, router, registry,
                               approved_project_sha=approved_project_sha,
                               local_authorization=local_authorization)
    unresolved = validate_existing_ledger(
        writer.journal_path, spec["sceneId"], reconciliation=reconciliation)
    need(current_project_sha() == approved_project_sha,
         "DYNAMIC_WRITE_SAVED_PROJECT_HASH_CHANGED")

    def provide_scope(step, ticket, prior_results):
        need(step["id"] == spec["stepId"] and
             ticket["command"] == spec["command"] and
             ticket["effect"] == spec["effect"] and
             router.contract_hash(ticket["command"]) ==
             spec["commandContractHash"],
             "DYNAMIC_WRITE_RESOLVED_OPERATION_CHANGED")
        # Result-dependent parameter bindings are not yet authorized for a
        # native mutation: resolve them in a separate reviewed source task.
        need(ticket["parameters"] == step["params"] and
             router.A.RUN.digest(ticket["parameters"]) ==
             spec["parametersHash"],
             "DYNAMIC_WRITE_DYNAMIC_PARAMS_REQUIRES_NEW_APPROVAL")
        need(current_project_sha() == approved_project_sha,
             "DYNAMIC_WRITE_WORKING_PLN_CHANGED")
        before = set(guid_inventory(api))
        affected, retained = set(spec["affectedGuids"]), set(spec["retainedGuids"])
        need(before == affected | retained and
             router.A.RUN.digest(sorted(before)) ==
             spec["expectedBeforeGuidSetHash"],
             "DYNAMIC_WRITE_CURRENT_GUID_INVENTORY_SCOPE_DRIFT")
        # Source BREP is read by the retained documentation system, not
        # inferred from GetAllElements which has no native type field.
        native_before = capture_model(api, sorted(before))
        import archicad_connected_components as C
        nodes = {e["guid"].lower():e for e in native_before["elements"]}
        need(set(nodes) == before and
             router.A.RUN.digest({
                 g: C.ROOF.geometry_signature(nodes[g]) for g in sorted(before)
             }) == spec["expectedBeforeNativeBrepHash"],
             "DYNAMIC_WRITE_COMPLETE_APPROVED_BREP_BASELINE_DRIFT")
        if unresolved:
            need(reconciliation["savedProjectSHA256"] ==
                 approved_project_sha and
                 reconciliation["guidSetHash"] ==
                 spec["expectedBeforeGuidSetHash"] and
                 reconciliation["brepSignaturesHash"] ==
                 spec["expectedBeforeNativeBrepHash"] and
                 reconciliation.get("modelWrites") == 0,
                 "DYNAMIC_WRITE_HISTORIC_RECONCILIATION_NOT_CURRENT")
        retained_brep = C.retained_geometry_signatures(
            native_before, sorted(retained))
        need(set(retained_brep) == retained,
             "DYNAMIC_WRITE_RETAINED_NATIVE_BREP_NOT_COMPLETE")
        source_proof = verifier.before(
            api=api, command=ticket["command"],
            parameters=ticket["parameters"],
            affected=sorted(affected), native_before=native_before)
        need(isinstance(source_proof, dict) and
             str(source_proof.get("status", "")).endswith("PASS"),
             "DYNAMIC_WRITE_SOURCE_SPECIFIC_PREFLIGHT_NOT_PASS")

        def preflight(live_api):
            validate_existing_ledger(writer.journal_path, spec["sceneId"],
                                     reconciliation=reconciliation)
            need(current_project_sha() == approved_project_sha and
                 set(guid_inventory(live_api)) == before,
                 "DYNAMIC_WRITE_LIVE_MODEL_CHANGED_BEFORE_DISPATCH")
            fresh = capture_model(live_api, sorted(before))
            fresh_nodes = {e["guid"].lower(): e for e in fresh["elements"]}
            need(set(fresh_nodes) == before and
                 router.A.RUN.digest({
                     g: C.ROOF.geometry_signature(fresh_nodes[g])
                     for g in sorted(before)
                 }) == spec["expectedBeforeNativeBrepHash"],
                 "DYNAMIC_WRITE_BREP_CHANGED_BEFORE_DISPATCH")
            return verifier.before(
                api=live_api, command=ticket["command"],
                parameters=ticket["parameters"], affected=sorted(affected),
                native_before=fresh)

        def postflight(native_reply, _):
            after = set(guid_inventory(api))
            native_after = capture_model(api, sorted(after))
            evidence = verifier.after(
                api=api, command=ticket["command"],
                parameters=ticket["parameters"],
                native_response=native_reply,
                before_guids=before, after_guids=after,
                affected=sorted(affected),
                native_before=native_before, native_after=native_after,
                source_proof=source_proof)
            need(isinstance(evidence, dict) and
                 str(evidence.get("status", "")).endswith("PASS"),
                 "DYNAMIC_WRITE_SOURCE_SPECIFIC_NATIVE_READBACK_NOT_PASS")
            return evidence

        return {
            "scene_id": spec["sceneId"],
            "affected": sorted(affected),
            "retained_signatures": retained_brep,
            "saved_sha256": approved_project_sha,
            "authorization": local_authorization,
            "impact": "MODEL",
            "verify_before": preflight,
            "verify_after": postflight,
        }

    return provide_scope


def prepare_scope_preview(spec, plan, router, registry, *,
                          approved_project_sha, local_authorization):
    """Integration result without native calls or write permission."""
    verifier = verify_contract(
        spec, plan, router, registry,
        approved_project_sha=approved_project_sha,
        local_authorization=local_authorization)
    return {
        "schema": "APA_AC29_DYNAMIC_MUTATION_SCOPE_PREVIEW_V1",
        "status": "EXISTING_DYNAMIC_WORKFLOW_SCOPE_PREPARED_NO_EXECUTION",
        "nativeCommand": spec["command"],
        "effect": spec["effect"],
        "codeOwnedVerifier": verifier.verifier_id,
        "existingGraphHash": plan["sourcePlanHash"],
        "engine": "EXISTING_APA_DYNAMIC_COMMANDS_SCENEWRITER",
        "nativeWritePermission": False,
        "automaticNativeExecution": False,
        "modelWrites": 0,
    }
