"""
BIMEXEC v1 — сырой адаптер поверх официального Archicad Python/JSON API + Tapir.

ЧЕСТНО ПРО КОМАНДЫ: имена и схемы команд в экосистеме Archicad меняются от
версии к версии, а документация расходится с фактом. Поэтому:
  * COMMAND_NAMES — единственное место, где править имена под вашу сборку;
  * available_commands() ПРОВЕРЯЕТ read-only команды реальным вызовом,
    а не верит списку;
  * схемы write-команд (CreateWalls / SetPropertyValuesOfElements) помечены
    как TEMPLATE — их надо сверить с установленной версией Tapir до первого
    реального write. Probe это и проверяет.

Установка: pip install archicad (официальный пакет Graphisoft), в Archicad
должен быть включён JSON-интерфейс и установлен Tapir Add-On.
"""
from __future__ import annotations

from typing import Any

# --- ИМЕНА КОМАНД. Править здесь под вашу сборку. ---------------------------
COMMAND_NAMES = {
    "GetProjectInfo": ("official", "GetProjectInfo"),
    "GetAllElements": ("official", "GetAllElements"),
    "GetElementsByType": ("official", "GetElementsByType"),
    "GetDetailsOfElements": ("official", "GetDetailsOfElements"),
    "GetPropertyValuesOfElements": ("official", "GetPropertyValuesOfElements"),
    "SetPropertyValuesOfElements": ("official", "SetPropertyValuesOfElements"),
    "GetStories": ("tapir", "GetStories"),
    # Tapir: создание элементов. Если ваша сборка не имеет CreateWalls —
    # probe честно скажет NOT_SUPPORTED, и Executor откажет.
    "CreateWalls": ("tapir", "CreateWalls"),
}

BUILTIN_ELEMENT_ID = "General_ElementID"
CUSTOM_MARKER_PROPERTY = ("BIMEXEC", "BIMEXEC_MARKER")   # (group, name)

TEMPLATE_NOTE = (
    "payload schema is a TEMPLATE: confirm against the installed Tapir version "
    "before the first real write"
)


class AdapterUnavailable(RuntimeError):
    pass


class TapirRaw:
    """RawArchicad поверх ACConnection (+ Tapir Add-On)."""

    def __init__(self, port: int | None = None, types: tuple[str, ...] = ("Wall", "Slab")) -> None:
        self.port = port
        self.types = types
        self.conn = None
        self._available: set[str] = set()
        self._connect()

    # -- подключение ---------------------------------------------------------

    def _connect(self) -> None:
        try:
            from archicad import ACConnection  # type: ignore
        except ImportError as e:
            raise AdapterUnavailable(
                "package 'archicad' is not installed (pip install archicad)"
            ) from e
        try:
            self.conn = ACConnection.connect(self.port) if self.port else ACConnection.connect()
        except Exception as e:
            raise AdapterUnavailable(
                f"no running Archicad with JSON interface: {e}"
            ) from e
        if not self.conn:
            raise AdapterUnavailable("ACConnection.connect() returned nothing")

    def _cmd(self, logical: str):
        """Возвращает вызываемый объект команды по логическому имени."""
        kind, name = COMMAND_NAMES[logical]
        if kind == "official":
            return getattr(self.conn.commands, name)
        from archicad import ACConnection  # noqa: F401  (типы берутся из conn)

        act = self.conn.types
        return lambda params=None: self.conn.commands.ExecuteAddOnCommand(
            act.AddOnCommandId("TapirCommand", name), params or {}
        )

    # -- перечисление --------------------------------------------------------

    def available_commands(self) -> set[str]:
        """Проверяем read-only команды РЕАЛЬНЫМ вызовом. Write-команды не
        трогаем: вызов ради проверки уже был бы мутацией."""
        if self._available:
            return self._available
        found: set[str] = set()
        for logical in ("GetProjectInfo", "GetAllElements", "GetElementsByType",
                        "GetDetailsOfElements", "GetPropertyValuesOfElements", "GetStories"):
            try:
                fn = self._cmd(logical)
                if logical == "GetElementsByType":
                    fn({"elementType": "Wall"})
                elif logical == "GetDetailsOfElements":
                    fn({"elements": []})
                elif logical == "GetPropertyValuesOfElements":
                    fn({"elements": [], "properties": []})
                else:
                    fn()
                found.add(logical)
            except Exception:
                pass
        # write-команды декларируем по наличию имени в таблице; фактическая
        # проверка происходит в write-фазе probe
        for logical in ("SetPropertyValuesOfElements", "CreateWalls"):
            try:
                self._cmd(logical)
                found.add(logical)
            except Exception:
                pass
        self._available = found
        return found

    # -- read ----------------------------------------------------------------

    def project_info(self) -> dict[str, Any]:
        info = self._cmd("GetProjectInfo")()
        d = _to_dict(info)
        return {
            "port": self.port,
            "project_path": d.get("projectPath") or d.get("projectLocation"),
            "project_name": d.get("projectName"),
            "is_untitled": bool(d.get("isUntitled")),
            "is_teamwork": bool(d.get("isTeamwork")),
            "archicad_version": d.get("archicadVersion") or "",
            "archicad_build": d.get("archicadBuild") or "",
        }

    def stories(self) -> list[dict[str, Any]]:
        fn = self._cmd("GetStories")
        res = _to_dict(fn())
        out = []
        for s in res.get("stories", []) or []:
            sd = _to_dict(s)
            out.append({"name": sd.get("name"), "elevation": _elevation(sd)})
        return out

    def count_by_type(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.types:
            try:
                els = self._cmd("GetElementsByType")({"elementType": t}) or []
                out[t] = len(els)
            except Exception:
                out[t] = 0
        return out

    def list_guids(self) -> list[str]:
        els = self._cmd("GetAllElements")() or []
        return [_guid(e) for e in els]

    def details(self, guid: str) -> dict[str, Any] | None:
        act = self.conn.types
        el = act.ElementId(guid) if hasattr(act, "ElementId") else guid
        res = self._cmd("GetDetailsOfElements")({"elements": [el]})
        items = _to_dict(res).get("details") or _to_dict(res).get("elements") or []
        if not items:
            return None
        d = _to_dict(items[0])
        return _normalize_details(d)

    def find_by_filter(self, type_: str, story_name: str, layer: str) -> list[str]:
        els = self._cmd("GetElementsByType")({"elementType": type_}) or []
        guids = [_guid(e) for e in els]
        out = []
        for g in guids:
            d = self.details(g) or {}
            if d.get("layer") == layer and (d.get("story") or {}).get("name") == story_name:
                out.append(g)
        return out

    # -- marker --------------------------------------------------------------

    def _property_id(self, medium: str):
        acu = self.conn.utilities
        if medium == "element_id":
            try:
                return acu.GetBuiltInPropertyId(BUILTIN_ELEMENT_ID)
            except Exception as e:
                raise NotImplementedError(f"builtin property {BUILTIN_ELEMENT_ID}: {e}") from e
        if medium == "property":
            group, name = CUSTOM_MARKER_PROPERTY
            try:
                return acu.GetUserDefinedPropertyId(group, name)
            except Exception as e:
                raise NotImplementedError(
                    f"user-defined property '{group}/{name}' is not available. "
                    f"Официальный JSON API НЕ умеет создавать свойства — их нужно "
                    f"создать один раз вручную или через Add-On."
                ) from e
        raise NotImplementedError(f"unknown medium {medium}")

    def get_marker(self, guid: str, medium: str) -> str | None:
        act = self.conn.types
        pid = self._property_id(medium)
        el = act.ElementId(guid)
        res = self.conn.commands.GetPropertyValuesOfElements([el], [pid])
        rows = _to_dict(res) or []
        if not rows:
            return None
        vals = _to_dict(rows[0]).get("propertyValues") or []
        if not vals:
            return None
        v = _to_dict(vals[0]).get("propertyValue")
        return _to_dict(v).get("value")

    def find_by_marker(self, exact: str | None = None, prefix: str | None = None) -> list[str]:
        """Сканирование по свойству. O(n), но не зависит от наличия
        поисковой команды в адаптере."""
        if prefix is None and exact is None:
            return []
        out: list[str] = []
        for medium in ("element_id", "property"):
            try:
                pid = self._property_id(medium)
            except NotImplementedError:
                continue
            guids = self.list_guids()
            act = self.conn.types
            els = [act.ElementId(g) for g in guids]
            res = self.conn.commands.GetPropertyValuesOfElements(els, [pid]) or []
            for row in res:
                rd = _to_dict(row)
                for pv in rd.get("propertyValues") or []:
                    val = _to_dict(_to_dict(pv).get("propertyValue")).get("value")
                    if not isinstance(val, str):
                        continue
                    if exact is not None and val == exact:
                        out.append(_guid(rd))
                    elif prefix is not None and val.startswith(prefix):
                        out.append(_guid(rd))
        return sorted(set(out))

    def set_marker(self, guid: str, value: str, medium: str) -> None:
        act = self.conn.types
        pid = self._property_id(medium)
        el = act.ElementId(guid)
        pv = act.NormalStringPropertyValue(value, type="string", status="normal")
        self.conn.commands.SetPropertyValuesOfElements([act.ElementPropertyValue(el, pid, pv)])

    # -- write (TEMPLATE) ----------------------------------------------------

    def create_wall(self, params: dict[str, Any]) -> str:
        """TEMPLATE: схема CreateWalls зависит от версии Tapir."""
        if "CreateWalls" not in self.available_commands():
            raise NotImplementedError("CreateWalls is not exposed by this adapter build")
        payload = {
            "walls": [
                {
                    "coordinates": {
                        "begCoordinate": {"x": params["from"][0], "y": params["from"][1]},
                        "endCoordinate": {"x": params["to"][0], "y": params["to"][1]},
                    },
                    "storyIndex": params.get("story_index", 0),
                    "height": params["height"],
                    "thickness": params["thickness"],
                    "layerName": params.get("layer"),
                    # TEMPLATE_NOTE
                }
            ]
        }
        res = _to_dict(self._cmd("CreateWalls")(payload))
        items = res.get("elements") or res.get("walls") or []
        if not items:
            raise AdapterUnavailable(f"CreateWalls returned no elements ({TEMPLATE_NOTE})")
        return _guid(items[0])


# --- утилиты приведения ответов --------------------------------------------


def _to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    for attr in ("to_dict", "dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                return fn()
            except Exception:
                pass
    d = getattr(obj, "__dict__", None)
    return dict(d) if isinstance(d, dict) else {}


def _guid(obj: Any) -> str:
    d = _to_dict(obj)
    g = d.get("guid") or d.get("elementId") or d.get("id")
    if isinstance(g, dict):
        g = g.get("guid")
    if g is None:
        g = getattr(obj, "guid", None)
    return str(g)


def _elevation(story: dict[str, Any]) -> float | None:
    for key in ("elevation", "level", "height"):
        if key in story and story[key] is not None:
            return float(story[key])
    return None


def _normalize_details(d: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    t = d.get("type") or d.get("elementType")
    if isinstance(t, dict):
        t = t.get("type") or t.get("elementType")
    if t:
        out["type"] = str(t)

    gen = d.get("general") or {}
    layer = _nested(gen, "layer", "name") or d.get("layerName")
    if layer:
        out["layer"] = str(layer)

    story = _nested(gen, "story", "name") or d.get("storyName")
    if story:
        out["story"] = {"name": str(story), "elevation": None}

    wl = d.get("wall") or d.get("wallDetails") or d.get("typeSpecificDetails") or {}
    geom = wl.get("geometry") or wl
    beg, end = geom.get("begCoordinate"), geom.get("endCoordinate")
    if beg and end:
        out["ref_line"] = {
            "from": [float(beg["x"]), float(beg["y"])],
            "to": [float(end["x"]), float(end["y"])],
        }
        dx = float(end["x"]) - float(beg["x"])
        dy = float(end["y"]) - float(beg["y"])
        out["length"] = (dx * dx + dy * dy) ** 0.5
        import math

        out["angle"] = math.degrees(math.atan2(dy, dx))
    for key_src, key_dst in (("height", "height"), ("thickness", "thickness")):
        v = wl.get(key_src)
        if v is not None:
            try:
                out[key_dst] = float(v)
            except (TypeError, ValueError):
                pass
    return out


def _nested(d: dict[str, Any], *path: str) -> Any:
    cur: Any = d
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur
