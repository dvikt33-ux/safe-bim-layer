#!/usr/bin/env python3
"""
BIMEXEC — T0A: ПОЛНОСТЬЮ READ-ONLY capability probe (редакция под AC29 + MCP 0.6.0).

Не выполняет НИ ОДНОГО mutating вызова: не CreateWalls, не
SetPropertyValuesOfElements, не API.SetPropertyValuesOfElements, не BIBIM
create_wall / change_element_parameter, не set_selection.

Фазы:
  0. DISCOVERY   — перебор портов: какой Archicad отвечает и с каким проектом
  1. MCP SESSION — настоящий MCP initialize + tools/list (закрывает HTTP 400)
  2. READ        — проверки capability с атрибуцией бэкенда
  3. RAW DUMP    — сырые ответы GetDetailsOfElements / GetStories в отчёт

Запуск (Windows):
    python probe_t0a.py --out capability_matrix.json
    python probe_t0a.py --ports 19723,19724 --mcp-url http://127.0.0.1:8001/mcp ^
        --out capability_matrix.json
    python probe_t0a.py --backend-module .\bibim_backend.py --backend-order bibim,tapir

exit 0 — probe выполнен (это НЕ go); 2 — ни один бэкенд не отвечает.
Go/no-go — в поле verdicts.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backends import (  # noqa: E402
    DEFAULT_TYPES,
    ELEMENT_ID_CANDIDATES,
    LAYER_PROPERTY,
    TAPIR_READ_COMMANDS,
    FORBIDDEN_COMMANDS,
    Backend,
    build_backends,
    custom_marker_address,
    custom_marker_ref,
    discover_ports,
    ref_label,
    write_json_atomic,
)

PROBE_VERSION = "1.1"


class R:
    def __init__(self, name: str) -> None:
        self.name = name
        self.supported: bool | None = None
        self.backend: str | None = None
        self.evidence: dict = {}
        self.notes: list[str] = []

    def ok(self, backend, **ev):
        self.supported, self.backend = True, backend
        self.evidence.update(ev)
        return self

    def no(self, backend, note, **ev):
        self.supported, self.backend = False, backend
        self.notes.append(note)
        self.evidence.update(ev)
        return self

    def unknown(self, backend, note, **ev):
        self.supported, self.backend = None, backend
        self.notes.append(note)
        self.evidence.update(ev)
        return self

    def as_dict(self):
        return {"supported": self.supported, "backend": self.backend,
                "evidence": self.evidence, "notes": self.notes}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="capability_matrix.json")
    ap.add_argument("--ports", default="19723,19724",
                    help="кандидаты JSON API портов Archicad")
    ap.add_argument("--mcp-url", default="http://127.0.0.1:8001/mcp")
    ap.add_argument("--backend-order", default="tapir,mcp")
    ap.add_argument("--backend-module", default=None)
    ap.add_argument("--expect-project", default=None)
    ap.add_argument("--dump-elements", type=int, default=1,
                    help="сколько сырых details положить в отчёт")
    args = ap.parse_args()

    ports = [int(p) for p in args.ports.split(",") if p.strip().isdigit()]
    caps: dict[str, R] = {}
    raw_dumps: dict[str, Any] = {}
    discovery: list[dict[str, Any]] = []

    print(f"BIMEXEC T0A read-only capability probe {PROBE_VERSION}")
    print(f"host: {platform.system()} {platform.release()} python {platform.python_version()}")

    # ================= ФАЗА 0: discovery ====================================
    print("\n[0] discovery: перебор портов (read-only)")
    discovery = discover_ports(ports)
    for d in discovery:
        if d.get("_error"):
            print(f"    port {d.get('port')}: {d['_error']}")
        else:
            print(f"    port {d.get('port')}: {d.get('project_name')} "
                  f"<{d.get('project_path')}> untitled={d.get('is_untitled')} "
                  f"teamwork={d.get('is_teamwork')} tapir={d.get('_addon_version')}")

    answered = [d for d in discovery if not d.get("_error")]
    r = R("port_project_discovery")
    if not answered:
        r.no("tapir", f"ни один из портов {ports} не ответил",
             ports=ports, detail=discovery)
    else:
        r.ok("tapir", answered=answered,
             note="порт и проект подтверждены live read-only вызовом")
    caps[r.name] = r

    # выбираем рабочий порт
    port = None
    for d in answered:
        if args.expect_project:
            if d.get("project_path") and os.path.normcase(str(d["project_path"])) == \
                    os.path.normcase(args.expect_project):
                port = d.get("port")
                break
        else:
            port = d.get("port")
            break
    if port is None and answered:
        port = answered[0].get("port")

    backends = build_backends(args.backend_order, port, args.mcp_url, args.backend_module)
    print(f"\n[1] backends (рабочий порт: {port})")
    live: list[Backend] = []
    availability: dict[str, dict] = {}
    for b in backends:
        try:
            ok, why = b.available()
        except Exception as e:
            ok, why = False, f"{type(e).__name__}: {e}"
        availability[b.name] = {"available": bool(ok), "detail": why}
        print(f"    {b.name:8s} {'OK  ' if ok else 'down'} {why}")
        if ok:
            live.append(b)
    if not live:
        print("\nSTOP: ни один бэкенд не отвечает.", file=sys.stderr)
        write_json_atomic(args.out, {"probe": "T0A", "version": PROBE_VERSION,
                                     "generated_at": _now(), "discovery": discovery,
                                     "backends": availability,
                                     "verdicts": {"executed": False}})
        return 2

    def first(fn_name, *a, **kw):
        last = None
        for b in live:
            try:
                return b.name, getattr(b, fn_name)(*a, **kw)
            except Exception as e:
                last = f"{b.name}: {type(e).__name__}: {e}"
        raise RuntimeError(last or "no backend")

    def backend_by_name(name):
        return next((b for b in live if b.name == name), None)

    # ================= MCP: tools/list =====================================
    r = R("mcp_tools_list")
    mcp_tools: list[str] = []
    for b in live:
        if b.name != "mcp":
            continue
        try:
            mcp_tools = b.tools_list()
            r.ok("mcp", count=len(mcp_tools), tools=mcp_tools)
        except Exception as e:
            r.unknown("mcp", f"{type(e).__name__}: {e}")
    if not any(b.name == "mcp" for b in live):
        r.no("mcp", "MCP-бэкенд не отвечает; runtime tools/list не получен")
    if mcp_tools:
        mutating = [t for t in mcp_tools if t in
                    ("create_elements", "set_element_data", "move_elements",
                     "delete_elements", "set_selection", "clear_selection",
                     "create_issue", "publish")]
        mode = "full" if mutating else ("verdicts-only" if mcp_tools else "unknown")
        r.evidence["mode_inferred"] = mode
        r.evidence["mutating_tools_present"] = mutating
    caps[r.name] = r

    # ================= identity ============================================
    r = R("project_identity")
    try:
        be, info = first("project_info")
        problems = []
        if info.get("is_untitled"):
            problems.append("is_untitled=True")
        if info.get("is_teamwork"):
            problems.append("is_teamwork=True")
        if not info.get("project_path"):
            problems.append("нет project_path")
        if args.expect_project and info.get("project_path") and \
                os.path.normcase(str(info["project_path"])) != os.path.normcase(args.expect_project):
            problems.append("project_path != --expect-project")
        (r.ok(be, **info) if not problems else r.no(be, "; ".join(problems), **info))
    except Exception as e:
        r.unknown(None, str(e))
    caps[r.name] = r
    archicad_info = dict(r.evidence)

    # ================= stories =============================================
    r = R("stories_index_map")
    story_map: list[dict[str, Any]] = []
    try:
        be, stories = first("stories")
        story_map = list(stories or [])
        if not story_map:
            r.no(be, "GetStories вернул пустой список")
        else:
            bad = [s for s in story_map
                   if s.get("name") is None or s.get("elevation") is None or s.get("index") is None]
            (r.ok(be, stories=story_map) if not bad else
             r.no(be, "у части этажей нет index/name/elevation: floorIndex невозможно "
                      "сопоставить с именем и отметкой", stories=story_map))
    except Exception as e:
        r.unknown(None, f"{type(e).__name__}: {e}")
    caps[r.name] = r
    raw_dumps["GetStories"] = story_map

    # ================= элементы ============================================
    r = R("list_guids")
    guids: list[str] = []
    try:
        be, g = first("all_elements")
        guids = list(g or [])
        (r.ok(be, n=len(guids), sample=guids[:5]) if guids
         else r.no(be, "проект пуст: в MCP_TEST.pln должна быть хотя бы одна тестовая стена"))
    except Exception as e:
        r.unknown(None, str(e))
    caps[r.name] = r

    r = R("count_by_type")
    try:
        be, counts = first("count_by_type")
        broken = {k: v for k, v in counts.items() if isinstance(v, int) and v < 0}
        (r.ok(be, counts=counts) if not broken
         else r.no(be, f"типы без ответа: {sorted(broken)}", counts=counts))
    except Exception as e:
        r.unknown(None, str(e))
    caps[r.name] = r

    r = R("elements_by_type")
    walls: list[str] = []
    try:
        be, els = first("elements_by_type", "Wall")
        walls = list(els or [])
        (r.ok(be, wall_count=len(walls), sample=walls[:5]) if walls
         else r.no(be, "стен не найдено"))
    except Exception as e:
        r.unknown(None, str(e))
    caps[r.name] = r

    # ================= ГЛАВНОЕ: geometry endpoints стены ===================
    r = R("wall_geometry_endpoints")
    wall_detail_raw = None
    if walls:
        try:
            be = caps["elements_by_type"].backend
            b = backend_by_name(be)
            wall_detail_raw = b.details_raw(walls[0]) if b else None
            d = b.details(walls[0]) if b else None
            raw_dumps["GetDetailsOfElements_sample"] = wall_detail_raw
            if not d:
                r.no(be, "details недоступны")
            elif "ref_line" not in d:
                r.no(be, "endpoints (beg/endCoordinate) не найдены в ответе: "
                         "верификация позиции стены невозможна",
                     guid=walls[0], normalized_fields=sorted(d),
                     raw=wall_detail_raw)
            else:
                missing = [k for k in ("type", "length", "height", "thickness") if k not in d]
                r.ok(be, guid=walls[0], normalized=d, missing=missing)
                if missing:
                    r.notes.append(f"нет полей: {missing}")
        except Exception as e:
            r.unknown(None, f"{type(e).__name__}: {e}")
    else:
        r.no(None, "не на чем проверять: в проекте нет стен")
    caps[r.name] = r

    # ================= слой: имя через property ============================
    r = R("layer_name_via_property")
    if walls:
        try:
            be = caps["elements_by_type"].backend
            b = backend_by_name(be)
            vals = b.get_property_values({"kind": "name", "address": LAYER_PROPERTY}, walls[:3])
            got = {g: v for g, v in (vals or {}).items() if v}
            (r.ok(be, address=LAYER_PROPERTY, resolved=got) if got
             else r.no(be, f"property {LAYER_PROPERTY} не вернул значений", raw=vals))
        except Exception as e:
            r.unknown(None, f"{type(e).__name__}: {e}")
    else:
        r.no(None, "нет стен")
    caps[r.name] = r

    # ================= носители маркера ====================================
    probe_guids = (walls[:3] or guids[:3] or [])

    # Element ID: перебор кандидатов адреса
    r = R("read_element_id")
    element_id_ref = None
    if probe_guids:
        for cand in ELEMENT_ID_CANDIDATES:
            try:
                be = caps["elements_by_type"].backend or live[0].name
                b = backend_by_name(be) or live[0]
                vals = b.get_property_values(cand, probe_guids)
                got = {g: v for g, v in (vals or {}).items() if v not in (None, "")}
                if got:
                    element_id_ref = cand
                    r.ok(be, address=ref_label(cand), resolved=got)
                    break
                r.evidence.setdefault("tried", []).append(
                    {"address": ref_label(cand), "result": "пусто"})
            except Exception as e:
                r.evidence.setdefault("tried", []).append(
                    {"address": ref_label(cand), "error": f"{type(e).__name__}: {e}"})
        if element_id_ref is None:
            r.no(None, "ни один кандидат адреса Element ID не дал значений",
                 tried=r.evidence.get("tried"))
    else:
        r.no(None, "нет элементов")
    caps[r.name] = r

    # user-defined property
    r = R("read_custom_property")
    custom_ref = custom_marker_ref()
    custom_ref["address"] = custom_marker_address()
    if probe_guids:
        try:
            be = caps["elements_by_type"].backend or live[0].name
            b = backend_by_name(be) or live[0]
            vals = b.get_property_values(custom_ref, probe_guids)
            ok_call = True
            got = {g: v for g, v in (vals or {}).items() if v not in (None, "")}
            r.ok(be, address=custom_marker_address(), call_ok=ok_call, resolved=got,
                 note="свойство читается; значений нет — ожидаемо до T0B")
        except Exception as e:
            msg = str(e)
            if "no id for address" in msg or "empty id" in msg or "not exist" in msg.lower():
                r.no(be, f"свойство {custom_marker_address()} не существует: его нужно "
                         f"создать один раз (Property Manager или Add-On)", error=msg)
            else:
                r.unknown(be, f"{type(e).__name__}: {msg}")
    else:
        r.no(None, "нет элементов")
    caps[r.name] = r

    # ================= поиск: скан + точное/префиксное сравнение ===========
    r = R("search_scan")
    scan_values: dict[str, str] = {}
    carrier_ref = element_id_ref or custom_ref
    if guids and carrier_ref:
        try:
            be = caps["read_element_id"].backend or caps["read_custom_property"].backend \
                or live[0].name
            b = backend_by_name(be) or live[0]
            vals = b.get_property_values(carrier_ref, guids)
            scan_values = {g: v for g, v in (vals or {}).items() if isinstance(v, str) and v}
            if not scan_values:
                r.no(be, "нет ни одного непустого значения маркерного поля: позитивный "
                         "контроль поиска нечем выполнить. Присвойте тестовой стене "
                         "Element ID (например W-TEST-001).",
                     address=ref_label(carrier_ref))
            else:
                pg, pv = sorted(scan_values.items())[0]
                hits_exact = [g for g, v in scan_values.items() if v == pv]
                prefix = pv[: max(1, min(4, len(pv)))]
                hits_prefix = [g for g, v in scan_values.items() if v.startswith(prefix)]
                sentinel = f"BX:PROBE:NOPE:{os.urandom(4).hex()}"
                neg_exact = [g for g, v in scan_values.items() if v == sentinel]
                neg_prefix = [g for g, v in scan_values.items() if v.startswith("BX:PROBE:")]
                ok = pg in hits_exact and hits_prefix and not neg_exact and not neg_prefix
                evidence = {
                    "address": ref_label(carrier_ref),
                    "method": "client-side scan of property values + startswith",
                    "probe_guid": pg, "probe_value": pv,
                    "positive_exact_hits": len(hits_exact),
                    "positive_prefix_hits": len(hits_prefix),
                    "negative_exact_hits": len(neg_exact),
                    "negative_prefix_hits": len(neg_prefix),
                    "scanned_elements": len(guids),
                }
                (r.ok(be, **evidence) if ok else
                 r.no(be, "позитивный или негативный контроль поиска провален", **evidence))
        except Exception as e:
            r.unknown(None, f"{type(e).__name__}: {e}")
    else:
        r.no(None, "нет элементов или нет читаемого носителя")
    caps[r.name] = r

    # Tapir server-side prefix search
    r = R("tapir_native_prefix_search")
    r.no(None, "NOT FOUND: отдельной Tapir-команды поиска по префиксу user-defined "
               "property локально нет; поиск реализуется клиентским сканом")
    caps[r.name] = r

    # ================= read-команды по одной ===============================
    r = R("tapir_read_commands")
    results: dict[str, dict] = {}
    for b in live:
        if b.name != "tapir":
            continue
        for cmd in TAPIR_READ_COMMANDS:
            try:
                b.raw_call(cmd, _minimal_payload(cmd))
                results[f"{b.name}.{cmd}"] = {"ok": True, "error": None}
            except Exception as e:
                results[f"{b.name}.{cmd}"] = {"ok": False,
                                              "error": f"{type(e).__name__}: {e}"}
    broken = sorted(k for k, v in results.items() if not v.get("ok"))
    r.evidence["commands"] = results
    if not results:
        r.no(None, "tapir-бэкенд не отвечает")
    elif broken:
        r.unknown("tapir", f"не отвечают: {broken}", broken=broken)
    else:
        r.ok("tapir", broken=[])
    caps[r.name] = r

    # ================= версия add-on =======================================
    r = R("tapir_addon_version")
    for b in live:
        if b.name == "tapir":
            try:
                v = b.addon_version()
                (r.ok("tapir", version=v) if v
                 else r.unknown("tapir", "GetAddOnVersion не вернул версию"))
            except Exception as e:
                r.unknown("tapir", f"{type(e).__name__}: {e}")
    if r.backend is None:
        r.unknown(None, "tapir-бэкенд недоступен")
    caps[r.name] = r

    # ================= кандидаты для T0B ===================================
    # T0B нужен конкретный GUID: печатаем стены, чтобы не искать его вручную.
    t0b_candidates: list[dict[str, Any]] = []
    try:
        be = caps["elements_by_type"].backend or live[0].name
        bb = backend_by_name(be) or live[0]
        for g in walls[:10]:
            d = bb.details(g) or {}
            t0b_candidates.append({
                "guid": g,
                "type": d.get("type"),
                "element_id": d.get("element_id"),
                "story_index": d.get("floor_index"),
                "layer": d.get("layer"),
            })
    except Exception as e:
        t0b_candidates.append({"error": f"{type(e).__name__}: {e}"})

    report = _build_report(discovery, availability, caps, archicad_info, raw_dumps,
                           t0b_candidates)
    print()
    print(_render(report))
    write_json_atomic(args.out, report)
    print(f"\nwritten: {args.out}")
    return 0


def _minimal_payload(cmd: str) -> dict:
    if cmd == "GetElementsByType":
        return {"elementType": "Wall"}
    if cmd == "GetDetailsOfElements":
        return {"elements": []}
    if cmd in ("GetPropertyValuesOfElements", "API.GetPropertyValuesOfElements"):
        return {"elements": [], "properties": []}
    if cmd == "API.GetPropertyIds":
        return {"propertyIds": [{"address": "ModelView_LayerName"}]}
    if cmd == "API.GetAttributesByType":
        return {"attributeType": "Layer"}
    if cmd == "API.GetLayerAttributes":
        return {"attributeIds": [{"index": 1}]}
    return {}


def _build_report(discovery, availability, caps, archicad_info, raw_dumps,
                  t0b_candidates: list[dict[str, Any]] | None = None) -> dict:
    carriers = []
    if caps["read_element_id"].supported:
        carriers.append("element_id")
    if caps["read_custom_property"].supported:
        carriers.append("property")

    # duplicate detection: префиксный поиск = клиентский скан (не server-side команда)
    if caps["search_scan"].supported:
        dup = "SCAN_PREFIX"
    elif caps["count_by_type"].supported and caps["elements_by_type"].supported:
        dup = "EMPTY_SCOPE_FALLBACK"
    else:
        dup = "NONE"

    blockers = ["T0B_marker_roundtrip_not_run"]
    for name in ("project_identity", "stories_index_map", "list_guids",
                 "count_by_type", "wall_geometry_endpoints", "search_scan",
                 "layer_name_via_property"):
        if not caps[name].supported:
            blockers.append(name)
    if not carriers:
        blockers.append("no_readable_marker_carrier")

    go = (len(blockers) == 1)      # единственная допустимая блокировка — «T0B не прогоняли»

    return {
        "probe": "T0A",
        "version": PROBE_VERSION,
        "generated_at": _now(),
        "archicad": archicad_info,
        "discovery": discovery,
        "backends": availability,
        "capabilities": {k: v.as_dict() for k, v in caps.items()},
        "marker_carriers_readable": carriers,
        "duplicate_detection": dup,
        "operations": {
            "create_wall": {
                "production_safe": False,
                "blocked_by": blockers,
                "note": "create_wall НЕ разрешён до T0B",
                "implemented_here": False,
                "hard_blocked_commands": sorted(FORBIDDEN_COMMANDS),
                "guard": "backends.py: _assert_not_forbidden() отклоняет любую "
                         "команду из hard_blocked_commands до отправки в Archicad",
            }
        },
        "raw_dumps": raw_dumps,
        "t0b_candidates": t0b_candidates or [],
        "verdicts": {"executed": True, "t0a_go": go,
                     "next_step": "T0B" if go else "устранить блокировки"},
    }


def _render(rep: dict) -> str:
    lines = ["capabilities:"]
    for name, c in rep["capabilities"].items():
        mark = {True: "OK  ", False: "NO  ", None: "??  "}[c["supported"]]
        lines.append(f"  [{mark}] {name:28s} backend={c['backend'] or '-'}")
        for n in c["notes"]:
            lines.append(f"          note: {n}")
    lines.append("")
    lines.append(f"readable marker carriers : {rep['marker_carriers_readable'] or 'NONE'}")
    lines.append(f"duplicate detection      : {rep['duplicate_detection']}")
    lines.append(f"create_wall production_safe: "
                 f"{rep['operations']['create_wall']['production_safe']}")
    lines.append(f"  blocked by              : {rep['operations']['create_wall']['blocked_by']}")
    lines.append("")
    eid_addr = ((rep["capabilities"].get("read_element_id") or {})
                .get("evidence", {}).get("address"))
    lines.append(f"element_id address (для T0B --element-id-address): {eid_addr or 'НЕ ПОДТВЕРЖДЁН'}")
    lines.append("GUID candidates for T0B (стены):")
    for c in rep.get("t0b_candidates") or []:
        if c.get("error"):
            lines.append(f"  error: {c['error']}")
        else:
            lines.append(f"  {c.get('guid')}  id={c.get('element_id')} "
                         f"story={c.get('story_index')} layer={c.get('layer')}")
    lines.append("")
    lines.append("T0A GO" if rep["verdicts"]["t0a_go"] else "T0A NO-GO")
    lines.append(f"next: {rep['verdicts']['next_step']}")
    return "\n".join(lines)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


if __name__ == "__main__":
    raise SystemExit(main())
