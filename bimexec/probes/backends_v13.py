"""
BIMEXEC probe compatibility layer v1.3 for Archicad 29 + Tapir 1.5.9.

This module intentionally leaves the v1.2 safety envelope intact and overrides only
the live API-shape mismatches proven by the 2026-09-26 T0A run:
- GetDetailsOfElements requires ElementIdArrayItem -> elementId.guid.
- Official Archicad utilities resolve built-in/user-defined properties.
- Property reads use the official GetPropertyValuesDictionary helper.
- Property writes use official SetPropertyValuesOfElements with typed values.
- Blank story names are treated as missing so the existing T0A criterion fails closed.
"""
from __future__ import annotations

import uuid
from typing import Any

import backends as base

PROBE_VERSION = "1.3"

# Only commands that are actually invoked in TapirCommand namespace and matter to T0.
# Official JSON API commands are exercised by the methods below, not by prefixing "API."
TAPIR_READ_COMMANDS_V13 = [
    "GetAddOnVersion",
    "GetProjectInfo",
    "GetStories",
    "GetAllElements",
    "GetElementsByType",
    "GetDetailsOfElements",
    "GetPropertyValuesOfElements",
]


class TapirBackendV13(base.TapirBackend):
    """AC29/Tapir 1.5.9 compatibility fixes without widening write scope."""

    def stories(self) -> list[dict[str, Any]]:
        out = super().stories()
        for story in out:
            name = story.get("name")
            if not isinstance(name, str) or not name.strip():
                story["name"] = None
        return out

    def details_raw(self, guid: str) -> dict[str, Any] | None:
        payload = {"elements": [{"elementId": {"guid": guid}}]}
        res = self._tapir("GetDetailsOfElements")(payload)
        d = base._to_dict(res)
        items = base._as_list(d.get("detailsOfElements") or d.get("details") or res)
        if not items:
            return None
        first = base._to_dict(items[0])
        if first.get("error"):
            raise base.BackendError(f"GetDetailsOfElements({guid}): {first['error']}")
        return first

    def resolve_property_id(self, ref: dict[str, Any]) -> Any:
        self._connect()
        kind = ref.get("kind")
        try:
            if kind == "builtin":
                return self.conn.utilities.GetBuiltInPropertyId(ref["id"])
            if kind == "user":
                return self.conn.utilities.GetUserDefinedPropertyId(
                    str(ref.get("group") or ""), str(ref.get("name") or "")
                )
            if kind == "name":
                address = str(ref.get("address") or "")
                # Current T0 name-based lookup is used for built-ins such as
                # ModelView_LayerName. Try official built-in resolution first.
                try:
                    return self.conn.utilities.GetBuiltInPropertyId(address)
                except Exception:
                    if "/" in address:
                        group, name = address.split("/", 1)
                        return self.conn.utilities.GetUserDefinedPropertyId(group, name)
                    raise
            if kind == "guid":
                # Kept for compatibility with the base contract. Current T0 does not
                # need to construct PropertyId from a raw GUID on the live path.
                return {"guid": ref["guid"]}
        except Exception as e:
            raise base.BackendError(
                f"resolve_property_id({base.ref_label(ref)}): {type(e).__name__}: {e}"
            ) from e
        raise base.BackendError(f"unknown property ref kind: {kind}")

    def _element_id(self, guid: str):
        self._connect()
        return self.conn.types.ElementId(uuid.UUID(str(guid)))

    def get_property_values(
        self, ref: dict[str, Any], guids: list[str]
    ) -> dict[str, Any | None]:
        self._connect()
        pid = self.resolve_property_id(ref)
        element_ids = [self._element_id(g) for g in guids]
        try:
            values = self.conn.utilities.GetPropertyValuesDictionary(element_ids, [pid])
        except Exception as e:
            raise base.BackendError(
                f"GetPropertyValuesDictionary({base.ref_label(ref)}): "
                f"{type(e).__name__}: {e}"
            ) from e

        out: dict[str, Any | None] = {}
        for guid, element_id in zip(guids, element_ids):
            row = values.get(element_id, {}) if isinstance(values, dict) else {}
            value = None
            if isinstance(row, dict):
                if pid in row:
                    value = row[pid]
                else:
                    # Defensive fallback for fake/test mappings whose PropertyId key
                    # is equivalent but not object-identical.
                    for key, candidate in row.items():
                        if base._to_dict(key) == base._to_dict(pid):
                            value = candidate
                            break
            out[guid] = value
        return out

    def set_property_value(
        self, guid: str, ref: dict[str, Any], value: str
    ) -> None:
        """T0B only: one official property write attempt, no retry."""
        self._connect()
        pid = self.resolve_property_id(ref)
        act = self.conn.types
        element_id = self._element_id(guid)
        try:
            property_value = act.NormalStringPropertyValue(str(value))
            item = act.ElementPropertyValue(element_id, pid, property_value)
            results = self.conn.commands.SetPropertyValuesOfElements([item])
        except Exception as e:
            raise base.BackendError(
                f"SetPropertyValuesOfElements({guid}, {base.ref_label(ref)}): "
                f"{type(e).__name__}: {e}"
            ) from e

        for result in results or []:
            err = getattr(result, "error", None)
            if err:
                raise base.BackendError(
                    f"SetPropertyValuesOfElements returned error: {base._to_dict(err) or err}"
                )


def discover_ports_v13(ports: list[int], timeout: float = 5.0) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for port in ports:
        try:
            b = TapirBackendV13(port=port)
            ok, why = b.available()
            if not ok:
                found.append(
                    {"port": port, "_error": why, "note": "порт не ответил; причина ниже"}
                )
                continue
            info = b.project_info()
            info["_backend"] = b.name
            info["_addon_version"] = b.addon_version()
            found.append(info)
        except Exception as e:
            found.append({"port": port, "_error": f"{type(e).__name__}: {e}"})
    return found


def build_backends_v13(
    order: str, port: int | None, mcp_url: str, module_path: str | None
) -> list[base.Backend]:
    out: list[base.Backend] = []
    if module_path:
        try:
            out.append(base.load_backend_module(module_path)())
        except Exception as e:
            print(f"[warn] backend module not loaded: {e}", file=base.sys.stderr)
    for name in [b.strip() for b in order.split(",") if b.strip()]:
        if name == "tapir":
            out.append(TapirBackendV13(port=port))
        elif name == "mcp":
            out.append(base.McpBackend(base_url=mcp_url))
        elif name == "bibim":
            out.append(base.BibimBackend())
    return out
