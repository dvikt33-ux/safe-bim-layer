# APA №2 22Z — контрааудит Б: монтаж/дублирование/ценность/безопасность
Повторная проверка цепочек отдельно от аудита А.

B1. MEP: APA V2 уже читает IFC port edges. `util.system` добавляет owner/peer, не второй граф. Native AC29 terminal ports этим не доказаны. Ворота: IFC4+IFC2X3 fixtures, отсутствие owner, экспорт без портов → fail-closed.
B2. DXF: C1 сохраняет raw geometry/handles; ezdxf Frontend+CustomJSONBackend даёт visible 2D geometry, но теряет source handle. Сравнение двух потоков допустимо как QA, не как доказанная one-to-one идентичность. XCLIP инверсия, OCS, MINSERT 2×3, нулевой spacing — обязательные fixtures.
B3. Provenance: IFC документ привязывать только к копии и двум проверенным GlobalId; PDF mark midpoint не физический opening. Пустые products не считать PASS.
B4. Publisher: пустой selectedNavigatorItemIds → publish all; без preflight **BLOCKED**. Не выполнять публикацию до whitelist+output sandbox+manifest.
B5. 4D/5D: `util.sequence` и `util.cost` read-only; cascade_schedule и assign_cost_value пишут в IFC, сейчас DEFER. Missing QTO ≠ zero. Не создавать новый scheduler или сметный движок.
B6. Hotlink: PR173 уже имеет одно LIVE batch 2 с защищённым снимком; повторная запись не нужна. Геометрия только 0 rotation/non-mirror, floor 0. Сохранение исходных GUID/BREP и journal обязательно.

Итог: 9 цепочек максимум 1 готовая библиотека + существующий Router/IFC. Для GPU ничего не запускается; 8 GB VRAM не gate; 48 GB RAM — только ресурсный лимит будущих IFC/DXF fixtures, замеров нет.
