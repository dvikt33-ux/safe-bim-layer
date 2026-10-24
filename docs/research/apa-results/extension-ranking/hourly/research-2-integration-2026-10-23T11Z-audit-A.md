# APA №2 | 11Z | Контрааудит A — не преувеличен ли G1 BREP-блокер?

**Гипотеза:** отсутствие `GetModelDumpV1` в pinned 262 безусловно запрещает read-only preflight нового двухэтажного здания.

**Проверка исходника:** `archicad_scene_run.py::scan_for_existing_geometry` вызывает `GetAllElements`, затем батчи `Get3DBoundingBoxes`; `GetModelDumpV1` вызывается только в ветке инвертированных bbox. При `elements=[]` не выполняется ни один батч; возвращается нулевая инвентаризация. Поэтому гипотеза **ОПРОВЕРГНУТА** для доказанно пустой scratch PLN. `GetModelDumpV1` по-прежнему нужен для части непустых моделей и G4. В `run_project` preflight остаются `GetProjectInfo/GetStories/GetAddOnVersion`, active story, материал, typed graph и identity, поэтому `G1=PASS` без фактического запуска **не заявлен**.

**Контрпример:** существующий BeamSegment/ColumnSegment с sentinel bbox вызывает `GetModelDumpV1`, которого нет в pinned каталоге. Поэтому перенос того же вывода на непустой PLN ошибочен.

**Вердикт:** `G1_CONDITIONAL_CLEAN_SCRATCH_ROUTE_SOURCE_VERIFIED`; SOURCE_ONLY. G0 runtime не проверен. Ни одного WRITE.
