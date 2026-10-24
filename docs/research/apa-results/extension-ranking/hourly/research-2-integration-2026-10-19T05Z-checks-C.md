# APA №2 — 2026-10-19 05Z — технические проверки

Каждый проход: вопрос → проверенный первоисточник → точный контракт → способ подключения/блокер → вердикт → следующая проверка. Проверки SOURCE; новых запусков кода, установок и LIVE нет.

### P19 — Как узнать publisher sets без публикации?
**Источник:** https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Контракт:** GetPublisherSetNames() → List[str]; только имена, без путей, содержимого и SHA файлов.
**Цепочка/блокер:** Официальный API29 → существующий Router, read-only preflight.
**Вердикт:** REUSE; names-only не является публикацией и не подтверждает актуальность PDF.
**Следующий контроль:** Проверить существование имени и отсутствие дублей в тестовом плане.

### P20 — Каков точный контракт Tapir PublishPublisherSet?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/schemas/tapir-live-1.5.10/tapir-scene-live.json ; https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/docs/research/apa-results/extension-ranking/NATIVE_D1_PREPARATION_20261018.md
**Контракт:** required publisherSetName; optional outputPath,selectedNavigatorItemIds; schema returns=null; запись внешних файлов.
**Цепочка/блокер:** Существующий native Router/Bridge с отдельным документным scope; в этом цикле НЕ ВЫЗЫВАТЬ.
**Вердикт:** DEFER LIVE; прямой response не доказывает существование PDF.
**Следующий контроль:** Список разрешённых выходных путей и типов файлов.

### P21 — Как доказать выпуск без ложного PASS?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-guarded-save-snapshot-20261019/scripts/apa_ac29_save_isolation.py#L98-L138 ; https://archicadapi.graphisoft.com/archicadPythonPackage/archicad.releases.ac29.html
**Контракт:** PR175 preserve_guarded_save: exact SHA snapshot для PLN, не Publisher; аналогичный принцип hash/readback применим к готовому файлу выпуска.
**Цепочка/блокер:** Нужен минимальный manifest (path,expected type,bytes,SHA256,source set,UTC) после разрешённого выпуска.
**Вердикт:** ADAPTER; готового Publisher artifact verifier в проверенном source не найдено (NOT_FOUND).
**Следующий контроль:** Проверить PDF header, SHA до/после, размер>0, уникальный путь.

### P22 — Как получить владельца IFC MEP-порта?
**Источник:** https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/system/index.html
**Контракт:** util.system.get_ports(element,flow_direction=None), get_port_element(port), get_element_systems(element).
**Цепочка/блокер:** Existing pinned IfcOpenShell 0.8.5 → APA read-only provider → BIM Graph.
**Вердикт:** REUSE/ADAPTER; orphan port должен иметь отдельный статус.
**Следующий контроль:** Fixture с 2 элементами, 3 портами и одним orphan.

### P23 — Как проверить peer и направление?
**Источник:** https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/system/index.html
**Контракт:** get_connected_port(port), get_connected_from/to(element,flow_direction=None); direction может быть NOTDEFINED.
**Цепочка/блокер:** Только IFC evidence; не выдавать отсутствие IFC connection за ошибку native MEP.
**Вердикт:** ADAPTER; peer reciprocity и owner проверяются отдельно.
**Следующий контроль:** Fixture connected, disconnected, flow unknown.

### P24 — Чего не хватает существующему PR165?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-high-density-readonly-v2-20261018/scripts/apa_high_density_readonly_v2.py#L170-L191 ; https://docs.ifcopenshell.org/autoapi/ifcopenshell/util/system/index.html
**Контракт:** _ifc_ports считает IfcDistributionPort/IfcRelConnectsPorts и unlinkedByIfcRelConnectsPorts; owner/flow не выводит.
**Цепочка/блокер:** Расширить existing V2 через util.system вместо нового графа/движка.
**Вердикт:** REUSE+ADAPTER; дополнить schema с ownerGlobalId,peerGlobalId,flow,status.
**Следующий контроль:** Сравнить 3 IFC fixtures, отказ при пустом наборе правил.

### P25 — Что реально доказано для пакетного Hotlink?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/docs/evidence/apa-ac29-hotlink-batch-20261018/live02/receipt.json ; https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/apa_ac29_hotlink_batch_oneshot.py
**Контракт:** PR173 receipt: before=69,after=119, batchCount=2,nativeBatchCalls=1,reopenVerified=true; savedSHA256 и BREP digest.
**Цепочка/блокер:** Переиспользовать original Router→SceneWriter→native verifier, только read-only provenance.
**Вердикт:** REUSE; не утверждать независимый ACCEPTED.
**Следующий контроль:** Сверить roots/children, 2 origins и исходный source SHA.

### P26 — Есть ли риск внешней записи после GuardedSave?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-guarded-save-snapshot-20261019/scripts/apa_ac29_save_isolation.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-guarded-save-snapshot-20261019/docs/APA_AC29_GUARDED_SAVE_ISOLATION_RU.md
**Контракт:** PR175 фиксирует поздний drift scratch PLN; ScratchWriteLease кооперативный и не блокирует внешние writers.
**Цепочка/блокер:** Не повторять LIVE; хранить immutable saved snapshot SHA и read-only reopen evidence.
**Вердикт:** REUSE protection concept; причина поздней записи UNKNOWN, не обвинять SaveProject.
**Следующий контроль:** Независимый аудит журнала и snapshot без повторного dispatch.

### P27 — Нужен ли второй исполнитель для Hotlink lineage?
**Источник:** https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/scripts/apa_ac29_hotlink_batch_oneshot.py#L386-L446 ; https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-ac29-native-contract-gaps-d1-20261018/docs/research/apa-results/extension-ranking/NATIVE_D1_PREPARATION_20261018.md
**Контракт:** verify_reopen сравнивает GUID-set hash, BREP hash, число новых roots, owned children и исходный module SHA.
**Цепочка/блокер:** Существующий BIM Graph + SceneWriter + native verifier; read-only cross-check provenance.
**Вердикт:** REUSE; новый writer REJECT; AC29 только, SDK30 не подменять.
**Следующий контроль:** Подтвердить source-owned GUID coverage и сохранность исходника.
