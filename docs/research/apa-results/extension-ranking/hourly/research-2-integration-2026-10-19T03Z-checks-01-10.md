# APA №2 — проверки P01–P10 (03Z)
Источник: https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html (официальный AC29 b3000).
P01. Zone input? GetElementsRelatedToZones(zones,elementTypes)→List[ElementsOrError], строки 700–718. Router reuse; типы строк не зафиксированы; проверить allowed types.
P02. Empty/error? ElementsOrError(elements?,error?), 2654–2669. Не заменять error на []; проверить invalid GUID.
P03. Adjacent? related grouped by type, 700–713, не доказывает adjacency. Блокер семантика; искать boundary source.
P04. Components? GetComponentsOfElements(elements), 548–565, positional order. Reuse JSON; проверить composite/single.
P05. Identity? ElementComponentId(elementId,componentId), 2549–2594. Два GUID; сохранять составной ключ.
P06. Values? GetPropertyValuesOfElementComponents(componentIds,propertyIds), 1018–1037. Reuse JSON; проверить propertyId errors.
P07. Status? NormalOrUserUndefinedPropertyValue(type,status,value), 3626–3642; notAvailable/notEvaluated, 3750–3779. Null не ноль; negative fixtures.
P08. Units? NormalLength m, Area m², Volume m³, 3430–3462/3555–3570/3732–3747. Typed unit adapter; mixed-unit QA.
P09. Layout? GetLayoutSettings(layoutNavigatorItemId)→LayoutParameters, 814–832; horizontal/vertical mm, 3098–3117. Reuse Publisher preflight; A3/A1.
P10. Revision? currentRevisionId/currentFinalRevisionId/hasIssuedRevision/hasActualRevision, 3129–3136. Только metadata; проверить issued/open.
SOURCE=10, OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=NOT_RUN.
