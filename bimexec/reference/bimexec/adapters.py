"""
BIMEXEC v1 — адаптер Archicad и его имитация для тестов.

Важно про имитацию: она воспроизводит не «сферический Archicad», а те
классы отказов, которые реально задокументированы:
  - E2: SetPropertyValuesOfElements -> "Teamwork Permission Denied" на Solo
  - E3: write возвращает успех, но значение не записано (silent no-op)
  - AC29: read-back ломается, пока write работает
  - create возвращает чужой GUID
  - таймаут ПОСЛЕ применения
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Any


class AdapterError(Exception):
    """Любой сбой адаптера. Router НЕ интерпретирует его как «не применено»."""


class AdapterTimeout(AdapterError):
    pass


@dataclass
class CreateResult:
    outcome: str                 # "ok" | "unknown"
    candidate_guid: str | None
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class WriteResult:
    outcome: str                 # "ok" | "unknown"
    raw: dict[str, Any] = field(default_factory=dict)


# --- «модель Archicad» ------------------------------------------------------


@dataclass
class Element:
    guid: str
    type: str
    story: dict[str, Any]
    layer: str
    ref_line: dict[str, Any] | None
    height: float | None
    thickness: float | None
    marker: str | None = None
    props: dict[str, Any] = field(default_factory=dict)


class FakeArchicad:
    """Минимальная in-memory модель с тем же разделяемым состоянием, что у
    настоящего Archicad: элементы, маркеры, счётчики, слой, выделение."""

    _guid = itertools.count(1)

    def __init__(self, project_info: dict[str, Any], stories: list[dict[str, Any]]) -> None:
        self.project_info = project_info
        self.stories = stories
        self.elements: dict[str, Element] = {}
        self.layer_state = {"locked": set(), "hidden": set()}
        self.selection: list[str] = []

    def new_guid(self) -> str:
        return f"GUID-{next(self._guid):04d}"

    def add(self, **kw) -> Element:
        e = Element(guid=self.new_guid(), **kw)
        self.elements[e.guid] = e
        return e

    def counts(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for e in self.elements.values():
            out[e.type] = out.get(e.type, 0) + 1
        return out

    def by_marker(self, exact: str | None = None, prefix: str | None = None) -> list[str]:
        out = []
        for e in self.elements.values():
            values = [e.marker] + list(e.props.values())
            for v in values:
                if not v:
                    continue
                if exact is not None and v == exact:
                    out.append(e.guid)
                    break
                if prefix is not None and v.startswith(prefix):
                    out.append(e.guid)
                    break
        return out

    def list_guids(self) -> list[str]:
        """Один вызов на шаг: дешёвая основа для state fingerprint.
        В реальном адаптере — GetAllElements / GetElementsByType по типам."""
        return sorted(self.elements)

    def move_first(self, dx: float = 0.5) -> None:
        """«Человек» двигает элемент мышью: состав модели не меняется,
        меняется только геометрия. Дешёвый fingerprint этого не видит."""
        victim = sorted(self.elements)[0]
        e = self.elements[victim]
        if e.ref_line:
            e.ref_line = {
                "from": [e.ref_line["from"][0] + dx, e.ref_line["from"][1]],
                "to": [e.ref_line["to"][0] + dx, e.ref_line["to"][1]],
            }

    def by_filter(self, type_: str, story_name: str, layer: str) -> list[str]:
        return [
            e.guid
            for e in self.elements.values()
            if e.type == type_ and e.story.get("name") == story_name and e.layer == layer
        ]


# --- адаптер ----------------------------------------------------------------


@dataclass
class Faults:
    """Инъекция отказов. Всё выключено = нормальный Archicad."""

    create_applied_but_timeout: bool = False      # применить, then AdapterTimeout
    create_returns_wrong_guid: bool = False       # проверяет tag-guard
    marker_write_unknown: bool = False            # E2: применить/не применить, ответа нет
    marker_silent_noop: bool = False              # E3: ответ ok, значение не записано
    readback_broken: bool = False                 # AC29: read падает, write работает
    readback_broken_after_marker: bool = False    # read ломается ПОСЛЕ привязки
    drop_independent_path: bool = False           # оставить только один путь read-back
    wrong_geometry: bool = False                  # created, но не там


class FakeAdapter:
    """Имитация BIBIM / Archicad-MCP / Tapir поверх FakeArchicad."""

    def __init__(self, ac: FakeArchicad, faults: Faults | None = None) -> None:
        self.ac = ac
        self.faults = faults or Faults()
        self.calls: list[str] = []
        self._foreign_guid: str | None = None
        self._details_calls = 0

    # -- read-only -----------------------------------------------------------

    def get_project_info(self) -> dict[str, Any]:
        self.calls.append("get_project_info")
        return dict(self.ac.project_info)

    def get_stories(self) -> list[dict[str, Any]]:
        self.calls.append("get_stories")
        return [dict(s) for s in self.ac.stories]

    def get_layer_state(self) -> dict[str, Any]:
        self.calls.append("get_layer_state")
        return {
            "locked": sorted(self.ac.layer_state["locked"]),
            "hidden": sorted(self.ac.layer_state["hidden"]),
        }

    def count_by_type(self) -> dict[str, int]:
        self.calls.append("count_by_type")
        return self.ac.counts()

    def list_guids(self) -> list[str]:
        self.calls.append("list_guids")
        return self.ac.list_guids()

    def find_by_filter(self, type_: str, story_name: str, layer: str) -> list[str]:
        self.calls.append("find_by_filter")
        return self.ac.by_filter(type_, story_name, layer)

    def get_details(self, guid: str) -> dict[str, Any] | None:
        self.calls.append("get_details")
        self._details_calls += 1
        # readback_broken_after_marker: первый вызов (tag-guard) работает,
        # дальше read-back недоступен — ровно сценарий AC29 «писать можно, читать нет»
        if self.faults.readback_broken or (
            self.faults.readback_broken_after_marker and self._details_calls > 1
        ):
            raise AdapterError("GetDetailsOfElements failed (AC29 schema mismatch)")
        e = self.ac.elements.get(guid)
        if e is None:
            return None
        return {
            "type": e.type,
            "story": dict(e.story),
            "layer": e.layer,
            "ref_line": dict(e.ref_line) if e.ref_line else None,
            "height": e.height,
            "thickness": e.thickness,
            "length": _seg_len(e.ref_line) if e.ref_line else None,
            "angle": _seg_angle(e.ref_line) if e.ref_line else None,
        }

    # -- marker --------------------------------------------------------------

    def set_marker(self, guid: str, marker: str, medium: str) -> WriteResult:
        self.calls.append("set_marker")
        if self.faults.marker_write_unknown:
            # E2: реальное поведение — неизвестно, применилось или нет.
            # Имитируем ХУДШИЙ вариант: применилось, но ответ потерян.
            e = self.ac.elements.get(guid)
            if e is not None:
                e.marker = marker
            raise AdapterTimeout("SetPropertyValuesOfElements: no response")
        if self.faults.marker_silent_noop:
            # E3: 200 OK, значение не записано
            return WriteResult("ok", {"success": True})
        e = self.ac.elements.get(guid)
        if e is None:
            raise AdapterError("element not found")
        e.marker = marker
        return WriteResult("ok", {"success": True})

    def read_marker(self, guid: str, medium: str) -> str | None:
        self.calls.append("read_marker")
        e = self.ac.elements.get(guid)
        return e.marker if e else None

    def find_by_marker(self, exact: str | None = None, prefix: str | None = None) -> list[str]:
        self.calls.append("find_by_marker")
        return self.ac.by_marker(exact=exact, prefix=prefix)

    # -- mutation ------------------------------------------------------------

    def create_wall(self, op: dict[str, Any]) -> CreateResult:
        self.calls.append("create_wall")
        story = op["story"]
        layer = op["layer"]
        if layer in self.ac.layer_state["locked"]:
            raise AdapterError("layer is locked")


        if self.faults.wrong_geometry:
            frm, to = [0.0, 0.0], [1.0, 0.0]
        else:
            frm, to = list(map(float, op["from"])), list(map(float, op["to"]))

        e = self.ac.add(
            type="Wall",
            story=dict(story),
            layer=layer,
            ref_line={"from": frm, "to": to},
            height=float(op["height"]),
            thickness=float(op["thickness"]),
        )

        if self.faults.create_applied_but_timeout:
            raise AdapterTimeout("create: connection dropped after apply")

        guid = e.guid
        if self.faults.create_returns_wrong_guid:
            other = [g for g in self.ac.elements if g != e.guid]
            if other:
                guid = other[0]
            else:  # создадим «чужой» элемент, чтобы GUID был валидным, но чужим
                foreign = self.ac.add(
                    type="Slab",
                    story=dict(story),
                    layer=layer,
                    ref_line=None,
                    height=None,
                    thickness=None,
                )
                guid = foreign.guid
        return CreateResult("ok", guid, {"guid": guid})


# -- helpers ------------------------------------------------------------------


def _seg_len(seg: dict[str, Any]) -> float:
    (x1, y1), (x2, y2) = seg["from"], seg["to"]
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5


def _seg_angle(seg: dict[str, Any]) -> float:
    (x1, y1), (x2, y2) = seg["from"], seg["to"]
    import math

    return math.degrees(math.atan2(y2 - y1, x2 - x1))


# --- сырой адаптер для probe поверх имитации --------------------------------


class FakeRaw:
    """Реализует протокол RawArchicad (см. probe.py) поверх FakeArchicad.

    Нужна, чтобы тестировать сам probe: логика проверок и негативных
    контролей одинакова для имитации и для живого Archicad.
    """

    def __init__(
        self,
        ac: FakeArchicad,
        unsupported_media: set[str] | None = None,
        no_prefix_search: bool = False,
        no_marker_search: bool = False,
        broken_details: bool = False,
    ) -> None:
        self.ac = ac
        self.unsupported = unsupported_media or set()
        self.no_prefix_search = no_prefix_search
        self.no_marker_search = no_marker_search
        self.broken_details = broken_details

    def available_commands(self) -> set[str]:
        return {"GetProjectInfo", "GetAllElements", "GetElementsByType",
                "GetDetailsOfElements", "GetPropertyValuesOfElements",
                "SetPropertyValuesOfElements", "GetStories", "CreateWalls"}

    def project_info(self) -> dict[str, Any]:
        return dict(self.ac.project_info)

    def stories(self) -> list[dict[str, Any]]:
        return [dict(s) for s in self.ac.stories]

    def count_by_type(self) -> dict[str, int]:
        return self.ac.counts()

    def list_guids(self) -> list[str]:
        return sorted(self.ac.elements)

    def details(self, guid: str) -> dict[str, Any] | None:
        if self.broken_details:
            raise AdapterError("GetDetailsOfElements failed (AC29 schema mismatch)")
        e = self.ac.elements.get(guid)
        if e is None:
            return None
        d = {
            "type": e.type,
            "story": dict(e.story),
            "layer": e.layer,
            "height": e.height,
            "thickness": e.thickness,
        }
        if e.ref_line:
            d["ref_line"] = dict(e.ref_line)
            d["length"] = _seg_len(e.ref_line)
            d["angle"] = _seg_angle(e.ref_line)
        return d

    def find_by_filter(self, type_: str, story_name: str, layer: str) -> list[str]:
        return self.ac.by_filter(type_, story_name, layer)

    def get_marker(self, guid: str, medium: str) -> str | None:
        if medium in self.unsupported:
            raise NotImplementedError(f"medium {medium} not available")
        e = self.ac.elements.get(guid)
        if e is None:
            return None
        if medium == "property":
            return e.props.get("BIMEXEC_MARKER")
        return e.marker

    def find_by_marker(self, exact: str | None = None, prefix: str | None = None) -> list[str]:
        if self.no_marker_search:
            raise NotImplementedError("no marker search")
        if prefix is not None and self.no_prefix_search:
            raise NotImplementedError("prefix search not supported")
        return self.ac.by_marker(exact=exact, prefix=prefix)

    def set_marker(self, guid: str, value: str, medium: str) -> None:
        if medium in self.unsupported:
            raise NotImplementedError(f"medium {medium} not available")
        e = self.ac.elements.get(guid)
        if e is None:
            raise AdapterError("element not found")
        if medium == "property":
            e.props["BIMEXEC_MARKER"] = value
        else:
            e.marker = value

    def create_wall(self, params: dict[str, Any]) -> str:
        e = self.ac.add(
            type="Wall",
            story=dict(params["story"]),
            layer=params["layer"],
            ref_line={"from": list(params["from"]), "to": list(params["to"])},
            height=float(params["height"]),
            thickness=float(params["thickness"]),
        )
        return e.guid


# --- мост: один raw-адаптер -> протокол исполнителя --------------------------


class ExecutorAdapter:
    """Адаптирует «сырой» адаптер (протокол probe.RawArchicad) к протоколу,
    которого ждёт Executor.

    Смысл: вы пишете ОДИН raw-адаптер под свой стек (BIBIM / Tapir / MCP),
    probe измеряет его возможности, исполнитель работает через этот мост.
    Две разные реализации одной и той же обёртки — это две разные правды о
    том, что умеет Archicad.
    """

    def __init__(self, raw: Any, medium: str, layer_state_known: bool = False) -> None:
        self.raw = raw
        self.medium = medium
        self.layer_state_known = layer_state_known
        self.faults = None   # совместимость с Executor._observe

    # -- read-only

    def get_project_info(self) -> dict[str, Any]:
        return self.raw.project_info()

    def get_stories(self) -> list[dict[str, Any]]:
        return self.raw.stories()

    def get_layer_state(self) -> dict[str, Any]:
        """known=False означает «адаптер не умеет сообщать состояние слоёв».
        Исполнитель тогда не применяет предусловие по слою — это честная дырка,
        а не молчаливое «слой в порядке»."""
        try:
            st = self.raw.layer_state()
        except (NotImplementedError, AttributeError):
            return {"locked": [], "hidden": [], "known": False}
        st = dict(st or {})
        st["known"] = self.layer_state_known
        return st

    def count_by_type(self) -> dict[str, int]:
        return self.raw.count_by_type()

    def list_guids(self) -> list[str]:
        return self.raw.list_guids()

    def find_by_filter(self, type_: str, story_name: str, layer: str) -> list[str]:
        return self.raw.find_by_filter(type_, story_name, layer)

    def get_details(self, guid: str) -> dict[str, Any] | None:
        return self.raw.details(guid)

    # -- marker

    def set_marker(self, guid: str, marker: str, medium: str) -> "WriteResult":
        self.raw.set_marker(guid, marker, medium or self.medium)
        return WriteResult("ok", {"success": True})

    def read_marker(self, guid: str, medium: str) -> str | None:
        return self.raw.get_marker(guid, medium or self.medium)

    def find_by_marker(self, exact: str | None = None, prefix: str | None = None) -> list[str]:
        return self.raw.find_by_marker(exact=exact, prefix=prefix)

    # -- mutation

    def create_wall(self, op: dict[str, Any]) -> "CreateResult":
        # Preserve explicit recipe fields. Story resolution belongs to the raw
        # AC29 contract; never inject story_index=0 or reference_line="center".
        fields = (
            "story", "layer", "from", "to", "height", "thickness",
            "reference_line", "structure_type", "composite_id", "story_index",
            "base_level", "top_link", "offset", "arc_angle",
        )
        guid = self.raw.create_wall({key: op[key] for key in fields if key in op})
        return CreateResult("ok", guid, {"guid": guid})
