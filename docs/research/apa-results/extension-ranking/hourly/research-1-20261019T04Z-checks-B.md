# APA №1 04Z — предметные SOURCE-проверки P10–P18

Тег v0.8.0, коммит 74d4ecc67581e60b552b6ef7f6ac47d187e0f2a6. Для каждого: MIT внешнего кода, Graphisoft лицензия отдельно; Windows11/AC29 заявлены, локальный Tapir1.5.10/AC29 build5101/оборудование NOT_VERIFIED. SOURCE=VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=NOT_VERIFIED; ACCEPTED=NO; балл экспертный, ускорение не измерялось.

## P10 XML import AC29: независимый дефект (96/100)
**Первоисточник:** https://community.graphisoft.com/t5/Project-data-BIM/Schedule-xml-import-in-Archicad-29-is-removing-fields/td-p/683387 (Graphisoft Community 11–12.11.2025).
**Контракт:** После XML export/import исчезло поле 3D Axonometry, несмотря на присутствие в XML; подтверждено модератором.
**Польза/ограничение/задание №2:** Запрет автоматического импорта без сравнения полей; №2: найти фикс или точный критерий восстановления.

## P11 OBJ→GDL (86/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/gdl/mesh.py#L40-L80 (gdl/mesh.py L40–80).
**Контракт:** parse_obj извлекает вершины, UV и материальные группы.
**Польза/ограничение/задание №2:** Масштаб и текстуры требуют проверки; №2: сравнить с текущим LibPart.

## P12 3DS→GDL (84/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/gdl/mesh.py#L84-L235 (gdl/mesh.py L84–235).
**Контракт:** parse_3ds обрабатывает pivot, дубликаты и совпадающие вершины.
**Польза/ограничение/задание №2:** Дедуп по bbox/count может смешать объекты; №2: негативные 3DS fixtures.

## P13 HSF генератор (89/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/gdl/generate.py#L230-L474 (gdl/generate.py L230–474).
**Контракт:** build_hsf создаёт ancestry.xml, paramlist.xml, libpartdocs.xml, Script_3D.
**Польза/ограничение/задание №2:** Для GSM нужен LP_XMLConverter AC29; №2: подтвердить точную версию.

## P14 Стабильный MainGUID (88/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/gdl/generate.py#L371-L376 (gdl/generate.py L371–376).
**Контракт:** cfg.resolve_guid(name) записывается в MainGUID библиотечной детали.
**Польза/ограничение/задание №2:** Не GUID размещения; №2: конфликт GUID/замена объекта.

## P15 GDL CLI (82/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/gdl/cli.py#L123-L184 (gdl/cli.py L123–184).
**Контракт:** build-source принимает libpart.toml/params.toml/scripts; inspect выводит bbox.
**Польза/ограничение/задание №2:** Build запрещён в текущем цикле; №2: готовая отдельная CLI версия.

## P16 Рендер-проверка GSM (79/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/gdl/deploy.py#L66-L88 (gdl/deploy.py L66–88).
**Контракт:** preview_image_bytes и preview_png формируют изображение размещённого объекта.
**Польза/ограничение/задание №2:** Размещение/удаление меняют PLN; №2: offline-only альтернативы.

## P17 Разметка генплана (87/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/core/road_marking.py#L190-L280 (core/road_marking.py L190–280).
**Контракт:** create_road_marking принимает source_guid или points, поддерживает dry_run и update_guid.
**Польза/ограничение/задание №2:** Чужой GDL writer не подключать; №2: автономный read-only инструмент.

## P18 Прилегание к рельефу (91/100)
**Первоисточник:** https://github.com/alesdev88/Archicad-MCP/blob/v0.8.0/src/archicad_mcp/core/drape.py#L173-L258 (core/drape.py L173–258).
**Контракт:** Slab top = zCoordinate+offsetFromTop; Mesh z учитывает story+level+z; holes проверяются.
**Польза/ограничение/задание №2:** Только Mesh/Slab, нужна проверка топологии; №2: готовый валидатор.
