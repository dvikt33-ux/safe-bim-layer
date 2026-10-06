"""Build the safe, deterministic core of the Archicad 29 SBIM template.

This script is deliberately fail-closed:
- validate: offline validation only, no Archicad connection and no writes.
- inspect: read-only live inventory of the currently open Archicad project.
- plan: read-only live preflight plus a concrete action plan.
- apply-core: writes ONLY the currently proven safe core:
  Project Info fields, Layers, Pen Tables, simple Line Types, Layer Combinations.
  It refuses a non-empty model unless --allow-nonempty is passed explicitly.

Later phases (fills/surfaces/building materials/composites/properties/favorites/views)
remain outside apply-core until their dependency-resolution gates are implemented.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

try:
    import yaml
except ImportError as exc:
    raise SystemExit("PyYAML is required: python -m pip install PyYAML>=6,<7") from exc

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "docs" / "archicad-template"
TAPIR_SCHEMA = ROOT / "tapir-1.5.8.json"
DEFAULT_PORT = 19723
EVIDENCE_ROOT = Path(os.environ.get(
    "SAFE_BIM_MVP_EVIDENCE",
    Path(tempfile.gettempdir()) / "safe-bim-mvp-evidence"
)) / "template-builder"

LAYER_SPEC = SPEC / "layer-registry-v0.1.yaml"
GRAPHICS_SPEC = SPEC / "graphics-registry-v0.1.yaml"
BASELINE_SPEC = SPEC / "project-baseline-v0.1.yaml"

SAFE_CORE_COMMANDS = {
    "GetProjectInfo", "GetProjectInfoFields", "CreateProjectInfoFields",
    "GetAllElements", "GetAttributesByType", "GetLayers",
    "CreateLayers", "CreateLayerCombinations",
    "CreatePenTables", "CreateLines", "GetModelViewOptions",
    "GetCalculationUnits", "GetGeoLocation", "GetStories",
}
ATTRIBUTE_TYPES = (
    "Layer", "LayerCombination", "PenTable", "Line", "Fill",
    "Surface", "BuildingMaterial", "Composite", "Profile", "MEPSystem",
)


def load_yaml(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")


class Tapir:
    def __init__(self, port: int, evidence_dir: Path):
        self.port = port
        self.evidence_dir = evidence_dir
        self.seq = 0

    def call(self, command: str, parameters=None, timeout=120):
        self.seq += 1
        stem = f"{self.seq:03d}-{command}"
        request = {
            "command": "API.ExecuteAddOnCommand",
            "parameters": {
                "addOnCommandId": {
                    "commandNamespace": "TapirCommand",
                    "commandName": command,
                },
                "addOnCommandParameters": parameters or {},
            },
        }
        payload = json.dumps(request, ensure_ascii=False).encode("utf-8")
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
        (self.evidence_dir / f"{stem}.request.json").write_bytes(payload)
        req = urllib.request.Request(
            f"http://127.0.0.1:{self.port}",
            payload,
            {"Content-Type": "application/json"},
        )
        started = time.perf_counter()
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read()
        elapsed = time.perf_counter() - started
        (self.evidence_dir / f"{stem}.response.json").write_bytes(raw)
        envelope = json.loads(raw)
        if not envelope.get("succeeded"):
            raise RuntimeError(f"{command} failed: {envelope}")
        result = envelope.get("result", {}).get("addOnCommandResponse", {})
        if isinstance(result, dict) and "error" in result:
            raise RuntimeError(f"{command} returned error: {result}")
        write_json(self.evidence_dir / f"{stem}.meta.json", {
            "command": command, "seconds": elapsed
        })
        return result


def schema_commands():
    schema = load_json(TAPIR_SCHEMA)
    return schema.get("commands", {})


def validate_command_capability():
    commands = schema_commands()
    missing = sorted(SAFE_CORE_COMMANDS - set(commands))
    if missing:
        raise ValueError(f"Tapir schema is missing required safe-core commands: {missing}")
    return {
        name: {
            "version": commands[name].get("version"),
            "category": commands[name].get("category"),
        }
        for name in sorted(SAFE_CORE_COMMANDS)
    }


def validate_specs():
    layers = load_yaml(LAYER_SPEC)
    graphics = load_yaml(GRAPHICS_SPEC)
    baseline = load_yaml(BASELINE_SPEC)

    errors = []
    warnings = []

    layer_items = layers.get("layers", [])
    layer_names = [x["name"] for x in layer_items]
    duplicates = sorted({x for x in layer_names if layer_names.count(x) > 1})
    if duplicates:
        errors.append(f"Duplicate layer names: {duplicates}")
    if "Archicad Layer" in layer_names:
        errors.append("Built-in Archicad Layer must not be redefined in SBIM registry.")
    for item in layer_items:
        group = item.get("group")
        if not isinstance(group, int) or group < 0:
            errors.append(f"Invalid intersection group for {item.get('name')}: {group}")

    known = set(layer_names)
    for combo_name, combo in (layers.get("layer_combinations") or {}).items():
        explicit = set(combo.get("show", [])) | set(combo.get("hide", []))
        unknown = sorted(explicit - known)
        if unknown:
            errors.append(f"{combo_name} references unknown registered layers: {unknown}")
        overlap = set(combo.get("show", [])) & set(combo.get("hide", []))
        if overlap:
            errors.append(f"{combo_name} both shows and hides: {sorted(overlap)}")

    pens = graphics.get("semantic_pens") or {}
    seen_pen_names = set()
    for raw_idx, pen in pens.items():
        idx = int(raw_idx)
        if idx < 1 or idx > 255:
            errors.append(f"Pen index outside 1..255: {idx}")
        if float(pen.get("width_mm", 0)) <= 0:
            errors.append(f"Pen {idx} has invalid width: {pen.get('width_mm')}")
        name = pen.get("name")
        if name in seen_pen_names:
            errors.append(f"Duplicate semantic pen name: {name}")
        seen_pen_names.add(name)

    line_names = []
    for line in graphics.get("line_types", []):
        name = line["name"]
        line_names.append(name)
        line_type = line.get("line_type")
        if line_type not in {"Solid", "Dashed", "Symbol"}:
            errors.append(f"{name}: unsupported line_type {line_type}")
        if line_type == "Dashed":
            pairs = line.get("dash_items", [])
            total = sum(float(x["dash_mm"]) + float(x["gap_mm"]) for x in pairs)
            period = float(line.get("period_mm", 0))
            if period <= 0 or not math.isclose(total, period, abs_tol=1e-9):
                errors.append(
                    f"{name}: period_mm={period} but dash/gap sum={total}"
                )
    if len(line_names) != len(set(line_names)):
        errors.append("Duplicate line type names.")

    api_unit = baseline.get("units", {}).get("sbim_api", {}).get("geometry_unit")
    if api_unit != "m":
        errors.append(f"SBIM API geometry unit must remain m, got {api_unit!r}")

    validate_command_capability()
    return {
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
        "warnings": warnings,
        "counts": {
            "layers": len(layer_items),
            "layerCombinations": len(layers.get("layer_combinations") or {}),
            "semanticPens": len(pens),
            "lineTypesCandidate": len(graphics.get("line_types", [])),
        },
    }


def attribute_headers(api: Tapir, attribute_type: str):
    result = api.call("GetAttributesByType", {"attributeType": attribute_type})
    if "attributes" not in result:
        raise RuntimeError(
            f"GetAttributesByType({attribute_type}) returned no attributes: {result}"
        )
    return result["attributes"]


def index_headers(headers):
    return {x["name"]: x for x in headers}


def live_inventory(api: Tapir):
    project = api.call("GetProjectInfo")
    fields = api.call("GetProjectInfoFields").get("fields", [])
    all_elements = api.call("GetAllElements")
    elements = all_elements.get("elements", [])
    attrs = {}
    for attribute_type in ATTRIBUTE_TYPES:
        try:
            attrs[attribute_type] = attribute_headers(api, attribute_type)
        except Exception as exc:
            attrs[attribute_type] = {"error": str(exc)}
    mvo = api.call("GetModelViewOptions").get("modelViewOptions", [])
    try:
        calculation_units = api.call("GetCalculationUnits")
    except Exception as exc:
        calculation_units = {"error": str(exc)}
    try:
        geo = api.call("GetGeoLocation")
    except Exception as exc:
        geo = {"error": str(exc)}
    try:
        stories = api.call("GetStories")
    except Exception as exc:
        stories = {"error": str(exc)}
    return {
        "project": project,
        "elementCount": len(elements),
        "projectInfoFields": fields,
        "attributes": attrs,
        "modelViewOptions": mvo,
        "calculationUnits": calculation_units,
        "geoLocation": geo,
        "stories": stories,
    }


def project_info_targets():
    return {
        "SBIM.TemplateVersion": "AC29_RU_SBIM_0.1-CANDIDATE",
        "SBIM.SchemaVersion": "0.1",
        "SBIM.Project.ObjectClass": "",
        "SBIM.Project.ActiveModules": "",
        "SBIM.Project.ModuleDepths": "",
        "SBIM.Project.NormativePackVersion": "",
        "SBIM.Project.RouteVersion": "",
        "SBIM.Project.CoordinationStatus": "DRAFT",
        "SBIM.Project.CoordinatePolicy": "PROJECT_ORIGIN_WITH_SURVEY_POINT",
    }


def plan_summary(inventory=None):
    validation = validate_specs()
    layers = load_yaml(LAYER_SPEC)
    graphics = load_yaml(GRAPHICS_SPEC)
    targets = project_info_targets()
    result = {
        "validation": validation,
        "safeCore": {
            "projectInfoFields": list(targets),
            "layers": [x["name"] for x in layers.get("layers", [])],
            "layerCombinations": list((layers.get("layer_combinations") or {}).keys()),
            "penTables": [x["name"] for x in graphics.get("pen_tables", [])],
            "lineTypes": [x["name"] for x in graphics.get("line_types", [])],
        },
        "deferred": [
            "Fills: exact vector/symbol patterns still require visual audit.",
            "Surfaces: exact RGB/textures intentionally deferred.",
            "Building Materials: require resolved Fill and Surface attribute IDs.",
            "Composites: require verified project/product/system thicknesses.",
            "Properties/Classifications: availability mapping must be resolved first.",
            "Favorites: created after verified type elements exist.",
            "MVO/Graphic Override preset creation is not exposed by current Tapir schema.",
            "Save As .TPL to a new path is not exposed by current Tapir schema.",
        ],
    }
    if inventory is not None:
        result["live"] = {
            "project": inventory["project"],
            "elementCount": inventory["elementCount"],
            "existingAttributeCounts": {
                key: len(value) if isinstance(value, list) else None
                for key, value in inventory["attributes"].items()
            },
            "existingMVO": [x.get("name") for x in inventory["modelViewOptions"]],
        }
    return result


def create_project_info_fields(api: Tapir):
    existing = api.call("GetProjectInfoFields").get("fields", [])
    by_name = {x["projectInfoName"]: x for x in existing}
    missing = [
        {"projectInfoName": name, "projectInfoValue": value}
        for name, value in project_info_targets().items()
        if name not in by_name
    ]
    if missing:
        api.call("CreateProjectInfoFields", {"projectInfoFields": missing})
    after = api.call("GetProjectInfoFields").get("fields", [])
    return {
        "created": [x["projectInfoName"] for x in missing],
        "present": {
            x["projectInfoName"]: x["projectInfoValue"]
            for x in after if x["projectInfoName"] in project_info_targets()
        },
    }


def create_layers(api: Tapir):
    spec = load_yaml(LAYER_SPEC)
    payload = []
    for item in spec.get("layers", []):
        payload.append({
            "name": item["name"],
            "isHidden": False,
            "isLocked": bool(item.get("default_locked", False)),
            "isWireframe": False,
            "intersectionGroupNr": int(item["group"]),
        })
    result = api.call("CreateLayers", {
        "layerDataArray": payload,
        "overwriteExisting": True,
    })
    headers = attribute_headers(api, "Layer")
    by_name = index_headers(headers)
    missing = sorted(set(x["name"] for x in payload) - set(by_name))
    if missing:
        raise RuntimeError(f"Layers absent after CreateLayers: {missing}")
    return {"nativeResult": result, "count": len(payload)}


def pen_payload(table, semantic_pens):
    overrides = {int(k): float(v) for k, v in (table.get("width_overrides") or {}).items()}
    policy = table.get("color_policy", "")
    pens = []
    for raw_idx, spec in semantic_pens.items():
        idx = int(raw_idx)
        item = {
            "index": idx,
            "width": overrides.get(idx, float(spec["width_mm"])),
            "description": spec["name"],
        }
        if policy == "registered_pens_black":
            item["color"] = {"red": 0.0, "green": 0.0, "blue": 0.0}
        pens.append(item)
    return pens


def create_pen_tables(api: Tapir):
    spec = load_yaml(GRAPHICS_SPEC)
    current = attribute_headers(api, "PenTable")
    if not current:
        raise RuntimeError("No existing Pen Table is available as deterministic source.")
    source_id = {"attributeId": current[0]["attributeId"]}
    tables = []
    for table in spec.get("pen_tables", []):
        tables.append({
            "name": table["name"],
            "isActiveForModel": bool(table.get("active_for_model", False)),
            "isActiveForLayout": bool(table.get("active_for_layout", False)),
            "sourceAttributeId": source_id,
            "pens": pen_payload(table, spec.get("semantic_pens") or {}),
        })
    result = api.call("CreatePenTables", {
        "penTableDataArray": tables,
        "overwriteExisting": True,
    })
    after = index_headers(attribute_headers(api, "PenTable"))
    missing = sorted(set(x["name"] for x in tables) - set(after))
    if missing:
        raise RuntimeError(f"Pen Tables absent after create: {missing}")
    return {"nativeResult": result, "count": len(tables), "source": current[0]["name"]}


def create_line_types(api: Tapir):
    spec = load_yaml(GRAPHICS_SPEC)
    lines = []
    for item in spec.get("line_types", []):
        data = {
            "name": item["name"],
            "scaleWithPlan": bool(item.get("scale_with_plan", False)),
            "lineType": item["line_type"],
        }
        if item["line_type"] == "Dashed":
            data["period"] = float(item["period_mm"])
            data["dashItems"] = [
                {"dash": float(x["dash_mm"]), "gap": float(x["gap_mm"])}
                for x in item.get("dash_items", [])
            ]
        lines.append(data)
    result = api.call("CreateLines", {
        "lineDataArray": lines,
        "overwriteExisting": True,
    })
    after = index_headers(attribute_headers(api, "Line"))
    missing = sorted(set(x["name"] for x in lines) - set(after))
    if missing:
        raise RuntimeError(f"Line Types absent after create: {missing}")
    return {"nativeResult": result, "count": len(lines)}


def layer_visibility(combo, name):
    show = set(combo.get("show", []))
    hide = set(combo.get("hide", []))
    show_prefixes = tuple(combo.get("show_prefixes", []))
    hide_prefixes = tuple(combo.get("hide_prefixes", []))
    is_show = name in show or (show_prefixes and name.startswith(show_prefixes))
    is_hide = name in hide or (hide_prefixes and name.startswith(hide_prefixes))
    if is_show and is_hide:
        raise ValueError(f"Layer combination conflict for {name}: both show and hide")
    if is_show:
        return False
    if is_hide:
        return True
    return True


def get_full_layer_state(api: Tapir):
    headers = attribute_headers(api, "Layer")
    ids = [{"attributeId": x["attributeId"]} for x in headers]
    result = api.call("GetLayers", {"attributeIds": ids})
    rows = {}
    for row in result.get("layers", []):
        if "name" in row:
            rows[row["name"]] = row
    return headers, rows


def create_layer_combinations(api: Tapir):
    spec = load_yaml(LAYER_SPEC)
    registered = {x["name"]: x for x in spec.get("layers", [])}
    headers, current = get_full_layer_state(api)
    combos = []
    for combo_name, combo in (spec.get("layer_combinations") or {}).items():
        layer_rows = []
        for header in headers:
            name = header["name"]
            cur = current.get(name, {})
            if name in registered:
                reg = registered[name]
                hidden = layer_visibility(combo, name)
                locked = bool(reg.get("default_locked", False))
                group = int(reg["group"])
                wireframe = False
            else:
                # Unmanaged layers stay isolated in SBIM combinations.
                # Archicad Layer remains visible because Archicad may need it internally,
                # but production geometry is forbidden there by policy.
                hidden = name != "Archicad Layer"
                locked = bool(cur.get("isLocked", False))
                group = int(cur.get("intersectionGroupNr", 0))
                wireframe = bool(cur.get("isWireframe", False))
            layer_rows.append({
                "attributeId": header["attributeId"],
                "isHidden": hidden,
                "isLocked": locked,
                "isWireframe": wireframe,
                "intersectionGroupNr": group,
            })
        combos.append({"name": combo_name, "layers": layer_rows})
    result = api.call("CreateLayerCombinations", {
        "layerCombinationDataArray": combos,
        "overwriteExisting": True,
    })
    after = index_headers(attribute_headers(api, "LayerCombination"))
    missing = sorted(set(x["name"] for x in combos) - set(after))
    if missing:
        raise RuntimeError(f"Layer combinations absent after create: {missing}")
    return {"nativeResult": result, "count": len(combos)}


def apply_safe_core(api: Tapir, allow_nonempty=False):
    validation = validate_specs()
    if validation["status"] != "PASS":
        raise RuntimeError(f"Spec validation failed: {validation['errors']}")

    project = api.call("GetProjectInfo")
    elements = api.call("GetAllElements").get("elements", [])
    if elements and not allow_nonempty:
        raise RuntimeError(
            f"Refusing template-core write: current project contains {len(elements)} elements. "
            "Use a clean candidate project or pass --allow-nonempty explicitly."
        )

    outcome = {
        "projectBefore": project,
        "elementCountBefore": len(elements),
        "steps": {},
    }
    outcome["steps"]["projectInfo"] = create_project_info_fields(api)
    outcome["steps"]["layers"] = create_layers(api)
    outcome["steps"]["penTables"] = create_pen_tables(api)
    outcome["steps"]["lineTypes"] = create_line_types(api)
    outcome["steps"]["layerCombinations"] = create_layer_combinations(api)

    # Read-back inventory is the authoritative postcondition.
    after = live_inventory(api)
    outcome["postconditions"] = {
        "elementCountAfter": after["elementCount"],
        "geometryCountUnchanged": after["elementCount"] == len(elements),
        "attributeCounts": {
            key: len(value) if isinstance(value, list) else None
            for key, value in after["attributes"].items()
        },
        "projectInfoFields": {
            x["projectInfoName"]: x["projectInfoValue"]
            for x in after["projectInfoFields"]
            if x["projectInfoName"].startswith("SBIM.")
        },
    }
    if not outcome["postconditions"]["geometryCountUnchanged"]:
        raise RuntimeError(
            "Unexpected model element count change during safe-core build; inspect evidence."
        )
    return outcome


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("validate", "inspect", "plan", "apply-core"),
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument(
        "--allow-nonempty",
        action="store_true",
        help="Allow apply-core in a project that already contains model elements.",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional JSON result path.",
    )
    args = parser.parse_args()

    run_id = time.strftime("%Y%m%d-%H%M%S")
    evidence = EVIDENCE_ROOT / run_id

    if args.action == "validate":
        result = validate_specs()
    else:
        api = Tapir(args.port, evidence)
        if args.action == "inspect":
            result = live_inventory(api)
        elif args.action == "plan":
            result = plan_summary(live_inventory(api))
        elif args.action == "apply-core":
            result = apply_safe_core(api, allow_nonempty=args.allow_nonempty)
        else:
            raise AssertionError(args.action)

    if args.out:
        write_json(Path(args.out), result)
    if args.action != "inspect":
        write_json(evidence / "result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    status = result.get("status") if isinstance(result, dict) else None
    if status == "FAIL":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
