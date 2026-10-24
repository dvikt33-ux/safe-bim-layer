# APA AC29 №2 / 17Z — два собственных независимых контрааудита

## A. Исходный код, версии, лицензии и точность API

Повторно сверены PR165 V2 blob `39b8b60474bd31607c126f764cc167438ace7d7e`, entrypoint blob `d5355970edfa37b61cea497529f23d5133d2db86`, V1 blob `7ac61d9e2b22ea911f4885446922a1bf943581c1`. В V1 исходнике указаны IfcOpenShell/IfcDiff/IfcTester 0.8.5 и ezdxf 1.4.5; ни wheel, ни Python 3.11/3.12 в локальной среде этим не доказаны. V2 source draft — НЕ установлен и НЕ выполнен. IfcOpenShell LGPL-3.0-or-later, ezdxf MIT, но лицензии всех транзитивных зависимостей и конкретных wheel требуют отдельной сверки.

Tapir: `NavigatorCommands.cpp` tag 1.5.9 blob `df359f7bdf94f9004617cf616c6d38cb98be08ae`; `ProjectCommands.cpp` tag 1.5.9 blob `99053b4ce5f32b33ae456a076f4355a68994e207`; upstream MIT. Локально обозначенная 1.5.10 НЕ проверена по бинарному SHA/командному каталогу. SDK29.3100 ≠ ABI AC29 build5101. Graphisoft SDK — проприетарный; не предлагать новый APX без разрешения.

STEP-to-JSON `package.json` blob `99eb84ffb3f24c8a6647d9bfd7c158e4940b2588`: 4.0.0 MIT. Реальный CLI `cli/step-to-json.js` blob `b0387561a607c58148fd8e3b339cecbb6df7b4fe`, README ошибочно ссылается на корень. `parse()` строит структуру без трансформаций; формат STEP AP203/AP214/AP242 не испытан. STEPhen `pyproject.toml` blob `797668989817a23f8599fb18f4944f2357f5ec27`: 0.0.1 Apache-2.0, CadQuery; sourcefile принимает .step/.csv, не .stp. Windows wheel/units/rotation convention NOT_VERIFIED.

BCF: `ifctester/reporter.py` blob `c4c79db33cbd57bd68ccb782892ec6b0e0c2dae5` использует `bcf.v2.bcfxml.BcfXml`. Открытый upstream issue https://github.com/IfcOpenShell/IfcOpenShell/issues/7152 о названиях viewpoint/snapshot запрещает объявлять BCF viewer ACCEPTED. IfcDiff документация 0.9.0post1 не переносится автоматически на локальный 0.8.5.

**A verdict:** 30/30 имеют source-contract, но compatibility evidence неполна. SOURCE_PARTIAL_VERIFIED; OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED — NO.

## B. Монтажный граф, дублирование, инженерная ценность, безопасность

1. PR165 использует оригинальный DynamicCommands и V1 six, добавляя 12 READ_ONLY; не создавать второй Router, IFC reader, SceneWriter, BIM Graph.
2. IFC relation samples ограничены 5000 строками, childrenSample 20: sample ≠ полный граф. GlobalId ≠ native Archicad GUID. `archicad_connected_ifc.inspect_export` уже умеет mapping/host-cut, его переиспользовать.
3. `IfcDiff` APA `-r type property container aggregate classification` не эквивалентен default attributes+geometry; нужен отдельный режим, не новая реализация.
4. Publisher с `selectedNavigatorItemIds=[]` передаёт nullptr и рискует публиковать весь set; fail-closed GUID whitelist. IfcPatch без `-o` пишет на входной IFC.
5. STEP-to-JSON CLI `fs.writeFileSync` может перезаписать .json, теряет placement; prefer safe library wrapper. STEPhen пишет относительные каталоги `doc/step/svg/html`, не направлять в stable APA.
6. DXF MINSERT `row_count/column_count` не разворачивается; raw `$INSUNITS` не учитывает units блока; DIMENSION textOverride не физическая длина.
7. PR159 поздний LIVE только scratch PLN; PR162 CI 12/12 не SceneWriter LIVE; PR164 verifier SOURCE only. PR160 PDF label centers не являются physical hosted opening anchors, generic MoveElements(copy=true) для окон/дверей запрещён.
8. MEP mixed-shape transition и SAF→PyNite full 6DOF/LCS/load adapter остаются BLOCKED/NOT_FOUND. STEPcode BSD-3/CMake — более тяжёлая альтернатива Node, не подключать ради дерева.
9. 8GB VRAM не нужны для raw IFC/DXF reader; 48GB RAM не подтверждают способность безопасно загрузить 4GiB IFC/CadQuery. Peak RSS и time-to-result не измерялись.

**B verdict:** REUSE/ADAPTER по 7 прикладным цепочкам; REJECT второй writer; DEFER тяжёлые расчётные и CAD пути. Ускорение не измерено.

## Gates и откат

SOURCE: SHA файла+версия+license+schema. OFFLINE: IFC2X3/IFC4, DXF MINSERT/units, STEP nested transforms, BCF ZIP/viewer, negative input/output fixtures. BUILD: Windows Python ABI, SDK29 отдельно. INSTALLED: фактические SHA wheel/Tapir/APX, V1 receipt. LIVE: только разрешённый scratch PLN и scoped SceneWriter. ACCEPTED: независимый GUID/geometry/host/port/outputs readback и сохранение/повторное открытие. Любой провал — без автоматического повторного CREATE; исходные PLN/IFC не изменять. Эти gates **не выполнялись**.

Ограничения: main, PLN/APX, код, NEXT_RESEARCH_PRIORITIES.md и PROJECT_PLAN.json revision182 не изменялись. MODEL_MODE_NOT_VERIFIABLE.
