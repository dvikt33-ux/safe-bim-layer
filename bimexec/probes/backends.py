r"""
BIMEXEC — pluggable backends для T0A / T0B.

ОБНОВЛЕНО по локальной инвентаризации от 2026-09-26:

  * Archicad 29, пакет archicad==29.3000
  * archicad-mcp-server==0.6.0 (режимы verdicts/full), multiconn-archicad==0.8.4,
    fastmcp==3.4.7, mcp==1.30.0
  * MCP endpoint: http://127.0.0.1:8001/mcp ; Archicad JSON API port: 19723
  * Tapir command definitions подтверждены локально; payload shapes взяты
    из установленных definitions, а не из догадок.

Ключевые отличия от прежней версии этого файла:
  1. MCP-клиент переписан: настоящий MCP streamable HTTP (initialize с
     заголовком Accept: application/json, text/event-stream, перебор версий
     протокола, Mcp-Session-Id, notifications/initialized, tools/list,
     tools/call, разбор SSE). Прежний «POST /call» для MCP неверен —
     именно поэтому initialize отдавал 400.
  2. Tapir payload shapes приведены к подтверждённым:
     GetElementsByType {"elementType":...}, GetDetailsOfElements
     {"elements":[{"guid":...}],"fields":[...]},
     properties {"elements":[{"guid":...}],"properties":[{"propertyId":{"guid":...}}]},
     API.GetAttributesByType {"attributeType":"Layer"},
     API.GetLayerAttributes {"attributeIds":[{"index":1}]}
  3. Нормализация details переписана под фактический ответ Tapir:
     type / id / floorIndex / layerIndex / drawIndex / hotlinkId /
     type-specific details / floorPlanPolygons. Имени этажа и имени слоя
     в ответе НЕТ — они резолвятся отдельно (см. resolve_story/layer_index).
  4. Слой читается как property ModelView_LayerName (имя напрямую), а не
     через layerIndex.
  5. Поиск по маркеру — только клиентский скан + сравнение (server-side
     prefix search в Tapir не найден).

ОБНОВЛЕНО по ЖИВОМУ прогону на Windows (2026-09-26, Archicad 29):

  * официального `commands.GetProjectInfo` НЕ СУЩЕСТВУЕТ (проверено:
    hasattr(...) == False). Есть `commands.GetProductInfo` и
    `commands.ExecuteAddOnCommand`.
  * поэтому доступность и поля проекта берутся из read-only Tapir
    `GetProjectInfo` (ExecuteAddOnCommand('TapirCommand','GetProjectInfo'));
    версия/сборка — опционально из official `GetProductInfo`.
    Отсутствие official GetProjectInfo НЕ делает бэкенд недоступным.
  * live-значения: порт 19723 отвечает, проект
    C:\Users\Admin\Downloads\MCP_TEST.pln, Tapir add-on 1.5.9,
    GetStories отдаёт {index, level, name} (level → elevation).
  * интерпретатор, в котором установлен archicad==29.3000:
    C:\Users\Admin\AppData\Roaming\uv\tools\archicad-mcp-server\Scripts\python.exe

НИ ОДИН метод здесь не пишет в модель, кроме set_property_value(),
который используется ТОЛЬКО в T0B.
"""
from __future__ import annotations

import abc
import importlib.util
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any

# --- адреса свойств ---------------------------------------------------------

LAYER_PROPERTY = "ModelView_LayerName"

# Кандидаты адреса «Element ID». Локально не подтверждено ни одного —
# T0A перебирает их и фиксирует, какой сработал.
ELEMENT_ID_CANDIDATES: list[dict[str, str]] = [
    {"kind": "builtin", "id": "General_ElementID"},
    {"kind": "name", "address": "General_ElementID"},
    {"kind": "name", "address": "General/Element ID"},
    {"kind": "name", "address": "Element ID"},
    {"kind": "name", "address": "BuiltIn/General_ElementID"},
]

CUSTOM_MARKER_GROUP = "BIMEXEC"
CUSTOM_MARKER_NAME = "BIMEXEC_MARKER"


def custom_marker_ref() -> dict[str, str]:
    return {"kind": "user", "group": CUSTOM_MARKER_GROUP, "name": CUSTOM_MARKER_NAME}


def custom_marker_address() -> str:
    return f"{CUSTOM_MARKER_GROUP}/{CUSTOM_MARKER_NAME}"


def ref_label(ref: dict[str, Any]) -> str:
    kind = ref.get("kind")
    if kind == "builtin":
        return f"builtin:{ref.get('id')}"
    if kind == "user":
        return f"user:{ref.get('group')}/{ref.get('name')}"
    if kind == "name":
        return f"name:{ref.get('address')}"
    if kind == "guid":
        return f"guid:{ref.get('guid')}"
    return str(ref)


# --- контракт ---------------------------------------------------------------


class BackendError(RuntimeError):
    """Сбой вызова. НИКОГДА не трактуется как «не применено»."""


class Backend(abc.ABC):
    name = "abstract"

    @abc.abstractmethod
    def available(self) -> tuple[bool, str]: ...

    @abc.abstractmethod
    def project_info(self) -> dict[str, Any]: ...

    @abc.abstractmethod
    def stories(self) -> list[dict[str, Any]]:
        """[{'index': int|None, 'name': str, 'elevation': float|None}]"""

    @abc.abstractmethod
    def all_elements(self) -> list[str]: ...

    @abc.abstractmethod
    def elements_by_type(self, element_type: str) -> list[str]: ...

    @abc.abstractmethod
    def count_by_type(self) -> dict[str, int]: ...

    @abc.abstractmethod
    def details_raw(self, guid: str) -> dict[str, Any] | None:
        """СЫРОЙ ответ — без нормализации. Нужен, чтобы увидеть фактуру."""

    @abc.abstractmethod
    def details(self, guid: str) -> dict[str, Any] | None:
        """Нормализованный: type, element_id, floor_index, layer_index,
        layer_name, ref_line{from,to}, length, angle, height, thickness."""

    @abc.abstractmethod
    def get_property_values(self, ref: dict[str, Any], guids: list[str]) -> dict[str, Any | None]: ...

    @abc.abstractmethod
    def set_property_value(self, guid: str, ref: dict[str, Any], value: str) -> None: ...

    def tools_list(self) -> list[str]:
        return []

    def raw_call(self, command: str, payload: dict[str, Any] | None = None) -> Any:
        """Произвольный read-only вызов по имени команды Tapir."""
        raise BackendError("raw_call not supported by this backend")

    def resolve_property_id(self, ref: dict[str, Any]) -> Any:
        raise BackendError("resolve_property_id not supported by this backend")


# --- MCP streamable HTTP клиент ---------------------------------------------


class McpClient:
    """Минимальный MCP-клиент поверх streamable HTTP.

    Порядок, который ожидает сервер:
      POST /mcp  {"method":"initialize", ...}
        заголовки: Content-Type: application/json
                   Accept: application/json, text/event-stream
      -> ответ JSON или SSE; в заголовке может прийти Mcp-Session-Id
      POST {"method":"notifications/initialized"}   (без id)
      POST {"method":"tools/list"}
      POST {"method":"tools/call","params":{"name":...,"arguments":{...}}}
    """

    PROTO_VERSIONS = ("2025-06-18", "2025-03-26", "2024-11-05")

    def __init__(self, url: str, timeout: float = 15.0) -> None:
        self.url = url.rstrip("/")
        self.timeout = timeout
        self.session_id: str | None = None
        self.protocol_version: str | None = None
        self.server_info: dict[str, Any] = {}
        self._id = 0
        self.last_error: str | None = None

    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _post(self, payload: dict[str, Any]) -> dict[str, Any] | None:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.session_id:
            headers["Mcp-Session-Id"] = self.session_id
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                ctype = (r.headers.get("Content-Type") or "").lower()
                sid = r.headers.get("Mcp-Session-Id")
                if sid:
                    self.session_id = sid
                body = r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            detail = ""
            try:
                detail = e.read().decode("utf-8", "replace")[:400]
            except Exception:
                pass
            self.last_error = f"HTTP {e.code} {e.reason}: {detail}"
            raise BackendError(self.last_error) from e
        except Exception as e:
            self.last_error = f"{type(e).__name__}: {e}"
            raise BackendError(self.last_error) from e

        if "text/event-stream" in ctype:
            return _sse_last_json(body)
        body = body.strip()
        return json.loads(body) if body else None

    def initialize(self) -> dict[str, Any]:
        errors: list[str] = []
        for ver in self.PROTO_VERSIONS:
            try:
                res = self._post({
                    "jsonrpc": "2.0",
                    "id": self._next_id(),
                    "method": "initialize",
                    "params": {
                        "protocolVersion": ver,
                        "capabilities": {},
                        "clientInfo": {"name": "bimexec-probe", "version": "1.0"},
                    },
                })
            except BackendError as e:
                errors.append(f"{ver}: {e}")
                continue
            if isinstance(res, dict) and res.get("error"):
                errors.append(f"{ver}: {res['error']}")
                continue
            self.protocol_version = ver
            result = res.get("result", {}) if isinstance(res, dict) else {}
            self.server_info = result.get("serverInfo", {}) or {}
            self._post({"jsonrpc": "2.0", "method": "notifications/initialized"})
            return result
        raise BackendError("initialize failed: " + " | ".join(errors))

    def tools_list(self) -> list[dict[str, Any]]:
        res = self._post({"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/list"})
        if isinstance(res, dict) and res.get("error"):
            raise BackendError(f"tools/list: {res['error']}")
        return ((res or {}).get("result") or {}).get("tools", []) or []

    def call(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        _assert_not_forbidden(name)
        res = self._post({
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": name, "arguments": arguments or {}},
        })
        if isinstance(res, dict) and res.get("error"):
            raise BackendError(f"tools/call {name}: {res['error']}")
        return (res or {}).get("result")


def _sse_last_json(body: str) -> dict[str, Any] | None:
    """Из SSE-потока берём последний валидный JSON из data:-строк."""
    out: dict[str, Any] | None = None
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        payload = line[5:].strip()
        if not payload or payload == "[DONE]":
            continue
        try:
            obj = json.loads(payload)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict) and ("result" in obj or "error" in obj):
            out = obj
    return out


# --- Tapir / official JSON --------------------------------------------------

TAPIR_READ_COMMANDS = [
    "GetAddOnVersion",
    "GetProjectInfo",
    "GetStories",
    "GetAllElements",
    "GetElementsByType",
    "GetDetailsOfElements",
    "GetPropertyValuesOfElements",
    "API.GetPropertyIds",
    "API.GetPropertyValuesOfElements",
    "API.GetAttributesByType",
    "API.GetLayerAttributes",
]

# T0B пишет ТОЛЬКО значения свойства. Ниже — команды, которые этот комплект
# НИКОГДА не вызывает: CreateWalls/create_wall запрещён до результатов T0B и
# явного отдельного решения. Список — не «разрешённые», а ЗАПРЕЩЁННЫЕ:
# try_command() жёстко отказывает по FORBIDDEN_COMMANDS.
FORBIDDEN_COMMANDS = frozenset({
    "CreateWalls",
    "CreateSlabs",
    "CreateColumns",
    "CreateZones",
    "CreateObjects",
    "DeleteElements",
    "MoveElements",
    "RotateElements",
    "ChangeSelection",
    "SetSelection",
})

DEFAULT_TYPES = ("Wall", "Slab", "Window", "Door", "Column", "Zone")


def _assert_not_forbidden(name: str) -> None:
    """Жёсткий предохранитель. Создание/удаление/перемещение геометрии и
    работа с selection в этом комплекте запрещены: T0A read-only, T0B пишет
    только значения свойств одного тестового элемента."""
    if name in FORBIDDEN_COMMANDS:
        raise BackendError(
            f"command {name!r} is FORBIDDEN in this kit "
            f"(no create_wall / delete / move / selection)"
        )


class TapirBackend(Backend):
    """Официальный пакет archicad (ACConnection) + Tapir Add-On.

    Payload shapes — по подтверждённым локальным definitions.
    """

    name = "tapir"

    def __init__(self, port: int | None = None,
                 types: tuple[str, ...] = DEFAULT_TYPES,
                 tapir_namespace: str = "TapirCommand") -> None:
        self.port = port
        self.types = types
        self.ns = tapir_namespace
        self.conn = None
        self._addon_version: str | None = None

    # подключение

    def _connect(self) -> None:
        if self.conn is not None:
            return
        try:
            from archicad import ACConnection  # type: ignore
        except ImportError as e:
            raise BackendError("package 'archicad' is not installed") from e
        try:
            self.conn = ACConnection.connect(self.port) if self.port else ACConnection.connect()
        except Exception as e:
            raise BackendError(f"no Archicad on port {self.port or 'default'}: {e}") from e
        if not self.conn:
            raise BackendError("ACConnection.connect() returned nothing")

    def _official(self, name: str):
        _assert_not_forbidden(name)
        self._connect()
        return getattr(self.conn.commands, name)

    def _tapir(self, name: str):
        _assert_not_forbidden(name)
        self._connect()
        act = self.conn.types
        return lambda params=None: self.conn.commands.ExecuteAddOnCommand(
            act.AddOnCommandId(self.ns, name), params if params is not None else {}
        )

    def available(self) -> tuple[bool, str]:
        """Доступность = отвечает read-only Tapir `GetProjectInfo`.

        Проверено на Archicad 29 / archicad==29.3000: официального
        `commands.GetProjectInfo` НЕ существует (есть `GetProductInfo`), поэтому
        official-вызов здесь использовать нельзя — иначе бэкенд ложно
        считается недоступным. Отсутствие official-команд версионирования
        не влияет на доступность.
        """
        try:
            self._connect()
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
        try:
            d = _to_dict(self._tapir("GetProjectInfo")())
        except Exception as e:
            return False, f"Tapir GetProjectInfo failed: {type(e).__name__}: {e}"
        if not d:
            return False, "Tapir GetProjectInfo вернул пустой ответ"
        version = self.addon_version()
        tail = f"; Tapir add-on {version}" if version else ""
        return True, f"Tapir GetProjectInfo OK (port={self.port}){tail}"

    # read

    def project_info(self) -> dict[str, Any]:
        """Поля проекта — из Tapir `GetProjectInfo` (read-only, подтверждено live).

        Версия и сборка Archicad берутся отдельно, через official
        `GetProductInfo`; если его нет — поля остаются пустыми, но бэкенд
        остаётся доступным.
        """
        d = _to_dict(self._tapir("GetProjectInfo")())
        if not d:
            raise BackendError("Tapir GetProjectInfo вернул пустой ответ")
        return {
            "project_path": d.get("projectPath") or d.get("projectLocation"),
            "project_name": d.get("projectName"),
            "is_untitled": bool(d.get("isUntitled")),
            "is_teamwork": bool(d.get("isTeamwork")),
            "archicad_version": self._product_info("version", "archicadVersion"),
            "archicad_build": self._product_info("build", "buildNumber"),
            "port": self.port,
            "instance_hint": f"port={self.port}",
        }

    def _product_info(self, *keys: str) -> str:
        """Official GetProductInfo — best effort. Его отсутствие НЕ ошибка."""
        try:
            d = _to_dict(self._official("GetProductInfo")())
        except Exception:
            return ""
        for k in keys:
            v = d.get(k)
            if v not in (None, ""):
                return str(v)
        return ""

    def stories(self) -> list[dict[str, Any]]:
        """GetStories. Возвращаем index, чтобы потом сопоставить с floorIndex.

        Live-форма (AC29, Tapir 1.5.9): элементы несут `index`, `name`, `level`;
        `level` → `elevation`. Список ищем по известным ключам, а если их нет —
        берём первый подходящий список сверху, чтобы не потерять этажи из-за
        имени ключа.
        """
        try:
            res = _to_dict(self._tapir("GetStories")())
        except Exception as e:
            raise BackendError(f"GetStories failed: {e}") from e
        raw = res.get("stories") or res.get("storyList")
        if raw is None:
            for v in res.values():
                if isinstance(v, list) and v and isinstance(v[0], (dict,)):
                    if any(k in _to_dict(v[0]) for k in ("index", "level", "name")):
                        raw = v
                        break
        out: list[dict[str, Any]] = []
        for i, s in enumerate(raw or []):
            sd = _to_dict(s)
            idx = sd.get("index", sd.get("floorIndex", i))
            out.append({
                "index": idx,
                "name": sd.get("name"),
                "elevation": _fnum(sd.get("elevation", sd.get("level"))),
            })
        return out

    def all_elements(self) -> list[str]:
        els = self._official("GetAllElements")() or []
        return [_guid(e) for e in els]

    def elements_by_type(self, element_type: str) -> list[str]:
        # подтверждённый payload: {"elementType": ...}; filters/databases опциональны
        els = self._tapir("GetElementsByType")({"elementType": element_type}) or []
        return [_guid(e) for e in _as_list(els)]

    def count_by_type(self) -> dict[str, int]:
        out: dict[str, int] = {}
        for t in self.types:
            try:
                out[t] = len(self.elements_by_type(t))
            except Exception:
                out[t] = -1      # -1 = команда не ответила, а не «ноль элементов»
        return out

    def details_raw(self, guid: str) -> dict[str, Any] | None:
        payload = {"elements": [{"guid": guid}]}
        res = self._tapir("GetDetailsOfElements")(payload)
        items = _as_list(_to_dict(res).get("details") or res)
        if not items:
            return None
        return _to_dict(items[0])

    def details(self, guid: str) -> dict[str, Any] | None:
        raw = self.details_raw(guid)
        if raw is None:
            return None
        return _normalize_tapir_details(raw)

    # properties

    def resolve_property_id(self, ref: dict[str, Any]) -> Any:
        self._connect()
        kind = ref.get("kind")
        try:
            if kind == "builtin":
                return self.conn.utilities.GetBuiltInPropertyId(ref["id"])
            if kind == "user" or kind == "name":
                address = ref.get("address") or f"{ref.get('group')}/{ref.get('name')}"
                return self._property_id_by_address(address)
            if kind == "guid":
                return {"guid": ref["guid"]}
        except Exception as e:
            raise BackendError(f"resolve_property_id({ref_label(ref)}): {e}") from e
        raise BackendError(f"unknown property ref kind: {kind}")

    def _property_id_by_address(self, address: str) -> Any:
        """MCP-путь: адрес вида 'Group/Name' -> propertyId через API.GetPropertyIds."""
        res = self._tapir("API.GetPropertyIds")({"propertyIds": [{"address": address}]})
        d = _to_dict(res)
        items = _as_list(d.get("propertyIds") or d.get("properties") or d.get("result"))
        if not items:
            raise BackendError(f"API.GetPropertyIds: no id for address '{address}'")
        first = _to_dict(items[0])
        pid = first.get("propertyId") or first
        if isinstance(pid, dict) and not pid.get("guid") and not pid.get("localizedName"):
            raise BackendError(f"API.GetPropertyIds: empty id for '{address}' ({first})")
        return pid

    def get_property_values(self, ref: dict[str, Any], guids: list[str]) -> dict[str, Any | None]:
        self._connect()
        pid = self.resolve_property_id(ref)
        out: dict[str, Any | None] = {}
        # подтверждённый payload: {"elements":[{"guid":...}],"properties":[{"propertyId":{...}}]}
        payload = {
            "elements": [{"guid": g} for g in guids],
            "properties": [{"propertyId": pid if isinstance(pid, dict) else _to_dict(pid)}],
        }
        res = self._tapir("GetPropertyValuesOfElements")(payload)
        rows = _as_list(_to_dict(res).get("properties") or _to_dict(res).get("result") or res)
        for row in rows:
            rd = _to_dict(row)
            g = rd.get("elementId") or rd.get("element") or {}
            if isinstance(g, dict):
                g = g.get("guid") or g.get("elementId")
            vals = rd.get("propertyValues") or []
            v = None
            if vals:
                vd = _to_dict(vals[0])
                vv = vd.get("propertyValue") if "propertyValue" in vd else vd
                v = _to_dict(vv).get("value")
            if g:
                out[str(g)] = v
        for g in guids:
            out.setdefault(g, None)
        return out

    def set_property_value(self, guid: str, ref: dict[str, Any], value: str) -> None:
        """T0B only."""
        self._connect()
        act = self.conn.types
        pid = self.resolve_property_id(ref)
        payload = {
            "elements": [{"guid": guid}],
            "properties": [{"propertyId": pid if isinstance(pid, dict) else _to_dict(pid)}],
            "values": [[{"value": value}]],
        }
        self._tapir("API.SetPropertyValuesOfElements")(payload)

    def raw_call(self, command: str, payload: dict[str, Any] | None = None) -> Any:
        return self._tapir(command)(payload or {})

    def addon_version(self) -> str | None:
        try:
            res = _to_dict(self._tapir("GetAddOnVersion")())
            return str(res.get("version") or res.get("addOnVersion") or "")
        except Exception:
            return None


# --- MCP backend ------------------------------------------------------------


class McpBackend(Backend):
    """Работа через MCP-сервер (archicad-mcp-server 0.6.0, режим full).

    Read-only инструменты, которые мы используем:
      list_instances, get_project_info, get_model_summary, find_elements,
      get_element_data, search_definitions, list_attributes, get_selection
    """

    name = "mcp"

    def __init__(self, base_url: str = "http://127.0.0.1:8001/mcp", timeout: float = 15.0) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.client = McpClient(base_url, timeout)
        self._tools: list[str] | None = None

    def _ensure(self) -> McpClient:
        if self.client.protocol_version is None:
            self.client.initialize()
        return self.client

    def available(self) -> tuple[bool, str]:
        try:
            self._ensure()
            return True, (f"MCP {self.base_url} proto={self.client.protocol_version} "
                          f"server={self.client.server_info.get('name')}")
        except Exception as e:
            return False, str(e)

    def tools_list(self) -> list[str]:
        c = self._ensure()
        tools = c.tools_list()
        self._tools = [t.get("name") for t in tools if t.get("name")]
        return self._tools

    def project_info(self) -> dict[str, Any]:
        c = self._ensure()
        d = _unwrap(c.call("get_project_info", {}))
        return {
            "project_path": d.get("projectPath") or d.get("projectLocation") or d.get("path"),
            "project_name": d.get("projectName") or d.get("name"),
            "is_untitled": bool(d.get("isUntitled")),
            "is_teamwork": bool(d.get("isTeamwork")),
            "archicad_version": str(d.get("archicadVersion") or ""),
            "archicad_build": str(d.get("archicadBuild") or ""),
            "port": None,
            "instance_hint": self.base_url,
        }

    def list_instances(self) -> list[dict[str, Any]]:
        c = self._ensure()
        d = _unwrap(c.call("list_instances", {}))
        items = _as_list(d.get("instances") or d.get("archicads") or d)
        return [_to_dict(i) for i in items]

    def stories(self) -> list[dict[str, Any]]:
        d = _unwrap(self._ensure().call("get_project_info", {}))
        raw = _as_list(d.get("stories") or [])
        out = []
        for i, s in enumerate(raw):
            sd = _to_dict(s)
            out.append({"index": sd.get("index", i), "name": sd.get("name"),
                        "elevation": _fnum(sd.get("elevation", sd.get("level")))})
        return out

    def all_elements(self) -> list[str]:
        d = _unwrap(self._ensure().call("find_elements", {"limit": 100000}))
        return [_guid(e) for e in _as_list(d.get("elements") or d)]

    def elements_by_type(self, element_type: str) -> list[str]:
        d = _unwrap(self._ensure().call(
            "find_elements", {"elementType": element_type, "limit": 100000}))
        return [_guid(e) for e in _as_list(d.get("elements") or d)]

    def count_by_type(self) -> dict[str, int]:
        out = {}
        for t in DEFAULT_TYPES:
            try:
                out[t] = len(self.elements_by_type(t))
            except Exception:
                out[t] = -1
        return out

    def details_raw(self, guid: str) -> dict[str, Any] | None:
        d = _unwrap(self._ensure().call("get_element_data", {"elements": [guid]}))
        items = _as_list(d.get("elements") or d.get("details") or d)
        return _to_dict(items[0]) if items else None

    def details(self, guid: str) -> dict[str, Any] | None:
        raw = self.details_raw(guid)
        return _normalize_tapir_details(raw) if raw else None

    def get_property_values(self, ref: dict[str, Any], guids: list[str]) -> dict[str, Any | None]:
        address = ref.get("address")
        if not address:
            if ref.get("kind") == "user":
                address = f"{ref.get('group')}/{ref.get('name')}"
            elif ref.get("kind") == "builtin":
                address = ref["id"]
        d = _unwrap(self._ensure().call(
            "get_element_data", {"elements": guids, "properties": [address]}))
        out: dict[str, Any | None] = {g: None for g in guids}
        for row in _as_list(d.get("elements") or d):
            rd = _to_dict(row)
            g = _guid(rd) or rd.get("guid")
            props = rd.get("properties") or {}
            val = None
            if isinstance(props, dict):
                val = props.get(address)
            if g:
                out[str(g)] = val
        return out

    def set_property_value(self, guid: str, ref: dict[str, Any], value: str) -> None:
        address = ref.get("address") or f"{ref.get('group')}/{ref.get('name')}"
        self._ensure().call("set_element_data", {
            "elements": [guid],
            "properties": {address: value},
        })


# --- BIBIM: НЕ подтверждён, считаем непроверенным ----------------------------


class BibimBackend(Backend):
    """НЕ РЕАЛИЗОВАН и НЕ ПОДТВЕРЖДЁН.

    По инвентаризации: локальный BIBIM package/source с полными schemas не
    найден; имена create_wall / get_element_info / get_elements_by_type /
    change_element_parameter присутствуют только как ожидаемые строки в
    router.py. Это не доказательство runtime availability.

    ПОКА BIBIM СЧИТАЕТСЯ ВНЕ SCOPE v1. Если он понадобится — реализуйте
    этот класс и подайте его через --backend-module.
    """

    name = "bibim"

    def available(self) -> tuple[bool, str]:
        return False, ("not verified: no local BIBIM schemas found; treated as OUT OF SCOPE "
                       "until --backend-module provides a verified implementation")

    def _todo(self, *a, **k):
        raise BackendError("BibimBackend is not implemented")

    project_info = _todo
    stories = _todo
    all_elements = _todo
    elements_by_type = _todo
    count_by_type = _todo
    details_raw = _todo
    details = _todo
    get_property_values = _todo
    set_property_value = _todo


# --- discovery --------------------------------------------------------------


def discover_ports(ports: list[int], timeout: float = 5.0) -> list[dict[str, Any]]:
    """Read-only перебор портов: кто отвечает и с каким проектом.

    Закрывает пункты инвентаризации «активный порт не подтверждён» и
    «текущий проект не подтверждён». Ничего не пишет.
    """
    found: list[dict[str, Any]] = []
    for port in ports:
        try:
            b = TapirBackend(port=port)
            ok, why = b.available()
            if not ok:
                found.append({"port": port, "_error": why,
                              "note": "порт не ответил; причина ниже"})
                continue
            info = b.project_info()
            info["_backend"] = b.name
            info["_addon_version"] = b.addon_version()
            found.append(info)
        except Exception as e:
            found.append({"port": port, "_error": f"{type(e).__name__}: {e}"})
    return found


# --- фабрика ----------------------------------------------------------------


def load_backend_module(path: str) -> type[Backend]:
    spec = importlib.util.spec_from_file_location("bimexec_user_backend", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load backend module: {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bimexec_user_backend"] = mod
    spec.loader.exec_module(mod)
    cls = getattr(mod, "BACKEND", None)
    if cls is None:
        raise RuntimeError(f"{path} must define BACKEND = <Backend subclass>")
    return cls


def build_backends(order: str, port: int | None, mcp_url: str,
                   module_path: str | None) -> list[Backend]:
    out: list[Backend] = []
    if module_path:
        try:
            out.append(load_backend_module(module_path)())
        except Exception as e:
            print(f"[warn] backend module not loaded: {e}", file=sys.stderr)
    for name in [b.strip() for b in order.split(",") if b.strip()]:
        if name == "tapir":
            out.append(TapirBackend(port=port))
        elif name == "mcp":
            out.append(McpBackend(base_url=mcp_url))
        elif name == "bibim":
            out.append(BibimBackend())
    return out


# --- приведение ответов -----------------------------------------------------


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


def _as_list(obj: Any) -> list[Any]:
    if obj is None:
        return []
    if isinstance(obj, list):
        return obj
    if isinstance(obj, dict):
        for key in ("elements", "details", "items", "stories", "result", "data"):
            if isinstance(obj.get(key), list):
                return obj[key]
        return [obj]
    return [obj]


def _unwrap(obj: Any) -> dict[str, Any]:
    """MCP tools/call кладёт полезную нагрузку в content[].text (JSON) или structuredContent."""
    d = _to_dict(obj)
    if "structuredContent" in d:
        return _to_dict(d["structuredContent"])
    content = d.get("content")
    if isinstance(content, list):
        for c in content:
            cd = _to_dict(c)
            if cd.get("type") == "text" and isinstance(cd.get("text"), str):
                try:
                    parsed = json.loads(cd["text"])
                except json.JSONDecodeError:
                    continue
                return parsed if isinstance(parsed, dict) else {"value": parsed}
    if "value" in d:
        return _to_dict(d["value"])
    return d


def _guid(obj: Any) -> str:
    d = _to_dict(obj)
    g = d.get("guid") or d.get("elementId") or d.get("id")
    if isinstance(g, dict):
        g = g.get("guid")
    if g is None:
        g = getattr(obj, "guid", None)
    return str(g) if g is not None else ""


def _fnum(v: Any) -> float | None:
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _find_coords(d: dict[str, Any]) -> dict[str, Any] | None:
    """Ищем beg/end координаты в нескольких вероятных местах."""
    keys = ("begCoordinate", "beginCoordinate", "startCoordinate", "begC")
    keys2 = ("endCoordinate", "endC", "finishCoordinate")
    for container in (d, d.get("geometry") or {}, d.get("wall") or {},
                      (d.get("details") or {}).get("wall") or {},
                      (d.get("details") or {}).get("geometry") or {},
                      d.get("details") or {}):
        if not isinstance(container, dict):
            continue
        beg = next((container[k] for k in keys if isinstance(container.get(k), dict)), None)
        end = next((container[k] for k in keys2 if isinstance(container.get(k), dict)), None)
        if beg and end:
            return {"from": [_fnum(beg.get("x")), _fnum(beg.get("y"))],
                    "to": [_fnum(end.get("x")), _fnum(end.get("y"))]}
    return None


def _normalize_tapir_details(raw: dict[str, Any]) -> dict[str, Any]:
    """Нормализация фактического ответа GetDetailsOfElements.

    Важно: имени этажа и имени слоя в ответе НЕТ — только floorIndex и
    layerIndex. Имя слоя резолвится отдельно через property ModelView_LayerName,
    имя этажа — через сопоставление floorIndex с GetStories.
    """
    out: dict[str, Any] = {}
    t = raw.get("type")
    if isinstance(t, dict):
        t = t.get("type") or t.get("elementType")
    if t:
        out["type"] = str(t)
    if raw.get("id") is not None:
        out["element_id"] = raw.get("id")
    if raw.get("floorIndex") is not None:
        out["floor_index"] = raw.get("floorIndex")
    if raw.get("layerIndex") is not None:
        out["layer_index"] = raw.get("layerIndex")
        out["layer"] = None            # резолвится через ModelView_LayerName
    out["story"] = None                # резолвится через floor_index -> GetStories

    det = raw.get("details") or {}
    coords = _find_coords(raw) or _find_coords(det)
    if coords:
        out["ref_line"] = coords
        dx = (coords["to"][0] or 0) - (coords["from"][0] or 0)
        dy = (coords["to"][1] or 0) - (coords["from"][1] or 0)
        import math

        out["length"] = (dx * dx + dy * dy) ** 0.5
        out["angle"] = math.degrees(math.atan2(dy, dx))

    for src in (det, raw):
        if not isinstance(src, dict):
            continue
        for key in ("height", "thickness"):
            if key not in out:
                v = src.get(key)
                if v is None and isinstance(src.get("wall"), dict):
                    v = src["wall"].get(key)
                if v is not None:
                    out[key] = _fnum(v)
    if raw.get("floorPlanPolygons"):
        out["has_floor_plan_polygons"] = True
    return out


# --- атомарная запись (Windows-safe) ----------------------------------------


def write_json_atomic(path: str, obj: Any) -> None:
    d = os.path.dirname(os.path.abspath(path)) or "."
    os.makedirs(d, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, sort_keys=True)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)
    try:
        fd = os.open(d, os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        pass
