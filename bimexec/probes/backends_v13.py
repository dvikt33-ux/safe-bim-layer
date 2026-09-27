"""
BIMEXEC probe compatibility layer v1.3 for Archicad 29 + Tapir 1.5.9.

Uses the live API shapes proven by the 2026-09-26 T0A run. H1 additionally
makes malformed/error reads fail closed via the shared ac29_contract helper;
the historical v1.3 implementation remains at c55f404. T0's write denylist
is unchanged. API shapes:
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
import ac29_contract as contract

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

    @contract.backend_boundary
    def project_info(self) -> dict[str, Any]:
        # Same live Tapir command, but absent flags must not become false.
        d = base._to_dict(self._tapir("GetProjectInfo")())
        if (d.get("error") or not isinstance(d.get("projectName"), str)
                or not d.get("projectName")
                or type(d.get("isUntitled")) is not bool
                or type(d.get("isTeamwork")) is not bool):
            raise base.BackendError("GetProjectInfo: incomplete identity")
        path = d.get("projectPath") or d.get("projectLocation")
        if not d["isUntitled"] and (not isinstance(path, str) or not path):
            raise base.BackendError("GetProjectInfo: saved project path unavailable")
        return {
            "project_path": path, "project_name": d["projectName"],
            "is_untitled": d["isUntitled"], "is_teamwork": d["isTeamwork"],
            "archicad_version": self._product_info("version", "archicadVersion"),
            "archicad_build": self._product_info("build", "buildNumber"),
            "port": self.port, "instance_hint": f"port={self.port}",
        }

    @contract.backend_boundary
    def stories(self) -> list[dict[str, Any]]:
        # No enumeration-position fallback for a missing index.
        return contract.story_map(self._tapir("GetStories")())

    @contract.backend_boundary
    def all_elements(self) -> list[str]:
        return contract.element_guids(self._official("GetAllElements")(), "GetAllElements")

    @contract.backend_boundary
    def elements_by_type(self, element_type: str) -> list[str]:
        return contract.element_guids(
            self._tapir("GetElementsByType")({"elementType": element_type}),
            "GetElementsByType")

    @contract.backend_boundary
    def count_by_type(self) -> dict[str, int]:
        # An explicit empty list is 0. Errors are never 0 (nor partial counts).
        return {kind: len(self.elements_by_type(kind)) for kind in self.types}

    @contract.backend_boundary
    def details_raw(self, guid: str) -> dict[str, Any]:
        payload = {"elements": [{"elementId": {"guid": guid}}]}
        res = self._tapir("GetDetailsOfElements")(payload)
        items = contract.rows(res, "detailsOfElements", "GetDetailsOfElements")
        if len(items) != 1:
            raise base.BackendError("GetDetailsOfElements: expected exactly one result")
        first = base._to_dict(items[0])
        if first.get("error") or not first.get("type") or not isinstance(first.get("details"), dict):
            raise base.BackendError(f"GetDetailsOfElements({guid}): unavailable details: {first!r}")
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

    @contract.backend_boundary
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
            missing = object()
            value = missing
            if isinstance(row, dict):
                if pid in row:
                    value = row[pid]
                else:
                    # Defensive fallback for fake/test mappings whose PropertyId key
                    # is equivalent but not object-identical.
                    for key, candidate in row.items():
                        expected_key = base._to_dict(pid)
                        if expected_key and base._to_dict(key) == expected_key:
                            value = candidate
                            break
            if value is missing:
                raise base.BackendError(f"property read missing row/value for {guid}")
            out[guid] = value
        return out

    def set_property_value(
        self, guid: str, ref: dict[str, Any], value: str
    ) -> None:
        """One official property write attempt, no retry; caller owns the write gate."""
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
