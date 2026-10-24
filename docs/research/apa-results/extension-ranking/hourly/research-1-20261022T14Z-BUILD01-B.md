# APA №1 — BUILD-01 — SOURCE 05–09 (G4)

Tapir upstream 1.7.2, MIT. SOURCE only, не INSTALLED/LIVE.

05. **Охват subelements?** [PR865](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/865): заявлены Stair/Railing/Curtain Wall, но автор требует проверить DevKit и индексы полигонов. **Решение:** не считать subelement mesh полной приёмкой. **№2:** независимый контроль по native BREP.

06. **AC29 quantities протестированы?** [PR860](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/860): заявлена сборка AC29, runtime-тест указан только для AC30 build3001. **Решение:** SOURCE/BUILD_CLAIM, не LIVE AC29. **№2:** не ставить в обязательный G4 без installed proof.

07. **Какие типы охвачены?** [PR860](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/860): Wall/Column/Beam/Slab/Roof/Shell/Morph/Zone и сегменты; Object не поддерживается. **№2:** окна/двери проверять отдельно по host/type.

08. **Ошибка одного GUID скрывается?** [PR860](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/860): unknown GUID, missing elementId, unsupported type дают per-item error. **№2:** fail-closed на любом обязательном GUID.

09. **Можно ли сверять composite skins?** [PR860](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/860): composites включают material, volume, area, core/finish; minOpeningSize меняет условные величины. **№2:** фиксировать параметры запроса, сравнить с официальными component properties.

**5 проверок, 2 первоисточника, 0 runtime тестов.** MODEL_MODE_NOT_VERIFIABLE.
