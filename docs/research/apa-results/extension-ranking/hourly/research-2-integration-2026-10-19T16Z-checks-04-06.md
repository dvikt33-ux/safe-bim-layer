# APA №2 16Z — технические SOURCE проверки 04-06

04. Вопрос: PR160 native hosted writer? Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/160/head/scripts/apa_ap2_massops_preflight.py#L140-L190 . Факт: wallHostGUID=null, nativeCalls=0, modelWrites=0. Адаптер: PDF source provenance only. Вердикт REUSE, следующий gate exact host GUID.
05. Вопрос: PR162 дублирует writer? Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/162/head/scripts/apa_ac29_group_strategy.py#L161-L278 . Факт: CloneNativeGroupV1/MoveElements(copy=true) через prepare_native_task, nativeWritePermission=false. Вердикт REUSE SceneWriter, проверить offline plan.
06. Вопрос: PR175 OS-wide lock? Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/refs/pull/175/head/scripts/apa_ac29_save_isolation.py#L43-L86 . Факт: exclusive lock file, expected SHA, cooperative only. Вердикт ADAPTER; offline 2-process contention.

Статус: SOURCE, новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED = 0.
