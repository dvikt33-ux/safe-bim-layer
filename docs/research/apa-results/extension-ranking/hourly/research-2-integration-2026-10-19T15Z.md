# APA AC29 — исследователь №2 — 19.10.2026 15Z
**SOURCE ONLY:** 30 технических проверок, два контрааудита, 10 интеграционных путей. Исследован только reuse существующего Router/Tapir/BIM Graph/SceneWriter, без второго исполнителя.

Прочитаны NEXT_RESEARCH_PRIORITIES.md, priority_matrix_20261018.json и candidates.json (61), audit-2026-10-19-14-tasks-2.md, research-1-20261019T09Z-checks.md, research-2-integration-2026-10-19T14Z.md, PROJECT_PLAN.json revision 182 (только чтение). Полного отчёта №1 09Z нет, checks доступны.

**Новая критическая находка:** Tapir 1.7.2 GraphicOverrideCriterion schema содержит 666 ключей без oneOf/required. C++ EmitCriterionNode выбирает первый известный ключ и возвращает true. Вход elementType+layer может проигнорировать layer, вход and+or может проигнорировать or. Это SOURCE-риск, не локальный runtime PASS. Нужен узкий semantic exactly-one gate, затем readback и проверка области действия.

**Вторая находка:** GetViewSettings — команда Tapir, а не собственный метод Graphisoft JSON AC29; возвращает имя graphicOverrideCombination, не GUID. Уже зарегистрирована в Tapir 1.5.9; предпочтителен текущий APX после IsAddOnCommandAvailable, без обновления.

Первоисточники:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicOverrideCriterion.cpp#L1073-L1150
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/RFIX/Images/CommonSchemaDefinitions.json
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/NavigatorCommands.cpp#L360-L399

## Приложения и доказательства
[Матрица 10 решений](research-2-integration-2026-10-19T15Z-matrix.md).
[Проверки 01–05](research-2-integration-2026-10-19T15Z-checks-01-05.md), [06–10](research-2-integration-2026-10-19T15Z-checks-06-10.md), [11–15](research-2-integration-2026-10-19T15Z-checks-11-15.md), [16–20](research-2-integration-2026-10-19T15Z-checks-16-20.md), [21–23](research-2-integration-2026-10-19T15Z-checks-21-23.md), [24–26](research-2-integration-2026-10-19T15Z-checks-24-26.md), [27–30](research-2-integration-2026-10-19T15Z-checks-27-30.md).
[Контрааудит А](research-2-integration-2026-10-19T15Z-audit-A.md), [контрааудит Б и передача №3](research-2-integration-2026-10-19T15Z-audit-B.md).

**Статусы этого цикла:** SOURCE 30; новые OFFLINE 0, BUILD 0, INSTALLED 0, LIVE 0, ACCEPTED 0. Не изменялись main, код, PLN/APX, очередь №3 или канон rev182. MODEL_MODE_NOT_VERIFIABLE.
