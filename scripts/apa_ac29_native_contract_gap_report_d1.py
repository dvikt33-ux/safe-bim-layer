"""Read-only inventory of existing native contracts; registers no commands."""
import argparse
import hashlib
import json
from pathlib import Path
import re

AREAS = {"groups": r"^(CreateGroups|GetGroupsOfElements|GetElementsOfGroups|GetSuspendGroupsMode|SetSuspendGroupsMode|GetNativeGroupRootsV1|CloneNativeGroupV1)$", "hotlinks": r"Hotlink", "publisher": r"Publish",
         "grid_axes": r"Grid|Axis", "properties": r"Property|Properties",
         "attributes": r"Attribute|Layer|Material"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def inventory(schema, manifest, receipt=None):
    schema, manifest = Path(schema), Path(manifest)
    catalog = json.loads(schema.read_text(encoding="utf8"))
    modules = json.loads(manifest.read_text(encoding="utf8"))
    provenance = "SNAPSHOT_ONLY"
    if receipt:
        receipt = Path(receipt)
        record = json.loads(receipt.read_text(encoding="utf8"))
        if record.get("schema") != "APA_AC29_READONLY_SESSION_FACTORY_INSTALL_V1" or record.get("schemaSHA256") != digest(schema):
            raise ValueError("D1_SCHEMA_RECEIPT_DRIFT")
        if set(record.get("provenanceSHA256", {})) != {"command_definitions.js", "common_schema_definitions.js"}:
            raise ValueError("D1_PROVENANCE_INCOMPLETE")
        for name, expected in record.get("provenanceSHA256", {}).items():
            if name not in {"command_definitions.js", "common_schema_definitions.js"} or digest(receipt.parent / name) != expected:
                raise ValueError("D1_PROVENANCE_DRIFT")
        provenance = "INSTALLED_RECEIPT_HASH_MATCH_NOT_FRESH_RUNTIME"
    groups = {}
    for area, pattern in AREAS.items():
        rows = []
        for name, contract in catalog["commands"].items():
            if re.search(pattern, name, re.I):
                rows.append(contract_summary(name, "existingTapirCatalog", contract))
        for namespace, commands in modules["sdkProviders"].items():
            for name, contract in commands.items():
                if re.search(pattern, name, re.I):
                    rows.append(contract_summary("AddOn." + namespace + "." + name, "existingSdkManifest", contract))
        groups[area] = {"existingContractCount": len(rows), "contracts": rows,
                        "liveRegistration": "NOT_PROBED", "nativeAcceptance": "NOT_RUN",
                        "gap": "NO_MATCHING_CONTRACT" if not rows else "REUSE_EXISTING_CONTRACTS_VERIFY_NATIVE_GATE"}
    return {"schema": "APA_AC29_NATIVE_CONTRACT_GAPS_D1", "areas": groups,
            "tapirSchemaSHA256": digest(schema), "sdkManifestSHA256": digest(manifest),
            "provenance": provenance, "snapshotVersionLabel": "1.5.10_NOT_REACQUIRED",
            "newCallableNativeCommands": 0, "catalogMutations": 0, "nativeCalls": 0, "plnWrites": 0,
            "route": ["DynamicCommands", "BIM Graph", "SceneWriter", "existing native bridge"]}


def contract_summary(name, source, contract):
    parameters = contract.get("parameters") or {}
    return {"command": name, "source": source,
            "inputRequired": parameters.get("required", []),
            "inputProperties": sorted(parameters.get("properties", {})),
            "contractSHA256": hashlib.sha256(json.dumps(contract, sort_keys=True).encode()).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--schema", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    report = inventory(args.schema, args.manifest, args.receipt)
    with args.output.open("x", encoding="utf8") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
