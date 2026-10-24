# APA №2 — 24.10.2026 03Z | индекс и GitHub-квитанция

**Статус:** SOURCE_ONLY; G0 BLOCKED_RUNTIME, G1 NOT_RUN, G2 SOURCE_PARTIAL, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. OFFLINE=0 новых; BUILD=0; INSTALLED=NOT_VERIFIED; LIVE=0 новых; ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.

**Новая дельта:** (1) официальный Rhino8>=8.11 `rhinocode list --json` позволяет read-only связать PID/version/active .3dm, но требует уже запущенного ScriptServer; (2) PR74 authored roof polygon ограничен `outline±0.35м`, `nativeComponents` не более 100, только 5 типов Create; (3) Rhino Content Cache Action=False не останавливает видимый Pull; bugs reset/append исправлялись в Rhino8.9/8.11, локальный SR неизвестен.

## Опубликованные доказательства — create_file с явным branch → fetch_file → byte-exact UTF-8 → вычисленный Git blob SHA-1

| Артефакт | Git blob SHA-1 (рассчитан и совпал с GitHub) | Commit |
|---|---|---|
| [Полный инженерный отчёт](research-2-integration-2026-10-24T03Z-report.md) | `16285d21a576f9fc5dfe171bc0d5b49e13654478` | `44b773d6301c32451feb2175f5ce3af740a0dedf` |
| [26 SOURCE-проверок](research-2-integration-2026-10-24T03Z-checks.md) | `736aa7d371978918f2a77476ca5089f46a0a4a6e` | `7a091c365cbb74ff4c0607b30de0c570d082a29c` |
| [Два контрааудита](research-2-integration-2026-10-24T03Z-audits.md) | `e8f0426fdbb33446c8c891e6d596cfc940fc1e11` | `01aef3d005c8a0bc340fdf4e753698749ccb8f00` |

**Проверка:** 3/3 файлов EXACT_MATCH; `main` и код не изменялись, никаких LIVE/установок/PLN/APX/merge. Данный индекс — четвёртый файл; его собственный blob SHA и commit сообщаются отдельно после повторного чтения. 26 проверок — **26 утверждений**, не 26 независимых источников. Два контрааудита документарные.

**Невыполненные блокеры:** локальный Rhino SR/ScriptServer, AC29 build/PLN/порт/APX/Tapir inventory, story/material binding, typed authored preflight, реальная синхронизация, GUID/IFC/BREP, Save/Open. FULL_TRIAD_SYNC=NOT_FOUND; MULTIPLANE_NATIVE_PR74=NOT_FOUND.

**Источники:** https://developer.rhino3d.com/en/guides/scripting/advanced-cli/ ; https://discourse.mcneel.com/t/content-cache-updated-guide/181883 ; https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ ; https://github.com/dvikt33-ux/safe-bim-layer/issues/192 ; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py .
