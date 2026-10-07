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
NAVIGATOR_REGISTRY = SPEC / "navigator-registry-v0.1.yaml"
DOCUMENTATION_SPEC = SPEC / "documentation-standard-v0.1.yaml"
FONT_MANIFEST = SPEC / "fonts-manifest.yaml"
SEED_PRESETS = SPEC / "seed-presets-registry-v0.1.yaml"
MASTER_LAYOUT_FORM3 = SPEC / "master-layout-form3-registry-v0.1.yaml"
FORM3_GEOMETRY = SPEC / "form3-geometry-v0.1.yaml"
MASTER_COORD_CALIBRATION = SPEC / "master-layout-coordinate-calibration-v0.1.yaml"
AUTOTEXT_REGISTRY = SPEC / "autotext-titleblock-registry-v0.1.yaml"
DWG_TRANSLATOR_REGISTRY = SPEC / "dwg-translator-registry-v0.1.yaml"
IFC_TRANSLATOR_REGISTRY = SPEC / "ifc-translator-registry-v0.1.yaml"

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
    attributes = load_yaml(ATTRIBUTE_REGISTRY)
    surfaces_registry = load_yaml(SURFACE_REGISTRY)
    fills_registry = load_yaml(FILL_REGISTRY)
    classifications = load_yaml(CLASSIFICATION_REGISTRY)
    data_schema = load_yaml(DATA_SCHEMA)
    navigator = load_yaml(NAVIGATOR_REGISTRY)
    documentation = load_yaml(DOCUMENTATION_SPEC)
    seed_presets = load_yaml(SEED_PRESETS)
    form3 = load_yaml(MASTER_LAYOUT_FORM3)
    form3_geometry = load_yaml(FORM3_GEOMETRY)
    autotext_registry = load_yaml(AUTOTEXT_REGISTRY)
    dwg_registry = load_yaml(DWG_TRANSLATOR_REGISTRY)
    ifc_registry = load_yaml(IFC_TRANSLATOR_REGISTRY)

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

    # Cross-registry integrity: Surface names must match the attribute registry exactly.
    attr_surface_names = [x["name"] for x in attributes.get("surfaces", [])]
    surface_defs = surfaces_registry.get("surfaces", [])
    surface_names = [x["name"] for x in surface_defs]
    if len(surface_names) != len(set(surface_names)):
        errors.append("Duplicate Surface names in surface-registry-v0.1.yaml.")
    missing_surface_defs = sorted(set(attr_surface_names) - set(surface_names))
    extra_surface_defs = sorted(set(surface_names) - set(attr_surface_names))
    if missing_surface_defs:
        errors.append(
            f"Surface registry missing Attribute Registry names: {missing_surface_defs}"
        )
    if extra_surface_defs:
        warnings.append(
            f"Surface registry contains extra visual surfaces: {extra_surface_defs}"
        )
    for item in surface_defs:
        color = item.get("color", [])
        if len(color) != 3 or any(float(v) < 0 or float(v) > 1 for v in color):
            errors.append(f"{item.get('name')}: RGB values must be three numbers in 0..1")
        transparency = float(item.get("transparency", 0))
        if transparency < 0 or transparency > 100:
            errors.append(
                f"{item.get('name')}: transparency outside 0..100: {transparency}"
            )

    # Fill canonical roles/names are the only allowed Building Material cut-fill refs.
    fill_entries = fills_registry.get("fills", [])
    fill_keys = [
        x.get("canonical_role") or x.get("name")
        for x in fill_entries
    ]
    if len(fill_keys) != len(set(fill_keys)):
        errors.append("Duplicate canonical Fill role/name in fill registry.")
    allowed_fill_status = {
        "runtime_resolve", "live_calibration_required",
        "blocked_visual_source", "candidate", "verified",
    }
    for item in fill_entries:
        if item.get("status") not in allowed_fill_status:
            errors.append(
                f"{item.get('canonical_role') or item.get('name')}: "
                f"unknown Fill status {item.get('status')!r}"
            )

    bm_items = attributes.get("building_materials", [])
    bm_names = [x["name"] for x in bm_items]
    bm_ids = [x.get("id") for x in bm_items]
    if len(bm_names) != len(set(bm_names)):
        errors.append("Duplicate Building Material names.")
    if len(bm_ids) != len(set(bm_ids)):
        errors.append("Duplicate Building Material stable IDs.")
    for item in bm_items:
        if item.get("cut_fill") not in fill_keys:
            errors.append(
                f"{item['name']}: unknown cut_fill {item.get('cut_fill')}"
            )
        if item.get("surface") not in surface_names:
            errors.append(
                f"{item['name']}: unknown Surface {item.get('surface')}"
            )
        priority = int(item.get("draft_priority", -1))
        if priority < 0 or priority > 999:
            errors.append(
                f"{item['name']}: intersection priority outside 0..999: {priority}"
            )

    # Classification and Property-group availability must remain one coherent schema.
    class_items = classifications.get("items", [])
    class_ids = [x["id"] for x in class_items]
    if len(class_ids) != len(set(class_ids)):
        errors.append("Duplicate SBIM Semantic classification item IDs.")
    availability = classifications.get("property_group_availability") or {}
    schema_groups = data_schema.get("property_groups") or {}
    if set(availability) != set(schema_groups):
        errors.append(
            "Classification property-group availability and data-schema groups differ: "
            f"availability={sorted(availability)}, schema={sorted(schema_groups)}"
        )
    for group_name, rule in availability.items():
        selected = rule.get("items")
        if selected != "ALL":
            unknown = sorted(set(selected or []) - set(class_ids))
            if unknown:
                errors.append(
                    f"{group_name}: availability references unknown classification IDs {unknown}"
                )

    # Navigator blueprint references must resolve to registered template names.
    view_folders = navigator.get("view_folders", [])
    if len(view_folders) != len(set(view_folders)):
        errors.append("Duplicate View Map folder names.")
    nav_views = navigator.get("views", [])
    view_names = [x["name"] for x in nav_views]
    if len(view_names) != len(set(view_names)):
        errors.append("Duplicate navigator View names.")
    registered_layer_combos = set((layers.get("layer_combinations") or {}).keys())
    registered_pen_tables = {x["name"] for x in graphics.get("pen_tables", [])}
    external = navigator.get("external_seed_dependencies") or {}
    registered_mvo = set(external.get("model_view_options", []))
    registered_go = set(external.get("graphic_override_combinations", []))
    registered_dims = set(external.get("dimension_styles", []))
    allowed_structure = {"EntireStructure", "CoreOnly", "WithoutFinishes", "StructureOnly"}
    allowed_scales = set(baseline.get("scales", []))
    for view in nav_views:
        if view.get("folder") not in view_folders:
            errors.append(f"{view['name']}: unknown View Map folder {view.get('folder')}")
        if view.get("layer_combination") not in registered_layer_combos:
            errors.append(
                f"{view['name']}: unknown Layer Combination {view.get('layer_combination')}"
            )
        if view.get("pen_table") not in registered_pen_tables:
            errors.append(f"{view['name']}: unknown Pen Table {view.get('pen_table')}")
        if view.get("mvo") not in registered_mvo:
            errors.append(f"{view['name']}: undeclared MVO dependency {view.get('mvo')}")
        if view.get("graphic_override") not in registered_go:
            errors.append(
                f"{view['name']}: undeclared Graphic Override dependency "
                f"{view.get('graphic_override')}"
            )
        if view.get("dimension_style") not in registered_dims:
            errors.append(
                f"{view['name']}: undeclared Dimension Style dependency "
                f"{view.get('dimension_style')}"
            )
        if view.get("structure_display") not in allowed_structure:
            errors.append(
                f"{view['name']}: invalid structure display {view.get('structure_display')}"
            )
        if int(view.get("scale", -1)) not in allowed_scales:
            errors.append(f"{view['name']}: scale {view.get('scale')} absent from baseline")

    masters = navigator.get("master_layout_blueprints", [])
    master_names = [x["name"] for x in masters]
    if len(master_names) != len(set(master_names)):
        errors.append("Duplicate Master Layout blueprint names.")
    for master in masters:
        if float(master.get("width_mm", 0)) <= 0 or float(master.get("height_mm", 0)) <= 0:
            errors.append(f"{master.get('name')}: invalid sheet size")

    # Master Layout sheet sizes must match the verified Form 3 / format registry.
    form3_sizes = form3.get("sheet_formats_mm") or {}
    for master in masters:
        expected = form3_sizes.get(master["name"])
        actual = [master.get("width_mm"), master.get("height_mm")]
        if expected is None:
            errors.append(
                f"{master['name']}: missing from master-layout Form 3 sheet registry"
            )
        elif [float(x) for x in expected] != [float(x) for x in actual]:
            errors.append(
                f"{master['name']}: Navigator size {actual} differs from Form 3 registry {expected}"
            )
    extra_form3_sizes = sorted(set(form3_sizes) - set(master_names))
    if extra_form3_sizes:
        warnings.append(
            f"Form 3 registry contains unused sheet formats: {extra_form3_sizes}"
        )
    if [float(form3.get("form3", {}).get("width_mm", 0)),
        float(form3.get("form3", {}).get("height_mm", 0))] != [185.0, 55.0]:
        errors.append("Form 3 canonical titleblock size must remain 185x55 mm.")

    core_geo = form3_geometry.get("core") or {}
    if [float(core_geo.get("width_mm", 0)),
        float(core_geo.get("height_mm", 0))] != [185.0, 55.0]:
        errors.append(
            "Form 3 geometry contract must use the canonical 185x55 mm core."
        )

    x_breaks = [float(x) for x in core_geo.get("x_breaks_mm", [])]
    y_breaks = [float(y) for y in core_geo.get("y_breaks_mm", [])]
    if (
        x_breaks != sorted(set(x_breaks))
        or x_breaks[:1] != [0.0]
        or x_breaks[-1:] != [185.0]
    ):
        errors.append(
            f"Form 3 x_breaks_mm must be unique/sorted from 0 to 185: {x_breaks}"
        )
    if (
        y_breaks != sorted(set(y_breaks))
        or y_breaks[:1] != [0.0]
        or y_breaks[-1:] != [55.0]
    ):
        errors.append(
            f"Form 3 y_breaks_mm must be unique/sorted from 0 to 55: {y_breaks}"
        )

    seen_segments = set()
    for i, seg in enumerate(form3_geometry.get("line_segments_mm", [])):
        if not isinstance(seg, list) or len(seg) != 4:
            errors.append(
                f"Form 3 line segment {i} must contain four coordinates: {seg}"
            )
            continue
        x0, y0, x1, y1 = [float(v) for v in seg]
        if not (
            0 <= x0 <= 185 and 0 <= x1 <= 185
            and 0 <= y0 <= 55 and 0 <= y1 <= 55
        ):
            errors.append(
                f"Form 3 line segment {i} escapes 185x55 core: {seg}"
            )
        if not (math.isclose(x0, x1) or math.isclose(y0, y1)):
            errors.append(
                f"Form 3 line segment {i} must be orthogonal: {seg}"
            )
        if math.isclose(x0, x1) and math.isclose(y0, y1):
            errors.append(
                f"Form 3 line segment {i} has zero length: {seg}"
            )
        canonical = (
            min(x0, x1), min(y0, y1),
            max(x0, x1), max(y0, y1),
        )
        if canonical in seen_segments:
            errors.append(f"Duplicate Form 3 line segment: {seg}")
        seen_segments.add(canonical)

    for cell_name, cell in (form3_geometry.get("cells") or {}).items():
        x0, y0, x1, y1 = [
            float(cell[k]) for k in ("x0", "y0", "x1", "y1")
        ]
        if not (x0 < x1 and y0 < y1):
            errors.append(
                f"{cell_name}: invalid Form 3 cell bounds {cell}"
            )
        if x0 not in x_breaks or x1 not in x_breaks:
            errors.append(
                f"{cell_name}: x bounds do not align with Form 3 break lines"
            )
        if y0 not in y_breaks or y1 not in y_breaks:
            errors.append(
                f"{cell_name}: y bounds do not align with Form 3 break lines"
            )

    left_columns = [
        float(x)
        for x in form3.get("form3", {}).get("left_columns_mm", [])
    ]
    if not math.isclose(
        sum(left_columns),
        float(core_geo.get("left_block_width_mm", -1)),
        abs_tol=1e-9,
    ):
        errors.append(
            "Form 3 left block width must equal 10+10+10+10+15+10=65 mm."
        )

    right_widths = form3.get("form3", {}).get("right_major_widths_mm") or {}
    right_sum = (
        float(right_widths.get("main_text", 0))
        + float(right_widths.get("auxiliary", 0))
    )
    if not math.isclose(
        right_sum,
        float(core_geo.get("right_block_width_mm", -1)),
        abs_tol=1e-9,
    ):
        errors.append(
            "Form 3 right block width must equal 70+50=120 mm."
        )

    if bool(
        (form3_geometry.get("optional_graph_27") or {})
        .get("draw_by_default")
    ):
        errors.append(
            "Graph 27 is conditional and must not be drawn by default."
        )

    nav_subsets = [x["name"] for x in navigator.get("layout_subsets", [])]
    doc_subsets = documentation.get("layout_subsets", [])
    if nav_subsets != doc_subsets:
        errors.append(
            "Navigator Layout subsets differ from documentation-standard ordering/names."
        )
    doc_masters = documentation.get("masters", [])
    if master_names != doc_masters:
        errors.append(
            "Navigator Master Layout blueprints differ from documentation-standard."
        )
    nav_pub = {x["name"] for x in navigator.get("publisher_blueprints", [])}
    doc_pub = set((documentation.get("publisher_sets") or {}).keys())
    if not nav_pub.issubset(doc_pub):
        errors.append(
            f"Navigator Publisher blueprints not declared in documentation-standard: "
            f"{sorted(nav_pub - doc_pub)}"
        )

    # Manual seed registry must exactly satisfy Navigator external preset dependencies.
    seed_mvo = {x["name"] for x in seed_presets.get("model_view_options", [])}
    seed_go = {x["name"] for x in seed_presets.get("graphic_override_combinations", [])}
    seed_dims = {x["name"] for x in seed_presets.get("dimension_styles", [])}
    if seed_mvo != registered_mvo:
        errors.append(
            "Seed MVO names differ from Navigator dependencies: "
            f"seed={sorted(seed_mvo)}, navigator={sorted(registered_mvo)}"
        )
    if seed_go != registered_go:
        errors.append(
            "Seed Graphic Override Combination names differ from Navigator dependencies: "
            f"seed={sorted(seed_go)}, navigator={sorted(registered_go)}"
        )
    if seed_dims != registered_dims:
        errors.append(
            "Seed Dimension Style names differ from Navigator dependencies: "
            f"seed={sorted(seed_dims)}, navigator={sorted(registered_dims)}"
        )

    # AutoText registry must use unique verified builtin keys and valid <KEY> tokens.
    builtin_keys = autotext_registry.get("verified_builtin_keys") or {}
    runtime_auto = (
        autotext_registry.get("runtime_validation") or {}
    ).get("required_builtin_keys_for_first_titleblock_test", [])
    missing_runtime_keys = sorted(set(runtime_auto) - set(builtin_keys))
    if missing_runtime_keys:
        errors.append(
            f"AutoText runtime validation references unknown builtin keys: {missing_runtime_keys}"
        )
    for graph_no, mapping in (autotext_registry.get("form3_mapping") or {}).items():
        key = mapping.get("key")
        token = mapping.get("token")
        if key and key not in builtin_keys:
            errors.append(f"Form 3 graph {graph_no}: unknown AutoText key {key}")
        if key and token != f"<{key}>":
            errors.append(
                f"Form 3 graph {graph_no}: token {token!r} must equal <{key}>"
            )
    expected_format_values = (
        (autotext_registry.get("form3_mapping") or {})
        .get(26, {})
        .get("values_by_master", {})
    )
    if set(expected_format_values) != set(form3_sizes):
        errors.append(
            "Form 3 graph 26 master-format mapping must cover exactly all registered masters."
        )

    # Publisher DWG/IFC translators must resolve to exchange-registry contracts.
    dwg_translators = {
        x["name"] for x in dwg_registry.get("translators", [])
    }
    ifc_translators = {
        x["name"] for x in ifc_registry.get("translators", [])
    }
    for pub in navigator.get("publisher_blueprints", []):
        translator = pub.get("translator")
        fmt = str(pub.get("format", "")).upper()
        if not translator:
            continue
        if fmt == "DWG" and translator not in dwg_translators:
            errors.append(
                f"{pub['name']}: DWG translator {translator!r} absent from DWG registry"
            )
        elif fmt == "IFC" and translator not in ifc_translators:
            errors.append(
                f"{pub['name']}: IFC translator {translator!r} absent from IFC registry"
            )
        elif fmt not in {"DWG", "IFC"}:
            warnings.append(
                f"{pub['name']}: translator {translator!r} declared for unexpected format {fmt!r}"
            )

    if "DWG_IN_REFERENCE" not in dwg_translators:
        errors.append("DWG translator registry must contain DWG_IN_REFERENCE.")
    if "IFC_REFERENCE_IMPORT" not in ifc_translators:
        errors.append("IFC translator registry must contain IFC_REFERENCE_IMPORT.")

    supported_property_types = {"string", "boolean", "integer", "length", "number", "enum"}
    property_count = 0
    for group_name, props in schema_groups.items():
        for prop_name, spec in props.items():
            property_count += 1
            if spec.get("type") not in supported_property_types:
                errors.append(
                    f"{group_name}.{prop_name}: unsupported schema property type "
                    f"{spec.get('type')!r}"
                )
            if spec.get("type") == "enum" and not spec.get("values"):
                errors.append(f"{group_name}.{prop_name}: enum has no values")

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
            "surfaces": len(surface_defs),
            "fillRoles": len(fill_entries),
            "buildingMaterials": len(bm_items),
            "classificationItems": len(class_items),
            "schemaProperties": property_count,
            "viewBlueprints": len(nav_views),
            "masterLayoutBlueprints": len(masters),
            "layoutSubsets": len(nav_subsets),
            "publisherBlueprints": len(nav_pub),
            "seedMVO": len(seed_mvo),
            "seedGraphicOverrideCombinations": len(seed_go),
            "seedDimensionStyles": len(seed_dims),
            "form3SheetFormats": len(form3_sizes),
            "verifiedAutoTextKeys": len(builtin_keys),
            "runtimeRequiredAutoTextKeys": len(runtime_auto),
            "dwgTranslatorContracts": len(dwg_translators),
            "ifcTranslatorContracts": len(ifc_translators),
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



def _collect_navigator_items(item, out=None):
    if out is None:
        out = []
    for child in (item or {}).get("children", []):
        nav = child.get("navigatorItem", {})
        if nav:
            out.append(nav)
            _collect_navigator_items(nav, out)
    return out


def plan_navigator(api: Tapir):
    """Read-only check of View/Layout prerequisites against the live Archicad project."""
    registry = load_yaml(NAVIGATOR_REGISTRY)
    existing_mvo = {
        x.get("name")
        for x in api.call("GetModelViewOptions").get("modelViewOptions", [])
        if x.get("name")
    }
    layer_combos = {
        x["name"] for x in attribute_headers(api, "LayerCombination")
    }
    pen_tables = {
        x["name"] for x in attribute_headers(api, "PenTable")
    }

    view_tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "PublicViewMap"}
    ).get("navigatorItemTree", {})
    layout_tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "LayoutBook"}
    ).get("navigatorItemTree", {})
    publisher_tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "PublisherSets"}
    ).get("navigatorItemTree", {})

    view_items = _collect_navigator_items(view_tree)
    layout_items = _collect_navigator_items(layout_tree)
    publisher_items = _collect_navigator_items(publisher_tree)

    existing_view_names = {x.get("name") for x in view_items if x.get("name")}
    existing_folder_names = {
        x.get("name") for x in view_items
        if x.get("type") == "FolderItem" and x.get("name")
    }
    existing_master_names = {
        x.get("name") for x in layout_items
        if x.get("type") == "MasterLayoutItem" and x.get("name")
    }
    existing_subset_names = {
        x.get("name") for x in layout_items
        if x.get("type") == "SubsetItem" and x.get("name")
    }
    existing_publisher_names = {
        x.get("name") for x in publisher_items if x.get("name")
    }

    deps = registry.get("external_seed_dependencies") or {}
    required_mvo = set(deps.get("model_view_options", []))
    required_go = set(deps.get("graphic_override_combinations", []))
    required_dims = set(deps.get("dimension_styles", []))

    view_plan = []
    for view in registry.get("views", []):
        blockers = []
        for kind, value, existing in (
            ("layer_combination", view["layer_combination"], layer_combos),
            ("pen_table", view["pen_table"], pen_tables),
            ("mvo", view["mvo"], existing_mvo),
        ):
            if value not in existing:
                blockers.append({"type": f"missing_{kind}", "name": value})

        # Tapir 1.5.8 exposes assignment of these names in ViewSettings but not
        # an enumeration/creation command for the preset registries themselves.
        blockers.append({
            "type": "unverified_graphic_override_seed",
            "name": view["graphic_override"],
            "declared": view["graphic_override"] in required_go,
        })
        blockers.append({
            "type": "unverified_dimension_style_seed",
            "name": view["dimension_style"],
            "declared": view["dimension_style"] in required_dims,
        })

        view_plan.append({
            "name": view["name"],
            "exists": view["name"] in existing_view_names,
            "folderExists": view["folder"] in existing_folder_names,
            "blockers": blockers,
            "state": "EXISTS" if view["name"] in existing_view_names else (
                "BLOCKED_SEED_PRESETS" if blockers else "READY_FOR_CREATE"
            ),
        })

    return {
        "status": "PASS",
        "writePerformed": False,
        "counts": {
            "existingMVO": len(existing_mvo),
            "requiredMVO": len(required_mvo),
            "missingMVO": len(required_mvo - existing_mvo),
            "existingViewItems": len(view_items),
            "plannedViews": len(view_plan),
            "existingMasterLayouts": len(existing_master_names),
            "plannedMasterLayouts": len(registry.get("master_layout_blueprints", [])),
            "existingLayoutSubsets": len(existing_subset_names),
            "plannedLayoutSubsets": len(registry.get("layout_subsets", [])),
            "existingPublisherItems": len(existing_publisher_names),
        },
        "missingMVO": sorted(required_mvo - existing_mvo),
        "unverifiableByTapir15": {
            "graphicOverrideCombinations": sorted(required_go),
            "dimensionStyles": sorted(required_dims),
        },
        "masterLayouts": [
            {
                "name": x["name"],
                "exists": x["name"] in existing_master_names,
                "status": x["status"],
            }
            for x in registry.get("master_layout_blueprints", [])
        ],
        "layoutSubsets": [
            {
                "name": x["name"],
                "exists": x["name"] in existing_subset_names,
            }
            for x in registry.get("layout_subsets", [])
        ],
        "publisherBlueprints": [
            {
                "name": x["name"],
                "exists": x["name"] in existing_publisher_names,
                "status": x["status"],
            }
            for x in registry.get("publisher_blueprints", [])
        ],
        "views": view_plan,
    }





def _layoutbook_items(api: Tapir):
    tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "LayoutBook"}
    ).get("navigatorItemTree", {})
    return _collect_navigator_items(tree)


def _layout_db_id_from_nav(api: Tapir, nav_item):
    result = api.call(
        "GetDatabaseIdFromNavigatorItemId",
        {"navigatorItemIds": [{"navigatorItemId": nav_item["navigatorItemId"]}]},
    )
    rows = result.get("databases", [])
    if len(rows) != 1 or "databaseId" not in rows[0]:
        raise RuntimeError(
            f"Could not resolve database for navigator item "
            f"{nav_item.get('name')}: {result}"
        )
    return rows[0]["databaseId"]


def _layout_settings_from_nav(api: Tapir, nav_item):
    db_id = _layout_db_id_from_nav(api, nav_item)
    result = api.call(
        "GetLayoutSettings",
        {"layoutDatabaseIds": [{"databaseId": db_id}]},
    )
    rows = result.get("layoutSettings", [])
    if len(rows) != 1:
        raise RuntimeError(
            f"Could not read layout settings for {nav_item.get('name')}: {result}"
        )
    return db_id, rows[0]





def plan_master_coordinate_calibration():
    """Offline plan for proving Master Layout paper-space orientation."""
    spec = load_yaml(MASTER_COORD_CALIBRATION)
    return {
        "status": "BLOCKED_LIVE_VISUAL_CALIBRATION",
        "writePerformed": False,
        "purpose": spec.get("purpose"),
        "confirmedApiFacts": spec.get("confirmed_api_facts"),
        "candidateConventionToTest": spec.get("candidate_convention_to_test"),
        "calibrationArtifacts": spec.get("calibration_artifacts"),
        "releaseGate": spec.get("release_gate"),
        "placementAfterConfirmation": spec.get("placement_after_confirmation"),
    }

def plan_form3_geometry():
    """Offline deterministic plan for the verified Form 3 core grid."""
    spec = load_yaml(FORM3_GEOMETRY)
    segments = spec.get("line_segments_mm", [])
    labels = spec.get("static_labels", [])
    return {
        "status": "PASS",
        "writePerformed": False,
        "coordinateSystem": spec.get("coordinate_system"),
        "core": spec.get("core"),
        "segmentCount": len(segments),
        "segmentsMm": segments,
        "staticLabelCount": len(labels),
        "staticLabels": labels,
        "optionalGraph27": spec.get("optional_graph_27"),
        "additionalLeftBlock": spec.get("additional_left_block"),
        "graph26": spec.get("graph_26"),
        "releaseGate": spec.get("release_gate"),
    }

def plan_autotext(api: Tapir):
    """Read-only validation of the custom AutoText reader and Form 3 keys."""
    registry = load_yaml(AUTOTEXT_REGISTRY)
    required = (
        registry.get("runtime_validation") or {}
    ).get("required_builtin_keys_for_first_titleblock_test", [])

    try:
        response = api.call("GetAutoTextsV1")
    except Exception as exc:
        return {
            "status": "BLOCKED_ADDON_REBUILD",
            "writePerformed": False,
            "reason": (
                "GetAutoTextsV1 is provided by the safe-bim overlay and is not "
                "available until the overlay add-on is rebuilt and loaded."
            ),
            "error": str(exc),
            "requiredKeys": required,
        }

    rows = response.get("autoTexts", [])
    by_key = {
        str(x.get("key", "")).strip("<>"): x
        for x in rows if x.get("key")
    }
    missing = [key for key in required if key not in by_key]
    return {
        "status": "PASS" if not missing else "BLOCKED_AUTOTEXT_KEYS",
        "writePerformed": False,
        "count": len(rows),
        "requiredKeys": required,
        "missingRequiredKeys": missing,
        "resolvedRequired": {
            key: by_key.get(key) for key in required if key in by_key
        },
        "allAutoTexts": rows,
        "embeddingSyntax": "<KEY>",
        "nextGate": (
            "master_layout_autotext_embedding_test"
            if not missing else "inspect_archicad_autotext_environment"
        ),
    }


def plan_master_layouts(api: Tapir):
    """Read-only plan for exact A4-A0 Master Layout shells."""
    registry = load_yaml(MASTER_LAYOUT_FORM3)
    expected = registry.get("sheet_formats_mm") or {}
    items = _layoutbook_items(api)
    masters = {
        x.get("name"): x
        for x in items
        if x.get("type") == "MasterLayoutItem" and x.get("name")
    }
    layouts = {
        x.get("name"): x
        for x in items
        if x.get("type") == "LayoutItem" and x.get("name")
    }

    plan = []
    for name, dims in expected.items():
        width, height = [float(x) for x in dims]
        temp_name = f"__SBIM_MASTER_SEED_{name}"
        row = {
            "name": name,
            "expectedSizeMm": [width, height],
            "tempSeedLayoutName": temp_name,
            "tempSeedLayoutAlreadyExists": temp_name in layouts,
        }
        existing = masters.get(name)
        if existing is None:
            row["state"] = (
                "BLOCKED_RESIDUAL_TEMP_LAYOUT"
                if temp_name in layouts else "READY_FOR_CREATE"
            )
        else:
            db_id, settings = _layout_settings_from_nav(api, existing)
            actual = [
                float(settings.get("horizontalSize", -1)),
                float(settings.get("verticalSize", -1)),
            ]
            row["databaseId"] = db_id
            row["actualSizeMm"] = actual
            row["sizeMatches"] = all(
                math.isclose(a, b, abs_tol=0.1)
                for a, b in zip(actual, [width, height])
            )
            row["state"] = "EXISTS_OK" if row["sizeMatches"] else "BLOCKED_SIZE_MISMATCH"
        plan.append(row)

    return {
        "status": "PASS",
        "writePerformed": False,
        "units": "mm",
        "source": "Graphisoft API_LayoutInfo",
        "counts": {
            "expectedMasters": len(expected),
            "existingOk": sum(x["state"] == "EXISTS_OK" for x in plan),
            "readyForCreate": sum(x["state"] == "READY_FOR_CREATE" for x in plan),
            "blocked": sum(x["state"].startswith("BLOCKED_") for x in plan),
        },
        "masters": plan,
        "geometryDeferred": True,
        "autotextDeferred": True,
    }


def apply_master_layout_shell(api: Tapir, allow_nonempty=False):
    """Create exact-size empty Master Layout shells, without titleblock geometry.

    Missing masters are created through a temporary seed Layout because the
    current Tapir command creates a Master Layout as part of CreateLayout.
    The Master size is then set/read back in millimeters and the temporary
    Layout is deleted. Existing same-name masters are never resized silently.
    """
    validation = validate_specs()
    if validation["status"] != "PASS":
        raise RuntimeError(f"Spec validation failed: {validation['errors']}")

    before_count = len(api.call("GetAllElements").get("elements", []))
    if before_count and not allow_nonempty:
        raise RuntimeError(
            f"Refusing Master Layout shell write: current project contains "
            f"{before_count} model elements. Use a clean candidate project or "
            f"pass --allow-nonempty explicitly."
        )

    initial_plan = plan_master_layouts(api)
    blocked = [
        x for x in initial_plan["masters"]
        if x["state"].startswith("BLOCKED_")
    ]
    if blocked:
        raise RuntimeError(
            "Master Layout shell preflight blocked. Existing same-name masters "
            "are not modified automatically and residual seed layouts are not "
            f"deleted automatically: {blocked}"
        )

    created = []
    registry = load_yaml(MASTER_LAYOUT_FORM3)
    expected = registry.get("sheet_formats_mm") or {}

    for name, dims in expected.items():
        current_plan = plan_master_layouts(api)
        row = next(x for x in current_plan["masters"] if x["name"] == name)
        if row["state"] == "EXISTS_OK":
            continue
        if row["state"] != "READY_FOR_CREATE":
            raise RuntimeError(f"{name}: unexpected state before create: {row}")

        width, height = [float(x) for x in dims]
        temp_name = f"__SBIM_MASTER_SEED_{name}"

        create_result = api.call(
            "CreateLayout",
            {
                "layoutsData": [{
                    "masterLayoutName": name,
                    "layoutName": temp_name,
                    "layoutParameters": {
                        "horizontalSize": width,
                        "verticalSize": height,
                        "doNotIncludeInNumbering": True,
                    },
                }]
            },
        )
        if not create_result.get("databases"):
            raise RuntimeError(f"{name}: CreateLayout returned no database: {create_result}")

        items = _layoutbook_items(api)
        master = next(
            (x for x in items if x.get("type") == "MasterLayoutItem"
             and x.get("name") == name),
            None,
        )
        temp_layout = next(
            (x for x in items if x.get("type") == "LayoutItem"
             and x.get("name") == temp_name),
            None,
        )
        if master is None or temp_layout is None:
            raise RuntimeError(
                f"{name}: Master or temporary Layout missing after CreateLayout."
            )

        master_db, before_settings = _layout_settings_from_nav(api, master)
        set_result = api.call(
            "SetLayoutSettings",
            {
                "layoutsData": [{
                    "layoutDatabaseId": master_db,
                    "horizontalSize": width,
                    "verticalSize": height,
                }]
            },
        )
        exec_rows = set_result.get("executionResults", [])
        if len(exec_rows) != 1 or not exec_rows[0].get("success"):
            raise RuntimeError(
                f"{name}: failed to set Master Layout size: {set_result}"
            )

        _, after_settings = _layout_settings_from_nav(api, master)
        actual = [
            float(after_settings.get("horizontalSize", -1)),
            float(after_settings.get("verticalSize", -1)),
        ]
        if not all(
            math.isclose(a, b, abs_tol=0.1)
            for a, b in zip(actual, [width, height])
        ):
            raise RuntimeError(
                f"{name}: Master Layout size read-back mismatch: "
                f"expected={[width, height]}, actual={actual}"
            )

        delete_result = api.call(
            "DeleteNavigatorItems",
            {"navigatorItemIds": [{
                "navigatorItemId": temp_layout["navigatorItemId"]
            }]},
        )
        delete_rows = delete_result.get("executionResults", [])
        if len(delete_rows) != 1 or not delete_rows[0].get("success"):
            raise RuntimeError(
                f"{name}: Master created, but temporary Layout cleanup failed: "
                f"{delete_result}"
            )

        created.append({
            "name": name,
            "sizeMm": actual,
            "masterSettingsBeforeSizeCorrection": {
                "horizontalSize": before_settings.get("horizontalSize"),
                "verticalSize": before_settings.get("verticalSize"),
            },
        })

    final_plan = plan_master_layouts(api)
    final_bad = [
        x for x in final_plan["masters"]
        if x["state"] != "EXISTS_OK"
    ]
    if final_bad:
        raise RuntimeError(f"Master Layout final read-back failed: {final_bad}")

    after_count = len(api.call("GetAllElements").get("elements", []))
    if after_count != before_count:
        raise RuntimeError(
            "Unexpected model element count change during Master Layout shell stage."
        )

    residual_items = _layoutbook_items(api)
    residual_seed = [
        x.get("name") for x in residual_items
        if x.get("type") == "LayoutItem"
        and str(x.get("name", "")).startswith("__SBIM_MASTER_SEED_")
    ]
    if residual_seed:
        raise RuntimeError(
            f"Residual temporary Master seed Layouts remain: {residual_seed}"
        )

    return {
        "status": "PASS",
        "writePerformed": bool(created),
        "createdMasters": created,
        "allMasters": final_plan["masters"],
        "modelElementCountUnchanged": True,
        "titleblockGeometryCreated": False,
        "autotextCreated": False,
        "nextGate": "live_masterlayout_window_line_text_test",
    }




def apply_master_coordinate_calibration(api: Tapir, allow_nonempty=False):
    """Interactively prove the A4_P Master Layout paper-space convention.

    Both candidate coordinate hypotheses are drawn at once. The command waits
    for an explicit H1/H2/ABORT answer while the marks are visible in Archicad,
    then deletes every sacrificial Line/Text in a finally cleanup path.
    """
    validation = validate_specs()
    if validation["status"] != "PASS":
        raise RuntimeError(f"Spec validation failed: {validation['errors']}")

    before_count = len(api.call("GetAllElements").get("elements", []))
    if before_count and not allow_nonempty:
        raise RuntimeError(
            f"Refusing Master coordinate calibration: current project contains "
            f"{before_count} model elements. Use a clean candidate project or "
            f"pass --allow-nonempty explicitly."
        )

    master_plan = plan_master_layouts(api)
    row = next((x for x in master_plan["masters"] if x["name"] == "A4_P"), None)
    if row is None or row.get("state") != "EXISTS_OK":
        return {
            "status": "BLOCKED_MASTER_LAYOUT",
            "writePerformed": False,
            "reason": "A4_P must exist with the exact registered size first.",
            "master": row,
        }

    items = _layoutbook_items(api)
    master = next(
        (
            x for x in items
            if x.get("type") == "MasterLayoutItem" and x.get("name") == "A4_P"
        ),
        None,
    )
    if master is None:
        raise RuntimeError("A4_P navigator item disappeared after preflight.")

    change = api.call("ChangeWindow", {"navigatorItemId": master["navigatorItemId"]})
    if not change.get("success", False):
        raise RuntimeError(f"Could not activate A4_P Master Layout: {change}")

    current = api.call("GetCurrentWindowType").get("currentWindowType")
    if current != "MasterLayout":
        raise RuntimeError(
            f"A4_P activation did not produce MasterLayout window: {current}"
        )

    created_ids = []
    answer = None
    cleanup_result = None

    def add_cross_and_label(x, y, label):
        arm = 0.004
        line_result = api.call(
            "CreateLineElements",
            {
                "linesData": [
                    {
                        "begCoordinate": {"x": x - arm, "y": y},
                        "endCoordinate": {"x": x + arm, "y": y},
                        "roomSeparator": False,
                    },
                    {
                        "begCoordinate": {"x": x, "y": y - arm},
                        "endCoordinate": {"x": x, "y": y + arm},
                        "roomSeparator": False,
                    },
                ]
            },
        )
        rows = line_result.get("elements", [])
        if len(rows) != 2 or any("elementId" not in r for r in rows):
            raise RuntimeError(
                f"Calibration cross creation failed for {label}: {line_result}"
            )
        created_ids.extend(r["elementId"] for r in rows)

        text_result = api.call(
            "CreateTexts",
            {
                "textsData": [{
                    "coordinate": {"x": x + 0.005, "y": y + 0.005, "z": 0.0},
                    "text": label,
                    "height": 2.5,
                    "justification": "Left",
                }]
            },
        )
        text_rows = text_result.get("elements", [])
        if len(text_rows) != 1 or "elementId" not in text_rows[0]:
            raise RuntimeError(
                f"Calibration label creation failed for {label}: {text_result}"
            )
        created_ids.append(text_rows[0]["elementId"])

    hypotheses = {
        "H1": {
            "description": "bottom-left origin; +X right; +Y up",
            "marks": [
                (0.010, 0.010, "H1 BL"),
                (0.200, 0.010, "H1 BR"),
                (0.010, 0.287, "H1 TL"),
                (0.200, 0.287, "H1 TR"),
            ],
        },
        "H2": {
            "description": "top-left origin; +X right; -Y down",
            "marks": [
                (0.010, -0.010, "H2 TL"),
                (0.200, -0.010, "H2 TR"),
                (0.010, -0.287, "H2 BL"),
                (0.200, -0.287, "H2 BR"),
            ],
        },
    }

    try:
        for hypothesis in hypotheses.values():
            for x, y, label in hypothesis["marks"]:
                add_cross_and_label(x, y, label)

        print("")
        print("MASTER LAYOUT COORDINATE CALIBRATION")
        print("Inspect A4_P in Archicad now.")
        print("H1 = bottom-left origin, +X right, +Y up")
        print("H2 = top-left origin, +X right, -Y down")
        print("ABORT = no convention is confirmed")
        while True:
            answer = input("Visible convention [H1/H2/ABORT]: ").strip().upper()
            if answer in {"H1", "H2", "ABORT"}:
                break
            print("Enter exactly H1, H2, or ABORT.")
    finally:
        if created_ids:
            cleanup_result = api.call(
                "DeleteElements",
                {
                    "elements": [
                        {"elementId": element_id}
                        for element_id in created_ids
                    ]
                },
            )
            if not cleanup_result.get("success", False):
                raise RuntimeError(
                    "Coordinate calibration marks were created but cleanup failed: "
                    f"{cleanup_result}"
                )

    after_count = len(api.call("GetAllElements").get("elements", []))
    if after_count != before_count:
        raise RuntimeError(
            "Unexpected model element count change during coordinate calibration."
        )

    if answer == "ABORT":
        return {
            "status": "BLOCKED_LIVE_VISUAL_CALIBRATION",
            "writePerformed": True,
            "confirmedConvention": None,
            "cleanup": {
                "success": True,
                "deletedCount": len(created_ids),
                "modelElementCountUnchanged": True,
            },
        }

    selected = hypotheses[answer]
    return {
        "status": "PASS",
        "writePerformed": True,
        "confirmedConvention": answer,
        "description": selected["description"],
        "masterLayout": "A4_P",
        "cleanup": {
            "success": True,
            "deletedCount": len(created_ids),
            "result": cleanup_result,
            "modelElementCountUnchanged": True,
        },
        "nextGate": "persist_coordinate_convention_then_apply_form3_core_geometry",
    }

def apply_master_layout_smoke(api: Tapir, allow_nonempty=False):
    """Create/read-back/delete a sacrificial Line + Text + AutoText-token Text.

    This gate proves Master Layout targeting, element creation, GUID read-back
    and cleanup. It does not claim rendered AutoText expansion is proven.
    """
    validation = validate_specs()
    if validation["status"] != "PASS":
        raise RuntimeError(f"Spec validation failed: {validation['errors']}")

    autotext = plan_autotext(api)
    if autotext.get("status") != "PASS":
        return {
            "status": autotext.get("status", "BLOCKED_AUTOTEXT"),
            "writePerformed": False,
            "reason": "Master Layout smoke requires a passing AutoText registry gate.",
            "autotextGate": autotext,
        }

    master_plan = plan_master_layouts(api)
    row = next((x for x in master_plan["masters"] if x["name"] == "A4_P"), None)
    if row is None or row.get("state") != "EXISTS_OK":
        return {
            "status": "BLOCKED_MASTER_LAYOUT",
            "writePerformed": False,
            "reason": "A4_P must exist with the exact registered size first.",
            "master": row,
        }

    items = _layoutbook_items(api)
    master = next(
        (
            x for x in items
            if x.get("type") == "MasterLayoutItem" and x.get("name") == "A4_P"
        ),
        None,
    )
    if master is None:
        raise RuntimeError("A4_P navigator item disappeared after preflight.")

    master_db = _layout_db_id_from_nav(api, master)
    change = api.call("ChangeWindow", {"navigatorItemId": master["navigatorItemId"]})
    if not change.get("success", False):
        raise RuntimeError(f"Could not activate A4_P Master Layout: {change}")

    current = api.call("GetCurrentWindowType").get("currentWindowType")
    if current != "MasterLayout":
        raise RuntimeError(
            f"A4_P activation did not produce MasterLayout window: {current}"
        )

    try:
        api.call("GetCurrent2DDocumentV1")
    except Exception as exc:
        return {
            "status": "BLOCKED_ADDON_REBUILD",
            "writePerformed": False,
            "reason": (
                "GetCurrent2DDocumentV1 is required for exact Line/Text/AutoText "
                "read-back and is available after rebuilding/loading the overlay."
            ),
            "error": str(exc),
        }

    created_ids = []
    cleanup_result = None
    return_result = None
    try:
        line_result = api.call(
            "CreateLineElements",
            {
                "linesData": [{
                    "begCoordinate": {"x": 0.020, "y": 0.020},
                    "endCoordinate": {"x": 0.060, "y": 0.020},
                    "roomSeparator": False,
                }]
            },
        )
        line_rows = line_result.get("elements", [])
        if len(line_rows) != 1 or "elementId" not in line_rows[0]:
            raise RuntimeError(f"Line smoke creation failed: {line_result}")
        line_id = line_rows[0]["elementId"]
        created_ids.append(line_id)

        text_result = api.call(
            "CreateTexts",
            {
                "textsData": [{
                    "coordinate": {"x": 0.020, "y": 0.030, "z": 0.0},
                    "text": "__SBIM_MASTER_TEXT_SMOKE__",
                    "height": 2.5,
                    "justification": "Left",
                }]
            },
        )
        text_rows = text_result.get("elements", [])
        if len(text_rows) != 1 or "elementId" not in text_rows[0]:
            raise RuntimeError(f"Text smoke creation failed: {text_result}")
        text_id = text_rows[0]["elementId"]
        created_ids.append(text_id)

        auto_result = api.call(
            "CreateTexts",
            {
                "textsData": [{
                    "coordinate": {"x": 0.020, "y": 0.040, "z": 0.0},
                    "text": "<BUILDING_NAME>",
                    "height": 2.5,
                    "justification": "Left",
                }]
            },
        )
        auto_rows = auto_result.get("elements", [])
        if len(auto_rows) != 1 or "elementId" not in auto_rows[0]:
            raise RuntimeError(f"AutoText-token smoke creation failed: {auto_result}")
        auto_id = auto_rows[0]["elementId"]
        created_ids.append(auto_id)

        line_query = api.call(
            "GetElementsByType",
            {"elementType": "Line", "databases": [{"databaseId": master_db}]},
        )
        text_query = api.call(
            "GetElementsByType",
            {"elementType": "Text", "databases": [{"databaseId": master_db}]},
        )

        def collect_guids(result):
            found = set()
            for result_row in result.get("elements", []):
                for element in result_row.get("elements", []):
                    guid = (element.get("elementId") or {}).get("guid")
                    if guid:
                        found.add(guid)
            return found

        line_guids = collect_guids(line_query)
        text_guids = collect_guids(text_query)
        expected_line_guid = line_id.get("guid")
        expected_text_guids = {text_id.get("guid"), auto_id.get("guid")}

        if expected_line_guid not in line_guids:
            raise RuntimeError(
                f"Created smoke Line not found in A4_P read-back: {line_query}"
            )
        if not expected_text_guids.issubset(text_guids):
            raise RuntimeError(
                f"Created smoke Texts not found in A4_P read-back: {text_query}"
            )

        details = api.call(
            "GetDetailsOfElements",
            {
                "elements": [
                    {"elementId": line_id},
                    {"elementId": text_id},
                    {"elementId": auto_id},
                ]
            },
        )

        native_2d = api.call("GetCurrent2DDocumentV1")
        native_lines = {
            x.get("guid"): x for x in native_2d.get("lines", []) if x.get("guid")
        }
        native_texts = {
            x.get("guid"): x for x in native_2d.get("texts", []) if x.get("guid")
        }
        line_read = native_lines.get(line_id.get("guid"))
        text_read = native_texts.get(text_id.get("guid"))
        auto_read = native_texts.get(auto_id.get("guid"))
        if line_read is None or text_read is None or auto_read is None:
            raise RuntimeError(
                "Native 2D reader could not find all sacrificial elements: "
                f"line={line_read is not None}, text={text_read is not None}, "
                f"auto={auto_read is not None}"
            )

        def coord_matches(actual, expected):
            return (
                actual is not None
                and math.isclose(float(actual.get("x", 999)), expected[0], abs_tol=1e-6)
                and math.isclose(float(actual.get("y", 999)), expected[1], abs_tol=1e-6)
            )

        if not coord_matches(line_read.get("begCoordinate"), (0.020, 0.020)):
            raise RuntimeError(f"Line begin coordinate mismatch: {line_read}")
        if not coord_matches(line_read.get("endCoordinate"), (0.060, 0.020)):
            raise RuntimeError(f"Line end coordinate mismatch: {line_read}")
        if not coord_matches(text_read.get("position"), (0.020, 0.030)):
            raise RuntimeError(f"Static Text coordinate mismatch: {text_read}")
        if not coord_matches(auto_read.get("position"), (0.020, 0.040)):
            raise RuntimeError(f"AutoText coordinate mismatch: {auto_read}")
        if not math.isclose(float(text_read.get("heightMm", -1)), 2.5, abs_tol=0.01):
            raise RuntimeError(f"Static Text height mismatch: {text_read}")
        if not math.isclose(float(auto_read.get("heightMm", -1)), 2.5, abs_tol=0.01):
            raise RuntimeError(f"AutoText height mismatch: {auto_read}")
        if text_read.get("rawText") != "__SBIM_MASTER_TEXT_SMOKE__":
            raise RuntimeError(f"Static Text raw content mismatch: {text_read}")
        if text_read.get("interpretedText") != "__SBIM_MASTER_TEXT_SMOKE__":
            raise RuntimeError(f"Static Text interpreted content mismatch: {text_read}")
        if auto_read.get("rawText") != "<BUILDING_NAME>":
            raise RuntimeError(f"AutoText raw token mismatch: {auto_read}")

        expected_building_name = (
            autotext.get("resolvedRequired", {})
            .get("BUILDING_NAME", {})
            .get("value")
        )
        if expected_building_name is None:
            raise RuntimeError(
                "BUILDING_NAME passed registry presence but returned no value."
            )
        if auto_read.get("interpretedText") != expected_building_name:
            raise RuntimeError(
                "AutoText interpreted value mismatch: "
                f"expected={expected_building_name!r}, actual={auto_read.get('interpretedText')!r}"
            )

        return_result = {
            "status": "PASS",
            "writePerformed": True,
            "masterLayout": "A4_P",
            "masterDatabaseId": master_db,
            "windowType": current,
            "coordinateUnit": "m",
            "textHeightUnit": "mm",
            "created": {
                "line": line_id,
                "text": text_id,
                "autoTextTokenText": auto_id,
            },
            "readBack": {
                "lineGuidPresent": True,
                "textGuidsPresent": True,
                "details": details.get("detailsOfElements", []),
            },
            "geometryIntent": {
                "lineMm": [[20.0, 20.0], [60.0, 20.0]],
                "staticTextAnchorMm": [20.0, 30.0],
                "autoTextAnchorMm": [20.0, 40.0],
                "textHeightMm": 2.5,
            },
            "autoTextToken": "<BUILDING_NAME>",
            "renderedAutoTextExpansionVerified": True,
            "exact2DReadBackVerified": True,
            "layoutScopedAutoTextVerified": False,
            "native2DReadBack": {
                "line": line_read,
                "staticText": text_read,
                "autoText": auto_read,
            },
            "nextGate": "layout_scoped_autotext_context_test",
        }
    finally:
        if created_ids:
            cleanup_result = api.call(
                "DeleteElements",
                {
                    "elements": [
                        {"elementId": element_id}
                        for element_id in created_ids
                    ]
                },
            )
            if not cleanup_result.get("success", False):
                raise RuntimeError(
                    "Sacrificial Master Layout elements were created but cleanup "
                    f"failed: {cleanup_result}"
                )

    return_result["cleanup"] = {
        "success": True,
        "deletedCount": len(created_ids),
        "result": cleanup_result,
    }
    return return_result


def apply_layout_autotext_smoke(api: Tapir, allow_nonempty=False):
    """Verify layout-scoped AutoText on a disposable Layout and subset.

    Creates one temporary subset and one temporary Layout based on A4_P,
    activates that Layout, creates three AutoText Text elements, validates
    their raw/interpreted content through GetCurrent2DDocumentV1, then removes
    the Text elements, Layout and subset. Residual same-name smoke items block
    instead of being deleted silently.
    """
    validation = validate_specs()
    if validation["status"] != "PASS":
        raise RuntimeError(f"Spec validation failed: {validation['errors']}")

    before_count = len(api.call("GetAllElements").get("elements", []))
    if before_count and not allow_nonempty:
        raise RuntimeError(
            f"Refusing Layout AutoText smoke: current project contains "
            f"{before_count} model elements. Use a clean candidate project or "
            f"pass --allow-nonempty explicitly."
        )

    try:
        api.call("GetCurrent2DDocumentV1")
    except Exception as exc:
        return {
            "status": "BLOCKED_ADDON_REBUILD",
            "writePerformed": False,
            "reason": (
                "GetCurrent2DDocumentV1 is required for interpreted layout-scoped "
                "AutoText read-back."
            ),
            "error": str(exc),
        }

    master_plan = plan_master_layouts(api)
    master_row = next(
        (x for x in master_plan["masters"] if x["name"] == "A4_P"),
        None,
    )
    if master_row is None or master_row.get("state") != "EXISTS_OK":
        return {
            "status": "BLOCKED_MASTER_LAYOUT",
            "writePerformed": False,
            "reason": "A4_P must exist with the exact registered size first.",
            "master": master_row,
        }

    subset_name = "__SBIM_AUTOTEXT_SMOKE_SUBSET__"
    layout_name = "__SBIM_AUTOTEXT_SMOKE_LAYOUT__"

    initial_items = _layoutbook_items(api)
    residual = [
        x for x in initial_items
        if x.get("name") in {subset_name, layout_name}
    ]
    if residual:
        return {
            "status": "BLOCKED_RESIDUAL_SMOKE_ITEMS",
            "writePerformed": False,
            "reason": (
                "Residual sacrificial Layout/subset found. They are not deleted "
                "automatically because their origin cannot be proven."
            ),
            "items": residual,
        }

    master = next(
        (
            x for x in initial_items
            if x.get("type") == "MasterLayoutItem" and x.get("name") == "A4_P"
        ),
        None,
    )
    if master is None:
        raise RuntimeError("A4_P navigator item disappeared after preflight.")

    created_text_ids = []
    created_layout_nav = None
    created_subset_nav = None
    cleanup_errors = []
    return_result = None

    try:
        subset_result = api.call(
            "CreateLayoutSubset",
            {
                "subsetsData": [{
                    "name": subset_name,
                    "ownPrefix": "AT-",
                    "numberingStyle": "01",
                    "startAt": 1,
                    "continueNumbering": False,
                    "useUpperPrefix": False,
                    "includeToIDSequence": True,
                    "customNumbering": False,
                    "addOwnPrefix": True,
                }]
            },
        )
        subset_rows = subset_result.get("navigatorItems", [])
        if len(subset_rows) != 1 or "navigatorItemId" not in subset_rows[0]:
            raise RuntimeError(
                f"Could not create sacrificial Layout subset: {subset_result}"
            )
        created_subset_nav = subset_rows[0]["navigatorItemId"]

        create_layout = api.call(
            "CreateLayout",
            {
                "layoutsData": [{
                    "masterNavigatorItemId": master["navigatorItemId"],
                    "layoutName": layout_name,
                    "parentNavigatorItemId": created_subset_nav,
                    "layoutParameters": {
                        "doNotIncludeInNumbering": False,
                        "displayMasterLayoutBelow": True,
                    },
                }]
            },
        )
        if not create_layout.get("databases"):
            raise RuntimeError(
                f"Could not create sacrificial Layout: {create_layout}"
            )

        items = _layoutbook_items(api)
        layout = next(
            (
                x for x in items
                if x.get("type") == "LayoutItem" and x.get("name") == layout_name
            ),
            None,
        )
        if layout is None:
            raise RuntimeError("Sacrificial Layout missing after CreateLayout.")
        created_layout_nav = layout["navigatorItemId"]
        layout_db = _layout_db_id_from_nav(api, layout)

        change = api.call("ChangeWindow", {"navigatorItemId": created_layout_nav})
        if not change.get("success", False):
            raise RuntimeError(
                f"Could not activate sacrificial Layout: {change}"
            )
        current = api.call("GetCurrentWindowType").get("currentWindowType")
        if current != "Layout":
            raise RuntimeError(
                f"Sacrificial Layout activation did not produce Layout window: {current}"
            )

        auto_context = api.call("GetAutoTextsV1")
        context_rows = {
            str(x.get("key", "")).strip("<>"): x
            for x in auto_context.get("autoTexts", [])
            if x.get("key")
        }
        required = [
            "LAYOUTNAME",
            "LAYOUTNUMBERINCURRENTSUBSET",
            "NUMBEROFLAYOUTSINCURRENTSUBSET",
        ]
        missing = [key for key in required if key not in context_rows]
        if missing:
            raise RuntimeError(
                f"Layout context is missing required AutoText keys: {missing}"
            )

        expected_name = context_rows["LAYOUTNAME"].get("value")
        expected_number = context_rows["LAYOUTNUMBERINCURRENTSUBSET"].get("value")
        expected_count = context_rows["NUMBEROFLAYOUTSINCURRENTSUBSET"].get("value")

        if expected_name != layout_name:
            raise RuntimeError(
                "LAYOUTNAME context mismatch: "
                f"expected={layout_name!r}, actual={expected_name!r}"
            )
        if not str(expected_number or "").strip():
            raise RuntimeError(
                "LAYOUTNUMBERINCURRENTSUBSET resolved to an empty value."
            )
        try:
            parsed_count = int(str(expected_count).strip())
        except (TypeError, ValueError):
            raise RuntimeError(
                "NUMBEROFLAYOUTSINCURRENTSUBSET is not an integer: "
                f"{expected_count!r}"
            )
        if parsed_count != 1:
            raise RuntimeError(
                "Sacrificial subset should contain exactly one Layout, but "
                f"AutoText reports {expected_count!r}."
            )

        token_specs = [
            ("LAYOUTNAME", 0.020),
            ("LAYOUTNUMBERINCURRENTSUBSET", 0.030),
            ("NUMBEROFLAYOUTSINCURRENTSUBSET", 0.040),
        ]
        created_by_key = {}
        for key, y in token_specs:
            result = api.call(
                "CreateTexts",
                {
                    "textsData": [{
                        "coordinate": {"x": 0.020, "y": y, "z": 0.0},
                        "text": f"<{key}>",
                        "height": 2.5,
                        "justification": "Left",
                    }]
                },
            )
            rows = result.get("elements", [])
            if len(rows) != 1 or "elementId" not in rows[0]:
                raise RuntimeError(
                    f"Could not create {key} AutoText smoke Text: {result}"
                )
            element_id = rows[0]["elementId"]
            created_text_ids.append(element_id)
            created_by_key[key] = element_id

        native_2d = api.call("GetCurrent2DDocumentV1")
        texts = {
            x.get("guid"): x for x in native_2d.get("texts", []) if x.get("guid")
        }
        verified = {}
        for key, y in token_specs:
            element_id = created_by_key[key]
            row = texts.get(element_id.get("guid"))
            if row is None:
                raise RuntimeError(
                    f"Native 2D reader did not return {key} smoke Text."
                )
            position = row.get("position") or {}
            if not (
                math.isclose(float(position.get("x", 999)), 0.020, abs_tol=1e-6)
                and math.isclose(float(position.get("y", 999)), y, abs_tol=1e-6)
            ):
                raise RuntimeError(
                    f"{key} smoke Text coordinate mismatch: {row}"
                )
            if not math.isclose(
                float(row.get("heightMm", -1)), 2.5, abs_tol=0.01
            ):
                raise RuntimeError(
                    f"{key} smoke Text height mismatch: {row}"
                )
            expected_raw = f"<{key}>"
            if row.get("rawText") != expected_raw:
                raise RuntimeError(
                    f"{key} raw token mismatch: {row}"
                )
            expected_value = context_rows[key].get("value")
            if row.get("interpretedText") != expected_value:
                raise RuntimeError(
                    f"{key} interpreted value mismatch: "
                    f"expected={expected_value!r}, "
                    f"actual={row.get('interpretedText')!r}"
                )
            verified[key] = {
                "raw": row.get("rawText"),
                "interpreted": row.get("interpretedText"),
                "position": row.get("position"),
                "heightMm": row.get("heightMm"),
            }

        return_result = {
            "status": "PASS",
            "writePerformed": True,
            "layoutScopedAutoTextVerified": True,
            "subset": {
                "name": subset_name,
                "expectedLayoutCount": 1,
                "reportedLayoutCount": parsed_count,
            },
            "layout": {
                "name": layout_name,
                "databaseId": layout_db,
                "masterLayout": "A4_P",
                "reportedNumberInSubset": expected_number,
            },
            "verified": verified,
            "nextGate": "generate_form3_titleblock_geometry",
        }
    finally:
        if created_text_ids:
            try:
                delete_texts = api.call(
                    "DeleteElements",
                    {
                        "elements": [
                            {"elementId": element_id}
                            for element_id in created_text_ids
                        ]
                    },
                )
                if not delete_texts.get("success", False):
                    cleanup_errors.append(
                        f"DeleteElements failed: {delete_texts}"
                    )
            except Exception as exc:
                cleanup_errors.append(f"DeleteElements exception: {exc}")

        if created_layout_nav is not None:
            try:
                delete_layout = api.call(
                    "DeleteNavigatorItems",
                    {"navigatorItemIds": [{
                        "navigatorItemId": created_layout_nav
                    }]},
                )
                rows = delete_layout.get("executionResults", [])
                if len(rows) != 1 or not rows[0].get("success"):
                    cleanup_errors.append(
                        f"Delete sacrificial Layout failed: {delete_layout}"
                    )
            except Exception as exc:
                cleanup_errors.append(
                    f"Delete sacrificial Layout exception: {exc}"
                )

        if created_subset_nav is not None:
            try:
                delete_subset = api.call(
                    "DeleteNavigatorItems",
                    {"navigatorItemIds": [{
                        "navigatorItemId": created_subset_nav
                    }]},
                )
                rows = delete_subset.get("executionResults", [])
                if len(rows) != 1 or not rows[0].get("success"):
                    cleanup_errors.append(
                        f"Delete sacrificial subset failed: {delete_subset}"
                    )
            except Exception as exc:
                cleanup_errors.append(
                    f"Delete sacrificial subset exception: {exc}"
                )

    if cleanup_errors:
        raise RuntimeError(
            "Layout AutoText smoke completed but cleanup was not clean: "
            + " | ".join(cleanup_errors)
        )

    after_items = _layoutbook_items(api)
    residual_after = [
        x for x in after_items
        if x.get("name") in {subset_name, layout_name}
    ]
    if residual_after:
        raise RuntimeError(
            f"Residual smoke navigator items after cleanup: {residual_after}"
        )

    after_count = len(api.call("GetAllElements").get("elements", []))
    if after_count != before_count:
        raise RuntimeError(
            "Unexpected model element count change during Layout AutoText smoke."
        )

    return_result["cleanup"] = {
        "success": True,
        "textElementsDeleted": len(created_text_ids),
        "layoutDeleted": True,
        "subsetDeleted": True,
        "modelElementCountUnchanged": True,
    }
    return return_result

def apply_navigator_shell(api: Tapir, allow_nonempty=False):
    """Create only safe Navigator containers: View folders and Layout subsets.

    This stage intentionally does not create Views, Master Layout graphics,
    Layouts, Drawings or Publisher Sets. Those depend on seed presets and
    titleblock/output configuration that Tapir 1.5.8 cannot fully author.
    """
    validation = validate_specs()
    if validation["status"] != "PASS":
        raise RuntimeError(f"Spec validation failed: {validation['errors']}")

    before_count = len(api.call("GetAllElements").get("elements", []))
    if before_count and not allow_nonempty:
        raise RuntimeError(
            f"Refusing Navigator-shell write: current project contains "
            f"{before_count} model elements. Use a clean candidate project or "
            f"pass --allow-nonempty explicitly."
        )

    registry = load_yaml(NAVIGATOR_REGISTRY)

    view_tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "PublicViewMap"}
    ).get("navigatorItemTree", {})
    existing_view_items = _collect_navigator_items(view_tree)
    existing_folder_names = {
        x.get("name") for x in existing_view_items
        if x.get("type") == "FolderItem" and x.get("name")
    }

    created_view_folders = []
    for folder_name in registry.get("view_folders", []):
        if folder_name in existing_folder_names:
            continue
        api.call("CreateViewMapFolder", {"folderName": folder_name})
        created_view_folders.append(folder_name)

    layout_tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "LayoutBook"}
    ).get("navigatorItemTree", {})
    existing_layout_items = _collect_navigator_items(layout_tree)
    existing_subset_names = {
        x.get("name") for x in existing_layout_items
        if x.get("type") == "SubsetItem" and x.get("name")
    }

    subset_payload = []
    for subset in registry.get("layout_subsets", []):
        if subset["name"] in existing_subset_names:
            continue
        subset_payload.append({
            "name": subset["name"],
            "ownPrefix": subset.get("prefix", ""),
            "numberingStyle": "01",
            "startAt": 1,
            "continueNumbering": False,
            "useUpperPrefix": False,
            "includeToIDSequence": True,
            "customNumbering": False,
            "addOwnPrefix": True,
        })
    subset_result = None
    if subset_payload:
        subset_result = api.call(
            "CreateLayoutSubset", {"subsetsData": subset_payload}
        )

    # Read-back is authoritative.
    after_view_tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "PublicViewMap"}
    ).get("navigatorItemTree", {})
    after_view_items = _collect_navigator_items(after_view_tree)
    after_folder_names = {
        x.get("name") for x in after_view_items
        if x.get("type") == "FolderItem" and x.get("name")
    }

    after_layout_tree = api.call(
        "GetNavigatorItemTree", {"navigatorMapId": "LayoutBook"}
    ).get("navigatorItemTree", {})
    after_layout_items = _collect_navigator_items(after_layout_tree)
    after_subset_names = {
        x.get("name") for x in after_layout_items
        if x.get("type") == "SubsetItem" and x.get("name")
    }

    expected_folders = set(registry.get("view_folders", []))
    expected_subsets = {x["name"] for x in registry.get("layout_subsets", [])}
    missing_folders = sorted(expected_folders - after_folder_names)
    missing_subsets = sorted(expected_subsets - after_subset_names)
    if missing_folders or missing_subsets:
        raise RuntimeError(
            "Navigator shell read-back failed: "
            f"missingFolders={missing_folders}, missingSubsets={missing_subsets}"
        )

    after_count = len(api.call("GetAllElements").get("elements", []))
    if after_count != before_count:
        raise RuntimeError(
            "Unexpected model element count change during Navigator-shell stage."
        )

    return {
        "status": "PASS",
        "writePerformed": bool(created_view_folders or subset_payload),
        "createdViewFolders": created_view_folders,
        "createdLayoutSubsets": [x["name"] for x in subset_payload],
        "existingOrPresentViewFolders": sorted(expected_folders),
        "existingOrPresentLayoutSubsets": sorted(expected_subsets),
        "modelElementCountUnchanged": True,
        "nativeSubsetResult": subset_result,
        "deferred": [
            "Views require verified MVO/Graphic Override/Dimension Style seeds.",
            "Master Layout frame/titleblock graphics remain source/seed gated.",
            "Publisher Set creation is not exposed by Tapir 1.5.8.",
        ],
    }


def check_windows_fonts():
    """Check required font families against Windows font registry without touching Archicad."""
    manifest = load_yaml(FONT_MANIFEST)
    if os.name != "nt":
        return {
            "status": "BLOCKED_PLATFORM",
            "platform": os.name,
            "reason": "Font preflight is intentionally Windows-specific for the Archicad 29 target.",
            "requiredFamilies": [
                x["family"] for x in manifest.get("fonts", []) if x.get("required")
            ],
        }

    import winreg

    registry_paths = [
        (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
        (winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts"),
    ]
    entries = []
    for hive, key_path in registry_paths:
        try:
            with winreg.OpenKey(hive, key_path) as key:
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                    except OSError:
                        break
                    entries.append({
                        "registryName": str(name),
                        "file": str(value),
                    })
                    i += 1
        except FileNotFoundError:
            continue

    result_fonts = []
    missing_required = []
    style_warnings = []
    for font in manifest.get("fonts", []):
        family = font["family"]
        matches = [
            e for e in entries
            if family.casefold() in e["registryName"].casefold()
        ]
        found = bool(matches)
        if font.get("required") and not found:
            missing_required.append(family)

        requested_styles = font.get("styles", [])
        style_presence = {}
        names_joined = " | ".join(x["registryName"] for x in matches).casefold()
        for style in requested_styles:
            token = style.casefold()
            # "Regular" is frequently omitted from the registry display name;
            # family presence is therefore sufficient for an advisory Regular check.
            style_found = found if token == "regular" else token in names_joined
            style_presence[style] = style_found
            if font.get("required") and found and not style_found:
                style_warnings.append(f"{family}: style not explicit in registry: {style}")

        result_fonts.append({
            "family": family,
            "required": bool(font.get("required")),
            "found": found,
            "requestedStyles": requested_styles,
            "stylePresenceAdvisory": style_presence,
            "registryMatches": matches,
            "role": font.get("role"),
        })

    return {
        "status": "PASS" if not missing_required else "FAIL",
        "platform": "Windows",
        "requiredMissing": missing_required,
        "warnings": style_warnings,
        "fonts": result_fonts,
    }



def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "action",
        choices=("validate", "font-preflight", "inspect", "plan", "plan-materials", "plan-data-schema", "plan-navigator", "plan-master-layouts", "plan-master-coordinate-calibration", "plan-form3-geometry", "plan-autotext", "apply-core", "apply-surfaces", "apply-ready-materials", "apply-data-schema", "apply-navigator-shell", "apply-master-layout-shell", "apply-master-layout-smoke", "apply-layout-autotext-smoke", "apply-master-coordinate-calibration"),
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
    elif args.action == "font-preflight":
        result = check_windows_fonts()
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
        elif args.action == "plan-navigator":
            result = plan_navigator(api)
        elif args.action == "plan-master-layouts":
            result = plan_master_layouts(api)
        elif args.action == "plan-master-coordinate-calibration":
            result = plan_master_coordinate_calibration()
        elif args.action == "plan-form3-geometry":
            result = plan_form3_geometry()
        elif args.action == "plan-autotext":
            result = plan_autotext(api)
        elif args.action == "apply-core":
            result = apply_safe_core(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-surfaces":
            result = apply_surfaces(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-ready-materials":
            result = apply_ready_building_materials(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-data-schema":
            result = apply_data_schema(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-navigator-shell":
            result = apply_navigator_shell(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-master-layout-shell":
            result = apply_master_layout_shell(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-master-layout-smoke":
            result = apply_master_layout_smoke(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-layout-autotext-smoke":
            result = apply_layout_autotext_smoke(api, allow_nonempty=args.allow_nonempty)
        elif args.action == "apply-master-coordinate-calibration":
            result = apply_master_coordinate_calibration(
                api, allow_nonempty=args.allow_nonempty
            )
        else:
            raise AssertionError(args.action)

    if args.out:
        write_json(Path(args.out), result)
    if args.action != "inspect":
        write_json(evidence / "result.json", result)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    status = result.get("status") if isinstance(result, dict) else None
    if status in ("FAIL", "BLOCKED_PLATFORM"):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
