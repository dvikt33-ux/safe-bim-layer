# APA №1 — инвентаризация закрытых функций и оставшихся дыр
Дата 2026-10-24. Статус SOURCE_ONLY. BUILD-01 issue #192. Без LIVE, установок, нового writer и изменения main/кода/PLN/APX.
## Влияние на BUILD-01
Новые SOURCE-кандидаты IfcHopperShell и ifcGH позволяют работать с IFC из Grasshopper, но не доказали сохранение GUID нативных объектов Archicad при roundtrip. IFC Bus — прототип синхронизации IFCJSON/MQTT/CRDT, не подтверждено наличие готового коннектора для AC29 build5101. G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. Нет нового PASS.
## Уже закрываемые функции (не путать с LIVE-приёмкой)
- Rhino 8 + Grasshopper: геометрия, параметрические зависимости.
- Graphisoft Grasshopper–Archicad Live Connection: поддерживаемые нативные BIM элементы; Deconstruct для чтения существующих параметров/геометрии; это не произвольная двусторонняя синхронизация всех типов.
- Rhino Content Cache: отслеживание Rhino-объектов и обновление вместо дублирования, не Archicad GUID.
- Speckle Rhino: обмен, версии, Rhino→Archicad в виде GDL-объектов, не гарантированная нативная Wall/Roof.
- Archicad Model Compare, Library Manager, PLN/PLA: контроль различий и резервирование.
- APA Tapir/SceneWriter: существующие писатели, результаты прошлых тестов; BUILD-01 в триаде не принят.
## Новые решения / первоисточники / ограничения / поручения №2
1. IfcHopperShell: https://ifchoppershell.github.io/grasshopper-documentation/ ; открытый бесплатный toolkit на IfcOpenShell для создания, модификации и анализа IFC в GH; контракт GH↔IFC, не AC29 native GUID; №2 проверить версии Rhino8, форматы IFC, GlobalId roundtrip OFFLINE и возможные расхождения семантики.
2. ifcGH: https://github.com/parametricos/ifcGH ; MPL-2.0, GH→IFC; не доказан нативный AC roundtrip; №2 сравнить с IfcHopperShell, исключить дублирование.
3. IFC Bus: https://www.vyzn.tech/en/news/datenintegration-zwischen-software-tools---ein-neuer-ansatz ; прототип Archicad/Grasshopper/другие, IFCJSON+MQTT+CRDT, last-write-wins, не подтверждён готовый бесплатный дистрибутив/лицензия/AC29 совместимость; №2 проверить публичный исходный код, наличие готовых адаптеров, гарантию сохранения GUID.
4. Speckle: https://speckle.systems/integrations/rhino/ ; Rhino7/8; Rhino→Archicad как GDL objects; №2 не считать native writer, проверить свойства/материалы и стабильность идентификаторов в опубликованных версиях.
5. Graphisoft Deconstruct: https://help.graphisoft.com/AC/22/INT/_AC22_Help/005_NewFeatures/005_NewFeatures-24.htm ; обратное чтение Archicad→GH, не обратная запись произвольных roof/wall; №2 составить матрицу полей/типов для AC29.
6. Speckle sharp connector releases: https://github.com/specklesystems/speckle-sharp-connectors/releases ; активная разработка fidelity Rhino/GH; №2 сверить точные версии и поддержку Archicad отдельным коннектором.
## Оставшиеся P0 пробелы
A. Универсальный обнаружитель изменений в любой из трёх программ с автоматическим маршрутом.
B. Stable identity mapping AC GUID ↔ Rhino Object ID ↔ GH element/IFC GlobalId с update-in-place всех native типов.
C. Семантическое разрешение одновременных правок (wall+opening+story+roof) без потери изменений; LWW недостаточно.
D. Атомарный откат или надёжный координированный rollback 3 приложений.
E. Доказанный полный native roundtrip multi-plane roof, hosted windows/doors, GDL parts, composites, properties and floors.
F. Независимая приёмка на BUILD-01 после Save/Close/Reopen.
## Контрааудит 1 — ложная двусторонность
IFC/mesh/GDL transport не равен update существующего нативного Wall/Window/Roof; IFC GlobalId не равен Archicad GUID. Не повышать SOURCE до LIVE.
## Контрааудит 2 — прототипы и лицензии
IFC Bus CRDT PoC — не готовый пакет; last-write-wins может уничтожить одну из конкурирующих правок. Не обещать бесплатную установку или совместимость без репозитория/релиза/лицензии. IfcHopperShell open source и ifcGH MPL, но не доказана совместимость с установленными сборками.
## Порядок исследований
№2: offline сравнительный эксперимент IFC GlobalId (IfcHopperShell/ifcGH), затем официальная GH-AC матрица native update, затем Speckle identity/version, затем IFC Bus source/license. №3: независимый аудит GUID, native type, GDL, roof, hosted openings, recovery. Никакой LIVE без отдельного разрешения.
MODEL_MODE_NOT_VERIFIABLE.
