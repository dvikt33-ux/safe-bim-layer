# APA AC29 — 20Z, перекрёстный аудит Б

**Инженерная применимость и дублирование.** Прочитаны PR #154 PDFVectors (blob 1a73b1ec), #159 CloneNativeGroupV1 (efd9f0f2), #160 AP2 source preflight без создания BIM (ae5f4c69), #162 group-first pure planner (153bc1e3). Второй Clone, Router, SceneWriter, PDF writer не создавать.

PR #175 save isolation (blob cf9ba7da): ScratchWriteLease кооперативен только для APA, внешние записи не блокирует. Не объявлять LIVE/ACCEPTED по SOURCE-коду.

ezdxf v1.4.5 disassemble.py (blob 5f341371): recursive_decompose раскрывает MINSERT, но не учитывает XCLIP; insert.py (a5c3d621) удаляет повторные offsets при нулевом spacing. Нужен raw/visible provenance, не новый parser.

Tapir1.5.9 NavigatorCommands.cpp (df359f7b): пустой selectedNavigatorItemIds ведёт к nullptr для ACAPI_ProjectOperation_Publish. Запретить Publish без непустого whitelist и изолированного каталога.

Вердикт: REUSE_EXISTING_FIRST. Источники SOURCE; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED новых=0. MODEL_MODE_NOT_VERIFIABLE.
