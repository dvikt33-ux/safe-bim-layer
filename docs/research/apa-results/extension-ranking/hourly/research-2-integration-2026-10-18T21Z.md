# APA AC29 — исследователь №2, 2026-10-18 21Z

Исследование подключения готовых решений к существующему APA. Проверены реестр 61 кандидата, очередь координатора №3 20Z, отчёт №1 21Z, план revision182. Новых установок, запусков Archicad, изменений кода, PLN, APX или main не проводилось. MODEL_MODE_NOT_VERIFIABLE.

## Существенное уточнение

В PR173 появился отчёт LIVE-02: два Hotlink размещены одним нативным вызовом CreateHotlinkInstances; сохранённый снимок повторно открыт, 69→119 GUID. Поздняя рабочая копия изменилась, поэтому принят только побайтово подтверждённый снимок, а не вся рабочая PLN. Это историческое подтверждение, не новый LIVE в данном исследовании.

В PR168 уже применяется ezdxf.recursive_decompose, раскрывающий MINSERT. Новый движок не требуется. Необходимо отдельно проверить учёт каждой ячейки MINSERT и активные XCLIP: библиотека не применяет обрезку при декомпозиции.

## Предварительный выбор

Hotlink — reuse; MINSERT/XCLIP — adapter в существующем C1; IFC MEP owner/peer — adapter через pinned util.system; mapped transform — adapter через util.placement; Publisher — предварительный whitelist; PDF→IFC provenance — IFC copy; 4D/5D — только чтение.

Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/173
Источник: https://github.com/dvikt33-ux/safe-bim-layer/pull/168
Источник: https://github.com/IfcOpenShell/IfcOpenShell/tree/ifcopenshell-python-0.8.5
Источник: https://github.com/mozman/ezdxf/tree/v1.4.5

Доказательства и полная матрица — в отдельных приложениях этого часа. SOURCE, не BUILD/INSTALLED/LIVE/ACCEPTED. Ускорение не измерялось.
