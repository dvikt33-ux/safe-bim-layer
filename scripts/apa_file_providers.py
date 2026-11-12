"""Attach source-file analysis and documentation to the existing APA router."""

from functools import partial
import hashlib
import json
from pathlib import Path

import apa_dxf_geometry_c1 as dxf_geometry
import apa_dxf_source_preflight as dxf_preflight
import apa_external_catalog as external
import apa_external_readonly as external_worker
import apa_high_density_readonly_v2 as v2
import apa_ifc_artifacts_b2 as ifc_artifacts
import apa_ifc_geometry_b3 as ifc_geometry
import apa_ifc_reports_b1 as ifc_reports
import apa_semantic_catalog as semantic
import apa_semantic_readonly as semantic_worker


DOCUMENTATION = "AddOn.APADocumentation.ModelDocumentation"


def document(a, guids, story, output):
    from archicad_bim_documentation import C, bundle, make_snapshot, write_package

    source = v2.input_file(a, ".json")
    destination = Path(output).resolve()
    stable = v2.STABLE.resolve()
    v2.require(destination.parent.is_dir() and not destination.exists()
               and stable not in destination.parents, "DOCUMENTATION_NEW_DIRECTORY_REQUIRED")
    payload = source.read_bytes()
    source_hash = hashlib.sha256(payload).hexdigest()
    model = json.loads(payload.decode("utf-8-sig"))
    if model.get("succeeded") is True:
        model = model["result"]["addOnCommandResponse"]
    v2.require(model.get("schemaVersion") == 1 and model.get("units") == "m"
               and model.get("coordinateSystem") == "ABSOLUTE_PROJECT_XYZ"
               and model.get("regenerated3D") is True, "DOCUMENTATION_NATIVE_DUMP_V1_REQUIRED")
    if "bodies" in model:
        model = C.G.normalize_dump(model)
    else:
        v2.require(all(isinstance(row.get("bodies"), list) for row in model["elements"]),
                   "DOCUMENTATION_NORMALIZED_BODIES_REQUIRED")
    selection = [element["guid"] for element in model["elements"]] if guids is None else guids
    package = bundle(make_snapshot(model, selection), story)
    v2.require(v2.digest(source) == source_hash, "DOCUMENTATION_SOURCE_CHANGED")
    write_package(package, destination)
    report = destination / "documentation.json"
    return {"schema": "APA_DOCUMENTATION_FROM_DUMP_V1",
            "sourceSha256": source_hash, "modelVersion": package["modelVersion"],
            "sampleOnly": model.get("sampleOnly") is True,
            "artifact": {"path": str(report), "sha256": v2.digest(report)},
            "specifications": {kind: spec["count"] for kind, spec in package["specifications"].items()},
            "nativeCalls": 0, "modelWrites": 0}


def crop_plan(a, page, clip, output, dpi=144):
    from apa_arch_plan_benchmark import extract

    source = v2.input_file(a, ".pdf")
    destination = Path(output).resolve()
    v2.require(destination.parent.is_dir() and v2.STABLE.resolve() not in destination.parents,
               "PDF_PLAN_CROP_OUTPUT_OUTSIDE_INSTALLED_APA_REQUIRED")
    return extract(source, page, clip, destination, dpi)


def opening_candidates(a, cropReceipt, sourceSha256, page, clip, output, modelReport=None):
    from apa_ap2_massops_preflight import inspect

    source = v2.input_file(a, ".pdf")
    destination = v2.output_file(output, source)
    result = inspect(source, cropReceipt, modelReport, page=page, clip=clip,
                     expected_source_hash=sourceSha256)
    payload = json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False)
    with destination.open("x", encoding="utf-8") as stream:
        stream.write(payload + "\n")
    return result


def attach_architectural_sources(router):
    string = {"type": "string", "minLength": 1}
    digest = {"type": "string", "pattern": "^[0-9a-f]{64}$"}
    common = {"a": string, "output": string, "page": {"type": "integer", "minimum": 1},
              "clip": {"type": "array", "minItems": 4, "maxItems": 4, "items": {"type": "number"}}}
    fields = {
        "PDFPlanCrop": {**common, "dpi": {"type": "integer", "minimum": 72, "maximum": 400}},
        "HostedOpeningCandidates": {**common, "cropReceipt": string, "sourceSha256": string,
                                    "modelReport": string},
    }
    output_fields = {
        "PDFPlanCrop": {"sourceSHA256": digest, "outputEvidence": string, "outputImage": string,
                        "rasterSHA256": digest},
        "HostedOpeningCandidates": {"sourceSHA256": digest, "readyForModelWrite": {"const": False},
                                    "candidateBatches": {"type": "array"}},
    }
    namespace = "APAArchitecturalSources"
    contracts = {}
    for name, props in fields.items():
        result = {**output_fields[name], "nativeCalls": {"const": 0}, "modelWrites": {"const": 0}}
        contracts[name] = {"version": "1", "category": "APA_ARCHITECTURAL_SOURCE_ANALYSIS",
                           "parameters": {"type": "object", "properties": props,
                                          "required": [k for k in props if k not in ("dpi", "modelReport")],
                                          "additionalProperties": False},
                           "returns": {"type": "object", "properties": result, "required": list(result)}}
    router.add_local_provider(namespace, contracts,
                              {"PDFPlanCrop": crop_plan, "HostedOpeningCandidates": opening_candidates},
                              "AP2 source-qualified PDF planning", {name: ["PyMuPDF"] for name in fields})
    for name in contracts:
        command = f"AddOn.{namespace}.{name}"
        router.review_policy(command, "READ_ONLY", "READ_ONLY",
                             {"source": "AP2 source-qualified PDF planning", "sha256": router.contract_hash(command)})


def attach(router, *, semantic_profile=None):
    external.register(router, runner=external_worker.execute)
    v2.register(router, runner=v2.execute)
    ifc_reports.register(router, runner=ifc_reports.execute)
    ifc_artifacts.register(router, runner=ifc_artifacts.execute)
    ifc_geometry.register(router, runner=ifc_geometry.execute)
    dxf_geometry.register(router, runner=dxf_geometry.execute)
    dxf_preflight.register(router, handler=dxf_preflight.execute)
    semantic.register(router, runner=partial(semantic_worker.execute, ml_config=semantic_profile),
                      names=None if semantic_profile else ("PDFPaths", "PDFPageRaster"))
    attach_architectural_sources(router)

    fields = {
        "a": {"type": "string", "minLength": 1},
        "guids": {"anyOf": [{"type": "array", "items": {"type": "string", "format": "uuid"},
                             "minItems": 1, "uniqueItems": True}, {"type": "null"}]},
        "story": {"type": "integer"},
        "output": {"type": "string", "minLength": 1},
    }
    contract = {
        "version": "1", "category": "APA_DOCUMENTATION",
        "description": "Prepare specifications from an explicit GUID set in a native dump.",
        "parameters": {"type": "object", "properties": fields, "required": list(fields),
                       "additionalProperties": False},
        "returns": {"type": "object", "required": ["schema", "sourceSha256", "modelVersion",
                                                     "artifact", "specifications", "nativeCalls", "modelWrites"]},
    }
    router.add_local_provider("APADocumentation", {"ModelDocumentation": contract},
                              {"ModelDocumentation": document}, "archicad_bim_documentation.py",
                              {"ModelDocumentation": []})
    router.review_policy(DOCUMENTATION, "READ_ONLY", "READ_ONLY",
                         {"source": "APA_DOCUMENTATION_FROM_DUMP_V1",
                          "sha256": router.contract_hash(DOCUMENTATION)})
