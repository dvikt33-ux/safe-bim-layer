# APA №1 — 30 предметных SOURCE-проверок, 23.10.2026 16:55Z

Ровно 30 отдельных технических вопросов, а НЕ 30 независимых документов или испытаний. Официальные Graphisoft AC29 и AC27 guides, Graphisoft Community и собственный PR74. AC27 используется только как исторический ориентир, точное поведение AC29 требует локальной проверки. Полный AC29 PDF недоступен для постраничного чтения из-за размера; индексированные фрагменты доступны. Все результаты SOURCE_ONLY.

| № | Категория | Проверенный вопрос / результат | Источник |
|---|---|---|---|
| S01 | AC29 | AC29 Live Connection build3000 supports Rhino7/8 | [A](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| S02 | AC29 | Windows installer shown as 16.8MB, not proof installed | [A](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| S03 | License | Connection add-on free; base Archicad and Rhino require licenses | [A](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| S04 | Edition | Start Edition unsupported | [A](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/) |
| S05 | Shell | Three native GH Shell types: Extruded, Revolved, Ruled | [B](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| S06 | Shell | Each Shell component takes two Curve/Vector/Axis geometry inputs | [B](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| S07 | Shell | Shell Settings support Basic/Composite structures | [B](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| S08 | Shell | Shell Settings expose building material or composite attribute | [B](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| S09 | CW | CW Boundary Custom uses Rhino/GH lines for nonstandard grid | [C](https://help.graphisoft.com/AC/27/INT/GC.pdf) |
| S10 | CW | Custom Frame Axes and Panel Points are component inputs | [C](https://help.graphisoft.com/AC/27/INT/GC.pdf) |
| S11 | CW | CW Boundary Custom ignores standard CW Scheme grid settings | [B](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| S12 | CW | Ordinary CW Scheme repeats a grid with frame/panel classes | [B](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| S13 | CW | Native CW frames and panels are not equivalent to Rhino Blocks | [B](https://help.graphisoft.com/AC/29/INT/GC.pdf) |
| S14 | Slab | GH Slab input requires horizontal closed planar contours | [C](https://help.graphisoft.com/AC/27/INT/GC.pdf) |
| S15 | Slab | Planar GH Surface may contain holes for native Slab | [C](https://help.graphisoft.com/AC/27/INT/GC.pdf) |
| S16 | Slab | Curved spline slab boundaries become segmented in AC | [C](https://help.graphisoft.com/AC/27/INT/GC.pdf) |
| S17 | Slab | Slab Settings switch Basic/Composite and change input set | [C](https://help.graphisoft.com/AC/27/INT/GC.pdf) |
| S18 | Door/Window | GH door/window component requires Wall host | [E](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection-Reference-geometry-for/ta-p/303717) |
| S19 | Door/Window | One GH curve may create several wall segments and duplicate openings | [E](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection-Reference-geometry-for/ta-p/303717) |
| S20 | Door/Window | GH list operations needed to select unique host segment | [E](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection-Reference-geometry-for/ta-p/303717) |
| S21 | Opening | AC29 native Opening tool supports Wall/Slab/Mesh/Roof/Beam | [F](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-258.htm) |
| S22 | Opening | Native Opening can cut several elements and has classification/properties | [F](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-258.htm) |
| S23 | Opening | Opening follows host; corresponding GH create component not established | [G](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-259.htm) |
| S24 | Library | AC29 Save Selection as Window/Door creates library part without handwritten GDL | [H](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-294.htm) |
| S25 | Library | Such custom Window/Door is non-parametric and can distort on stretch | [H](https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-294.htm) |
| S26 | Geometry | Graphisoft recommends arcs to avoid many Walls/Beams from splines | [D](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564) |
| S27 | Geometry | Graphisoft warns Morph mesh polygon count can cause severe slowdowns | [D](https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564) |
| S28 | QA | AC29 conditional quantities may ignore holes below size threshold | [K](https://help.graphisoft.com/AC/29/INT/_AC29_Help/140_UserInterfaceDialogBoxes/140_UserInterfaceDialogBoxes-27.htm) |
| S29 | Identity | AC29 Unique ID/GUID differs from user element ID | [J](https://help.graphisoft.com/AC/29/INT/_AC29_Help/060_ElementParameters/060_ElementParameters-2.htm) |
| S30 | APA | PR74 already provides native 21-element building; no second writer | [L](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) |

## Контраограничения
1. Нативный тип Shell/CW/Slab не доказывает неизменный GUID, корректную BIM-классификацию, Save/Open или обратную синхронизацию.
2. Archicad Opening Tool и Grasshopper Door/Window — разные операции; наличие первого не доказывает готовый GH node для него.
3. Руководство AC29 PDF индексируется как историческая версия 2.1, тогда как текущий дистрибутив для AC29 указан build3000: не смешивать версии руководства и плагина.
4. Сведения о GH ownership/GUID, QA и Content Cache уже были в отчётах 13Z–15:59Z; они не считаются новыми решениями этого прохода.
5. Новые акценты: native Shell trio, custom CW, Slab holes, multi-segment hosted openings, AC29 custom Window/Door no-code, native Opening boundary.
6. Нет новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED доказательств.

MODEL_MODE_NOT_VERIFIABLE.
