"""
Тестовый бэкенд: in-memory модель, используется ТОЛЬКО чтобы прогнать
probe_t0a.py / probe_t0b.py в отрыве от Archicad. На Windows не нужен.
"""
import sys, os, math
sys.path.insert(0, os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "probes")))
from backends import Backend, BackendError

MODEL = {
    "guids": ["G-0001", "G-0002", "G-0003"],
    "types": {"G-0001": "Wall", "G-0002": "Wall", "G-0003": "Slab"},
    "props": {"G-0001": {"General_ElementID": "W-101"},
              "G-0002": {"General_ElementID": "W-102"},
              "G-0003": {"General_ElementID": "S-01"}},
    "user_props": {"G-0001": {}, "G-0002": {}, "G-0003": {}},
}
PROJECT = {
    "project_path": r"C:\PLN\MCP_TEST.pln", "project_name": "MCP_TEST",
    "is_untitled": False, "is_teamwork": False,
    "archicad_version": "29", "archicad_build": "29.0.0", "port": 19723,
    "instance_hint": r"C:\PLN\MCP_TEST.pln",
}


class FakeBackend(Backend):
    name = "fake"

    def available(self): return True, "in-memory test model"

    def project_info(self): return dict(PROJECT)

    def stories(self): return [{"name": "Ground Floor", "elevation": 0.0}]

    def all_elements(self): return list(MODEL["guids"])

    def elements_by_type(self, t): return [g for g, tt in MODEL["types"].items() if tt == t]

    def count_by_type(self):
        out = {}
        for t in ("Wall", "Slab", "Window", "Door"):
            out[t] = len(self.elements_by_type(t))
        return out

    def details_raw(self, guid):
        # старый double: сырых Tapir-ответов нет, отдаём None
        return None

    def details(self, guid):
        if guid not in MODEL["guids"]: return None
        if MODEL["types"][guid] != "Wall": return {"type": "Slab", "layer": "A-SLAB",
                                                   "story": {"name": "Ground Floor", "elevation": 0.0}}
        return {"type": "Wall", "layer": "A-WALL",
                "story": {"name": "Ground Floor", "elevation": 0.0},
                "ref_line": {"from": [1.5, 2.5], "to": [6.5, 2.5]},
                "length": 5.0, "angle": 0.0, "height": 3.0, "thickness": 0.30}

    def _store(self, ref):
        return MODEL["user_props"] if ref.get("kind") == "user" else MODEL["props"]

    def get_property_values(self, ref, guids):
        store = self._store(ref)
        key = ref.get("id") if ref.get("kind") == "builtin" else ref.get("name")
        out = {}
        for g in guids:
            if g not in MODEL["guids"]:
                raise BackendError(f"unknown guid {g}")
            out[g] = store.get(g, {}).get(key)
        return out

    def resolve_property_id(self, ref):
        key = ref.get("id") or ref.get("name")
        if ref.get("kind") == "user" and key not in ("BIMEXEC_MARKER",):
            raise BackendError("user-defined property does not exist")
        return {"guid": f"PROP-{key}"}

    def set_property_value(self, guid, ref, value):
        store = self._store(ref)
        key = ref.get("id") if ref.get("kind") == "builtin" else ref.get("name")
        if ref.get("kind") == "user" and key not in ("BIMEXEC_MARKER",):
            raise BackendError("user-defined property does not exist")
        store.setdefault(guid, {})[key] = value

    def try_command(self, logical_name):
        if logical_name == "GetAddOnVersion":
            return {"ok": False, "error": "ValidationError: Extra inputs are not permitted"}
        return {"ok": True, "error": None}


BACKEND = FakeBackend
