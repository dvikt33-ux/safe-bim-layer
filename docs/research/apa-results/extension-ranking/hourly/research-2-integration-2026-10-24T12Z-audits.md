# APA №2 | 2026-10-24 12Z | Два внутренних контрааудита SOURCE

**Это контрааудиты исследователя №2, не независимый аудит №3 и не BUILD-01 приёмка.**

## A — «Одинаковый .gh + одинаковая геометрия = одинаковый native BIM»

**Контртезис:** одна и та же GH схема гарантирует совпадение материалов, параметров, этажных настроек и GUID в любом PLN.

**Опровержение:** [официальный AC29 GH Guide](https://help.graphisoft.com/AC/29/INT/GC.pdf) указывает наследование незаданных GH параметров из текущих Default Settings AC при создании; часть параметров не представлена в GH, часть сохраняется после ручной правки в AC, а GH-controlled параметры перезаписываются при re-execution. Следовательно, равенство видимых GH входов не доказывает равенство AC-native properties. Дополнительно [issue #192](https://github.com/dvikt33-ux/safe-bim-layer/issues/192) прямо отмечает отсутствие material fields в сохранённом CreateSlabs контракте PR149 и требует независимый native readback.

**Вердикт:** `GEOMETRY_EQUAL_NOT_NATIVE_EQUAL`. Для G0 фиксировать Defaults/Favorites/attribute GUID; G2 проверять конкретный typed schema; G4 readback GUID, BIM-type, story, building material, composite, BREP. В BUILD-01 не включать GH Design writer параллельно SceneWriter. Отсутствие локального теста — `NOT_VERIFIED`.

## B — «Подключённый GH/пауза/копирование дают безопасное завершение операции»

**Контртезис:** индикатор `Connected` означает, что именно нужный .gh управляет правильным PLN; `GH solved` означает завершённую AC запись; Copy/Paste и Pause не влияют на identity/ownership.

**Опровержение:** [официальный AC29 GH Guide](https://help.graphisoft.com/AC/29/INT/GC.pdf) разрешает много открытых .gh, но подключён только один, при этом ожидающий диалог AC приостанавливает связь; `Synchronize=False` не доказывает удаления; Copy/Paste GH-native теряет связь с GH code. [existing APA connected CLI](https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_connected_components.py#L425-L440) проверяет всё множество GUID. Rhino Content Cache Push/Purge — самостоятельный Rhino writer, а не AC commit ([McNeel](https://discourse.mcneel.com/t/content-cache-updated-guide/181883/1)).

**Вердикт:** `CONNECTED_NOT_COMMITTED`; `PAUSE_NOT_ROLLBACK`; `COPY_NOT_LINKED`. Требовать exact AC PLN/Rhino .3dm/connected GH .gh identity, no pending modal, whole GUID inventory, post-write native readback, Save/Close/Reopen. При UNKNOWN — STOP + read-only reconciliation, no automatic retry. Полная трехсторонняя транзакция/undo `NOT_FOUND`.

**Оба контрааудита:** SOURCE_ONLY, OFFLINE=0 новых, BUILD=0, INSTALLED=NOT_VERIFIED, LIVE=0 новых, ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.
