"""Opt-in IFC reports through existing APA DynamicCommands; no native calls.

Uses already provisioned V1 vendors. ODS is a ZIP artifact, never JSON input.
All reports go to a newly created directory outside the installed APA.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import apa_high_density_readonly_v2 as V2

NAMESPACE = "APAIFCReportsB1"
COMMANDS = {"IFCSelect": "select", "IFCSchemaValidate": "validate",
            "IDSReportODS": "ids-ods"}
SCHEMA = "APA_IFC_REPORTS_B1"


def parameters(action):
    fields = {"a": {"type": "string", "minLength": 1},
              "output": {"type": "string", "minLength": 1}}
    if action == "select":
        fields["query"] = {"type": "string", "minLength": 1, "maxLength": 4096}
    if action == "ids-ods":
        fields["ids"] = {"type": "string", "minLength": 1}
    return fields


def inputs(action, params):
    V2.require(action in COMMANDS.values(), "B1_UNKNOWN_ACTION")
    V2.require(set(params) == set(parameters(action)) and
               all(isinstance(x, str) and x for x in params.values()),
               "B1_INVALID_PARAMETERS")
    if action == "select":
        V2.require(len(params["query"]) <= 4096, "B1_QUERY_TOO_LONG")
    sources = [V2.input_file(params["a"], ".ifc")]
    if action == "ids-ods":
        sources.append(V2.input_file(params["ids"], ".ids"))
    out = Path(params["output"]).resolve()
    stable = V2.STABLE.resolve()
    V2.require(out.parent.is_dir() and not out.exists() and
               out != stable and stable not in out.parents,
               "B1_OUTPUT_MUST_BE_NEW_DIRECTORY_OUTSIDE_APA")
    return sources, out


def versions(action):
    names = ["ifcopenshell"] + (["ifctester"] if action == "ids-ods" else [])
    found = {name: importlib.metadata.version(name) for name in names}
    V2.require(all(v == "0.8.5" for v in found.values()), "B1_VENDOR_VERSION_DRIFT")
    return found


def ods_readback(path):
    V2.require(path.stat().st_size <= 200 * 1024**2, "B1_ARTIFACT_TOO_LARGE")
    with zipfile.ZipFile(path) as archive:
        V2.require(sum(x.file_size for x in archive.infolist()) <= 200 * 1024**2,
                   "B1_ZIP_EXPANSION_TOO_LARGE")
        V2.require(archive.testzip() is None and "content.xml" in archive.namelist()
                   and archive.read("mimetype") ==
                   b"application/vnd.oasis.opendocument.spreadsheet", "B1_INVALID_ODS")
    return {"name": path.name, "type": "application/vnd.oasis.opendocument.spreadsheet",
            "sha256": V2.digest(path), "bytes": path.stat().st_size}


def execute(action, params):
    sources, out = inputs(action, params)
    vendor = versions(action)
    before = [V2.digest(p) for p in sources]
    import ifcopenshell
    model = ifcopenshell.open(str(sources[0]))
    out.mkdir(exist_ok=False)
    artifacts = []
    if action == "select":
        from ifcopenshell.util.selector import filter_elements
        selected = sorted(filter_elements(model, params["query"]), key=lambda e: e.id())
        rows = [{"stepId": e.id(), "ifcClass": e.is_a(), "globalId": V2.gid(e),
                 "name": getattr(e, "Name", None),
                 "inverseReferences": V2.sample([
                     {"stepId": r.id(), "ifcClass": r.is_a(), "globalId": V2.gid(r)}
                     for r in sorted(model.get_inverse(e), key=lambda r: r.id())])}
                for e in selected[:V2.SAMPLE_LIMIT]]
        result = {"query": params["query"], "elements": V2.sample(rows, len(selected)),
                  "nativeGuidMappingVerified": False}
    elif action == "validate":
        import ifcopenshell.validate
        logger = ifcopenshell.validate.json_logger()
        ifcopenshell.validate.validate(model, logger, express_rules=False)
        result = {"issues": V2.sample(logger.statements),
                  "schemaValid": not logger.statements, "expressRulesChecked": False,
                  "geometryChecked": False, "russianCodeComplianceClaimed": False}
    else:
        from ifctester import ids, reporter
        specification = ids.open(str(sources[1]))
        specification.validate(model)
        report = reporter.Ods(specification)
        report.report()
        artifact = out / "ids-report.ods"
        report.to_file(str(artifact))
        artifacts.append(ods_readback(artifact))
        result = {"idsPassed": bool(report.results["status"]),
                  "specifications": len(specification.specifications)}
    V2.require(before == [V2.digest(p) for p in sources], "B1_SOURCE_CHANGED")
    evidence = {"schema": SCHEMA, "action": action, "vendors": vendor,
                "sources": [{"name": p.name, "sha256": h} for p, h in zip(sources, before)],
                "sourceUnchanged": True, "ifcSchema": model.schema,
                "adapterSha256": V2.digest(__file__), "artifacts": artifacts,
                "result": result, "nativeCalls": 0, "modelWrites": 0}
    with (out / "report.json").open("x", encoding="utf-8") as stream:
        json.dump(evidence, stream, ensure_ascii=False, indent=2, allow_nan=False, default=str)
    return json.loads((out / "report.json").read_text(encoding="utf-8"))


def call(action, params):
    sources, out = inputs(action, params)
    before = [V2.digest(p) for p in sources]
    script = Path(__file__).resolve()
    adapter = V2.digest(script)
    args = [str(V2.verified_python()), "-B", str(script), action]
    for key, value in params.items():
        args.extend(["--" + key, value])
    process = subprocess.run(args, capture_output=True, text=True, timeout=1200)
    V2.require(process.returncode == 0, "B1_VENDOR_FAILED:" + process.stderr[-1200:])
    path = out / "report.json"
    V2.require(path.is_file() and path.stat().st_size <= 200 * 1024**2, "B1_REPORT_MISSING_OR_LARGE")
    data = json.loads(path.read_text(encoding="utf-8"))
    V2.require(V2.digest(script) == adapter and before == [V2.digest(p) for p in sources]
               and data.get("schema") == SCHEMA and data.get("action") == action
               and data.get("adapterSha256") == adapter
               and data.get("sourceUnchanged") is True
               and data.get("sources") == [{"name": p.name, "sha256": h} for p, h in zip(sources, before)]
               and data.get("nativeCalls") == data.get("modelWrites") == 0,
               "B1_EVIDENCE_MISMATCH")
    expected = [ods_readback(out / "ids-report.ods")] if action == "ids-ods" else []
    V2.require(data.get("artifacts") == expected, "B1_ARTIFACT_MISMATCH")
    return data


def register(router):
    """Extend the caller's existing router; never create a second router."""
    V2.verified_python()
    contracts, handlers = {}, {}
    for name, action in COMMANDS.items():
        fields = parameters(action)
        contracts[name] = {"name": name, "version": "1", "category": "APA_IFC_REPORTS",
            "parameters": {"type": "object", "properties": fields,
                           "required": list(fields), "additionalProperties": False},
            "returns": {"type": "object", "required": ["schema", "sources", "result",
                                                           "artifacts", "nativeCalls", "modelWrites"]}}
        handlers[name] = (lambda act: lambda **kw: call(act, kw))(action)
    router.add_local_provider(NAMESPACE, contracts, handlers, SCHEMA,
                              {name: [] for name in COMMANDS})
    for name in COMMANDS:
        key = "AddOn." + NAMESPACE + "." + name
        router.review_policy(key, "READ_ONLY", "READ_ONLY",
                             {"source": SCHEMA, "sha256": router.contract_hash(key)})
    return sorted("AddOn." + NAMESPACE + "." + name for name in COMMANDS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=COMMANDS.values())
    for key in ("a", "output", "query", "ids"):
        parser.add_argument("--" + key)
    args = vars(parser.parse_args())
    action = args.pop("action")
    execute(action, {k: v for k, v in args.items() if v is not None})


if __name__ == "__main__":
    main()
