# CHECKPOINT — безопасный CLI / Preflight / SBIM Project Info, 26.10.2026

**Ветка:** `fix/template-write-preflight-contract-20261026`  
**Base (без изменений):** `feature/working-archicad-mvp`  
**PR:** [#195](https://github.com/dvikt33-ux/safe-bim-layer/pull/195), DRAFT  
**Статус:** `PASS_OFFLINE`, `NOT_LIVE`, `TPL_NOT_CREATED`.

## Критические ошибки, выявленные после checkpoint 792f7d8

1. PowerShell launcher передавал `--expected-project-path` ко всем `apply-*`, но Python `argparse` не объявлял этот параметр. Результат: команды записи даже после успешного `confirm-project` завершались на разборе аргументов.
2. `apply_safe_core` успешно выполнял отдельные операции и делал readback, но возвращал JSON **без** `status`; status gate с 26.10 отклонял его, хотя могли уже произойти записи.
3. После исправления статусов стало важно гарантировать, что `PASS` включает проверку **точного набора и значений полей SBIM Project Info**, а не только отсутствие ошибок API и неизменное число модельных элементов.
4. Default `-Stage all-safe` не был консервативен для первого вызова. При вызове отдельной стадии `core`/материалов/навигатора preflight не выполнялся в том же запуске.

## Исправления в PR #195

- Разобранный `--expected-project-path` сравнивается с точным путём активного проекта через `GetProjectInfo`, до любого `apply-*`. При отсутствии или отличии — `BLOCKED_PROJECT_CONFIRMATION`/`BLOCKED_ACTIVE_PROJECT_CHANGED`, код выхода 2.
- `apply_safe_core` отдаёт `status=PASS` только после полного `live_inventory=PASS`, сверки всех `project_info_targets()` с фактически прочитанными полями и неизменного количества модельных элементов.
- Launcher по умолчанию запускает `preflight` (только чтение); любой standalone write-stage предваряется четырьмя шагами `font-preflight → validate → inspect → plan`. `all-safe` уже содержит их первым этапом.
- Текстовые инструкции `TEMPLATE_BUILDER_README.md` и `LIVE_EXECUTION_RUNBOOK_v0.1.md` обновлены.
- В наборе `tests/test_archicad_template_status.py` теперь **14** сценариев (предыдущие 8 плюс 6): успешный и блокируемый inventory/plan/CLI, неуспех при отсутствующем/чужом пути, доказательство отказа без вызова `apply_safe_core`, неполный inventory, отсутствующий SBIM Project Info.

## Подтверждено GitHub Actions

[CI #40363683723](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/40363683723)  
**Проверенный source HEAD:** `98f312e5ea57a56506ee327de14cbd51fbf9b2dc`  
Статус workflow: `completed/success`.

По первичным логам:
- `Ran 14 tests`, `OK`;
- `Parsed 27 YAML files`;
- `validate` — `PASS`, `errors=[]`, `warnings=[]`;
- Python compile, вспомогательный скрипт и загрузка артефакта завершились успешно.

**Предел доказательства:** регрессионные тесты используют FakeTapir и заменённые операции записи. Они НЕ вызывают Archicad и не доказывают, что Windows PowerShell, установленный APX и реальный PLN прошли новый gate.

## Контролируемое продолжение

1. Проверить фактический Windows Archicad 29.2.1 (5101), точные порт, PID, projectPath и доступные команды установленного Tapir. Не считать pinned `tapir-1.5.8.json` автоматически равным сообщаемой 1.5.10.
2. Выполнить лишь:
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage preflight
   ```
   Архивировать все JSON/summary и статус этапов.
3. Запись `core` в **новый отдельный сохранённый пустой PLN** — только после успешного preflight и явного подтверждения конкретного пути через `confirm-project`, с полной обратной проверкой Project Info/атрибутов/элементов.
4. Материалы, оформление Формы 3, AutoText, DWG/IFC и `.tpl` остаются отдельными стадиями приёмки.

**Ограничения:** рабочие/исходные PLN, APX и `main` не менялись; `feature/working-archicad-mvp` не обновлялась автоматически; никаких Windows LIVE утверждений или результата `.tpl`.
