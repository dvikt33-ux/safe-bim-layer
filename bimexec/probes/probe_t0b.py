#!/usr/bin/env python3
"""
BIMEXEC — T0B: controlled marker round-trip. ПЕРВЫЙ НАСТОЯЩИЙ WRITE.

Геометрию НЕ создаём. Берём ОДИН заведомо тестовый элемент с известным GUID
в одноразовом MCP_TEST.pln и прогоняем маркер через полный цикл с возвратом
исходного значения.

    PRECHECK (read-only)
      → SAVED        исходное значение маркерного поля сохранено в receipt
      → WRITTEN      записан BX:PROBE:<nonce>
      → READ_BACK    прочитано, строковое равенство
      → FIND_EXACT   поиск по точному маркеру → ровно один GUID == исходному
      → FIND_PREFIX  поиск по префиксу BX:PROBE: → ровно один GUID == исходному
      → RESTORED     записано исходное значение
      → VERIFY_RESTORE  прочитано, доказано восстановление

ПРАВИЛА:
  * никаких повторов: одна попытка на шаг;
  * любой timeout / ambiguous / «write ok, но read-back не совпал» → UNKNOWN и STOP;
  * receipt пишется и сбрасывается на диск ДО каждой мутации — если процесс
    умрёт, в receipt ровно то значение, которое надо удалить руками;
  * exit 0 ТОЛЬКО если все шаги прошли И восстановление доказано.

Запуск (Windows):
    python probe_t0b.py --guid <GUID> --expect-project "C:\\...\\MCP_TEST.pln" --dry-run
    python probe_t0b.py --guid <GUID> --expect-project "C:\\...\\MCP_TEST.pln" \
        --carrier both --i-understand-this-writes-to-archicad

    exit 0 — go, 1 — STOP, 2 — ошибка запуска/подключения
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
import uuid
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backends import (  # noqa: E402
    ELEMENT_ID_CANDIDATES,
    Backend,
    custom_marker_address,
    custom_marker_ref,
    ref_label,
    build_backends,
    discover_ports,
    write_json_atomic,
)

PROBE_VERSION = "1.0"
MARKER_PREFIX = "BX:PROBE:"


class Stop(Exception):
    """Немедленная остановка. Состояние модели могло измениться — это фиксируем."""

    def __init__(self, stage: str, reason: str, status: str = "UNKNOWN"):
        super().__init__(reason)
        self.stage = stage
        self.reason = reason
        self.status = status


class Receipt:
    """Долговечный след T0B. Пишется ДО каждой мутации."""

    def __init__(self, path: str) -> None:
        self.path = path
        self.data: dict[str, Any] = {
            "probe": "T0B",
            "version": PROBE_VERSION,
            "host": f"{platform.system()} {platform.release()}",
            "started_at": _now(),
            "stages": [],
            "status": "RUNNING",
            "carriers": [],
            "cleanup": None,
        }

    def stage(self, name: str, **kw) -> None:
        self.data["stages"].append({"stage": name, "at": _now(), **kw})
        self.flush()

    def set(self, **kw) -> None:
        self.data.update(kw)
        self.flush()

    def flush(self) -> None:
        write_json_atomic(self.path, self.data)


def _element_id_candidates(explicit: str | None) -> list[dict[str, str]]:
    """Явный адрес выигрывает у перебора: T0A уже мог подтвердить конкретный."""
    if not explicit:
        return list(ELEMENT_ID_CANDIDATES)
    if explicit.startswith("builtin:"):
        return [{"kind": "builtin", "id": explicit.split(":", 1)[1]}]
    return [{"kind": "name", "address": explicit}]


def _resolve_element_id_ref(b: Backend, guid: str, explicit: str | None,
                            receipt: "Receipt") -> dict[str, str] | None:
    """Read-only: первый кандидат, который отдал непустое значение."""
    tried: list[dict[str, str]] = []
    for cand in _element_id_candidates(explicit):
        try:
            vals = b.get_property_values(cand, [guid]) or {}
            v = vals.get(guid)
            if v not in (None, ""):
                receipt.data.setdefault("element_id_probe", {})["resolved"] = ref_label(cand)
                receipt.flush()
                return cand
            tried.append({"address": ref_label(cand), "result": "пусто"})
        except Exception as e:
            tried.append({"address": ref_label(cand),
                          "error": f"{type(e).__name__}: {e}"})
    receipt.data.setdefault("element_id_probe", {})["tried"] = tried
    receipt.flush()
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--guid", required=True, help="GUID тестового элемента в MCP_TEST.pln")
    ap.add_argument("--expect-project", required=True,
                    help="ожидаемый путь PLN; несовпадение = STOP")
    ap.add_argument("--out", default="t0b_receipt.json")
    ap.add_argument("--report", default="t0b_report.json")
    ap.add_argument("--carrier", choices=("element_id", "property", "both"), default="both")
    ap.add_argument("--element-id-address", default=None,
                    help="явный адрес Element ID (например General_ElementID или "
                         "builtin:General_ElementID); по умолчанию перебор кандидатов")
    ap.add_argument("--backend-order", default="tapir,mcp")
    ap.add_argument("--backend-module", default=None)
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--ports", default="19723,19724",
                    help="кандидаты API-порта Archicad для автопоиска (--port точнее)")
    ap.add_argument("--mcp-url", default="http://127.0.0.1:8001/mcp")
    ap.add_argument("--dry-run", action="store_true",
                    help="только PRECHECK, без записи (режим по умолчанию)")
    ap.add_argument("--allow-write", action="store_true",
                    help="первый из ДВУХ ключей записи; сам по себе ничего не включает")
    ap.add_argument("--i-understand-this-writes-to-archicad", action="store_true",
                    help="второй из ДВУХ ключей записи; сам по себе ничего не включает")
    args = ap.parse_args()

    # Два ключа: запись ТОЛЬКО при наличии ОБОИХ. Один ключ — не запись.
    write_enabled = bool(args.allow_write and args.i_understand_this_writes_to_archicad)
    args.write_enabled = write_enabled   # в _run() читаем отсюда
    if args.allow_write != args.i_understand_this_writes_to_archicad:
        missing = ("--i-understand-this-writes-to-archicad" if args.allow_write
                   else "--allow-write")
        print(f"STOP: указан только один ключ записи, не хватает {missing}.\n"
              f"      Запись включается ТОЛЬКО двумя ключами одновременно:\n"
              f"        --allow-write --i-understand-this-writes-to-archicad",
              file=sys.stderr)
        return 1

    if os.path.exists(args.out):
        print(f"STOP: receipt уже существует: {args.out}\n"
              f"      Предыдущий прогон мог оставить маркер в модели. "
              f"Проверьте его и удалите файл вручную.", file=sys.stderr)
        return 1

    receipt = Receipt(args.out)
    receipt.set(guid=args.guid, expect_project=args.expect_project, dry_run=args.dry_run)
    receipt.flush()

    lock = args.out + ".lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except FileExistsError:
        print(f"STOP: другой probe уже запущен ({lock})", file=sys.stderr)
        receipt.set(status="STOP", reason="concurrent probe lock exists")
        return 1

    try:
        return _run(args, receipt)
    except Stop as s:
        receipt.set(status=s.status, stopped_at_stage=s.stage, reason=s.reason)
        print(f"\nSTOP at {s.stage}: {s.reason}", file=sys.stderr)
        print(f"receipt: {args.out} (там значение маркера для ручной уборки)", file=sys.stderr)
        return 1
    except Exception as e:
        receipt.set(status="UNKNOWN", reason=f"{type(e).__name__}: {e}")
        print(f"\nUNKNOWN: {type(e).__name__}: {e}", file=sys.stderr)
        print(f"receipt: {args.out}", file=sys.stderr)
        return 1
    finally:
        try:
            os.unlink(lock)
        except OSError:
            pass


def _run(args, receipt: Receipt) -> int:
    port = args.port
    if port is None:
        # порт не задан вручную — read-only перебор кандидатов
        for cand in discover_ports([int(p) for p in args.ports.split(",")
                                    if p.strip().isdigit()]):
            if not cand.get("_error"):
                port = cand.get("port")
                print(f"  port auto-discovered: {port} "
                      f"({cand.get('project_path') or cand.get('project_name')})")
                break
    backends = build_backends(args.backend_order, port, args.mcp_url, args.backend_module)
    live = []
    for b in backends:
        try:
            ok, why = b.available()
        except Exception as e:
            ok, why = False, str(e)
        print(f"  backend {b.name:8s} {'OK  ' if ok else 'down'} {why}")
        if ok:
            live.append(b)
    if not live:
        raise Stop("BACKEND", "ни один бэкенд не отвечает", "NO_GO")

    b: Backend = live[0]
    receipt.set(backend=b.name)

    # ================= S0: PRECHECK (read-only) =============================
    info = b.project_info()
    receipt.stage("PRECHECK", project=info, note="read-only")
    problems = []
    if info.get("is_untitled"):
        problems.append("is_untitled=True")
    if info.get("is_teamwork"):
        problems.append("is_teamwork=True")
    path = info.get("project_path") or ""
    if not path:
        problems.append("нет project_path")
    elif os.path.normcase(path) != os.path.normcase(args.expect_project):
        problems.append(f"project_path='{path}' != --expect-project")
    if problems:
        raise Stop("PRECHECK", "; ".join(problems), "NO_GO")

    guids = list(b.all_elements() or [])
    if args.guid not in guids:
        raise Stop("PRECHECK", f"GUID {args.guid} не найден в проекте ({len(guids)} элементов)", "NO_GO")

    details = b.details(args.guid) or {}
    if not details:
        raise Stop("PRECHECK", "details элемента недоступны: верификация невозможна", "NO_GO")
    receipt.stage("PRECHECK_ELEMENT", details=details)
    print(f"  element {args.guid}: type={details.get('type')} "
          f"story={details.get('story')} layer={details.get('layer')}")

    carriers: list[tuple[str, dict]] = []
    if args.carrier in ("element_id", "both"):
        ref = _resolve_element_id_ref(b, args.guid, args.element_id_address, receipt)
        if ref is None:
            msg = ("Element ID: ни один кандидат адреса не читается. "
                   "Укажите адрес вручную: --element-id-address General_ElementID "
                   "(или тот, который T0A записал в capabilities.read_element_id.address)")
            print(f"  carrier element_id  NOT resolvable: {msg}")
            if args.carrier == "element_id":
                raise Stop("PRECHECK", msg, "NO_GO")
        else:
            print(f"  carrier element_id  resolved as {ref_label(ref)}")
            carriers.append(("element_id", ref))
    if args.carrier in ("property", "both"):
        ref = custom_marker_ref()
        ref["address"] = custom_marker_address()
        carriers.append(("property", ref))

    readable = []
    for label, ref in carriers:
        try:
            vals = b.get_property_values(ref, [args.guid])
            readable.append((label, ref, (vals or {}).get(args.guid)))
            print(f"  carrier {label:12s} readable, current={(vals or {}).get(args.guid)!r}")
        except Exception as e:
            print(f"  carrier {label:12s} NOT readable: {type(e).__name__}: {e}")
    if not readable:
        raise Stop("PRECHECK", "ни один носитель маркера не читается", "NO_GO")

    all_values = _scan(b, [r for _, r, _ in readable], guids)
    leftover = [g for g, v in all_values.items() if isinstance(v, str) and v.startswith(MARKER_PREFIX)]
    if leftover:
        raise Stop("PRECHECK",
                   f"в проекте уже есть элементы с префиксом {MARKER_PREFIX}: {leftover}. "
                   f"Это наследие предыдущего прерванного probe — удалите его вручную до T0B.",
                   "NO_GO")

    if args.dry_run or not args.write_enabled:
        receipt.set(status="DRY_RUN_OK",
                    note="PRECHECK пройден; запись не выполнялась. "
                         "Для записи нужны ОБА ключа: --allow-write "
                         "--i-understand-this-writes-to-archicad")
        print("\nDRY-RUN OK: PRECHECK пройден, запись НЕ выполнялась.")
        print(f"receipt: {args.out}")
        return 0

    # ================= цикл по носителям ====================================
    results: dict[str, Any] = {}
    for label, ref, original in readable:
        marker = f"{MARKER_PREFIX}{uuid.uuid4().hex}"
        print(f"\n--- carrier {label} ({ref_label(ref)})")
        res: dict[str, Any] = {"marker": marker, "original": original, "stages": {}}

        # SAVED: исходное значение уже прочитано — фиксируем в receipt ДО записи
        receipt.set(carriers=receipt.data.get("carriers", []) + [{
            "carrier": label, "ref": ref_label(ref), "guid": args.guid,
            "original": original, "marker": marker, "status": "WRITING",
        }])
        receipt.stage("SAVED", carrier=label, original=original)
        res["stages"]["SAVED"] = True

        # WRITTEN — одна попытка, без повторов
        try:
            b.set_property_value(args.guid, ref, marker)
        except Exception as e:
            raise Stop("WRITTEN", f"{label}: {type(e).__name__}: {e}", "UNKNOWN")
        receipt.stage("WRITTEN", carrier=label, marker=marker)
        res["stages"]["WRITTEN"] = True
        receipt.set(cleanup={"carrier": label, "guid": args.guid,
                             "value_to_remove": marker,
                             "restore_to": original,
                             "how": "в Archicad вручную вернуть значение поля"})

        # READ_BACK — строковое равенство
        back = _read_one(b, ref, args.guid)
        if back != marker:
            raise Stop("READ_BACK",
                       f"{label}: write прошёл, но прочитано {back!r} != {marker!r}. "
                       f"Класс дефекта «silent no-op» — этот носитель непригоден.", "UNKNOWN")
        res["stages"]["READ_BACK"] = True
        receipt.stage("READ_BACK", carrier=label, value=back)

        # FIND_EXACT
        vals = _scan(b, [ref], guids)
        hits_exact = [g for g, v in vals.items() if v == marker]
        if hits_exact != [args.guid]:
            raise Stop("FIND_EXACT",
                       f"{label}: ожидали [{args.guid}], получили {hits_exact}", "UNKNOWN")
        res["stages"]["FIND_EXACT"] = True
        receipt.stage("FIND_EXACT", carrier=label, hits=hits_exact)

        # FIND_PREFIX
        hits_prefix = [g for g, v in vals.items()
                       if isinstance(v, str) and v.startswith(MARKER_PREFIX)]
        if hits_prefix != [args.guid]:
            raise Stop("FIND_PREFIX",
                       f"{label}: ожидали [{args.guid}], получили {hits_prefix}", "UNKNOWN")
        res["stages"]["FIND_PREFIX"] = True
        receipt.stage("FIND_PREFIX", carrier=label, hits=hits_prefix)

        # RESTORED
        try:
            b.set_property_value(args.guid, ref, original if original not in (None, "") else "")
        except Exception as e:
            raise Stop("RESTORED",
                       f"{label}: не удалось вернуть исходное значение: {e}. "
                       f"В модели остался маркер {marker} — удалите вручную.", "UNKNOWN")
        res["stages"]["RESTORED"] = True
        receipt.stage("RESTORED", carrier=label, restored_to=original)

        # VERIFY_RESTORE
        after = _read_one(b, ref, args.guid)
        want = original if original not in (None, "") else None
        got = after if after not in (None, "") else None
        if got != want:
            raise Stop("VERIFY_RESTORE",
                       f"{label}: ожидали {want!r}, прочитано {after!r}. "
                       f"Исходное значение НЕ восстановлено — верните его вручную.", "UNKNOWN")
        res["stages"]["VERIFY_RESTORE"] = True
        receipt.stage("VERIFY_RESTORE", carrier=label, value=after)

        # финальный контроль: в проекте не осталось BX:PROBE:
        vals = _scan(b, [ref], guids)
        still = [g for g, v in vals.items()
                 if isinstance(v, str) and v.startswith(MARKER_PREFIX)]
        if still:
            raise Stop("FINAL_SWEEP", f"{label}: остались маркеры {still}", "UNKNOWN")

        res["ok"] = True
        results[label] = res
        _mark_carrier(receipt, label, "OK")
        print(f"  OK: round-trip + restore доказаны")

    receipt.set(status="OK", cleanup=None, finished_at=_now())
    report = {
        "probe": "T0B", "version": PROBE_VERSION, "generated_at": _now(),
        "archicad": info, "backend": b.name, "guid": args.guid,
        "results": results,
        "verdicts": {
            "t0b_go": True,
            "carriers_verified": sorted(results),
            "recommended_carrier": _recommend(results),
        },
    }
    write_json_atomic(args.report, report)
    print(f"\nT0B GO. Проверенные носители: {sorted(results)}")
    print(f"Рекомендуемый носитель: {report['verdicts']['recommended_carrier']}")
    print(f"report: {args.report}")
    return 0


def _recommend(results: dict) -> str | None:
    """Тие-брейкер см. T0_PLAN.md: при равной надёжности предпочитаем
    user-defined property, потому что Element ID — пользовательские данные."""
    ok = [k for k, v in results.items() if v.get("ok")]
    if "property" in ok:
        return "property"
    if "element_id" in ok:
        return "element_id"
    return None


def _read_one(b: Backend, ref: dict, guid: str) -> Any:
    vals = b.get_property_values(ref, [guid]) or {}
    return vals.get(guid)


def _scan(b: Backend, refs: list[dict], guids: list[str]) -> dict[str, Any]:
    """Полный проход по маркерному полю. O(n), но это единственный способ
    поиска без нативной поисковой команды."""
    out: dict[str, Any] = {}
    for ref in refs:
        try:
            vals = b.get_property_values(ref, guids) or {}
        except Exception:
            continue
        for g, v in vals.items():
            if isinstance(v, str) and v:
                out[g] = v
    return out


def _mark_carrier(receipt: Receipt, label: str, status: str) -> None:
    for c in receipt.data.get("carriers", []):
        if c.get("carrier") == label:
            c["status"] = status
    receipt.flush()


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


if __name__ == "__main__":
    raise SystemExit(main())
