# APA №1 — закрытие пробела обнаружения изменений через IfcDiff
Дата: 2026-10-24. BUILD-01 issue #192. SOURCE_ONLY.
## Новая находка
IfcDiff (IfcOpenShell 0.9.0post1 documentation) — готовое сравнение двух IFC моделей: added/deleted/changed по IFC GlobalId, геометрия, свойства, тип, container/story, aggregate, classification, отношения. Источник https://docs.ifcopenshell.org/ifcdiff.html . Доступен CLI/library и GUI в Bonsai. Лицензия точной распространяемой сборки в этом исследовании не верифицирована. Это не синхронизатор и не writer в Archicad. Зависит от стабильного IFC GlobalId. Геометрические изменения могут быть ложноположительными при смене представления extrusion/mesh.
## Дополнительная находка
Graphisoft GH-AC Teamwork статья https://community.graphisoft.com/t5/Teamwork-BIMcloud/Grasshopper-ARCHICAD-Live-connection-Teamwork/ta-p/303680 документирует Grasshopper Source Definition и Last update from Grasshopper для идентификации происхождения GH-элементов, а также потерю SEO при delete/recreate. Источник исторический; применимость к AC29 build5101 не проверена.
## Поручение №2
OFFLINE: экспортировать две проверенные копии IFC из BUILD-01, сравнить IfcDiff с включёнными relationships type/property/container/aggregate/classification, сопоставить GlobalId с readback Archicad GUID, отдельно проверить window-host, roof и этаж. Не считать это разрешением LIVE. Уточнить доступность GUI Bonsai, но не устанавливать без разрешения. Проверить на AC29 GH source metadata. При стабильном GlobalId сформировать отчёт diff; при смене ID — FAIL identity.
## Статусы
G0 BLOCKED, G1 NOT_RUN, G2 SOURCE_ONLY, G3 NOT_AUTHORIZED, G4/G5 NOT_RUN. Ни одной новой LIVE приёмки. Дыры: native roundtrip всех типов, автоматический conflict merge, cycle prevention, cross-app rollback, identity AC↔Rhino↔GH, автоматический route. IFC Bus остаётся прототипом, не готовой промышленной интеграцией.
## Контрааудит
1) IFC GlobalId ≠ Archicad GUID; IfcDiff detects changes but does not guarantee identity or fix models.
2) GH Source Definition/Last update — исторические признаки, не универсальный ownership registry; не доказывают конкурентную безопасность.
Main/код/PLN/APX не менялись, установок/LIVE нет. MODEL_MODE_NOT_VERIFIABLE.
