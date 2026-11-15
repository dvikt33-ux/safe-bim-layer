"""Load release-matched Tapir contracts and reproducibly import upstream catalogs."""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re
import subprocess

import archicad_batch_contracts as CONTRACTS
import archicad_project_accelerator as APA
from apa_release import MANIFEST, read_release, verify_member
from archicad_dynamic_commands import DynamicCommands


ROOT = Path(__file__).resolve().parents[1]
SCHEMA = "APA_TAPIR_CATALOG_V1"
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.]+)?")
REVISION = re.compile(r"[a-f0-9]{40}")
SHA256 = re.compile(r"[a-f0-9]{64}")
FILES = ("command_definitions.js", "common_schema_definitions.js")
NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
WRITE_OR_SERVICE = CONTRACTS.SPECIAL_REVIEW | CONTRACTS.BIM_RECIPE_CANDIDATES | {
    "GenerateDocumentation", "MoveElements", "CloneNativeGroupV1", "CreateNativeGroupV1",
    "UngroupNativeGroupV1", "SaveProjectAs",
}


def router_for(snapshot):
    common = snapshot["common_schemas"]
    if any(not NAME.fullmatch(name) or row.get("name") != name or row.get("api") != "tapir"
           or row.get("namespace", "TapirCommand") != "TapirCommand"
           or row.get("provider", "TapirCommand") != "TapirCommand"
           or row.get("commandName", name) != name for name, row in snapshot["commands"].items()):
        raise ValueError("TAPIR_CATALOG_INVALID_COMMAND_ID")
    for ref in CONTRACTS._refs(snapshot):
        if (not isinstance(ref, str) or not ref.startswith("#/") or "/" in ref[2:]
                or ref[2:].replace("~1", "/").replace("~0", "~") not in common):
            raise ValueError("TAPIR_CATALOG_UNRESOLVED_OR_EXTERNAL_SCHEMA_REFERENCE")
    return DynamicCommands(snapshot)


def record_for(snapshot, archicad_versions, evidence):
    """A source review authorizes reads for these exact input/output contracts."""
    router = router_for(snapshot)
    operations = {}
    for command, proof in sorted(evidence.items()):
        if command not in snapshot["commands"] or command in WRITE_OR_SERVICE:
            raise ValueError("TAPIR_REVIEWED_COMMAND_NOT_READ_ELIGIBLE")
        if not proof.get("source") or not SHA256.fullmatch(proof.get("sha256", "")):
            raise ValueError("TAPIR_SOURCE_REVIEW_REQUIRED")
        operations[command] = dict(kind="READ_ONLY", impact="READ_ONLY", evidence=proof)
    return dict(schema=SCHEMA, archicadVersions=sorted(set(archicad_versions)), snapshot=snapshot,
                review=dict(operations=operations,
                            contractHashes={name: router.contract_hash(name) for name in operations}))


def load_for_runtime(config, runtime):
    version = runtime["tapirVersion"]
    if not isinstance(version, str) or not VERSION.fullmatch(version):
        raise ValueError("TAPIR_RUNTIME_VERSION_INVALID")
    path = Path(config["catalog"]) if "catalog" in config else ROOT / "schemas/tapir-bridge" / (version + ".json")
    if not path.is_file():
        raise ValueError("TAPIR_CATALOG_FOR_RUNTIME_REQUIRED")
    if "catalog" not in config and (ROOT / MANIFEST).is_file():
        verify_member(ROOT, read_release(ROOT), path.relative_to(ROOT).as_posix())
    raw = path.read_bytes()
    digest = sha256(raw).hexdigest()
    if "catalog" in config and digest != config["catalogSha256"]:
        raise ValueError("TAPIR_CATALOG_HASH_DRIFT")
    record = json.loads(raw)
    if (not isinstance(record, dict) or record.get("schema") != SCHEMA
            or runtime["archicadVersion"] not in record["archicadVersions"]):
        raise ValueError("TAPIR_CATALOG_PRODUCT_INCOMPATIBLE")
    snapshot = record["snapshot"]
    if "relativePath" in snapshot:
        # Reuse the original pinned live export in the Windows distribution.
        schema_root = (ROOT / "schemas").resolve()
        source = (schema_root / snapshot["relativePath"]).resolve(strict=True)
        if not source.is_relative_to(schema_root) or sha256(source.read_bytes()).hexdigest() != snapshot["sha256"]:
            raise ValueError("TAPIR_CATALOG_REFERENCED_SNAPSHOT_DRIFT")
        snapshot = APA.catalog_with_provenance(source)
    if CONTRACTS.source_version(snapshot) != version:
        raise ValueError("TAPIR_CATALOG_RUNTIME_VERSION_MISMATCH")
    router = router_for(snapshot)
    review = record["review"]
    if (set(review["operations"]) != set(review["contractHashes"])
            or any(row["kind"] != "READ_ONLY" or row["impact"] != "READ_ONLY"
                   or name in WRITE_OR_SERVICE
                   for name, row in review["operations"].items())):
        raise ValueError("TAPIR_READ_POLICY_INVALID")
    if review["operations"]:
        router.load_policies(review)
    return router, digest


def import_release(repo, revision, version, archicad_versions, review, output):
    """Generate data from an immutable Tapir checkout, without evaluating JavaScript."""
    if not REVISION.fullmatch(revision) or not VERSION.fullmatch(version):
        raise ValueError("EXACT_TAPIR_SOURCE_REVISION_AND_VERSION_REQUIRED")
    if not archicad_versions or any(type(v) is not int or v < 25 for v in archicad_versions):
        raise ValueError("TAPIR_COMPATIBLE_ARCHICAD_VERSIONS_REQUIRED")
    if not isinstance(review, dict):
        raise ValueError("TAPIR_SOURCE_REVIEW_REQUIRED")
    git = ["git", "--no-pager", "-C", str(repo)]

    def source(path):
        relative = PurePosixPath(path)
        if relative.is_absolute() or ".." in relative.parts or not relative.parts:
            raise ValueError("TAPIR_SOURCE_PATH_INVALID")
        return subprocess.run(git + ["show", f"{revision}:{relative.as_posix()}"],
                              check=True, capture_output=True, timeout=30).stdout

    definition = source("archicad-addon/Sources/AddOnVersion.hpp")
    if f'"{version}"'.encode() not in definition:
        raise ValueError("TAPIR_SOURCE_RELEASE_VERSION_MISMATCH")
    files = {name: source("docs/archicad-addon/" + name) for name in FILES}
    evidence = {}
    for command, path in review.items():
        if not path.startswith("archicad-addon/Sources/"):
            raise ValueError("TAPIR_SOURCE_REVIEW_PATH_INVALID")
        content = source(path)
        if f'"{command}"'.encode() not in content:
            raise ValueError("TAPIR_SOURCE_REVIEW_COMMAND_MISSING")
        evidence[command] = dict(source=f"{revision}:{path}", sha256=sha256(content).hexdigest())
    snapshot = APA.documentation_catalog(files, {"tapirVersion": version, "sourceRevision": revision},
                                         origin="Tapir release documentation at a pinned Git revision")
    record = record_for(snapshot, archicad_versions, evidence)
    data = (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                       allow_nan=False) + "\n").encode("utf-8")
    with Path(output).open("xb") as stream:
        stream.write(data)
    return dict(status="TAPIR_CATALOG_IMPORTED", tapirVersion=version, sourceRevision=revision,
                documentedCommands=len(snapshot["commands"]), reviewedReads=len(review),
                catalogSha256=sha256(data).hexdigest(), inputs=snapshot["_metadata"]["inputs"])
