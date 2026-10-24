# APA №2 — BUILD-01, 19Z

**Вклад:** установлен точный барьер `CreateSlabs` без `buildingMaterialId/structureType` и несовместимость PR126 packed с PR74 single-GUID. G0 требует SHA загруженного APX и runtime command inventory. Решение: существующий компилятор/SceneWriter, qualified Favorite и single-create до приёмки.

**G0 NOT_FOUND:** единая проверенная команда полного installed inventory/APX SHA не обнаружена. Минимальный read-only adapter: хешировать локальный загруженный APX и опросить `IsAddOnCommandAvailable` по каждому ID pinned каталога; затем сверить runtime schemas, без CREATE.

30 реальных SOURCE-чтений, 9 маршрутов, 2 контрааудита. Приложения повторно прочитаны, SHA проверены:

- [SOURCE 01–14](research-2-integration-2026-10-22T19Z-checks-A.md)
- [SOURCE 15–30](research-2-integration-2026-10-22T19Z-checks-B.md)
- [9 маршрутов](research-2-integration-2026-10-22T19Z-matrix.md)
- [Контрааудит А](research-2-integration-2026-10-22T19Z-audit-A.md)
- [Контрааудит Б](research-2-integration-2026-10-22T19Z-audit-B.md)
- [SHA-манифест](research-2-integration-2026-10-22T19Z-sha-manifest.json)

Матрицы: 61/61 уникальных ID в обоих файлах, пересечение 61/61; PROJECT_PLAN историческая rev182, 91 задача (только чтение).

SOURCE=30; OFFLINE=0; BUILD=0; INSTALLED=0; LIVE=0; ACCEPTED=0. G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. MODEL_MODE_NOT_VERIFIABLE. NEXT, main, PLN/APX и код не менялись.

06Z: SHA-манифест трёх приложений восстановлен; исходный главный отчёт отсутствует. Архив PARTIAL_NOT_ACCEPTED.
