# APA №1 — BUILD-01 | 2026-10-23 08Z | VERIFIED SOURCE INDEX

## Воздействие на BUILD-01

**НОВОЕ:** [Tapir PR #1440](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1440), OPEN на 23.10.2026, описывает crash при закрытии Archicad с работающим Palette script; автор испытал исправление на **Archicad 29.0 JPN build 5101 Windows**. Для G4 это условный pre-close safety blocker; локальный Tapir 1.5.10 не проверялся и не обновлялся.

**G0:** готовый read-only маршрут [Microsoft ListDLLs](https://learn.microsoft.com/en-us/sysinternals/downloads/listdlls) → [PowerShell Get-FileHash](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.utility/get-filehash?view=powershell-5.1) → existing [DynamicCommands.probe_runtime](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/scripts/archicad_dynamic_commands.py#L309-L324). Нет Windows доступа, фактический APX/PID/порт/PLN/SHA/schema неизвестны: **G0 BLOCKED**.

**G1/G2:** источник [№2 07Z](research-2-integration-2026-10-23T07Z-report.md) подтверждает статический gap provider-schema vs SceneWriter post-CREATE (Windows/Doors/Slabs/Columns), Beam adapter opt-in. Наш контрааудит выявил три ложные готовности upstream: merged #1149 AC27-only; merged #1141 без открытых backend #968/#1140; merged #1025 при открытом базовом #964. Нельзя считать их установленными функциями AC29.

**Ни одни ворота G0–G5 не получили PASS. Новое нативное здание не создавалось.**

## Опубликованные приложения (все пути и Git blob SHA перепроверены)

1. [S01–S29: 29 содержательных SOURCE-контрактов](research-1-20261023T08Z-BUILD01-SOURCE.md) — blob `f4300bb9a441f536bdcd308c5261c3139820c3d2`, commit `7f2b25d1b7a1bb148fa5fced1281b5e5a1111087`.
2. [C01–C06: шесть полных карточек решений](research-1-20261023T08Z-BUILD01-CARDS.md) — blob `57ad70aa8793019e4329ca98580214325959aa4e`, commit `91880ba410ef1e1d4582cf998a5911f327502c1e`.
3. [A01–A02: два независимых контрааудита](research-1-20261023T08Z-BUILD01-AUDITS.md) — blob `bc7c49e95782411b8d32cb4debbe28887dcc1923`, commit `1c064b0bc402954ae7d23e234fdc90c3b1491c11`.
4. [Манифест проверенных Git blob SHA-1](research-1-20261023T08Z-BUILD01-GIT-SHA-MANIFEST.json) — blob `7218d4075cbab070f7200619ecfb390e3c9ef4b9`, commit `57049ce8e69f4b197a01c71e47773df134f0c191`.

**Методика:** 29 проверок конкретных контрактов по официальным источникам и версионированным PR/исходникам; несколько контрактов относятся к одному файлу, это не 29 разных производителей и не 29 испытаний Archicad. Контроль exact readback выполнен после create_file, дополнительно Git blob SHA-1 сверены перед публикацией индекса; SHA-256 файлов не вычислялся. Важность 0–100 экспертная, не benchmark.

## Состояние и адресное задание №2

| Gate | Status | Непосредственный безопасный шаг |
|---|---|---|
| G0 runtime/APX/schema | **BLOCKED** | PID, loaded APX path/SHA, port, PLN, registration/schema |
| G1 whole building DAG | NOT_RUN | существующий PR74/SceneWriter: read-only preflight/реальный OFFLINE_PASS |
| G2 native commands/material/host | SOURCE_ONLY | fail-closed writer-required поля; отдельный scope ModifySlabs; Beam adapter только при необходимости |
| G3 scratch native CREATE | NOT_AUTHORIZED | отдельное разрешение на scratch PLN/port/plan hash |
| G4 Save/GUI Close/Open/BREP | NOT_RUN | GuardedSave; перед Close отсутствие работающих palette scripts; independent readback |
| G5 второе здание | NOT_RUN | другое задание и другой scratch после G4 |

**Приоритет №2:** (1) G0 фактическая идентичность загруженного APX и схемы; (2) G1/G2 строгий existing compiler preflight, без новых writers и повторов CREATE; (3) G4 предусмотреть риск PR1440 при GUI close. IFC/Hotlink/DXF/PDF/MEP/SAF/Publisher не вытесняют P0 без доказанного blocker.

[Issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) · [PR #74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) · [NEXT_RESEARCH_PRIORITIES](../NEXT_RESEARCH_PRIORITIES.md) · [матрица 61](../priority_matrix_20261018.json) · [исторический PROJECT_PLAN rev182](https://github.com/dvikt33-ux/safe-bim-layer/blob/049576378c961c5d7a9a62611f4091e3da70d309/docs/research/apa-results/control/PROJECT_PLAN.json).

**Исследовательская публикация DONE_PUBLISHED (только четыре приложения + этот индекс, после точного readback).** Это НЕ DONE по BUILD-01. SOURCE=29; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. Main, код, PLN/APX, установки, LIVE, PR merge не изменялись. Opera Browser Connector не подключён; пользовательские вкладки не трогались. MODEL_MODE_NOT_VERIFIABLE.
