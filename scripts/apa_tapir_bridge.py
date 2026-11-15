"""Versioned Tapir discovery and guarded reads via the existing DynamicCommands router."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from threading import Lock

from jsonschema import ValidationError

from archicad_native_api import ArchicadAPIError, native_command
import archicad_batch_contracts as CONTRACTS
import archicad_project_accelerator as APA
import archicad_tapir_catalog as CATALOG
from archicad_tapir_profile import exact_file, guard, hash_file, profile_from_path


PAGE_SIZE = 32
READ_LIMIT = 16 * 1024 * 1024


def _read_transport(port, command, parameters):
    return native_command(port, command, parameters, timeout=20, max_response=READ_LIMIT)


def _contract(router, command):
    definition = router.catalog["commands"][command]
    shared = router.catalog["common_schemas"]
    schemas = {}
    pending = list(CONTRACTS._refs(definition))
    while pending:
        name = pending.pop()[2:].replace("~1", "/").replace("~0", "~")
        if name not in schemas:
            schemas[name] = shared[name]
            pending.extend(CONTRACTS._refs(shared[name]))
    return dict(parameters=definition.get("parameters"), returns=definition.get("returns"),
                commonSchemas=schemas, contractHash=router.contract_hash(command))


class TapirControl:
    def __init__(self, profile, transport=None):
        self.profile = exact_file(str(profile))
        self.profile_sha = hash_file(self.profile)
        self.transport = transport or _read_transport
        self.evidence = self.profile.with_name(self.profile.stem + "-tapir-evidence")
        self.lock = Lock()
        self._config()

    def _config(self):
        self._check_profile()
        config = profile_from_path(self.profile)
        self._check_profile()
        return config

    def _check_profile(self):
        if hash_file(self.profile) != self.profile_sha:
            raise ValueError("TAPIR_READ_PROFILE_DRIFT")

    def perform(self, operation, command=None, parameters=None, offset=0, probe=False):
        with self.lock:
            try:
                return self._perform(operation, command, parameters, offset, probe)
            except ArchicadAPIError as exc:
                return dict(status="BLOCKED", reason=exc.code, command=exc.command, detail=exc.detail)
            except ValidationError as exc:
                return dict(status="BLOCKED", reason="TAPIR_SCHEMA_VALIDATION_FAILED",
                            command=command, schemaPath=list(exc.absolute_schema_path),
                            detail=exc.message[:1000])
            except (OSError, ValueError, KeyError, TypeError, RuntimeError) as exc:
                return dict(status="BLOCKED", reason=str(exc), command=command)

    def _perform(self, operation, command, parameters, offset, probe):
        if operation not in {"status", "catalog", "read"}:
            raise ValueError("TAPIR_READ_OPERATIONS_ONLY")
        if (command is not None and not isinstance(command, str)
                or operation == "read" and not command
                or parameters is not None and operation != "read"
                or type(offset) is not int or offset < 0
                or probe and (operation != "catalog" or not command)):
            raise ValueError("TAPIR_TOOL_ARGUMENTS_INVALID")
        config = self._config()
        if self.evidence.resolve() != self.evidence:
            raise ValueError("TAPIR_EVIDENCE_DIRECTORY_REDIRECTED")
        self.evidence.mkdir(exist_ok=True)
        port = config["port"]
        api = APA.EvidenceAPI(lambda name, params: self.transport(port, name, params), self.evidence)
        runtime = guard(config, api)
        facts = dict(runtime=runtime, port=port, profileSha256=self.profile_sha, modelWrites=0)
        try:
            router, catalog_sha = CATALOG.load_for_runtime(config, runtime)
        except ValueError as exc:
            if operation == "status" and str(exc) == "TAPIR_CATALOG_FOR_RUNTIME_REQUIRED":
                self._check_profile()
                return dict(facts, status="TAPIR_RUNTIME_IDENTIFIED", catalogStatus=str(exc))
            raise
        names = sorted(router.catalog["commands"])
        facts.update(catalogSha256=catalog_sha, documentedCommands=len(names),
                     reviewedReads=len(router.policies), source=router.catalog["_metadata"])
        if operation == "status":
            self._check_profile()
            return dict(facts, status="TAPIR_RUNTIME_IDENTIFIED")

        def same_project():
            self._check_profile()
            current = guard(config, api)
            if current != runtime:
                raise ValueError("TAPIR_PROJECT_OR_RUNTIME_CHANGED_DURING_READ")
            return current

        if command and command not in router.catalog["commands"]:
            raise ValueError("COMMAND_NOT_DISCOVERED")
        if operation == "catalog":
            selected = [command] if command else names[offset:offset + PAGE_SIZE]
            if probe:
                router.probe_runtime(api, command, required=False)
                same_project()
            rows = [dict(name=name, effect=router.operation_kind(name),
                         runtimeRegistered=router.registration.get(name)) for name in selected]
            result = dict(facts, status="TAPIR_CATALOG", commands=rows, offset=offset)
            if command:
                result["contract"] = _contract(router, command)
            elif offset + PAGE_SIZE < len(names):
                result["nextOffset"] = offset + PAGE_SIZE
            self._check_profile()
            return result
        if router.operation_kind(command) != "READ_ONLY":
            raise ValueError("SOURCE_REVIEWED_READ_ONLY_EFFECT_REQUIRED")
        # The local profile and exact catalog are pinned before dispatch. The
        # existing router validates the ticket, registration and response.
        ticket = router.prepare(command, {} if parameters is None else parameters)
        result = router.read(api, ticket, reviewed_read_only=True, project_guard=same_project)
        same_project()
        self._check_profile()
        return dict(facts, status="TAPIR_READ_VERIFIED", command=command, runtimeRegistered=True,
                    contractHash=router.contract_hash(command), parameters=ticket["parameters"], result=result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="operation", required=True)
    for operation in ("status", "catalog", "read"):
        action = sub.add_parser(operation)
        action.add_argument("--profile", required=True, type=Path)
        if operation != "status":
            action.add_argument("--command", required=operation == "read")
        if operation == "catalog":
            action.add_argument("--offset", type=int, default=0)
            action.add_argument("--probe", action="store_true")
        if operation == "read":
            action.add_argument("--parameters", type=Path)
    imports = sub.add_parser("import-catalog")
    imports.add_argument("--source-repo", type=Path, required=True)
    imports.add_argument("--revision", required=True)
    imports.add_argument("--tapir-version", required=True)
    imports.add_argument("--archicad-version", type=int, action="append", required=True)
    imports.add_argument("--review", type=Path, required=True, help="JSON mapping of reviewed names to source files")
    imports.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.operation == "import-catalog":
            result = CATALOG.import_release(args.source_repo, args.revision, args.tapir_version,
                                            args.archicad_version, json.loads(args.review.read_bytes()), args.output)
        else:
            parameters = getattr(args, "parameters", None)
            result = TapirControl(args.profile.resolve(strict=True)).perform(
                args.operation, getattr(args, "command", None),
                json.loads(parameters.read_bytes()) if parameters else None,
                getattr(args, "offset", 0), getattr(args, "probe", False))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        result = dict(status="BLOCKED", reason=str(exc))
    print(json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2))
    return 2 if result["status"] == "BLOCKED" else 0
