# APA №1 — два независимых контрааудита, research-1-20261023T1559Z-TRIAD-AC29-QA

## Аудит A — версии, источник, лицензия и реальная доступность
1. Все новые положительные контракты C01–C06 подтверждены документацией Graphisoft именно AC29. AC29 GH Connection build3000 с поддержкой Rhino8 подтверждён страницей производителя, но локальный AC29 build5101 + add-on + Rhino SR + GH plugins не прочитаны. Поэтому INSTALLED=UNKNOWN, LIVE=NOT_RUN.
2. У Rhino Hotlink нативная семантика **GDL Object**, не Wall/Roof/Slab; он может быть QA/reference каналом, но не альтернативой SceneWriter для BIM.
3. IDS Import только задаёт классификации/свойства и IFC mapping; не выполняет нормативную проверку и не обновляет существующие определения.
4. Критический NEGATIVE: Graphisoft AC29 официально прекратил Solibri Inside/Design Checker; MEP calculations cloud-license-only. Рекомендации «бесплатная штатная Solibri QA» отвергнуты.
5. Source: https://www.graphisoft.com/it-it/downloads/add-ons/rhino-grasshopper/; https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-41.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/120_Interoperability/120_Interoperability-17.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/005_NewFeatures/005_NewFeatures-27.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/085_MEPDesigner/085_MEPDesigner-41.htm.

## Аудит B — инженерная применимость, конфликт владения и ложные PASS
1. У двух маршрутов разные владельцы: GH-AC native writer для GH-owned BIM, SceneWriter для APA-owned BIM; Rhino .3dm Hotlink — отдельная read-only геометрическая подложка. Запрет dual-writer на одном GUID.
2. Hotlink Update **не является** непрерывной синхронизацией: Modified→Update; даже автоматическая настройка обновления при открытии/публикации не обеспечивает обратный AC→Rhino путь. Model Compare показывает 3D разницу, не GUID stability.
3. Collision Detection может выдать ложно успокаивающий результат при скрытых слоях/выделении; SEO и priority connections исключаются. Для доказательства связности нужны native BREP+SEO+host readback.
4. Physical Model Quality помогает найти зазоры и несоединённые Core, но его Eurocode-ориентированные ratio-пороги не эквивалентны СП. Нет подтверждения автоматического запуска через существующий APA.
5. Обновление/Relink Hotlink может очищать Undo: до LIVE нужна изолированная scratch PLN, snapshot и явное разрешение.
6. Для BUILD-01 G0 BLOCKED; G1 NOT_RUN; G2 SOURCE_ONLY; G3 NOT_AUTHORIZED; G4/G5 NOT_RUN. Ни один новый gate не закрыт.
7. Source: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-1.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-64.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-2.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/092_ModelCheck/092_ModelCheck-3.htm; https://help.graphisoft.com/AC/29/INT/_AC29_Help/081_ModelCompare/081_ModelCompare-5.htm.

**Адресные поручения №2:** C01-C07 в порядке P0, затем P1. **Аудит №3:** отдельно проверить недублирование, ложный Solibri Inside, UI-ограничения видимости, GUID/ID provenance и корректность отчётов №1/№2.

Проверены source pages, не локальные установки. Main/код/PLN/APX не изменялись. MODEL_MODE_NOT_VERIFIABLE.
