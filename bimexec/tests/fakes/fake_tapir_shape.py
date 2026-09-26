"""
Имитация ФАКТИЧЕСКОЙ схемы ответов Tapir (по инвентаризации):
type / id / floorIndex / layerIndex + type-specific details.
Только для прогона probe_t0a.py на Linux. На Windows не нужен.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "probes")))
from backends import Backend, BackendError, _normalize_tapir_details  # noqa: E402

WALL_RAW = {
    "type": "Wall",
    "id": "W-TEST-001",
    "floorIndex": 0,
    "layerIndex": 3,
    "drawIndex": 7,
    "hotlinkId": None,
    "details": {
        "wall": {
            "begCoordinate": {"x": 1.5, "y": 2.5},
            "endCoordinate": {"x": 6.5, "y": 2.5},
            "height": 3.0,
            "thickness": 0.30,
            "referenceLineLocation": "Center",
            "structureType": "Basic",
        }
    },
}

MODEL = {
    "guids": ["G-0001", "G-0002", "G-0003"],
    "types": {"G-0001": "Wall", "G-0002": "Wall", "G-0003": "Slab"},
    "raw": {
        "G-0001": WALL_RAW,
        "G-0002": dict(WALL_RAW, id="W-TEST-002"),
        "G-0003": {"type": "Slab", "id": "S-01", "floorIndex": 0, "layerIndex": 2, "details": {}},
    },
    "props": {
        "G-0001": {"General_ElementID": "W-TEST-001", "ModelView_LayerName": "A-WALL"},
        "G-0002": {"General_ElementID": "W-TEST-002", "ModelView_LayerName": "A-WALL"},
        "G-0003": {"General_ElementID": "S-01", "ModelView_LayerName": "A-SLAB"},
    },
    "user_props": {},
}

PROJECT = {
    "project_path": r"C:\PLN\MCP_TEST.pln",
    "project_name": "MCP_TEST",
    "is_untitled": False,
    "is_teamwork": False,
    "archicad_version": "29",
    "archicad_build": "29.3000",
    "port": 19723,
    "instance_hint": "port=19723",
}


class FakeTapirShape(Backend):
    name = "tapir"

    def available(self):
        return True, "fake tapir-shape model"

    def project_info(self):
        return dict(PROJECT)

    def stories(self):
        return [{"index": 0, "name": "Ground Floor", "elevation": 0.0},
                {"index": 1, "name": "Floor 1", "elevation": 3.0}]

    def all_elements(self):
        return list(MODEL["guids"])

    def elements_by_type(self, t):
        return [g for g, tt in MODEL["types"].items() if tt == t]

    def count_by_type(self):
        return {t: len(self.elements_by_type(t)) for t in ("Wall", "Slab", "Window", "Door")}

    def details_raw(self, g):
        return MODEL["raw"].get(g)

    def details(self, g):
        raw = self.details_raw(g)
        return _normalize_tapir_details(raw) if raw else None

    def get_property_values(self, ref, guids):
        store = MODEL["user_props"] if ref.get("kind") == "user" else MODEL["props"]
        key = ref.get("id") or ref.get("name") or ref.get("address")
        out = {}
        for g in guids:
            if g not in MODEL["guids"]:
                raise BackendError("unknown guid")
            if ref.get("kind") == "user" and key != "BIMEXEC_MARKER":
                raise BackendError("no id for address 'BIMEXEC/BIMEXEC_MARKER'")
            out[g] = store.get(g, {}).get(key)
        return out

    def set_property_value(self, g, ref, v):
        # тот же store, из которого читает get_property_values:
        # user-defined property и builtin живут в разных местах
        store = MODEL["user_props"] if ref.get("kind") == "user" else MODEL["props"]
        key = ref.get("id") or ref.get("name") or ref.get("address")
        store.setdefault(g, {})[key] = v

    def raw_call(self, cmd, payload=None):
        if cmd == "GetAddOnVersion":
            return {"version": "1.5.9"}
        return {}

    def addon_version(self):
        return "1.5.9"


BACKEND = FakeTapirShape
