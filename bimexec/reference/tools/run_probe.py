#!/usr/bin/env python3
"""
BIMEXEC capability probe (T0).

  python3 tools/run_probe.py                       # read-only probe
  python3 tools/run_probe.py --allow-write         # + создание одной тестовой стены
  python3 tools/run_probe.py --out caps.json --allow-write

Код возврата: 0 — сертифицировано, 1 — НЕ сертифицировано (fail closed),
2 — ошибка подключения/запуска.

--allow-write создаёт в проекте ОДНУ тестовую стену и записывает в неё маркер.
Запускать только в одноразовом проекте-песочнице. Probe не удаляет артефакты:
в v1 delete вне scope, поэтому список артефактов печатается для ручной уборки.
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bimexec.probe import Probe, ProbeConfig, render_text


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", help="куда записать capability matrix (JSON)")
    ap.add_argument("--allow-write", action="store_true",
                    help="выполнить write-фазу (создаёт 1 стену в ОДНОРАЗОВОМ проекте)")
    ap.add_argument("--raw", choices=("tapir", "fake"), default="tapir")
    ap.add_argument("--port", type=int, default=None)
    ap.add_argument("--medium", default="element_id,property",
                    help="кандидаты носителя маркера в порядке приоритета")
    ap.add_argument("--story", default="Ground Floor")
    ap.add_argument("--elevation", type=float, default=0.0)
    ap.add_argument("--layer", default="A-WALL")
    args = ap.parse_args()

    media = tuple(m.strip() for m in args.medium.split(",") if m.strip())
    cfg = ProbeConfig(
        allow_write=args.allow_write,
        media=media,
        story={"name": args.story, "elevation": args.elevation},
        layer=args.layer,
    )

    if args.raw == "fake":
        from bimexec.adapters import FakeArchicad

        project = {
            "port": 19723,
            "project_path": "/pln/sandbox.pln",
            "project_name": "SANDBOX",
            "is_untitled": False,
            "is_teamwork": False,
            "archicad_version": "29",
            "archicad_build": "29.0.0",
        }
        raw = _fake_raw(FakeArchicad(project, [{"name": args.story, "elevation": args.elevation}]))
    else:
        try:
            from bimexec.tapir_raw import AdapterUnavailable, TapirRaw

            raw = TapirRaw(port=args.port)
        except AdapterUnavailable as e:
            print(f"connection FAILED: {e}", file=sys.stderr)
            print("\nПроверьте: Archicad запущен, JSON-интерфейс включён, "
                  "установлен пакет 'archicad' (pip install archicad).", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"connection FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            return 2

    report = Probe(raw, cfg).run()
    print(render_text(report))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, sort_keys=True)
        print(f"\nwritten: {args.out}")

    return 0 if report["verdicts"]["certified"] else 1


def _fake_raw(ac):
    from bimexec.adapters import FakeRaw

    return FakeRaw(ac)


if __name__ == "__main__":
    raise SystemExit(main())
