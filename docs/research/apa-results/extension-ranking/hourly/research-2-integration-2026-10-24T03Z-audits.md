# APA №2 — 24.10.2026 03Z | два контрааудита

## Контрааудит 1 — «Content Cache = полная трёхсторонняя синхронизация?»

**Гипотеза:** Rhino Content Cache Push/Pull + Graphisoft GH–AC29 Live Connection автоматически синхронизируют всё здание без конфликтов. **Проверка:** официальный McNeel 17.05.2024 описывает только Rhino/GH objects и Rhino ID; Action False сохраняет Pull при видимом Result, Bake без ID может дублировать, Purge удаляет. Официальный Graphisoft Deconstruct/Send Changes — отдельное AC→GH чтение; PR74 — отдельный APA→AC writer. Ни один источник не даёт единый журнал транзакций, GUID crosswalk, атомарный commit/rollback и разрешение циклов. **Контрвывод:** FULL_TRIAD_SYNC=NOT_FOUND. Безопасная граница — один owner на элемент и один write path, freeze, readback. **Не тестировано LIVE.**

## Контрааудит 2 — «В Archicad есть MultiPlane Roof, значит PR74 автоматически его построит?»

**Гипотеза:** штатный инструмент MultiPlane Roof AC29 можно считать покрытием сложной кровли в BUILD-01. **Проверка:** официальный AC29 Roof Tool умеет создавать один нативный MultiPlane GUI, но immutable authored PR74 допускает только CreateRoofs с Basic/pivotLine и polygonCoordinates внутри outline±0.35, не MultiPlane input; исходный пример имеет 0.15м отступ. Разбиение MultiPlane на SinglePlane меняет элементный состав, не доказывает GUID preservation. **Контрвывод:** нативная возможность GUI ≠ автоматизированный маршрут существующего writer; MULTIPLANE_NOT_FOUND, OVERHANG_GT_0_35_BLOCKED_IN_AUTHORED_POLYGON. Нельзя заменять native Roof Morph/mesh без согласования. **Не тестировано OFFLINE/LIVE.**

**Ограничение аудита:** оба — независимые логические контрпроверки SOURCE, не независимая инженерная экспертиза или приёмка BUILD-01. G0 BLOCKED_RUNTIME; G1 NOT_RUN; G2 SOURCE_PARTIAL; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. MODEL_MODE_NOT_VERIFIABLE.
