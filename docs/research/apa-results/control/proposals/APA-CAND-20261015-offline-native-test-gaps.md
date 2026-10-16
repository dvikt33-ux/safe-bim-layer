# APA-CAND-20261015 — новые офлайн-сценарии и хост-гейты

- Status: **PENDING_AUDIT / NOT_ADMITTED_TO_PROJECT_PLAN**.
- Evidence: [1282-case JUnit run](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38726439729), [PR #100](https://github.com/dvikt33-ux/safe-bim-layer/pull/100).
- Никаких статусов S-ID в `control/PROJECT_PLAN.json` не изменено. Нужно решение независимого аудита о принятии кандидатов.

| Кандидат | Содержание | Критерий приёмки |
|---|---|---|
| APA-CAND-20261015-A | Семантические property/fuzz проверки маршрутизатора динамических команд: scope/authorization, schema drift, namespace collisions, неизвестные side effects | Детерминированные проверки с негативными образцами и точными правилами отказа; без выполнения записей |
| APA-CAND-20261015-B | Проверка C++ native assembly wrapper для CurtainWall/Railing/ExtrudedShell: профили, индексы, выделение и освобождение памяти, значения по умолчанию | AC29 SDK BUILD evidence + отдельные позитивные/негативные runtime случаи в защищённом PLN; не принимать Python mocks за live |
| APA-CAND-20261015-C | Регрессионные snapshots реальных Generic Opening host bindings и сложных native-сборок для BIM DependencyImpact | Фикстуры из допустимого read-only live dump с полными GUID/типами/источниками, negative cases, без выдуманных geometry-BREP |
| APA-CAND-20261015-D | Выявление slow/flaky кейсов и перекоса между шардами; повторная проверка только изменённых модулей | Времена на уровне pytest testcase из JUnit и CI, отчёт со статистикой, карантин без скрытия failures |

Нельзя механически наращивать число однотипных offline assertions ради отчётной цифры. Цель — расширить инженерное и семантическое покрытие, а офлайн-пакету оставить вспомогательную роль.
