"""
BIMEXEC v1 — capability probe (T0).

Назначение: эмпирически измерить, что реально умеет связка
Archicad 29 + адаптер, и выдать capability matrix, на основании которой
Executor либо разрешает операцию, либо отказывает.

Принципы:
  1. Матрица заполняется по ФАКТУ, а не по документации. В AC29 документация
     расходится с поведением (read-команды падают при работающем write).
  2. Обязательны НЕГАТИВНЫЕ КОНТРОЛИ: поиск несуществующего маркера обязан
     вернуть 0, а заведомо неверное ожидание — провалить верификацию.
     Без них «проверка прошла» ничего не доказывает.
  3. Fail closed: если write-фаза не выполнялась, marker binding остаётся
     UNCERTIFIED и Executor отказывает — а не «наверное работает».
"""
from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Protocol

PROBE_VERSION = "1.0"


class ProbeVerdict(str, Enum):
    CERTIFIED = "CERTIFIED"
    NOT_SUPPORTED = "NOT_SUPPORTED"
    FAILED = "FAILED"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


@dataclass
class ProbeCheck:
    name: str
    verdict: ProbeVerdict
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "verdict": self.verdict.value, "detail": self.detail}


# --- интерфейс «сырого» адаптера --------------------------------------------


class RawArchicad(Protocol):
    """Минимум, который должен уметь реальный адаптер (BIBIM / Tapir / MCP)."""

    def available_commands(self) -> set[str]: ...
    def project_info(self) -> dict[str, Any]: ...
    def stories(self) -> list[dict[str, Any]]: ...
    def count_by_type(self) -> dict[str, int]: ...
    def list_guids(self) -> list[str]: ...
    def details(self, guid: str) -> dict[str, Any] | None: ...
    def find_by_filter(self, type_: str, story_name: str, layer: str) -> list[str]: ...
    def get_marker(self, guid: str, medium: str) -> str | None: ...
    def find_by_marker(self, exact: str | None = None, prefix: str | None = None) -> list[str]: ...
    def set_marker(self, guid: str, value: str, medium: str) -> None: ...
    def create_wall(self, params: dict[str, Any]) -> str: ...


# --- probe ------------------------------------------------------------------


@dataclass
class ProbeConfig:
    allow_write: bool = False
    media: tuple[str, ...] = ("element_id", "property")
    story: dict[str, Any] = field(default_factory=lambda: {"name": "Ground Floor", "elevation": 0.0})
    layer: str = "A-WALL"
    # намеренно «некруглые» и попарно различные величины: ловят подмену осей,
    # знака и полей местами
    wall_from: tuple[float, float] = (1.5, 2.5)
    wall_to: tuple[float, float] = (6.5, 2.5)
    wall_height: float = 3.0
    wall_thickness: float = 0.30
    scratch_radius_check: bool = True


class Probe:
    def __init__(self, raw: RawArchicad, config: ProbeConfig | None = None) -> None:
        self.raw = raw
        self.cfg = config or ProbeConfig()
        self.checks: list[ProbeCheck] = []
        self.artifacts: list[dict[str, Any]] = []
        self.archicad: dict[str, Any] = {}
        self.adapter_meta: dict[str, Any] = {"commands_seen": 0}

    # -- helpers

    def _run(self, name: str, fn: Callable[[], ProbeCheck | dict[str, Any]]) -> ProbeCheck:
        """Ни одна проверка probe не должна ронять весь прогон."""
        try:
            res = fn()
            if isinstance(res, ProbeCheck):
                pc = res
            else:
                pc = ProbeCheck(name, ProbeVerdict.CERTIFIED, res)
        except NotImplementedError as e:
            pc = ProbeCheck(name, ProbeVerdict.NOT_SUPPORTED, {"error": str(e)})
        except Exception as e:  # fail closed: сбой = UNKNOWN, а не «поддерживается»
            pc = ProbeCheck(name, ProbeVerdict.UNKNOWN, {"error": f"{type(e).__name__}: {e}"})
        self.checks.append(pc)
        return pc

    @staticmethod
    def _verdict(name: str) -> ProbeVerdict:
        return ProbeVerdict(name)

    def _get(self, name: str) -> ProbeCheck | None:
        return next((c for c in self.checks if c.name == name), None)

    def _is(self, name: str, verdict: ProbeVerdict) -> bool:
        c = self._get(name)
        return c is not None and c.verdict is verdict

    # -- фаза A: read-only

    def _phase_readonly(self) -> None:
        def connection():
            cmds = self.raw.available_commands()
            self.adapter_meta["commands_seen"] = len(cmds)
            if not cmds:
                return ProbeCheck("connection", ProbeVerdict.FAILED, {"error": "no commands exposed"})
            return ProbeCheck("connection", ProbeVerdict.CERTIFIED, {"commands": len(cmds)})

        def project():
            info = self.raw.project_info()
            self.archicad = dict(info)
            problems = []
            if info.get("is_untitled"):
                problems.append("project is untitled: identity is not stable")
            if info.get("is_teamwork"):
                problems.append("Teamwork/BIMcloud: out of scope for v1")
            if not info.get("project_path"):
                problems.append("no project_path")
            return ProbeCheck(
                "project_identity",
                ProbeVerdict.CERTIFIED if not problems else ProbeVerdict.FAILED,
                {"info": info, "problems": problems},
            )

        def stories():
            s = self.raw.stories()
            if not s:
                return ProbeCheck("stories_read", ProbeVerdict.FAILED, {"error": "no stories"})
            bad = [x for x in s if not x.get("name") or x.get("elevation") is None]
            if bad:
                # имя+отметка обязательны: индекс как идентичность не годится
                return ProbeCheck("stories_read", ProbeVerdict.FAILED, {"stories": s, "bad": bad})
            return ProbeCheck("stories_read", ProbeVerdict.CERTIFIED, {"stories": s})

        def counts():
            c = self.raw.count_by_type()
            return ProbeCheck("count_by_type", ProbeVerdict.CERTIFIED, {"counts": c})

        def guids():
            g = self.raw.list_guids()
            return ProbeCheck("list_guids", ProbeVerdict.CERTIFIED, {"n": len(g)})

        def details():
            g = self.raw.list_guids()
            if not g:
                return ProbeCheck("details_by_guid", ProbeVerdict.NOT_SUPPORTED,
                                  {"error": "empty project: nothing to read"})
            d = self.raw.details(g[0])
            if not d:
                return ProbeCheck("details_by_guid", ProbeVerdict.FAILED, {"guid": g[0]})
            return ProbeCheck("details_by_guid", ProbeVerdict.CERTIFIED, {"fields": sorted(d)})

        def filt():
            hits = self.raw.find_by_filter("Wall", self.cfg.story["name"], self.cfg.layer)
            return ProbeCheck("find_by_filter", ProbeVerdict.CERTIFIED, {"hits": len(hits)})

        def medium_read():
            out = {}
            for m in self.cfg.media:
                try:
                    guids = self.raw.list_guids()
                    out[m] = self.raw.get_marker(guids[0], m) if guids else None
                    out[f"{m}_callable"] = True
                except NotImplementedError:
                    out[f"{m}_callable"] = False
                except Exception as e:
                    out[f"{m}_callable"] = False
                    out[f"{m}_error"] = str(e)
            return ProbeCheck("marker_medium_read", ProbeVerdict.CERTIFIED, out)

        def marker_search_exact():
            """НЕГАТИВНЫЙ КОНТРОЛЬ: поиск заведомо несуществующего маркера
            обязан вернуть ровно 0. Если вернул «всё» или упал — путь поиска
            непригоден, и весь binding-протокол не работает."""
            sentinel = f"BX:PROBE:NOPE:{uuid.uuid4().hex}"
            out: dict[str, Any] = {"sentinel": sentinel}
            try:
                hits = self.raw.find_by_marker(exact=sentinel)
            except NotImplementedError:
                return ProbeCheck("marker_search_exact", ProbeVerdict.NOT_SUPPORTED, out)
            except Exception as e:
                out["error"] = f"{type(e).__name__}: {e}"
                return ProbeCheck("marker_search_exact", ProbeVerdict.UNKNOWN, out)
            out["hits"] = len(hits)
            return ProbeCheck(
                "marker_search_exact",
                ProbeVerdict.CERTIFIED if len(hits) == 0 else ProbeVerdict.FAILED,
                out,
            )

        def marker_search_prefix():
            sentinel = f"BX:PROBE:NOPE:{uuid.uuid4().hex}:"
            out: dict[str, Any] = {"sentinel": sentinel}
            try:
                hits = self.raw.find_by_marker(prefix=sentinel)
            except NotImplementedError:
                return ProbeCheck("marker_search_prefix", ProbeVerdict.NOT_SUPPORTED, out)
            except Exception as e:
                out["error"] = f"{type(e).__name__}: {e}"
                return ProbeCheck("marker_search_prefix", ProbeVerdict.UNKNOWN, out)
            out["hits"] = len(hits)
            return ProbeCheck(
                "marker_search_prefix",
                ProbeVerdict.CERTIFIED if len(hits) == 0 else ProbeVerdict.FAILED,
                out,
            )

        for fn in (connection, project, stories, counts, guids, details, filt,
                   medium_read, marker_search_exact, marker_search_prefix):
            self._run(fn.__name__, fn)

    # -- фаза B: write (только в одноразовом проекте и только с явного согласия)

    def _phase_write(self) -> None:
        params = {
            "story": self.cfg.story,
            "layer": self.cfg.layer,
            "from": list(self.cfg.wall_from),
            "to": list(self.cfg.wall_to),
            "height": self.cfg.wall_height,
            "thickness": self.cfg.wall_thickness,
            "reference_line": "center",
            "base_level": 0.0,
            "top_link": "absolute",
        }

        before = self.raw.count_by_type()
        guid = None

        def create():
            nonlocal guid
            guid = self.raw.create_wall(params)
            if not guid:
                return ProbeCheck("create_wall", ProbeVerdict.FAILED, {"error": "no guid returned"})
            self.artifacts.append(
                {"guid": guid, "kind": "wall", "cleanup": "manual (undo or delete in Archicad)"}
            )
            return ProbeCheck("create_wall", ProbeVerdict.CERTIFIED, {"guid": guid})

        c = self._run("create_wall", create)
        if c.verdict is not ProbeVerdict.CERTIFIED or not guid:
            for nm in ("details_of_created", "count_delta", "marker_write_roundtrip",
                       "marker_search_hit", "verify_discriminates"):
                self.checks.append(ProbeCheck(nm, ProbeVerdict.SKIPPED, {"reason": "create failed"}))
            return

        def details_of_created():
            d = self.raw.details(guid)
            if not d:
                return ProbeCheck("details_of_created", ProbeVerdict.FAILED, {})
            need = {"type", "story", "layer", "ref_line", "height", "thickness", "length", "angle"}
            missing = sorted(need - set(d))
            return ProbeCheck(
                "details_of_created",
                ProbeVerdict.CERTIFIED if not missing else ProbeVerdict.FAILED,
                {"fields": sorted(d), "missing": missing, "details": d},
            )

        def count_delta():
            after = self.raw.count_by_type()
            delta = {k: after.get(k, 0) - before.get(k, 0) for k in set(after) | set(before)}
            ok = delta.get("Wall", 0) == 1
            return ProbeCheck(
                "count_delta",
                ProbeVerdict.CERTIFIED if ok else ProbeVerdict.FAILED,
                {"before": before, "after": after, "delta": delta},
            )

        def marker_roundtrip():
            """Главная проверка: write -> read -> строковое равенство.
            «Write вернул ok» в этом API не значит «записано»."""
            out: dict[str, Any] = {}
            certified_medium = None
            for m in self.cfg.media:
                value = f"BX:PROBE:{uuid.uuid4().hex}"
                try:
                    self.raw.set_marker(guid, value, m)
                    back = self.raw.get_marker(guid, m)
                    out[m] = {"wrote": value, "read_back": back, "equal": back == value}
                    if back == value and certified_medium is None:
                        certified_medium = m
                        break   # не перезаписываем маркер следующим носителем
                except NotImplementedError:
                    out[m] = {"supported": False}
                except Exception as e:
                    out[m] = {"error": f"{type(e).__name__}: {e}"}
            self.artifacts.append(
                {"guid": guid, "kind": "marker", "medium": certified_medium, "cleanup": "manual"}
            )
            out["certified_medium"] = certified_medium
            return ProbeCheck(
                "marker_write_roundtrip",
                ProbeVerdict.CERTIFIED if certified_medium else ProbeVerdict.FAILED,
                out,
            )

        def marker_hit():
            rt = self._get("marker_write_roundtrip")
            medium = (rt.detail or {}).get("certified_medium") if rt else None
            if not medium:
                return ProbeCheck("marker_search_hit", ProbeVerdict.SKIPPED, {"reason": "no medium"})
            value = (rt.detail or {}).get(medium, {}).get("wrote")
            hits_exact = self.raw.find_by_marker(exact=value)
            prefix_hits: list[str] | None = None
            if self._is("marker_search_prefix", ProbeVerdict.CERTIFIED):
                prefix_hits = list(self.raw.find_by_marker(prefix="BX:PROBE:"))
            ok = hits_exact == [guid]
            return ProbeCheck(
                "marker_search_hit",
                ProbeVerdict.CERTIFIED if ok else ProbeVerdict.FAILED,
                {
                    "exact": hits_exact,
                    "prefix_hits": len(prefix_hits) if prefix_hits is not None else None,
                    "expected": guid,
                },
            )

        def verify_discriminates():
            """НЕГАТИВНЫЙ КОНТРОЛЬ верификации: production-код обязан
            сказать OK на правильное ожидание и FAILED на сдвинутое."""
            from .verify import Capability, evaluate

            d = self.raw.details(guid) or {}
            cap = Capability(
                op="create_wall",
                exec_backend="probe",
                readable_fields={
                    "exists", "type", "story", "layer", "marker_exact",
                    "ref_line", "length", "height", "thickness", "angle", "count_delta",
                },
            )
            # спецификация той же формы, что в production: включает mandatory
            # floor целиком (marker_exact, ref_line, count_delta)
            rt = self._get("marker_write_roundtrip")
            medium = (rt.detail or {}).get("certified_medium") if rt else None
            marker_value = (rt.detail or {}).get(medium, {}).get("wrote") if medium else None

            spec = {
                "type": "Wall",
                "story": {"name": self.cfg.story["name"], "elevation": self.cfg.story["elevation"]},
                "layer": self.cfg.layer,
                "marker_exact": {"exact": marker_value} if marker_value else False,
                "ref_line": {
                    "from": list(self.cfg.wall_from),
                    "to": list(self.cfg.wall_to),
                    "tolerance": 0.01,
                },
                "height": {"expected": self.cfg.wall_height, "tolerance": 0.001},
                "thickness": {"expected": self.cfg.wall_thickness, "tolerance": 0.001},
                "length": {"expected": self._expected_length(), "tolerance": 0.05},
                "count_delta": {"Wall": 1},
            }
            obs = {k: v for k, v in d.items() if v is not None}
            obs["exists"] = True
            obs["marker"] = marker_value
            obs["count_delta"] = {"Wall": 1}
            obs["paths"] = ["guid", "filter", "marker", "count"]

            good, _ = evaluate({"op": "create_wall", "id": "PROBE"}, spec, obs, cap)
            bad_spec = json.loads(json.dumps(spec))
            bad_spec["height"] = {"expected": self.cfg.wall_height + 0.5, "tolerance": 0.001}
            worse, _ = evaluate({"op": "create_wall", "id": "PROBE"}, bad_spec, obs, cap)

            ok = good.value == "OK" and worse.value == "FAILED"
            return ProbeCheck(
                "verify_discriminates",
                ProbeVerdict.CERTIFIED if ok else ProbeVerdict.FAILED,
                {"on_correct": good.value, "on_wrong": worse.value,
                 "note": "expected OK / FAILED"},
            )

        for fn in (details_of_created, count_delta, marker_roundtrip, marker_hit, verify_discriminates):
            self._run(fn.__name__, fn)

    def _expected_length(self) -> float:
        (x1, y1), (x2, y2) = self.cfg.wall_from, self.cfg.wall_to
        return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    # -- запуск и сертификация

    def run(self) -> dict[str, Any]:
        self._phase_readonly()
        if self.cfg.allow_write:
            self._phase_write()
        else:
            for nm in ("create_wall", "details_of_created", "count_delta",
                       "marker_write_roundtrip", "marker_search_hit", "verify_discriminates"):
                self.checks.append(
                    ProbeCheck(nm, ProbeVerdict.SKIPPED,
                               {"reason": "write phase not enabled (--allow-write)"})
                )
        return self.report()

    def report(self) -> dict[str, Any]:
        by_name = {c.name: c for c in self.checks}
        rt = by_name.get("marker_write_roundtrip")
        medium = (rt.detail or {}).get("certified_medium") if rt else None

        prefix_ok = self._is("marker_search_prefix", ProbeVerdict.CERTIFIED)
        fallback_ok = self._is("count_by_type", ProbeVerdict.CERTIFIED) and self._is(
            "find_by_filter", ProbeVerdict.CERTIFIED
        )
        # без префиксного поиска дубли от прошлых запусков ловятся только
        # предусловием «пустая область» — оно требует count_by_type + фильтра
        dup_detection = "PREFIX" if prefix_ok else ("EMPTY_SCOPE_FALLBACK" if fallback_ok else "NONE")

        caps_certified = (
            self._is("connection", ProbeVerdict.CERTIFIED)
            and self._is("project_identity", ProbeVerdict.CERTIFIED)
            and self._is("stories_read", ProbeVerdict.CERTIFIED)
            and self._is("count_by_type", ProbeVerdict.CERTIFIED)
            and self._is("list_guids", ProbeVerdict.CERTIFIED)
            and self._is("details_of_created", ProbeVerdict.CERTIFIED)
            and self._is("find_by_filter", ProbeVerdict.CERTIFIED)
            and self._is("marker_search_exact", ProbeVerdict.CERTIFIED)
            and self._is("marker_write_roundtrip", ProbeVerdict.CERTIFIED)
            and self._is("marker_search_hit", ProbeVerdict.CERTIFIED)
            and self._is("verify_discriminates", ProbeVerdict.CERTIFIED)
            and self._is("count_delta", ProbeVerdict.CERTIFIED)
            and dup_detection != "NONE"
        )

        # readable_fields = поля из details + инфраструктурные проверки,
        # подтверждённые отдельными capability-проверками
        fields = set((by_name["details_of_created"].detail or {}).get("fields", [])
                     if "details_of_created" in by_name else [])
        if self._is("details_of_created", ProbeVerdict.CERTIFIED):
            fields.add("exists")
        if self._is("marker_search_exact", ProbeVerdict.CERTIFIED) and self._is(
            "marker_write_roundtrip", ProbeVerdict.CERTIFIED
        ):
            fields.add("marker_exact")
        if self._is("count_by_type", ProbeVerdict.CERTIFIED):
            fields.add("count_delta")

        backends = set()
        if self._is("details_of_created", ProbeVerdict.CERTIFIED):
            backends.add("GetDetailsOfElements")
        if self._is("find_by_filter", ProbeVerdict.CERTIFIED):
            backends.add("GetElementsByType")
        if medium:
            backends.add("PropertyAPI")

        capability = {
            "op": "create_wall",
            "exec_backend": self.adapter_meta.get("backend", "unknown"),
            "readback_backends": sorted(backends),
            "readable_fields": sorted(fields),
            "marker_medium": medium,
            "marker_search_exact": self._is("marker_search_exact", ProbeVerdict.CERTIFIED),
            "marker_search_prefix": prefix_ok,
            "duplicate_detection": dup_detection,
            "count_by_type": self._is("count_by_type", ProbeVerdict.CERTIFIED),
            "production_safe": bool(caps_certified),
            "probe_certified": bool(caps_certified),
            "adapter_version": self.adapter_meta.get("adapter_version", ""),
        }

        return {
            "probe_version": PROBE_VERSION,
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "archicad": self.archicad,
            "adapter": self.adapter_meta,
            "checks": [c.as_dict() for c in self.checks],
            "capabilities": {"create_wall": capability},
            "artifacts": self.artifacts,
            "verdicts": {
                "write_phase": "RUN" if self.cfg.allow_write else "SKIPPED",
                "certified": bool(caps_certified),
            },
        }


def render_text(report: dict[str, Any]) -> str:
    lines = [
        f"BIMEXEC capability probe {report['probe_version']} — {report['generated_at']}",
        f"Archicad: {report['archicad'].get('archicad_version', '?')} "
        f"build {report['archicad'].get('archicad_build', '?')}",
        f"Project:  {report['archicad'].get('project_path') or report['archicad'].get('project_name')}",
        "",
    ]
    for c in report["checks"]:
        mark = {
            "CERTIFIED": "OK  ",
            "NOT_SUPPORTED": "--  ",
            "FAILED": "FAIL",
            "UNKNOWN": "??? ",
            "SKIPPED": "skip",
        }[c["verdict"]]
        lines.append(f"  [{mark}] {c['name']}")
        if c["verdict"] in ("FAILED", "UNKNOWN"):
            lines.append(f"          {c['detail']}")
    lines.append("")
    cap = report["capabilities"]["create_wall"]
    lines.append(f"marker medium        : {cap['marker_medium'] or 'NONE'}")
    lines.append(f"duplicate detection  : {cap['duplicate_detection']}")
    lines.append(f"artifacts to clean up: {len(report['artifacts'])}")
    for a in report["artifacts"]:
        lines.append(f"   - {a}")
    lines.append("")
    lines.append(
        "CERTIFIED for production" if report["verdicts"]["certified"]
        else "NOT CERTIFIED — Executor will refuse to run"
    )
    return "\n".join(lines)
