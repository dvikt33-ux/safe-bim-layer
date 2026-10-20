# APA №2 — исследование способов интеграции, 2026-10-20 01Z

SOURCE-only. Выполнено 30 проверок первоисточников и два контрааудита. Новых OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED=0. MODEL_MODE_NOT_VERIFIABLE.

Основные находки: в tagged Tapir 1.5.9 уже существуют GetNavigatorItemTree (PublisherSets, publisherSetName, GUID children), CreateWindows и CreateDoors (ownerWallId, centerOffset, размеры, ориентация, favoriteName). Повторная разработка этих команд не нужна. В GetNavigatorItemTree ошибки чтения детей скрываются, поэтому полная инвентаризация Publisher без дополнительного контроля не доказана. Пустой whitelist Publish передаётся как nullptr и опасен. ezdxf1.4.5 игнорирует XCLIP при recursive_decompose; MINSERT уже обрабатывается, но zero spacing дедуплицирует позиции. IfcOpenShell0.8.5 get_connected_port возвращает первого peer; полный граф требует чтения IfcRelConnectsPorts. Готов get_referenced_elements для IFC2X3/IFC4. PR173 LIVE receipt не равен независимой бинарной приёмке; PR175 lease не блокирует внешние записи.

Источники: https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp ; https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ExtendedElementCommands.cpp ; https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py ; https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcopenshell-python/ifcopenshell/util/system.py .

Публикация частичная до дополнения матрицей и 30 адресными проверками; не считать полный отчёт завершённым.
