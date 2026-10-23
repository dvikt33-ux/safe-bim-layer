# APA — восстановленный отчёт: целостность Composites / Building Materials

**ПЛАН:** APA-P10 — аудит AC29. **ДЕЙСТВИЕ:** APA-P10.A01 — SDK и нативная модель. **ПОДШАГ:** APA-P10.A01.S02 — этажи, строительные материалы, surfaces и composites.

- Дата оригинального исследования: **2026-10-10**.
- Тип публикации: **RECOVERED_FROM_CHAT** — сохранено из предыдущего ответа, получившего `GITHUB_PUBLISH_BLOCKED`.
- Исходные заявленные фазы: SOURCE + OFFLINE / SYNTHETIC; исходные **13/13 PASS только REPORTED**, независимого воспроизведения в этой публикации нет.
- **LIVE Archicad 29: NOT_VERIFIED**, локальный Tapir 1.5.10: NOT_VERIFIED.
- Цель: сохранить технические гипотезы, ссылки и проверяемый план, не объявлять закрытой задачу.

## 1. Риск скрытой неполноты GetComposites

По предыдущему исследовательскому отчёту команда `GetComposites` в Tapir 1.5.9 вызывает `ACAPI_Attribute_GetDefExt`. Сообщается о ветке, способной вернуть Composite (GUID, индекс, имя) без массива `skins` при ошибке чтения слоёв, без явной ошибки клиенту. Дополнительно, JSON не сообщает нативное `nComps`, позволяющее отделить полную выборку от усечённой.

**Источник для независимой проверки:** [Tapir 1.5.9, AttributeCommands.cpp, GetComposites](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AttributeCommands.cpp#L1976-L2137), [Graphisoft Archicad 29.3100 API_CompWallType](https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/struct_a_p_i___comp_wall_type.html).

По оригинальному отчёту `API_CompWallType` хранит `nComps`, `totalThick`, `cwall_compItems` и `cwall_compLItems`; число разделительных линий ожидается `nComps+1`. Точные поля следует независимо проверить в SDK 29, прежде чем считать source_verified.

**Для MVP:** оставить существующий Tapir, добавить внешний fail-closed контроль полноты: число слоёв, ненулевые строительные материалы, толщина и явный `nComps` из независимого источника. Если нет доказательств, статус `BLOCKED_INCOMPLETE_ATTRIBUTE` / `NOT_VERIFIED`, не PASS.

## 2. Риск неполного каталога Building Materials

В оригинальном отчёте отмечено, что `GetAttributesByType` вызывает `ACAPI_Attribute_GetAttributesByType` без проверки кода возврата; нативная ошибка может маскироваться пустым результатом. `GetBuildingMaterials` предоставляет `cutSurfaceIndex` — индекс, а не постоянный GUID материала поверхности. Перед применением к APA требуется независимо удостоверить код и схему.

**Исходники:** [GetAttributesByType 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AttributeCommands.cpp#L106-L171), [GetBuildingMaterials 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/AttributeCommands.cpp#L2393-L2544).

Цепочка проверки: `Element GUID -> Composite -> Skin -> Building Material -> Surface`. Не смешивать Building Material, surface override и вычисленный материал грани из Native Model Dump.

## 3. Reported offline checks

Прежний ответ сообщает о **8 статических + 5 синтетических PASS = 13/13**: отсутствующий слой, неизвестный материал, ошибочное число skins, структурно корректный но неполный JSON, явная ошибка. **Raw tests/logs не приложены**; это REPORTED, не independently verified.

## 4. Архитектуры

| Критерий | A — Tapir + внешний валидатор | B — новый нативный C++ resolver |
|---|---|---|
| Повторное использование | Уже имеющиеся JSON-команды | Новая SDK-реализация |
| Новый APX | Не нужен для внешнего контроля | Нужен |
| nComps и код ошибки | Требуется независимый источник | Можно возвращать напрямую |
| Риск | Silent omission при слабой проверке | Дополнительный код/регрессии |
| Время/производительность | NOT_MEASURED | NOT_MEASURED |

**Предварительный выбор:** A ради быстрого MVP, B только если доказано, что требуемые данные недоступны без native bridge.

## 5. Read-only acceptance и независимый аудит

На одной неизменённой тестовой модели получить многослойную стену, перекрытие и кровлю; сверить список слоёв, `nComps`, толщины, GUID Building Material и surface. PASS — подтверждены все элементы цепочки; FAIL — доказанный пропуск/несогласованность; NOT_VERIFIED — нет нативного эталона.

**Аудитору:** возможно ли в установленном модифицированном Tapir 1.5.10 получить нативные `nComps` и коды `GetDefExt` без нового APX? Провести отдельный provenance check исходники → сборка → установленный APX.

**Безопасность:** только восстановление текста. Никаких LIVE-вызовов, сборки, изменений PLN/APX/main.
