# APA — восстановление отчёта: Native Hotlink identity и MEP Transition

- **Дата восстановления:** 2026-10-10
- **Original Run ID:** `APA-RUN-20261010-112034Z-HOTLINK-MEP-277E19`
- **Provenance:** `RECOVERED_FROM_CHAT`; факты ниже изложены в ранее выданном отчёте, который по целевому GitHub path давал 404. Нынешнее восстановление — не повторный исходный аудит.
- **ПЛАН:** APA-P10 — Независимый технический аудит AC29
- **ДЕЙСТВИЕ:** APA-P10.A01 — SDK и нативная модель; связанный APA-P10.A02 — инструменты и интеграции
- **ТЕКУЩИЙ ПОДШАГ:** APA-P10.A01.S02 — связи элементов/атрибутов и APA-P10.A02.S04 — MEP
- **SOURCE:** `REPORTED_FROM_PRIOR_CHAT`; **OFFLINE:** NOT_RUN; **BUILD:** NOT_RUN; **LIVE:** NOT_VERIFIED; **PERFORMANCE:** NOT_MEASURED.
- **Версия:** Graphisoft Archicad API DevKit 29.3100, целевой Archicad 29 build 5101.

## APA-HOTLINK-01 — нативная таблица соответствия GUID

**Первоисточник:** https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/group___hotlink.html

**Названные в предыдущем аудите прочитанные разделы:** `ACAPI_Hotlink_GetHotlinkProxyElementTable`, `ACAPI_Hotlink_GetHotLinkOwner`, `ACAPI_Hotlink_GetHotlinkNodes`, `ACAPI_Hotlink_GetHotlinkNodeTree`, `ACAPI_Hotlink_GetHotlinkSourceStatus`. Предыдущий отчёт привёл Git blob SHA `277e31227ecd2614bff0a3895eff3bcd3a5b58fe` (повторно не сверялся).

**Проверенный, по сообщениям предыдущего прохода, факт:** `GetHotlinkProxyElementTable` даёт сопоставление GUID размещённого proxy элемента и GUID исходного элемента Hotlink. `GetHotLinkOwner` определяет модуль-владелец, `GetHotlinkNodeTree` отражает вложенные модули, `GetHotlinkSourceStatus` — доступность источника. Поддержка вложенных модулей в Archicad 29: https://help.graphisoft.com/AC/29/INT/_AC29_Help/080_Collaboration/080_Collaboration-60.htm .

**Выгода:** повторяемые секции, этажи, блоки сохраняют устойчивое сопоставление происхождения элемента, без неоднозначного сопоставления по одинаковой геометрии.

**Сравнение:** native Hotlink API (предпочтительно для PLN) / геометрическое сопоставление в Model Dump (дополнительная контрольная проверка) / IFC (для внешних моделей; не заменяет внутренний Hotlink identity).

**Решение:** ИНТЕГРИРОВАТЬ read-only адаптер; не реализовывать собственный GUID matching по геометрии как основной источник. **Риски:** GUID исходного элемента ≠ GUID экземпляра ≠ GUID самого Hotlink; обновление/разрыв/удаление Hotlink меняет PLN, запрещено в текущем исследовании; BIMcloud/Teamwork доступ зависит от окружения. Graphisoft SDK — не независимый пакет MIT/Apache. Иностранный платный ИИ не требуется.

**Следующий read-only тест:** два экземпляра одного модуля на отдельном тестовом PLN; получить owner/source mappings и дерево, сверить с Model Dump; ни одной записи в PLN.

## APA-MEP-TRANSITION-01 — готовые параметры инженерных переходов

**Первоисточник:** https://github.com/GRAPHISOFT/archicad-api-devkit/blob/29.3100/docs/class_a_c_a_p_i_1_1_m_e_p_1_1_transition.html

**Названные прочитанные разделы:** `GetRoutingNodeId`, `GetNarrowerPortID`, `GetWiderPortID`, `GetPreferenceTable`, `IsControlledByPreference`, `GetLength`, `GetOffsetY`, `GetOffsetZ`. Предыдущий отчёт привёл blob SHA `19474cf0273a9d7b226ddcbaafad5f15b3a57012` (повторно не сверялся).

**Ранее сообщённый факт:** `ACAPI::MEP::Transition` содержит привязку к узлу трассы, более узкому/широкому портам, геометрию перехода и информацию, определяется ли переход таблицей предпочтений; `GetPreferenceTable()` применима к трубопроводам и воздуховодам, но возвращает ошибку для CableCarrier. Наличие таблицы предпочтений не подтверждает соблюдение нормативов; логическое соединение портов не гарантирует физическое.

**Выгода:** извлекать MEP-семантику напрямую вместо обратного вычисления параметров перехода по BREP/полигональной геометрии. **Решение:** ИНТЕГРИРОВАТЬ выборочно с проверкой типа системы и предусловий; Tapir может уже покрывать часть полей, требуется сравнение перед написанием нового адаптера.

**Сравнение:** native MEP API (точная нативная семантика, нужен native Add-on) / Tapir MEP JSON (дешевле интеграция, покрытие переходов не подтверждено) / собственный геометрический анализ (дорого и неоднозначно; отклонить для MVP).

**Совместимость/стоимость:** DevKit 29.3100 документирует класс для AC29; независимой платной облачной модели не нужно; лицензия и конкретные права installed Archicad 29 требуют проверки. **LIVE NOT_VERIFIED**, manual MEP availability не доказывает API-доступ.

**Следующий тест:** на изолированном тестовом проекте только читать порты/узлы двух-трёх переходов, включая CableCarrier; сверить Tapir и интерфейс Archicad, GUID до/после.

## Передача аудитору и критерии принятия

1. Сверить указанные Doxygen-разделы, pinned tag 29.3100, сигнатуры в SDK headers, предыдущие blob SHA.
2. Проверить направление mapping Hotlink (proxy/source) и типы GUID на реальном read-only примере.
3. Доказать документированное исключение CableCarrier и проверить семантику MEP preference.
4. Оценить дублирование с Tapir 1.5.10 прежде чем планировать нативный код.
5. `REPORTED_FROM_PRIOR_CHAT` нельзя повышать в SOURCE_VERIFIED без повторного чтения, а тем более в BUILD/LIVE без испытаний.

**Публикация отчёта фиксируется отдельным GitHub commit/readback; сам документ не содержит самоцитирующий commit SHA.**
