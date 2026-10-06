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
ATTRIBUTE_REGISTRY = SPEC / "attribute-registry-v0.1.yaml"
SURFACE_REGISTRY = SPEC / "surface-registry-v0.1.yaml"
FILL_REGISTRY = SPEC / "fill-registry-v0.1.yaml"
CLASSIFICATION_REGISTRY = SPEC / "classification-registry-v0.1.yaml"
DATA_SCHEMA = SPEC / "data-schema-v0.1.yaml"

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

    def native(self, command: str, parameters=None, timeout=120):
        """Call a built-in Graphisoft JSON command (not an Add-On command)."""
        self.seq += 1
        safe = command.replace(".", "-")
        stem = f"{self.seq:03d}-{safe}"
        request = {"command": command, "parameters": parameters or {}}
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
        result = envelope.get("result", {})
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



def get_fill_runtime_index(api: Tapir):
    """Map canonical fill roles/names to actual Fill headers without duplicating singleton fills."""
    registry = load_yaml(FILL_REGISTRY)
    headers = attribute_headers(api, "Fill")
    by_name = index_headers(headers)
    ids = [{"attributeId": h["attributeId"]} for h in headers]
    details_result = api.call(
        "GetFills",
        {"attributeIds": ids, "fields": ["subType", "useForWalls"]},
    )
    detail_by_name = {
        row["name"]: row for row in details_result.get("fills", [])
        if isinstance(row, dict) and "name" in row
    }

    resolved = {}
    diagnostics = []
    for item in registry.get("fills", []):
        canonical = item.get("canonical_role") or item.get("name")
        if item.get("creation") == "resolve_existing_singleton":
            subtype = item["required_subtype"]
            matches = [
                h for h in headers
                if detail_by_name.get(h["name"], {}).get("subType") == subtype
            ]
            if len(matches) == 1:
                resolved[canonical] = matches[0]
                diagnostics.append({
                    "canonical": canonical,
                    "state": "RESOLVED_SINGLETON",
                    "actualName": matches[0]["name"],
                    "index": matches[0]["index"],
                })
            else:
                diagnostics.append({
                    "canonical": canonical,
                    "state": "BLOCKED_SINGLETON_RESOLUTION",
                    "requiredSubtype": subtype,
                    "matches": [x["name"] for x in matches],
                })
        elif item.get("name") in by_name:
            resolved[canonical] = by_name[item["name"]]
            diagnostics.append({
                "canonical": canonical,
                "state": "RESOLVED_BY_NAME",
                "actualName": item["name"],
                "index": by_name[item["name"]]["index"],
            })
        else:
            diagnostics.append({
                "canonical": canonical,
                "state": "MISSING",
                "registryStatus": item.get("status"),
            })
    return resolved, diagnostics


def material_dependency_plan(api: Tapir):
    """Read-only resolution of Building Material dependencies by canonical role/name."""
    registry = load_yaml(ATTRIBUTE_REGISTRY)
    fill_map, fill_diagnostics = get_fill_runtime_index(api)
    surface_headers = attribute_headers(api, "Surface")
    bm_headers = attribute_headers(api, "BuildingMaterial")

    surfaces = index_headers(surface_headers)
    existing_bm = index_headers(bm_headers)

    materials = []
    ready = 0
    for item in registry.get("building_materials", []):
        fill_name = item.get("cut_fill")
        surface_name = item.get("surface")
        blockers = []
        if fill_name and fill_name not in fill_map:
            blockers.append({"type": "missing_or_unverified_fill", "name": fill_name})
        if surface_name and surface_name not in surfaces:
            blockers.append({"type": "missing_surface", "name": surface_name})

        state = "EXISTS" if item["name"] in existing_bm else (
            "READY_FOR_CREATE" if not blockers else "BLOCKED_DEPENDENCY"
        )
        if state == "READY_FOR_CREATE":
            ready += 1

        materials.append({
            "id": item.get("id"),
            "name": item["name"],
            "state": state,
            "draftPriority": item.get("draft_priority"),
            "collision": item.get("collision"),
            "cutFill": {
                "canonical": fill_name,
                "actualName": fill_map.get(fill_name, {}).get("name") if fill_name else None,
                "index": fill_map.get(fill_name, {}).get("index") if fill_name else None,
            },
            "surface": {
                "name": surface_name,
                "index": surfaces.get(surface_name, {}).get("index") if surface_name else None,
            },
            "blockers": blockers,
        })

    return {
        "status": "PASS",
        "writePerformed": False,
        "counts": {
            "materials": len(materials),
            "alreadyExisting": sum(x["state"] == "EXISTS" for x in materials),
            "readyForCreate": ready,
            "blockedDependency": sum(
                x["state"] == "BLOCKED_DEPENDENCY" for x in materials
            ),
            "surfaceAttributesPresent": len(surface_headers),
        },
        "fillResolution": fill_diagnostics,
        "missingSurfaces": sorted({
            x["surface"]["name"] for x in materials
            if x["surface"]["name"] and x["surface"]["index"] is None
        }),
        "materials": materials,
    }


def _require_clean_or_explicit(api: Tapir, allow_nonempty: bool, stage: str):
    elements = api.call("GetAllElements").get("elements", [])
    if elements and not allow_nonempty:
        raise RuntimeError(
            f"Refusing {stage}: current project contains {len(elements)} elements. "
            "Use a clean candidate project or pass --allow-nonempty explicitly."
        )
    return len(elements)


def apply_surfaces(api: Tapir, allow_nonempty=False):
    """Create/overwrite the deterministic texture-free visual Surface registry."""
    before_count = _require_clean_or_explicit(api, allow_nonempty, "surface write")
    registry = load_yaml(SURFACE_REGISTRY)
    defaults = registry.get("render_defaults", {})
    payload = []
    for item in registry.get("surfaces", []):
        material_type = item["material_type"]
        preset = defaults.get(material_type, {})
        r, g, b = [float(x) for x in item["color"]]
        payload.append({
            "name": item["name"],
            "materialType": material_type,
            "ambientReflection": float(preset.get("ambient_reflection", 50)),
            "diffuseReflection": float(preset.get("diffuse_reflection", 70)),
            "specularReflection": float(preset.get("specular_reflection", 10)),
            "transparency": float(item.get("transparency", 0)),
            "shine": float(preset.get("shine", 0)),
            "surfaceColor": {"red": r, "green": g, "blue": b},
        })

    native = api.call("CreateSurfaces", {
        "surfaceDataArray": payload,
        "overwriteExisting": True,
    })
    headers = index_headers(attribute_headers(api, "Surface"))
    missing = sorted(set(x["name"] for x in payload) - set(headers))
    if missing:
        raise RuntimeError(f"Surfaces absent after CreateSurfaces: {missing}")

    ids = [{"attributeId": headers[x["name"]]["attributeId"]} for x in payload]
    details = api.call("GetSurfaces", {
        "attributeIds": ids,
        "fields": ["materialType", "transparency", "surfaceColor", "texture"],
    }).get("surfaces", [])
    by_name = {x["name"]: x for x in details if isinstance(x, dict) and "name" in x}
    mismatches = []
    for expected in payload:
        actual = by_name.get(expected["name"])
        if not actual:
            mismatches.append({"name": expected["name"], "reason": "no_readback"})
            continue
        color = actual.get("surfaceColor", {})
        for key, exp in expected["surfaceColor"].items():
            if not math.isclose(float(color.get(key, -1)), exp, abs_tol=1e-6):
                mismatches.append({
                    "name": expected["name"],
                    "reason": f"surfaceColor.{key}",
                    "expected": exp,
                    "actual": color.get(key),
                })
        if not math.isclose(
            float(actual.get("transparency", -1)),
            float(expected["transparency"]),
            abs_tol=1e-6,
        ):
            mismatches.append({
                "name": expected["name"],
                "reason": "transparency",
                "expected": expected["transparency"],
                "actual": actual.get("transparency"),
            })

    after_count = len(api.call("GetAllElements").get("elements", []))
    if after_count != before_count:
        raise RuntimeError("Unexpected model element count change during surface stage.")
    if mismatches:
        raise RuntimeError(f"Surface read-back mismatch: {mismatches[:10]}")
    return {
        "status": "PASS",
        "createdOrOverwritten": len(payload),
        "elementCountUnchanged": True,
        "nativeResult": native,
    }


def apply_ready_building_materials(api: Tapir, allow_nonempty=False):
    """Create only materials whose Fill and Surface dependencies resolve in the live project."""
    before_count = _require_clean_or_explicit(api, allow_nonempty, "Building Material write")
    registry = load_yaml(ATTRIBUTE_REGISTRY)
    plan = material_dependency_plan(api)
    plan_by_name = {x["name"]: x for x in plan["materials"]}
    source_by_name = {x["name"]: x for x in registry.get("building_materials", [])}

    payload = []
    for name, resolved in plan_by_name.items():
        if resolved["state"] != "READY_FOR_CREATE":
            continue
        source = source_by_name[name]
        payload.append({
            "name": name,
            "id": source.get("id", ""),
            "description": (
                "SBIM candidate material. Physical properties intentionally undefined "
                "until a verified source is attached."
            ),
            "connPriority": int(source["draft_priority"]),
            "cutFillIndex": int(resolved["cutFill"]["index"]),
            "cutFillPen": 17,
            "cutFillBackgroundPen": 0,
            "cutSurfaceIndex": int(resolved["surface"]["index"]),
            "showUncutLines": True,
            "collisionDetection": bool(source.get("collision", True)),
            "cutFillOrientation": "ProjectOrigin",
        })

    if not payload:
        return {
            "status": "PASS",
            "createdOrOverwritten": 0,
            "reason": "No READY_FOR_CREATE materials; dependencies remain blocked.",
            "plan": plan,
        }

    native = api.call("CreateBuildingMaterials", {
        "buildingMaterialDataArray": payload,
        "overwriteExisting": True,
    })
    headers = index_headers(attribute_headers(api, "BuildingMaterial"))
    missing = sorted(set(x["name"] for x in payload) - set(headers))
    if missing:
        raise RuntimeError(f"Building Materials absent after create: {missing}")

    ids = [{"attributeId": headers[x["name"]]["attributeId"]} for x in payload]
    details = api.call("GetBuildingMaterials", {
        "attributeIds": ids,
        "fields": [
            "id", "description", "connPriority", "cutFillIndex",
            "cutFillPen", "cutFillBackgroundPen", "cutSurfaceIndex",
            "cutFillOrientation", "collisionDetection",
        ],
    }).get("buildingMaterials", [])
    by_name = {x["name"]: x for x in details if isinstance(x, dict) and "name" in x}
    mismatches = []
    for expected in payload:
        actual = by_name.get(expected["name"])
        if not actual:
            mismatches.append({"name": expected["name"], "reason": "no_readback"})
            continue
        for field in (
            "id", "connPriority", "cutFillIndex", "cutFillPen",
            "cutFillBackgroundPen", "cutSurfaceIndex",
            "cutFillOrientation", "collisionDetection",
        ):
            if actual.get(field) != expected.get(field):
                mismatches.append({
                    "name": expected["name"], "reason": field,
                    "expected": expected.get(field), "actual": actual.get(field),
                })

    after_count = len(api.call("GetAllElements").get("elements", []))
    if after_count != before_count:
        raise RuntimeError(
            "Unexpected model element count change during Building Material stage."
        )
    if mismatches:
        raise RuntimeError(f"Building Material read-back mismatch: {mismatches[:10]}")
    return {
        "status": "PASS",
        "createdOrOverwritten": len(payload),
        "elementCountUnchanged": True,
        "nativeResult": native,
        "stillBlocked": [
            x for x in plan["materials"] if x["state"] == "BLOCKED_DEPENDENCY"
        ],
    }



def _flatten_classification_items(items, out):
    for wrapper in items or []:
        item = wrapper.get("classificationItem", wrapper)
        if not isinstance(item, dict):
            continue
        item_id = item.get("id")
        guid = item.get("classificationItemId", {}).get("guid")
        if item_id and guid:
            out[item_id] = {
                "guid": guid,
                "name": item.get("name"),
                "description": item.get("description", ""),
            }
        _flatten_classification_items(item.get("children", []), out)


def get_sbim_classification_state(api: Tapir):
    registry = load_yaml(CLASSIFICATION_REGISTRY)
    target = registry["system"]
    systems = api.native("API.GetAllClassificationSystems", {}).get(
        "classificationSystems", []
    )
    matches = [x for x in systems if x.get("name") == target["name"]]
    if len(matches) > 1:
        raise RuntimeError(
            f"Multiple Classification Systems named {target['name']!r}; manual repair required."
        )
    if not matches:
        return {
            "exists": False,
            "system": None,
            "items": {},
            "missingItemIds": [x["id"] for x in registry.get("items", [])],
        }
    system = matches[0]
    result = api.native(
        "API.GetAllClassificationsInSystem",
        {"classificationSystemId": system["classificationSystemId"]},
    )
    items = {}
    _flatten_classification_items(result.get("classificationItems", []), items)
    expected = [x["id"] for x in registry.get("items", [])]
    return {
        "exists": True,
        "system": system,
        "items": items,
        "missingItemIds": [x for x in expected if x not in items],
    }


def ensure_sbim_classification(api: Tapir):
    registry = load_yaml(CLASSIFICATION_REGISTRY)
    state = get_sbim_classification_state(api)
    if not state["exists"]:
        system = registry["system"]
        api.call("CreateClassificationSystems", {
            "classificationSystemsWithItems": [{
                "classificationSystem": {
                    "name": system["name"],
                    "description": system["description"],
                    "source": system["source"],
                    "version": system["version"],
                    "date": system["date"],
                },
                "classificationItems": [
                    {
                        "id": item["id"],
                        "name": item["name"],
                        "description": item["description"],
                    }
                    for item in registry.get("items", [])
                ],
            }]
        })
        state = get_sbim_classification_state(api)

    if state["missingItemIds"]:
        raise RuntimeError(
            "Existing SBIM Semantic classification is incomplete; "
            f"missing IDs: {state['missingItemIds']}. "
            "Failing closed instead of mutating a partially used classification tree."
        )
    return state


def property_availability_map(class_state):
    registry = load_yaml(CLASSIFICATION_REGISTRY)
    all_items = class_state["items"]
    mapping = {}
    for group_name, spec in (
        registry.get("property_group_availability") or {}
    ).items():
        ids = spec.get("items")
        selected = list(all_items) if ids == "ALL" else list(ids or [])
        missing = [x for x in selected if x not in all_items]
        if missing:
            raise RuntimeError(
                f"{group_name} availability references missing classifications: {missing}"
            )
        mapping[group_name] = [
            {"classificationItemId": {"guid": all_items[x]["guid"]}}
            for x in selected
        ]
    return mapping


def plan_data_schema(api: Tapir):
    class_state = get_sbim_classification_state(api)
    schema = load_yaml(DATA_SCHEMA)
    existing = api.call("GetAllProperties").get("properties", [])
    existing_key = {
        (p.get("propertyGroupName"), p.get("propertyName")): p
        for p in existing
    }
    groups = schema.get("property_groups", {})
    return {
        "status": "PASS",
        "writePerformed": False,
        "classification": {
            "exists": class_state["exists"],
            "missingItemIds": class_state["missingItemIds"],
            "resolvedItems": len(class_state["items"]),
        },
        "propertyGroups": {
            name: {
                "properties": len(props),
                "existingProperties": sum(
                    (name, prop_name) in existing_key for prop_name in props
                ),
            }
            for name, props in groups.items()
        },
        "totalSchemaProperties": sum(len(x) for x in groups.values()),
        "existingSchemaProperties": sum(
            (group_name, prop_name) in existing_key
            for group_name, props in groups.items()
            for prop_name in props
        ),
    }


def _property_definition_payload(group_name, prop_name, spec, availability):
    ptype = spec["type"]
    type_map = {
        "string": "string",
        "boolean": "boolean",
        "integer": "integer",
        "length": "length",
        "number": "number",
        "enum": "singleEnum",
    }
    if ptype not in type_map:
        raise RuntimeError(
            f"Unsupported property type in v0.1 builder: {group_name}.{prop_name} -> {ptype}"
        )
    out = {
        "name": prop_name,
        "description": f"SBIM schema property {group_name}.{prop_name}",
        "type": type_map[ptype],
        "isEditable": True,
        "availability": availability,
        "group": {"name": group_name},
    }
    if ptype == "enum":
        out["possibleEnumValues"] = [
            {
                "enumValue": {
                    "displayValue": str(value),
                    "nonLocalizedValue": str(value),
                }
            }
            for value in spec.get("values", [])
        ]
    # Deliberately omit defaultValue in schema v0.1.
    # Defaults such as NOT_CHECKED are applied by Favorites/agent, not asserted globally.
    return {"propertyDefinition": out}


def apply_data_schema(api: Tapir, allow_nonempty=False):
    """Create SBIM Semantic classification plus scoped Property Groups/Definitions."""
    before_count = _require_clean_or_explicit(api, allow_nonempty, "data schema write")
    class_state = ensure_sbim_classification(api)
    availability = property_availability_map(class_state)
    schema = load_yaml(DATA_SCHEMA)
    groups = schema.get("property_groups", {})

    existing_props = api.call("GetAllProperties").get("properties", [])
    existing_key = {
        (p.get("propertyGroupName"), p.get("propertyName")): p
        for p in existing_props
    }
    existing_group_names = {
        p.get("propertyGroupName") for p in existing_props
        if p.get("propertyGroupName")
    }

    group_payload = [
        {"propertyGroup": {
            "name": group_name,
            "description": f"SBIM managed property group {group_name}",
        }}
        for group_name in groups
        if group_name not in existing_group_names
    ]
    group_result = None
    if group_payload:
        group_result = api.call(
            "CreatePropertyGroups", {"propertyGroups": group_payload}
        )

    create_defs = []
    for group_name, props in groups.items():
        if group_name not in availability:
            raise RuntimeError(
                f"No classification availability declared for property group {group_name}"
            )
        for prop_name, spec in props.items():
            if (group_name, prop_name) in existing_key:
                continue
            create_defs.append(
                _property_definition_payload(
                    group_name, prop_name, spec, availability[group_name]
                )
            )

    property_result = None
    if create_defs:
        property_result = api.call(
            "CreatePropertyDefinitions",
            {"propertyDefinitions": create_defs},
        )

    after_props = api.call("GetAllProperties").get("properties", [])
    after_key = {
        (p.get("propertyGroupName"), p.get("propertyName")): p
        for p in after_props
    }
    missing = [
        f"{group_name}.{prop_name}"
        for group_name, props in groups.items()
        for prop_name in props
        if (group_name, prop_name) not in after_key
    ]
    if missing:
        raise RuntimeError(
            f"SBIM property definitions missing after create: {missing}"
        )

    after_count = len(api.call("GetAllElements").get("elements", []))
    if after_count != before_count:
        raise RuntimeError("Unexpected model element count change during data-schema stage.")

    return {
        "status": "PASS",
        "classificationSystem": class_state["system"].get("name"),
        "classificationItems": len(class_state["items"]),
        "propertyGroupsRequested": len(groups),
        "propertyDefinitionsCreated": len(create_defs),
        "totalSchemaPropertiesPresent": sum(len(x) for x in groups.values()),
        "elementCountUnchanged": True,
        "nativeGroupResult": group_result,
        "nativePropertyResult": property_result,
    }



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("validate", "inspect", "plan", "plan-materials", "plan-data-schema", "apply-core", "apply-surfaces", "apply-ready-materials", "apply-data-schema"),
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
        elif args.action == "plan-materials":
            result = material_dependency_plan(api)
        elif args.action == "plan-data-schema":
            result = plan_data_schema(api)
        elif args.action == "apply-core":
            result = apply_safe_core(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-surfaces":
            result = apply_surfaces(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-ready-materials":
            result = apply_ready_building_materials(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-data-schema":
            result = apply_data_schema(api, allow_nonempty=args.allow_nonempty)
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
