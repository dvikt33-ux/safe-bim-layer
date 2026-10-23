# APA-P10.A02.S01 — Tapir 1.5.9/1.7.0: координаты этажей

Дата: 2026-10-10. Фаза SOURCE, SYNTHETIC 8/8. Archicad 29 LIVE и установленный Tapir 1.5.10: NOT_VERIFIED.

В исходниках Tapir у CreateWalls при явном floorIndex параметр zCoordinate является относительным bottomOffset; без floorIndex это абсолютный Z. У CreateBeams при явном floorIndex zCoordinate остаётся абсолютным, а ResolveFloorIndexAndOffset вычитает отметку этажа. Это документированное различие интерфейсов, а не подтверждённый дефект Tapir. Универсальный APA writer обязан преобразовывать координаты отдельно для каждого типа элемента.

Второе наблюдение: GetFloorIndexAndOffset при Z ниже всех этажей возвращает индекс 0 даже если его нет в проекте; ResolveFloorIndexAndOffset сохраняет отсутствующий явный индекс. Перед созданием элементов необходима проверка индексов по GetStories.

Пример: этаж 2 имеет отметку 4.5 м; запрос floorIndex=2, zCoordinate=5.0 приводит к wall.bottomOffset=5.0 (расчётная отметка 9.5 м), а beam.level=0.5 (расчётная отметка 5.0 м). Только SYNTHETIC, LIVE NOT_VERIFIED.

Архитектуры: A — внешний адаптер worldZ/storyIndex → относительный offset по типу команды (выбор для MVP, не требует APX); B — новый C++ resolver (сложнее, без измерений скорости). Тест PASS: worldZ после обратного пересчёта совпадает, недопустимые этажи отклоняются; FAIL: расхождение/недопустимый floorInd в payload. Вопрос аудиту: проверяет ли установленный Tapir 1.5.10 индекс этажа и существует ли type-specific Z normalization в APA?

Источники:
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.0/archicad-addon/Sources/ExtendedElementCommands.cpp#L3420-L3637
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.0/archicad-addon/Sources/CommandBase.cpp#L759-L821
- https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp#L3414-L3630
- https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___wall_type.html

Полный текст исследования остаётся в ответе ChatGPT до успешного GitHub readback. PLN, APX, main не изменялись.
