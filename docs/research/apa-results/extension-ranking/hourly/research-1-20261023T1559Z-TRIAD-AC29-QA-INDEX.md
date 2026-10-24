# APA №1 — research-1-20261023T1559Z-TRIAD-AC29-QA — индекс проверенного исследования

## Реальное влияние на BUILD-01
**Новые подтверждённые готовые средства:** штатный AC29 .3dm Hotlink→Update→Model Compare; независимый Model Compare двух PLN-снимков; Collision Detection; Physical Model Quality Check; IDS import BIM-схем; Rhino Original ID/Layer provenance для GDL-подложки. **Новый отрицательный результат:** Solibri Inside/Design Checker прекращён для AC29; MEP Designer расчёты требуют cloud license.
**Не доказано:** автоматическая синхронизация из любой из трёх программ, сохранение native GUID при пересоздании, автоматический запуск этих проверок из APA, нормативное соответствие СП. Hotlink Rhino→AC — GDL, НЕ native Wall/Roof.

**G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4 NOT_RUN; G5 NOT_RUN.** Исторический PR74 ограниченный LIVE-прототип не является новым BUILD-01. Ни одной новой записи Archicad.

## Подтверждённые публикации
- [research-1-20261023T1559Z-TRIAD-AC29-QA-SOURCE.md](research-1-20261023T1559Z-TRIAD-AC29-QA-SOURCE.md) — commit `4b50b5da26306bc2b69603737e0da522ec977dfb`; blob `92c803a1f20d5a32b363b1fd669908a835bf4d4e`; exact_readback=true; chars=7297
- [research-1-20261023T1559Z-TRIAD-AC29-QA-CARDS.md](research-1-20261023T1559Z-TRIAD-AC29-QA-CARDS.md) — commit `843835681dc48e1dd739b734438cdaa0a830be13`; blob `28b8fbd9d618101a3a0bd19c88d4388b11028c82`; exact_readback=true; chars=5895
- [research-1-20261023T1559Z-TRIAD-AC29-QA-AUDITS.md](research-1-20261023T1559Z-TRIAD-AC29-QA-AUDITS.md) — commit `4cd64e87719c7df562935a6f6d844cb51470d7c4`; blob `132fff54ac098cb5a6d96bbfcfa98b6df4f1f4a7`; exact_readback=true; chars=3402

**Объём:** 28 различных предметных SOURCE-проверок (не 28 разных сайтов), 7 карточек (6 положительных и 1 отрицательная), 2 контрааудита. Все 3 приложения опубликованы в research branch и проверены fetch_file на точное совпадение. Свежие №2/№3 и матрица 61 не были найдены по достоверным путям — не считаются прочитанными.

**Поручение №2:** сначала read-only маршрут Rhino Hotlink→Model Compare, затем collision/physical QA с контролем visibility/selection, затем IDS schema, отдельно native GUID readback. **Поручение №3:** независимая проверка ложной двусторонности и прекращённого Solibri.

Main, код, PLN/APX, установки, LIVE, платные API, merge не затронуты. MODEL_MODE_NOT_VERIFIABLE.
