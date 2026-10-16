# APA BDD дом — блокировка STORY_MISMATCH и исправление read-only проверки

Дата: 2026-10-16; код в ветке `fix/apa-bdd-readonly-story-binding-20261016`, draft PR #122.

## Фактическое наблюдение

- Пользователь запустил `scripts/apa_bdd_existing_router_readback.py --publish`, branch `feature/apa-bdd-live-router-readback-20261016`, Archicad 29 build 5101 / port 19727.
- Результат: `APA ROUTER BLOCKED: ValueError STORY_MISMATCH: active story must match pinned binding`; exit code **2**.
- Приватный диагностический файл: https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/safe-bim-mailbox/gpt-live/results/apa-bdd-existing-router-20261016T162036Z-459ed1c1.json
- Отчёт подтверждает статус `BLOCKED_NO_MODEL_MUTATION_REQUESTED`, `writeRequested=false`.

## Где именно предпосылка неверна

В `scripts/archicad_scene_run.py` функция `guarded_project(api,required_story=None)` при `required_story=None` требует `actStory==0`, `floor[0].floorId==1`, `floor[0].level==0.0`. В режиме 3D или на другом активном этаже `actStory` может отличаться от индекса первого этажа. Это не означает отсутствия первого этажа или неправильного PLN. **Из опубликованного файла невозможно узнать фактическое значение actStory**, потому что исполнитель завершился с ошибкой до публикации подробной модели. Возможно также несоответствие floorId/level, оно станет явным при новой проверке.

Эта проверка вызывается дважды на read-only маршруте: непосредственно из `apa_bdd_existing_router_readback.py`, а также из `DynamicCommands.read()`. Она нужна для безопасности мутирующего `SceneWriter`, но UI view не является основанием запрещать только чтение native-модели.

## Минимальное изменение существующего APA

1. Новая `archicad_scene_run.guarded_project_for_read(api)` в **том же** существующем модуле: точные сохранённые путь и имя PLN, запрет untitled/Teamwork, обязательный первый этаж с GUID-совместимой парой `index=0/floorId=1/level=0`, структура этажей, установленный Tapir 1.5.10. Отдельно регистрирует текущий `actStory` и полную топологию этажей в итоговой квитанции, **не требует** `actStory==0`.
2. `DynamicCommands.read()` использует эту функцию для GET-команд.
3. Read-only launcher дважды сверяет новый проектный binding (до и после графа), полный комплект 261 GUID и SHA исходного/рабочего файлов, `api.write_attempts=0`.
4. **Мутирующий `SceneWriter.guarded_binding()` и `guarded_project()` НЕ ИЗМЕНЕНЫ:** при записи требование активного этажа сохранено.
5. Нет второго API dispatcher, нового SceneWriter, дополнительной SQLite-БД, новых model writes или изменения пользователя UI.

## Статус

`OFFLINE_TEST_PASS` для верхних/3D видов и отсутствия послаблений write guard. Статус `LIVE_APA_ROUTE_PASS` **не подтверждён**, пока новая версия не запущена на реальном Archicad. Обновлённый запуск выполнится без создания/изменения/сохранения элементов; при ошибке автоматически выгрузит отчёт в GitHub.

Следующий шаг: `gh repo clone ... --branch fix/apa-bdd-readonly-story-binding-20261016` в новый временный каталог и `scripts/apa_bdd_existing_router_readback.py --publish`; проверить отчёт самостоятельно через GitHub, не требуя пересылки консольных логов.