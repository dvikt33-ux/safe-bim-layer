"""APA AC29 high-density READ_ONLY sidecar (draft source; NOT installed).

Twelve separately addressable IFC/DXF facts checks. Uses only the exact vendor
environment already provisioned for APA external read-only V1. Native API calls
and PLN/APX writes are deliberately absent. Registration is opt-in, session-local.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys

STABLE = Path(r"C:\LocalAI\APA_AC29_Stable")
V1 = STABLE / "external-tools" / "apa-readonly-v1"
SAMPLE_LIMIT = 5000
MAX_SOURCE_BYTES = 4 * 1024 ** 3

# Names are deliberately separate from the existing V1 six commands.
COMMANDS = {
    "IFCSchemaInventory": ("ifc-schema", ".ifc"),
    "IFCGlobalIdAudit": ("ifc-globalids", ".ifc"),
    "IFCSpatialRelations": ("ifc-spatial", ".ifc"),
    "IFCOpeningRelations": ("ifc-openings", ".ifc"),
    "IFCPortRelations": ("ifc-ports", ".ifc"),
    "IFCPropertySetCoverage": ("ifc-psets", ".ifc"),
    "IFCClassificationCoverage": ("ifc-classifications", ".ifc"),
    "IFCGeoReferenceAudit": ("ifc-georef", ".ifc"),
    "DXFLayerInventory": ("dxf-layers", ".dxf"),
    "DXFBlockInsertions": ("dxf-blocks", ".dxf"),
    "DXFTextAnnotations": ("dxf-text", ".dxf"),
    "DXFDimensionEntities": ("dxf-dimensions", ".dxf"),
}
ACTIONS = {action: ext for action, ext in COMMANDS.values()}
NAMESPACE = "APAHighDensityReadOnlyV2"


def require(ok, error):
    if not ok:
        raise ValueError(error)


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def input_file(value, extension):
    p = Path(value).resolve(strict=True)
    require(p.is_file() and p.suffix.lower() == extension,
            "READONLY_SOURCE_EXTENSION_INVALID")
    require(p.stat().st_size <= MAX_SOURCE_BYTES,
            "READONLY_SOURCE_TOO_LARGE")
    return p


def output_file(value, source):
    p = Path(value).resolve()
    require(p.suffix.lower() == ".json" and p.parent.is_dir() and
            not p.exists() and p != source,
            "READONLY_OUTPUT_MUST_BE_NEW_JSON")
    # No report in the stable APA install; no original model modifications.
    stable = STABLE.resolve()
    require(p != stable and stable not in p.parents,
            "READONLY_OUTPUT_INSIDE_STABLE_APA_REFUSED")
    return p


def sample(items, total=None):
    """Bound JSON evidence size; always declare incomplete samples."""
    rows = list(items[:SAMPLE_LIMIT])
    count = len(items) if total is None else total
    return {"total": count, "items": rows, "truncated": count > len(rows)}


def gid(element):
    if element is None:
        return None
    value = getattr(element, "GlobalId", None)
    return str(value) if value else None


def typename(element):
    return element.is_a() if element is not None else None


def by_type_if_exists(model, name):
    try:
        return model.by_type(name)
    except RuntimeError:
        # Not all IFC entity definitions exist in every IFC schema (IFC2X3/4/4X3).
        return []


def _ifc_schema(model):
    physical = list(model.by_type("IfcProduct"))
    roots = list(model.by_type("IfcRoot"))
    spatial = by_type_if_exists(model, "IfcSpatialStructureElement")
    return {"ifcSchema": model.schema, "rootCount": len(roots),
            "productCount": len(physical), "spatialCount": len(spatial),
            "productTypes": dict(sorted(Counter(x.is_a() for x in physical).items())),
            "status": "EXPORTED_IFC_ONLY_NOT_NATIVE_MODEL_DUMP"}


def _ifc_globalids(model):
    roots = model.by_type("IfcRoot")
    seen = set()
    duplicates, missing = [], []
    duplicate_count = missing_count = 0
    for x in roots:
        value = gid(x)
        if not value:
            missing_count += 1
            if len(missing) < SAMPLE_LIMIT:
                missing.append({"ifcClass": x.is_a(), "stepId": x.id()})
        elif value in seen:
            duplicate_count += 1
            if len(duplicates) < SAMPLE_LIMIT:
                duplicates.append(value)
        else:
            seen.add(value)
    return {"rootCount": len(roots), "distinctGlobalIds": len(seen),
            "missingCount": missing_count, "duplicateCount": duplicate_count,
            "missingExamples": missing, "duplicateExamples": duplicates,
            "examplesTruncated": max(missing_count, duplicate_count) > SAMPLE_LIMIT,
            "nativeGuidMappingChecked": False}


def _ifc_spatial(model):
    aggregate = model.by_type("IfcRelAggregates")
    containment = model.by_type("IfcRelContainedInSpatialStructure")
    rows = []
    for r in aggregate:
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"relation": "aggregate", "parent": gid(r.RelatingObject),
                         "childCount": len(r.RelatedObjects),
                         "childrenSample": [gid(x) for x in r.RelatedObjects[:20]]})
    for r in containment:
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"relation": "containment", "parent": gid(r.RelatingStructure),
                         "childCount": len(r.RelatedElements),
                         "childrenSample": [gid(x) for x in r.RelatedElements[:20]]})
    return sample(rows, len(aggregate) + len(containment))


def _ifc_openings(model):
    voids = model.by_type("IfcRelVoidsElement")
    fills = model.by_type("IfcRelFillsElement")
    rows = []
    for r in voids:
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"kind": "void", "wallOrHost": gid(r.RelatingBuildingElement),
                         "opening": gid(r.RelatedOpeningElement)})
    for r in fills:
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"kind": "fill", "opening": gid(r.RelatingOpeningElement),
                         "windowOrDoor": gid(r.RelatedBuildingElement)})
    return {"voids": len(voids), "fills": len(fills),
            "relations": sample(rows, len(voids) + len(fills)),
            "physicalHostGeometryChecked": False}


def _ifc_ports(model):
    ports = by_type_if_exists(model, "IfcDistributionPort")
    connected = by_type_if_exists(model, "IfcRelConnectsPorts")
    referenced = set()
    rows = []
    for r in connected:
        a = gid(r.RelatingPort)
        b = gid(r.RelatedPort)
        if a:
            referenced.add(a)
        if b:
            referenced.add(b)
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"from": a, "to": b, "relation": gid(r)})
    no_edge = [gid(p) for p in ports if gid(p) not in referenced]
    return {"ports": len(ports), "portConnections": len(connected),
            "unlinkedByIfcRelConnectsPorts": len(no_edge),
            "unlinkedExamples": no_edge[:SAMPLE_LIMIT],
            "relations": sample(rows, len(connected)),
            "nativeMEPConnectionVerified": False,
            "note": "Missing exported port relation does not prove a faulty native MEP connection."}


def _ifc_psets(model):
    rels = model.by_type("IfcRelDefinesByProperties")
    names = Counter()
    object_assignments = 0
    for r in rels:
        definition = r.RelatingPropertyDefinition
        name = getattr(definition, "Name", None) or definition.is_a()
        names[str(name)] += len(r.RelatedObjects)
        object_assignments += len(r.RelatedObjects)
    return {"propertyRelations": len(rels),
            "assignedObjectReferences": object_assignments,
            "coverageBySetName": dict(sorted(names.items())),
            "russianCodeComplianceClaimed": False}


def _ifc_classifications(model):
    rels = by_type_if_exists(model, "IfcRelAssociatesClassification")
    rows = []
    for r in rels:
        c = r.RelatingClassification
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"classificationType": typename(c),
                         "code": getattr(c, "Identification", None) or
                                 getattr(c, "ItemReference", None),
                         "relatedCount": len(r.RelatedObjects)})
    return sample(rows, len(rels))


def _ifc_georef(model):
    conversions = by_type_if_exists(model, "IfcMapConversion")
    systems = by_type_if_exists(model, "IfcProjectedCRS")
    rows = []
    for o in conversions:
        rows.append({key: getattr(o, key, None) for key in (
            "Eastings", "Northings", "OrthogonalHeight",
            "XAxisAbscissa", "XAxisOrdinate", "Scale")})
    crs = [{"name": getattr(x, "Name", None),
            "description": getattr(x, "Description", None)} for x in systems]
    sites = by_type_if_exists(model, "IfcSite")
    return {"ifcSchema": model.schema, "mapConversions": rows[:SAMPLE_LIMIT],
            "projectedCrs": crs[:SAMPLE_LIMIT],
            "siteReferenceCoordinates": [
                {"name": x.Name, "latitude": x.RefLatitude, "longitude": x.RefLongitude}
                for x in sites[:SAMPLE_LIMIT]],
            "ifc2x3MayLackMapConversion": True,
            "worldCoordinateCalibrationVerified": False}


def vec(value):
    if value is None:
        return None
    return [float(v) for v in value]


def _dxf_layers(doc):
    msp = doc.modelspace()
    counts = Counter(str(x.dxf.get("layer", "0")) for x in msp)
    layers = []
    for x in doc.layers:
        layers.append({"name": x.dxf.name, "color": x.dxf.color,
                       "off": x.is_off() if hasattr(x, "is_off") else None,
                       "modelspaceCount": counts.get(x.dxf.name, 0)})
    return {"insunitsCode": doc.header.get("$INSUNITS", 0),
            "layers": sample(layers), "modelspaceEntities": sum(counts.values()),
            "unitConversionApplied": False}


def _dxf_blocks(doc):
    msp = doc.modelspace()
    rows = []
    count = 0
    for x in msp:
        if x.dxftype() != "INSERT":
            continue
        count += 1
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"blockName": x.dxf.name, "layer": x.dxf.layer,
                         "insert": vec(x.dxf.insert),
                         "xscale": x.dxf.get("xscale", 1.0),
                         "yscale": x.dxf.get("yscale", 1.0),
                         "zscale": x.dxf.get("zscale", 1.0),
                         "rotationDegrees": x.dxf.get("rotation", 0.0),
                         "attributes": [
                             {"tag": a.dxf.tag, "text": a.dxf.text}
                             for a in x.attribs[:40]]})
    return {"insertions": sample(rows, count), "transformsApplied": False,
            "bimFamiliesInferred": False}


def _dxf_text(doc):
    rows = []
    count = 0
    for x in doc.modelspace():
        typ = x.dxftype()
        if typ not in ("TEXT", "MTEXT"):
            continue
        count += 1
        if len(rows) < SAMPLE_LIMIT:
            raw = x.dxf.get("text") if typ == "TEXT" else x.text
            rows.append({"entity": typ, "layer": x.dxf.layer, "rawText": raw,
                         "insert": vec(x.dxf.get("insert")),
                         "style": x.dxf.get("style")})
    return {"annotations": sample(rows, count), "ocrPerformed": False}


def _dxf_dimensions(doc):
    rows = []
    count = 0
    for x in doc.modelspace():
        if x.dxftype() != "DIMENSION":
            continue
        count += 1
        if len(rows) < SAMPLE_LIMIT:
            rows.append({"layer": x.dxf.layer,
                         "dimensionTypeCode": x.dxf.get("dimtype"),
                         "textOverride": x.dxf.get("text"),
                         "basePoint": vec(x.dxf.get("defpoint")),
                         "blockName": x.dxf.get("geometry")})
    return {"dimensions": sample(rows, count),
            "geometryOrScaleRecalculated": False,
            "dimensionIsAuthoritativeConstructionMeasure": False}


IFC_HANDLERS = {
    "ifc-schema": _ifc_schema,
    "ifc-globalids": _ifc_globalids,
    "ifc-spatial": _ifc_spatial,
    "ifc-openings": _ifc_openings,
    "ifc-ports": _ifc_ports,
    "ifc-psets": _ifc_psets,
    "ifc-classifications": _ifc_classifications,
    "ifc-georef": _ifc_georef,
}
DXF_HANDLERS = {
    "dxf-layers": _dxf_layers,
    "dxf-blocks": _dxf_blocks,
    "dxf-text": _dxf_text,
    "dxf-dimensions": _dxf_dimensions,
}


def verified_python():
    """Reuse an already installed V1 isolated interpreter, no packages installed."""
    require(platform.system() == "Windows", "WIN32_ISOLATED_RUNTIME_REQUIRED")
    python = V1 / "venv" / "Scripts" / "python.exe"
    receipt = V1 / "installation.json"
    require(python.is_file() and receipt.is_file(),
            "V1_ISOLATED_VENDOR_INSTALL_REQUIRED")
    manifest = json.loads(receipt.read_text(encoding="utf-8"))
    require(manifest.get("schema") == "APA_EXTERNAL_READONLY_INSTALL_V1",
            "V1_MANIFEST_SCHEMA_INVALID")
    for key, filename in (("adapterSHA256", "apa_external_readonly.py"),
                          ("catalogSHA256", "apa_external_catalog.py"),
                          ("requirementsSHA256", "requirements-external-readonly.txt")):
        item = V1 / filename
        require(item.is_file() and manifest.get(key) == digest(item),
                "V1_VENDOR_INSTALL_HASH_MISMATCH:" + filename)
    return python


def call(action, params):
    """Invoke reviewed independent process. Never run a user-selected module."""
    require(action in ACTIONS, "V2_ACTION_NOT_WHITELISTED")
    require(set(params) == {"a", "output"} and
            all(isinstance(v, str) and v for v in params.values()),
            "V2_INVALID_PARAMETERS")
    src = input_file(params["a"], ACTIONS[action])
    out = output_file(params["output"], src)
    py = verified_python()
    script = Path(__file__).resolve(strict=True)
    before = digest(script)
    result = subprocess.run(
        [str(py), str(script), action, "--a", str(src), "--output", str(out)],
        check=False, capture_output=True, text=True, timeout=1200)
    require(digest(script) == before, "V2_SCRIPT_CHANGED_DURING_EXECUTION")
    require(result.returncode == 0 and out.is_file(),
            "V2_ANALYSIS_FAILED:" + (result.stdout + result.stderr)[-1200:])
    require(out.stat().st_size < 200 * 1024 ** 2, "V2_REPORT_OVER_200MB")
    data = json.loads(out.read_text(encoding="utf-8"))
    require(data.get("schema") == "APA_HIGH_DENSITY_READONLY_V2" and
            data.get("action") == action and data.get("modelWrites") == 0 and
            data.get("nativeCalls") == 0 and
            data.get("sources", [{}])[0].get("sha256") == digest(src) and
            data.get("adapterSha256") == before,
            "V2_EVIDENCE_UNVERIFIED")
    return data


def register(router):
    """Opt-in attachment to existing DynamicCommands; does not alter V1 six."""
    verified_python()
    props = {"a": {"type": "string", "minLength": 1},
             "output": {"type": "string", "minLength": 1}}
    contracts, handlers, dependencies = {}, {}, {}
    for command, (action, _) in COMMANDS.items():
        contracts[command] = {
            "name": command, "version": "2",
            "category": "APA_READONLY_IFC_DXF",
            "description": "IFC/DXF source evidence only: " + action,
            "parameters": {"type": "object", "properties": props,
                           "required": ["a", "output"],
                           "additionalProperties": False},
            "returns": {"type": "object",
                        "required": ["schema", "action", "sources", "result",
                                     "modelWrites", "nativeCalls"]}}
        handlers[command] = (lambda act: lambda **kw: call(act, kw))(action)
        dependencies[command] = []
    router.add_local_provider(NAMESPACE, contracts, handlers,
                              "APA_HIGH_DENSITY_READONLY_V2_SOURCE_DRAFT",
                              dependencies)
    for name in COMMANDS:
        key = "AddOn." + NAMESPACE + "." + name
        router.review_policy(key, "READ_ONLY", "READ_ONLY",
                             {"source": "APA_HIGH_DENSITY_READONLY_V2",
                              "sha256": router.contract_hash(key)})
    return {"status": "V2_READONLY_REGISTERED_NOT_NATIVE_WRITER",
            "commands": sorted("AddOn." + NAMESPACE + "." + x for x in COMMANDS),
            "addedCommands": len(COMMANDS), "nativeCalls": 0, "modelWrites": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=sorted(ACTIONS))
    parser.add_argument("--a", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    require(sys.version_info[:2] in {(3, 11), (3, 12)} and
            platform.system() == "Windows", "V2_VENDOR_PYTHON_311_OR_312_REQUIRED")
    src = input_file(args.a, ACTIONS[args.action])
    out = output_file(args.output, src)
    if args.action in IFC_HANDLERS:
        import ifcopenshell
        result = IFC_HANDLERS[args.action](ifcopenshell.open(str(src)))
    else:
        import ezdxf
        result = DXF_HANDLERS[args.action](ezdxf.readfile(str(src)))
    report = {"schema": "APA_HIGH_DENSITY_READONLY_V2",
              "status": "SOURCE_FILE_FACTS_NOT_BIM_ACCEPTANCE",
              "action": args.action,
              "sources": [{"name": src.name, "sha256": digest(src)}],
              "adapterSha256": digest(Path(__file__)),
              "result": result,
              "modelWrites": 0, "nativeCalls": 0}
    with out.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, ensure_ascii=False,
                  allow_nan=False, default=str)
        stream.write("\n")
    print("APA_STATUS: V2_READONLY_EVIDENCE_CREATED")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print("APA_STATUS: V2_READONLY_BLOCKED")
        print("ERROR:", type(exc).__name__ + ": " + str(exc))
        sys.exit(2)
