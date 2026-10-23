# APA №2 21Z — 30 предметных SOURCE-проверок (не 30 источников, не runtime)
Ключи: P=[pinned Tapir 1.5.10](https://github.com/dvikt33-ux/safe-bim-layer/blob/f7c37b84b76c040c417ccd58a5543326e50f673a/schemas/tapir-live-1.5.10/tapir-scene-live.json); A=[PR74 accelerator](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py); R=[SceneWriter](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py); D=[Documentation](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_bim_documentation.py); B=[BUILD-01](https://github.com/dvikt33-ux/safe-bim-layer/issues/192); G=[Graphisoft](https://www.graphisoft.com/en-de/downloads/add-ons/rhino-grasshopper/); J=[jSwan](https://github.com/andrewheumann/jSwan); I=[IfcOpenShell](https://docs.ifcopenshell.org/ifcopenshell-python/geometry_processing.html).
| № | Факт / граница | Проверенный первоисточник |
|---:|---|---|
|01|G0–G5 требуют новое здание, не повтор PR74|B|
|02|PR74 исторический 21-element 2-storey native prototype|[PR74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74)|
|03|Pinned 1.5.10 содержит 262 commands; GetModelDumpV1 отсутствует|P|
|04|GetAddOnVersion v0.1.0 возвращает version, но не APX SHA|P|
|05|GetStories v1.1.5 возвращает actStory/stories|P|
|06|guarded_project требует projectName/path, non-Untitled, non-Teamwork, story index/floorId/level и точный Tapir|R|
|07|bind_authorized_saved_copy требует path/name/SHA256/authorization_ref|R|
|08|compiler требует `schemaVersion=apa-authored-project/1`|A|
|09|compiler требует `units=meters`|A|
|10|compiler требует `brief.targetProjectPath=RUN.EXPECTED_PATH`|A|
|11|run_project authored запрещает mode=offline|A|
|12|run_project authored требует preflight/execute и callable transport|A|
|13|authored nativeComponents allowlist: Columns/Doors/Windows/Walls/Roofs|A|
|14|CreateBeams в authored nativeComponents отсутствует|A|
|15|authored CreateRoofs требует pivotLine, Basic и buildingMaterialId|A|
|16|SceneWriter ALLOWED_WRITES содержит Walls/Slabs/Columns/Windows/Doors/Objects|R|
|17|SceneWriter EXTENDED_WRITES включает Roofs/Beams, но это не authored whitelist|R|
|18|ApplyFavoritesToElements v1.5.4 существует и требует favoritesToApply|P|
|19|applySettings/Classifications/Categories/Properties default=true, менять выборочно|P|
|20|ApplyFavoritesToElements отсутствует в A.NATIVE_MUTATIONS|A|
|21|ApplyFavoritesToElements отсутствует в R.ALLOWED_WRITES/EXTENDED_WRITES и D.DOCUMENT_COMMANDS|R+D|
|22|GetFavoritesByType v1.2.2 требует elementType|P|
|23|GetDesignOptionForElements v1.5.1 возвращает четыре option states|P|
|24|GetDesignOptionForElements отсутствует в A.EvidenceAPI.READS|A|
|25|GetConnectedElements v1.1.4 требует elements + connectedElementType|P|
|26|GetConnectedElements отсутствует в A.EvidenceAPI.READS|A|
|27|GetIFCIdsOfElements v1.5.1 существует, но отсутствует в A.EvidenceAPI.READS|P+A|
|28|CreateSlabs v1.0.3 не содержит structureType/buildingMaterialId; ModifySlabs v1.4.0 содержит и предупреждает про holes|P|
|29|Graphisoft AC29 GH Connection build3000 официально поддерживает Rhino8/Windows; installed не доказан|G|
|30|jSwan JSON points default X/Y/Z, Lock Structure null; IfcOpenShell mesh default/BRep optional|J+I|

**Статические SOURCE-предикаты:** 13/13 PASS при чтении immutable PR74 исходников: authored offline reject; exact target; три READ allowlist omissions; три WRITE allowlist omissions; saved copy binding; guard version; roof pivot; authored Beam exclusion; Publisher in documentation. Это анализ текста, не вызов `run_project`. SOURCE=30 assertions, OFFLINE=0, BUILD=0, INSTALLED=0, LIVE=0, ACCEPTED=0.
