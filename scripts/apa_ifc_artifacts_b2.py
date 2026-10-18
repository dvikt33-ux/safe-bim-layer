"""Fixed upstream CSV, ExtractElements and BCF adapters for APA AC29.

Opt-in registration on the existing router. All mutations operate on a private
IFC copy and all outputs use a new directory, never the source or installed APA.
"""
import argparse
import csv
import importlib.metadata
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import zipfile
from xml.etree import ElementTree as ET

import apa_high_density_readonly_v2 as V2

NAMESPACE = "APAIFCArtifactsB2"
SCHEMA = "APA_IFC_ARTIFACTS_B2"
COMMANDS = {"IFCCSVExport": "csv", "IFCExtractElements": "extract", "IFCBCFIssues": "bcf"}
FILES = {"csv": "properties.csv", "extract": "subset.ifc", "bcf": "issues.bcfzip"}
PACKAGES = {"csv": "ifccsv", "extract": "ifcpatch", "bcf": "bcf-client"}


def fields(action):
    props = {key: {"type": "string", "minLength": 1} for key in ("a", "output", "query")}
    if action == "csv":
        props["attributes"] = {"type": "array", "minItems": 1, "maxItems": 100,
                               "items": {"type": "string", "minLength": 1}}
    if action == "bcf":
        props.update({key: {"type": "string", "minLength": 1} for key in ("title", "description", "author")})
    return props


def inputs(action, params):
    V2.require(action in FILES, "B2_UNKNOWN_ACTION")
    V2.require(set(params) == set(fields(action)), "B2_INVALID_PARAMETERS")
    V2.require(all(isinstance(v, str) and v for k, v in params.items() if k != "attributes"),
               "B2_STRING_PARAMETERS_REQUIRED")
    V2.require(len(params["query"]) <= 4096, "B2_QUERY_TOO_LONG")
    if action == "csv":
        attrs = params["attributes"]
        V2.require(isinstance(attrs, list) and 1 <= len(attrs) <= 100 and
                   all(isinstance(x, str) and 0 < len(x) <= 4096 for x in attrs), "B2_INVALID_ATTRIBUTES")
    source = V2.input_file(params["a"], ".ifc")
    out = Path(params["output"]).resolve()
    V2.require(out.parent.is_dir() and not out.exists() and out != V2.STABLE.resolve()
               and V2.STABLE.resolve() not in out.parents, "B2_NEW_DIRECTORY_REQUIRED")
    return source, out


def artifact_readback(path, action):
    V2.require(path.is_file() and path.stat().st_size < 200 * 1024**2, "B2_ARTIFACT_MISSING_OR_LARGE")
    details = {}
    if action == "csv":
        with path.open(encoding="utf-8", newline="") as stream:
            reader = csv.reader(stream)
            header = next(reader)
            count = 0
            for row in reader:
                V2.require(len(row) == len(header), "B2_CSV_WIDTH_MISMATCH")
                count += 1
            details = {"headers": header, "rows": count}
    elif action == "extract":
        with path.open("rb") as stream:
            V2.require(stream.read(64).startswith(b"ISO-10303-21;"), "B2_IFC_HEADER_INVALID")
    else:
        with zipfile.ZipFile(path) as archive:
            V2.require(sum(x.file_size for x in archive.infolist()) < 200 * 1024**2
                       and archive.testzip() is None, "B2_BCF_ZIP_INVALID")
            version = ET.fromstring(archive.read("bcf.version"))
            V2.require(version.attrib.get("VersionId") == "2.1", "B2_BCF_VERSION_INVALID")
            views = [x for x in archive.namelist() if x.endswith(".bcfv")]
            guids = []
            for view in views:
                root = ET.fromstring(archive.read(view))
                guids.extend(x.attrib["IfcGuid"] for x in root.findall(".//Selection/Component"))
            details = {"viewpoints": len(views), "selectedIfcGuids": sorted(guids)}
    return {"name": path.name, "format": action, "bytes": path.stat().st_size,
            "sha256": V2.digest(path), **details}


def execute(action, params):
    source, out = inputs(action, params)
    versions = {p: importlib.metadata.version(p) for p in ("ifcopenshell", PACKAGES[action])}
    V2.require(all(v == "0.8.5" for v in versions.values()), "B2_VENDOR_VERSION_DRIFT")
    before = V2.digest(source)
    out.mkdir(exist_ok=False)
    import ifcopenshell
    from ifcopenshell.util.selector import filter_elements
    with tempfile.TemporaryDirectory(prefix="private-copy-", dir=out) as temporary:
        copy = Path(temporary) / "source.ifc"
        shutil.copyfile(source, copy)
        V2.require(V2.digest(copy) == before, "B2_COPY_HASH_MISMATCH")
        model = ifcopenshell.open(str(copy))
        selected = sorted(filter_elements(model, params["query"]), key=lambda x: x.id())
        V2.require(selected, "B2_SELECTION_EMPTY")
        artifact = out / FILES[action]
        result = {"selected": len(selected)}
        if action == "csv":
            from ifccsv import IfcCsv
            raw = Path(temporary) / "raw.csv"
            IfcCsv().export(model, selected, list(params["attributes"]), output=str(raw), format="csv")
            escaped = 0
            with raw.open(encoding="utf-8", newline="") as src, artifact.open("x", encoding="utf-8", newline="") as dst:
                writer = csv.writer(dst)
                for row in csv.reader(src):
                    safe = []
                    for value in row:
                        if value.lstrip().startswith(("=", "+", "-", "@")):
                            value = "'" + value
                            escaped += 1
                        safe.append(value)
                    writer.writerow(safe)
            result["spreadsheetFormulaEscapes"] = escaped
        elif action == "extract":
            from ifcpatch.recipes.ExtractElements import Patcher
            # Fixed recipe class bypasses IFCPATCH_RECIPE_DIR plugin overrides.
            patch = Patcher(model, query=params["query"], assume_asset_uniqueness_by_name=False)
            patch.patch()
            patch.file.write(str(artifact))
            readback = ifcopenshell.open(str(artifact))
            expected = {V2.gid(x) for x in selected}
            V2.require(None not in expected and expected <= {V2.gid(x) for x in readback.by_type("IfcRoot")},
                       "B2_EXTRACT_GUID_READBACK_FAILED")
            result.update(selectedGlobalIds=sorted(expected), outputSchema=readback.schema,
                          geometryEquivalenceVerified=False)
        else:
            from bcf.v2.bcfxml import BcfXml
            V2.require(len(selected) <= 2000 and all(x.is_a("IfcProduct") and
                       getattr(x, "ObjectPlacement", None) is not None and V2.gid(x) for x in selected),
                       "B2_BCF_REQUIRES_PLACED_PRODUCTS_MAX_2000")
            bcf = BcfXml.create_new("APA exported IFC issues")
            for element in selected:
                topic = bcf.add_topic(params["title"], params["description"], params["author"],
                                      topic_type="Issue", topic_status="Open")
                topic.add_viewpoint(element)
            bcf.save(artifact)
            readback = artifact_readback(artifact, action)
            V2.require(readback["selectedIfcGuids"] == sorted(V2.gid(x) for x in selected),
                       "B2_BCF_GUID_READBACK_FAILED")
            result.update(topics=len(selected), nativeGuidMappingVerified=False, snapshotsCreated=False)
        metadata = artifact_readback(artifact, action)
    V2.require(before == V2.digest(source), "B2_SOURCE_CHANGED")
    receipt = {"schema": SCHEMA, "action": action, "vendors": versions,
               "source": {"name": source.name, "sha256": before}, "sourceUnchanged": True,
               "adapterSha256": V2.digest(__file__), "artifact": metadata, "result": result,
               "nativeCalls": 0, "modelWrites": 0, "copyOnly": True}
    with (out / "report.json").open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, indent=2, ensure_ascii=False, allow_nan=False)
    return receipt


def call(action, params, python):
    source, out = inputs(action, params)
    before, adapter = V2.digest(source), V2.digest(__file__)
    completed = subprocess.run([str(python), "-B", str(Path(__file__).resolve()), action,
                                "--parameters", json.dumps(params)], capture_output=True,
                               text=True, timeout=1200)
    V2.require(completed.returncode == 0, "B2_VENDOR_FAILED:" + completed.stderr[-1200:])
    report = out / "report.json"
    V2.require(report.is_file() and report.stat().st_size < 200 * 1024**2, "B2_REPORT_INVALID")
    data = json.loads(report.read_text(encoding="utf-8"))
    V2.require(before == V2.digest(source) and adapter == V2.digest(__file__)
               and data.get("adapterSha256") == adapter and data.get("schema") == SCHEMA
               and data.get("action") == action and data.get("source") == {"name": source.name, "sha256": before}
               and data.get("sourceUnchanged") is True and data.get("copyOnly") is True
               and data.get("modelWrites") == data.get("nativeCalls") == 0
               and data.get("artifact") == artifact_readback(out / FILES[action], action), "B2_READBACK_FAILED")
    return data


def register(router, python):
    """python is trusted deployment configuration, not a routed user parameter."""
    python = Path(python).resolve(strict=True)
    contracts, handlers = {}, {}
    for name, action in COMMANDS.items():
        props = fields(action)
        contracts[name] = {"name": name, "version": "1", "category": "APA_IFC_ARTIFACTS",
            "parameters": {"type": "object", "properties": props, "required": list(props), "additionalProperties": False},
            "returns": {"type": "object", "required": ["schema", "artifact", "source", "copyOnly", "nativeCalls", "modelWrites"]}}
        handlers[name] = (lambda a: lambda **kw: call(a, kw, python))(action)
    router.add_local_provider(NAMESPACE, contracts, handlers, SCHEMA, {x: [] for x in COMMANDS})
    for name in COMMANDS:
        key = "AddOn." + NAMESPACE + "." + name
        router.review_policy(key, "READ_ONLY", "READ_ONLY", {"source": SCHEMA, "sha256": router.contract_hash(key)})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=FILES)
    parser.add_argument("--parameters", required=True)
    args = parser.parse_args()
    execute(args.action, json.loads(args.parameters))
