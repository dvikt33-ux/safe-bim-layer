# APA №1 — два контрааудита, 23Z

**Аудит A — источники и версии.** Проверены официальные Graphisoft Archicad 29 C++ API, справка AC29 и pinned IfcOpenShell source tag. Native PDF markup API существует с AC29, но работает с PDF, созданными Archicad; это не PDF→BIM. IfcClash экспортирует BCF v2, тогда как AC29 UI поддерживает BCF3. У bcf-client pyproject GPLv3 classifier, в общем каталоге указано LGPL3+: юридический статус NOT_VERIFIED. В подпроектах pinned tag version=0.0.0, wheel и локальная установка не доказаны.

**Аудит B — польза и дублирование.** Канон rev182: A11.S03 PARTIAL, S08/S10 BLOCKED, A07.S03 READY. IFCTESTER и IFCCLASH уже входят в 61 кандидата; IfcFM не выделен отдельно. Не дублировать PR154 PDF vectors, PR159/162 CloneNativeGroupV1, PR167 BCF sidecar и PR170 IFC geometry. IfcFM duplicate_keys перезаписывает записи, federate пропускает повторы: lossless НЕ доказан. IDS import и BCF/PDF native import не запускались, поскольку изменяют PLN.

Оба аудита выполнены как независимая повторная оценка тех же 30 SOURCE-проверок. SOURCE=30; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_CHECKED; ACCEPTED=NO. Opera NOT_VERIFIED: новая вкладка потребовала интерактивного подтверждения. MODEL_MODE_NOT_VERIFIABLE.
