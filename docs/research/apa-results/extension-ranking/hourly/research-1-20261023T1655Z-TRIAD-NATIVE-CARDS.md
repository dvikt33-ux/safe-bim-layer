# APA №1 — 7 карточек ГОТОВЫХ средств и границ, 23.10.2026 16:55Z

**Контекст:** BUILD-01 issue #192; AC29 build5101 / Rhino8 / GH / Tapir1.5.10. Все SOURCE_ONLY, INSTALLED/LIVE/ACCEPTED не проверены. Официальный Graphisoft GH–AC AC29 build3000, бесплатный add-on к отдельно лицензируемым Archicad/Rhino. Часть точных входов ниже подтверждена официальными guides AC27–29, поэтому локальная AC29 schema-инвентаризация обязательна. Не добавлять второй writer: APA PR74/SceneWriter остаётся владельцем уже созданных им элементов.

## C1655-01 — Shell Extruded / Revolved / Ruled как нативные BIM-оболочки [P0, NEW]
- **Операция:** параметрическая сложная кровля/свод/оболочка вместо преобразования в Morph.
- **Готовое:** GH–AC Shell Ext./Rev./Ruled, каждый с двумя Curve/Vector/Axis входами; Shell Settings → Basic/Composite → Building Material/Composite.
- **Источник:** https://help.graphisoft.com/AC/29/INT/GC.pdf (раздел Shell Components), https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/ (AC29 build3000, Rhino8).
- **Направление:** Rhino/GH geometry → native AC Shell. Произвольный обратный Shell-edit AC→GH не доказан.
- **Ограничение:** тип Shell ≠ тип Roof, нет гарантии редактируемого multi-plane Roof, GUID retention/holes/SEO не проверены. 
- **№2:** составить 3 GH no-code определения только как SOURCE-схемы (профиль+вектор, профиль+ось, 2 профиля), сравнить с native APA Shell PR97 и выбрать одного владельца каждого Shell.
- **ГОТОВО:** после отдельного разрешения — native Shell GUID, structure, material, BREP, story, Save/Open; сейчас NOT_RUN.

## C1655-02 — CW Boundary Custom: нативный фасад с произвольным рисунком [P0, NEW]
- **Операция:** построить сложный фасад с раскладкой стоек/ригелей/панелей, а не сотни отдельных Rhino objects.
- **Готовое:** GH–AC Curtain Wall Boundary Custom с Boundary, Custom Frame Axes, Panel Points, Frame/Panel Settings и классами.
- **Источник:** https://help.graphisoft.com/AC/27/INT/GC.pdf (раздел CW Boundary Custom); https://help.graphisoft.com/AC/29/INT/GC.pdf (CW Scheme Settings), https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-152.htm.
- **Направление:** Rhino/GH lines + pattern → native AC Curtain Wall, Frame, Panel. Обратная произвольная правка не доказана.
- **Критическая ловушка:** Boundary Custom ИГНОРИРУЕТ Scheme Settings grid, поэтому нельзя одновременно считать обе схемы действующими. AC27 точные входы сверить на установленной AC29.
- **№2:** GH component map для одной секции фасада и матрица CW GUID / frame/panel count/class; PR81 Shell/CW не дублировать.
- **ГОТОВО:** после разрешения native CW parent/children, counts, materials, Save/Open; сейчас SOURCE.

## C1655-03 — GH Slab с отверстиями через planar Surface [P0, NEW]
- **Операция:** создать плиту перекрытия с внутренними контурами (шахта, лестничный проём) сразу как Slab.
- **Готовое:** GH–AC Slab принимает horizontal closed planar curve либо planar Surface с отверстиями; Slab Settings Basic/Composite.
- **Источник:** https://help.graphisoft.com/AC/27/INT/GC.pdf (Slab Component), https://help.graphisoft.com/AC/29/INT/GC.pdf.
- **Направление:** Rhino/GH planar surface → native AC Slab. Не произвольный 3D Brep и не гарантия Native Opening element.
- **Ограничение:** spline-границы могут сегментироваться; неизвестно, сохраняет ли текущая установленная версия внутренние контуры и GUID при пересчёте.
- **№2:** описать source-only контроль количества holes/loops, signed areas, units и BREP до/после; сравнить с PR74, где сложные holes пока запрещены.
- **ГОТОВО:** native Slab с проверенным inner polygon, объемом и Save/Open; сейчас NOT_RUN.

## C1655-04 — оптимизация Rhino кривых до нативных Wall/Beam [P1, NEW]
- **Операция:** избежать превращения одной криволинейной стены в сотни коротких Wall/Beam сегментов.
- **Готовое:** штатные Rhino/GH arc-curve operations; рекомендация Graphisoft упрощать кривые до дуг перед передачей в AC.
- **Источник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection/ta-p/303564.
- **Направление:** Rhino/GH curve preflight → GH native Wall/Beam.
- **Ограничение:** документация историческая, точная сегментация зависит от геометрии и AC29; нельзя считать 1 GH curve = 1 AC Wall.
- **№2:** таблица curve segment count / native wall count / max deviation / host mapping; не менять существующий SceneWriter.
- **ГОТОВО:** отсутствие непредусмотренных коротких элементов и дубликатов; SOURCE.

## C1655-05 — защита hosted openings при GH wall segmentation [P0, NEW]
- **Операция:** не размножать одно окно на каждом сегменте стены.
- **Готовое:** GH list operations для явного выбора единственного wall segment перед Door/Window Point/Distance.
- **Источник:** https://community.graphisoft.com/t5/Modeling/Grasshopper-ARCHICAD-Live-connection-Reference-geometry-for/ta-p/303717.
- **Направление:** GH host segment selection → native AC Window/Door. Не универсальная привязка к любому AC Wall GUID.
- **Ограничение:** уже известное требование Wall host уточнено новой документированной ловушкой: один GH curve может дать несколько AC Walls и несколько openings. Нужно проверить сопоставление сегмента/GUID.
- **№2:** сформировать invariant 1 authored opening → 1 native opening → 1 verified host Wall GUID; reject при ambiguity; source-only.
- **ГОТОВО:** native host GUID + opening GUID + уникальная точка вставки после Save/Open; NOT_RUN.

## C1655-06 — native Opening AC29 не равен GH Door/Window [P0, NEGATIVE CONTRACT]
- **Операция:** шахты и отверстия в Slab, Roof, Beam и нескольких элементах одновременно.
- **Готовое:** Archicad 29 Opening Tool с host Wall/Slab/Mesh/Roof/Beam, polygon/rect/circle, infinite/limited, classification/properties.
- **Источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-258.htm ; https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-259.htm.
- **Направление:** нативная AC операция, не подтверждён GH create node. Не считать Slab hole эквивалентом самостоятельного Opening с GUID.
- **Ограничение:** готовый безкодовый маршрут GH→AC Native Opening NOT_FOUND в проверенных источниках. Нельзя обещать, что GH заменит отсутствующую команду Tapir.
- **№2:** отдельная матрица native Opening vs slab inner polygon vs hosted Window/Door; поиск готового AC29 GH компонента только по доказанному контракту.
- **ГОТОВО:** SOURCE квалификация либо NOT_FOUND; никаких новых писателей.

## C1655-07 — Save Selection as Door/Window: библиотечная деталь без GDL-кода [P1, NEW]
- **Операция:** нестандартная форма окна/двери, созданная геометрическими средствами и сохранённая как библиотечная деталь.
- **Готовое:** AC29 File → Libraries and Objects → Save Selection as → Window/Door; Embedded Library.
- **Источник:** https://help.graphisoft.com/AC/29/INT/_AC29_Help/040_ElementsVB/040_ElementsVB-294.htm.
- **Направление:** AC geometry → GDL Library Part → AC hosted Window/Door. Не прямой Rhino/GH write, не BIM wall/roof.
- **Ограничение:** сохранённая геометрия не является полноценно параметрической, изменение габаритов растяжением может её исказить; библиотека проекта меняется — нужен отдельный допуск.
- **№2:** подготовить только read-only инструкцию и критерий отклонения: когда стандартная Library Part достаточна, когда нестандартный no-code вариант оправдан; не сохранять сейчас.
- **ГОТОВО:** на изолированном проекте после разрешения library identity, host, hole geometry, orientation, reopen; сейчас SOURCE.

## Вывод
Новые готовые пути действительно расширяют BIM-семантику **Shell / Curtain Wall / Slab с отверстиями**, но не дают доказанной симметричной синхронизации. Приоритет №2: **C01 + C02 + C03** как безкодовые SOURCE-маршруты, затем защита host C05. Первый BUILD-01 с уже существующими Wall/Slab/Roof/Window/Door не усложнять этими кандидатами без обоснования.

MODEL_MODE_NOT_VERIFIABLE.
