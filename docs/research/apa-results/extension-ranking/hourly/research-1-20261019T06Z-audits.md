# APA №1 06Z — два независимых контрааудита

## А — первичность, версия, совместимость
Метод: проверить SOURCE отдельно от локальной применимости, сопоставить исходники фиксированного тега, лицензию, wheel, AC29/Tapir, ложные подтверждения.
1. **PASS SOURCE:** 30 контрактов и веток из восьми файлов `src/ifcopenshell-python/ifcopenshell/util/*.py` в теге `ifcopenshell-python-0.8.5`; не полагаться на online docs 0.9.0.
2. **PASS LICENSE:** заголовок `__init__.py` LGPL v3-or-later, `COPYING.LESSER`; условия распространения не проверены юристом.
3. **PASS PLATFORM METADATA:** PyPI 0.8.5 Win64 wheels Py3.11 SHA a994cb398aa822b0153ace11fc19deea108706d3a10339de9ac9dc13da21076d и Py3.12 SHA 7927921dbfd18024f44780880c37e48460bbca7476da3b0c2607e044b31521d5. Это не локальная установка.
4. **NOT_VERIFIED:** побайтовое соответствие колёс Git-тегу, версия фактического runtime, размеры IFC в 48 GB RAM, совместимость конкретного экспортёра AC29 build5101.
5. **NOT_APPLICABLE:** Tapir 1.5.10 не обязан предоставлять эти методы: это Python IFC utility вне Archicad. Нет новых APX/PLN операций.
6. **CONTRACT LIMIT:** P13 `TODO 2d`; P15/16/18/19/24 fallback без исключения; P06 no visited-set. Не повышать эти функции до полного QA.
7. **SOURCE vs runtime:** никаких вызовов методов, ни Windows fixture, ни benchmark не было. Публикация не означает ACCEPTED.
**Вердикт А:** 30/30 статических source inspections; совместимость «формат IFC и wheel Windows» подтверждена только на уровне метаданных; локальное применение НЕ ПРОВЕРЕНО.

## Б — инженерная польза, дублирование, приёмка
Метод: независимо сопоставить каждую функцию с уже существующими APA и с реальным архитектурным результатом.
1. **C1 HOST:** PR160 распознаёт PDF-метки, но не physical anchor; P01–04 дают IFC host chain, только если в экспорте существуют связи. Новый native creator не нужен.
2. **C2 TRANSFORM:** PR159/162 CloneNativeGroupV1 и PR173 batch Hotlink уже имеют собственные native операции; IFC mapped-transform нужен только для внешнего QA. 2D блокер P13.
3. **C3 GEO:** georeference без map source/CRS не доказывает правильную посадку здания; возвращаемые 0/identity — не инженерный факт. QGIS не переустанавливать.
4. **C4 GROUP:** IfcGroup не тождественен Archicad groupId; P06 может зависнуть на цикле — оценка риска, не воспроизведение. Не конвертировать в copy.
5. **C5 MATERIAL:** nominal IFC layers не равны native AC29 composite/BREP и не подтверждают СП/ГОСТ. Учитывать пустые и неоднородные material sets.
6. **C6 UNITS:** default scale=1 без UnitAssignment может ложно подтвердить площадь/объём; это обязательный QA gate до QTO, не сметный модуль.
7. **C7 GEOMETRY:** triangle volume non-manifold неопределён; item ID ≠ Archicad GUID. Не подменять native BREP readback.
8. **MEP:** P26–27 — уточнение уже открытой №2 задачи 05Z (IfcOpenShell util.system); новая карточка не создавалась, чтобы избежать дубликата.
9. **SAM/SAF:** A11.S08 BLOCKED, отсутствие аналитических членов/нагрузок нельзя исправить геометрией IfcWall; никаких ложных рекомендаций.
10. **No second writer:** все 7 карточек — существующий IfcOpenShell read-only; никакой новой установки/кодовой ветки.
**Вердикт Б:** C1/C2/C3/C6 наиболее полезны; все 7 — SOURCE кандидаты, 0 ACCEPTED. Баллы экспертные, без замеров.

**Статусы:** SOURCE=30; OFFLINE=NOT_RUN; BUILD=NOT_RUN; INSTALLED=NOT_VERIFIED; LIVE=NOT_RUN; ACCEPTED=NO. MODEL_MODE_NOT_VERIFIABLE.