# APA AC29 — 20Z, перекрёстный аудит А

**Доказательства и совместимость.** Проверены DevKit29.3000 Hotlink (blob 277e3122), Tapir1.5.9 CommandBase.cpp (c39e4f34), APA DynamicCommands (c05017ee). SDK, add-on и JSON-проверка APA — три уровня, не доказательство локальной версии Tapir1.5.10.

Graphisoft DevKit29.3000 LICENSE (1e1ec1f4) содержит специальное соглашение, не MIT; Tapir1.5.9 LICENSE (1cdb2cb9) — MIT. №1 должен заполнять лицензию в каждой карточке.

IfcOpenShell util/system.py 0.8.5 (39d92070) использует IFC4 IsNestedBy, IFC2X3 HasPorts; get_connected_port отдаёт первого peer; FLOW_DIRECTION содержит NOTEDEFINED. Это не доказательство полного native MEP графа.

В GitHub аудит 19Z по ожидаемым путям имеет только A 01–15 (blob bd99d110), B и tasks отсутствуют; исходный локальный файл требует восстановления. Статус PARTIAL/NOT_ACCEPTED.

Вердикт: SOURCE_VALID_WITH_GAPS. Новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0.
