# APA №2 08Z — матрица 09–10

09 Layout/ViewMap: Graphisoft AC29 CreateLayout/CreateLayoutSubset/CloneProjectMapItemToViewMap/GetLayoutSettings; Tapir 1.5.9 GetViewSettings и batch clone. Router→Navigator tree→future native calls. ADAPTER 95, АДАПТАЦИЯ. Риски mm↔m, per-item partial batch, sourceGuid отсутствует в проверенном 1.5.9. ГОТОВО read-only tree+revision, затем только с разрешением 2 layouts/2 views и saved GUID readback.

10 Attribute/Pen: Graphisoft AC29 GetAttributeFolderStructure/GetAttributeFolders/GetActivePenTables/GetPenTableAttributes/GetLayerCombinationAttributes. Router→официальный JSON→BIM Graph. REUSE 93, БЫСТРО. Риск: layer combo IDs не означают visibility/locked. ГОТОВО полный обход, ошибки per-ID, model/layout pens отдельно, UNKNOWN_VISIBILITY. SOURCE ONLY.

Источник: https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html