# APA №2 21Z — два независимых контрааудита и монтажные ворота

## Контрааудит A: исходники, версии, лицензии
Повторно прочитаны **pinned**, а не latest: IfcOpenShell `ifcopenshell-python-0.8.5` util.system/placement/representation/cost/sequence/document; ezdxf `v1.4.5` disassemble/insert/xclip и MIT LICENSE; Tapir `1.5.9` NavigatorCommands и MIT LICENSE; PR165/168/170 и LIVE-02 PR173. Историческая локальная маркировка Tapir1.5.10 не доказывает точное соответствие upstream 1.5.9. В 0.8.5 get_mappeditem_transformation имеет TODO 2d; get_connected_port берёт первый peer; assign_cost_value удаляет прежние CostValues; recalculate_schedule обновляет TaskTime и может бросить RecursionError при цикле. SDK30 не принимался как доказательство SDK29. Локальные binary wheel SHA и runtime imports в этом цикле NOT_VERIFIED.

## Контрааудит B: монтаж, дублирование, инженерная польза, безопасность
PR168 уже декомпозирует MINSERT, но groups[digest].append только один раз на parent; нужна проверка cell identity. XCLIP не применяется upstream — false visible geometry, fail-closed. PR170 world bounds не заменяют mapped-matrix QA. PR165 IFC ports не доказывает native MEP соединение. IFC 4D/5D setters не использовать в read-only. PR173 подтверждён native receipts и reopen **только exact snapshot**; поздний scratch SHA изменился по неатрибутированной причине, не повышать до production ACCEPTED. 0.438 секунды CreateHotlinkInstances без baseline — не коэффициент ускорения.

## Безопасный граф и ворота
APA → существующий Router/Bridge/SceneWriter → pinned library/API (максимум 3 внешних звена) → JSON/IFC copy → независимый readback. SOURCE: точный tag, ABI, license, units/GUID. OFFLINE: отдельные IFC/DXF fixtures, positive/negative, source SHA. BUILD: Windows Python3.11/3.12; не менять APX. INSTALLED: exact wheel/hash, opt-in registration, no rebind. LIVE: отдельное разрешение на scratch PLN, один native dispatch, no replay, SQLite/BREP/save/reopen. ACCEPTED: независимая инженерная проверка и rollback. **В текущем цикле только SOURCE 30; новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED = 0.**

## Координатору №3 (на утверждение)
1. PR168: MINSERT cell-level и XCLIP gate.
2. PR165: IFC MEP owner/peer через pinned util.system.
3. PR170: mapped mirror/nonuniform QA.
4. PR173: принять исторический LIVE-02 snapshot как тест; исследовать scratch drift без повтора.
5. Publisher: whitelist/unique identity/output manifest.
6. 4D/5D: только чтение, без mutation.

## Вопросы №1
1. Готовый XCLIP-visible и MINSERT cell identity helper для ezdxf1.4.5?
2. Pinned пример IFC2X3/IFC4 reciprocal MEP ports?
3. Готовый 2D mapped transform wrapper для IfcOpenShell0.8.5?
4. Официальный SDK29 Publisher GUID selector и локальный Tapir1.5.10 catalog?
5. Бесплатный лицензированный источник 5D ставок/единиц?
6. Безопасный автономный 4D viewer без CDN и HTML injection?

Ссылки на доказательства: [проверки A](research-2-integration-2026-10-18T21Z-checks-A.md), [B1](research-2-integration-2026-10-18T21Z-checks-B1.md), [B2](research-2-integration-2026-10-18T21Z-checks-B2.md), [LIVE-02](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-hotlink-coordinate-batch-20261018/docs/evidence/apa-ac29-hotlink-batch-20261018/live02/README_RU.md).
