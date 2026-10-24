# APA №2 04Z — проверки 15–18

15. Tapir1.5.9 GetHotlinks: ошибки node/root/tree не всегда сериализуются. UNKNOWN; далее fail-closed census.
16. ElementCommands.cpp L1490–1506: GetDetailsOfElements для Hotlink возвращает nodeId, origin, rotation, mirror, floorDifference, флаги. REUSE BIM Graph.
17. L889–892: у связанного элемента есть hotlinkId при ненулевом header.hotlinkGuid. REUSE owner edge.
18. SDK29 GetHotlinkNodes(enableUnplaced=true) читает кэш; Tapir использует внутри, но не выдаёт полный read-only список. ADAPTER.
