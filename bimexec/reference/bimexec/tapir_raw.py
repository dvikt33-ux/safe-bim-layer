"""Reference runtime bridge to the live-tested AC29 / Tapir 1.5.9 contract.

Read/property transport is TapirBackendV13, not a parallel official/TEMPLATE
protocol. Wall construction/dispatch and observation are shared with the live
probes in probes/ac29_contract.py. This adapter grants NO production permission.
Executor capability/WriteGate gates remain unchanged. Full repository layout is
required (reference/ alone is not a standalone installation).
"""
from __future__ import annotations

from functools import wraps
import ntpath
from pathlib import Path
import sys
from typing import Any
import uuid

from .adapters import AdapterError

_PROBES = Path(__file__).resolve().parents[2] / "probes"
if str(_PROBES) not in sys.path:
    sys.path.insert(0, str(_PROBES))
from backends_v13 import TapirBackendV13  # noqa: E402
import ac29_contract as contract  # noqa: E402


class AdapterUnavailable(AdapterError):
    """Read/precondition failure, or unknown write outcome. Never evidence of absence."""


def adapter_boundary(fn):
    """All transport/shape errors reach Executor as its typed AdapterError."""
    @wraps(fn)
    def call(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except AdapterError:
            raise
        except Exception as exc:
            raise AdapterUnavailable(f"{fn.__name__}: {type(exc).__name__}: {exc}") from exc
    return call


class TapirRaw:
    """RawArchicad protocol, using the measured v1.3 backend.

    expected_project must be explicitly configured before ANY write. backend is
    injectable for offline tests; the default constructs only the lazy v1.3
    backend (no Archicad call on import or construction).
    """

    def __init__(self, port: int | None = None, types: tuple[str, ...] = ("Wall", "Slab"),
                 *, expected_project: str | None = None, backend: Any = None) -> None:
        self.port = port
        self.types = types
        self.expected_project = expected_project
        self.backend = backend if backend is not None else TapirBackendV13(port=port, types=types)
        self.backend.types = types

    def available_commands(self) -> set[str]:
        """Observed read availability only; never dispatch a write for discovery."""
        found = set()
        for command, read in (
            ("GetProjectInfo", self.project_info), ("GetStories", self.stories),
            ("GetAllElements", self.list_guids), ("GetElementsByType", self.count_by_type),
        ):
            try:
                read()
                found.add(command)
            except AdapterError:
                pass
        # Use a real existing Wall, not an empty-details invocation to certify shape.
        try:
            walls = self.backend.elements_by_type("Wall")
            if walls:
                self.details(walls[0])
                found.add("GetDetailsOfElements")
                self.get_marker(walls[0], "element_id")
                found.add("GetPropertyValuesOfElements")
        except Exception:
            pass
        return found

    @adapter_boundary
    def project_info(self) -> dict[str, Any]:
        info = self.backend.project_info()
        if (info.get("is_untitled") is not False or info.get("is_teamwork") is not False
                or not info.get("project_path") or not info.get("project_name")):
            raise AdapterUnavailable("saved Solo project with explicit identity required")
        if self.expected_project is not None and ntpath.normcase(ntpath.normpath(info["project_path"])) != ntpath.normcase(ntpath.normpath(self.expected_project)):
            raise AdapterUnavailable("project does not match expected_project")
        version = str(info.get("archicad_version") or "")
        if version and version.split(".")[0] != "29":
            raise AdapterUnavailable("only the AC29 contract is covered")
        return info

    @adapter_boundary
    def stories(self) -> list[dict[str, Any]]:
        return self.backend.stories()

    @adapter_boundary
    def count_by_type(self) -> dict[str, int]:
        return self.backend.count_by_type()

    @adapter_boundary
    def list_guids(self) -> list[str]:
        return self.backend.all_elements()

    @adapter_boundary
    def details(self, guid: str) -> dict[str, Any]:
        # Empty/error/missing required fields => AdapterUnavailable, never None.
        return contract.observe_wall(self.backend, guid, self.stories())

    @adapter_boundary
    def find_by_filter(self, type_: str, story_name: str, layer: str) -> list[str]:
        result = []
        for guid in self.backend.elements_by_type(type_):
            d = self.details(guid)  # Never discard failed detail reads as nonmatches.
            if d["type"] == type_ and d["story"]["name"] == story_name and d["layer"] == layer:
                result.append(guid)
        return result

    @staticmethod
    def _marker_ref(medium: str) -> dict[str, str]:
        if medium != "element_id":
            raise AdapterUnavailable("only the live-tested General_ElementID carrier is covered")
        return contract.ELEMENT_ID_REF

    @adapter_boundary
    def get_marker(self, guid: str, medium: str) -> str:
        values = self.backend.get_property_values(self._marker_ref(medium), [guid])
        value = values.get(guid)
        if not isinstance(value, str):
            raise AdapterUnavailable("Element ID read unavailable; not a negative match")
        return value

    @adapter_boundary
    def find_by_marker(self, exact: str | None = None, prefix: str | None = None) -> list[str]:
        if (exact is None) == (prefix is None):
            raise AdapterUnavailable("specify exactly one of exact or prefix")
        guids = self.list_guids()
        values = self.backend.get_property_values(contract.ELEMENT_ID_REF, guids) if guids else {}
        result = []
        for guid in guids:
            value = values.get(guid)
            if not isinstance(value, str):
                raise AdapterUnavailable("incomplete Element ID scan; cannot prove absence")
            if (value == exact if exact is not None else value.startswith(prefix)):
                result.append(guid)
        return result

    def _write_precheck(self) -> None:
        if not isinstance(self.expected_project, str) or not self.expected_project.strip():
            raise AdapterUnavailable("writes require explicit expected_project")
        self.project_info()
        if self.backend.addon_version() != contract.ADDON_VERSION:
            raise AdapterUnavailable("Tapir 1.5.9 must be confirmed before dispatch")

    @adapter_boundary
    def set_marker(self, guid: str, value: str, medium: str) -> None:
        ref = self._marker_ref(medium)
        self._write_precheck()
        self.backend.set_property_value(guid, ref, value)

    @adapter_boundary
    def create_wall(self, params: dict[str, Any]) -> str:
        self._write_precheck()
        floor = contract.resolve_story(self.stories(), params["story"])
        if "story_index" in params and params["story_index"] != floor:
            raise AdapterUnavailable("story_index contradicts resolved name+elevation")
        # No guessed top-link/flip/basic/profile semantics. The historical wire
        # recipe did not carry top_link; H1 must not pretend it did.
        if params.get("top_link") is not None:
            raise AdapterUnavailable("top_link is not covered by the tested wire recipe")
        for key in ("base_level", "offset", "arc_angle"):
            if key in params and contract.number(params[key], key) != 0.0:
                raise AdapterUnavailable(f"{key} outside tested recipe")
        uuid.UUID(params["composite_id"])  # Explicit caller-supplied identity, never choose a default.
        payload = contract.wall_payload(
            params["from"], params["to"], floor_index=floor,
            height=params["height"], thickness=params["thickness"],
            reference_line=params["reference_line"], structure_type=params["structure_type"],
            composite_id=params["composite_id"])
        # ONE CreateWalls call, no retry, no hidden layer/property writes.
        return contract.create_wall_once(self.backend, payload)[0]
