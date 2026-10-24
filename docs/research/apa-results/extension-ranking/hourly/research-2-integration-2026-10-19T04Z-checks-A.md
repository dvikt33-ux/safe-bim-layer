# APA №2 04Z — проверки 01–10 (SOURCE)

Каждый проход: вопрос → первоисточник → контракт → вердикт/следующий gate. Ссылки pinned: [APA branch](https://github.com/dvikt33-ux/safe-bim-layer/tree/research/apa-extension-ranking-hub-20261018), [Tapir 1.5.9](https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9), [Archicad-MCP v0.8.0](https://github.com/alesdev88/Archicad-MCP/tree/v0.8.0).

01. **Очередь:** актуальна ли №3? APA NEXT_RESEARCH_PRIORITIES.md blob 2cb49edc: последний аудит 18.10 20Z. VERDICT STALE; next: №3 должен обновить, №2 продолжает по последней.
02. **Свежий №1:** существует ли 04Z? research-1-20261019T04Z.md blob 926d9314: 27 SOURCE и шесть карточек. PASS source; next: адаптеры C1–C6.
03. **План:** не изменён? PROJECT_PLAN.json blob c2ab2f9d: revision=182, dispatch требует CAS, запрет второго scheduler. REUSE; next: не писать в план.
04. **Hotlink:** был ли LIVE? PR173 live02/receipt.json: 69→119 GUID, batchCount=2, nativeBatchCalls=1, saveCalls=1, reopenVerified=true. LIVE previous, ACCEPTED no; next: provenance QA, не replay.
05. **V2 Router:** существует ли путь? PR165 scripts/apa_high_density_session_factory_v2.py: 6 V1 + 12 V2, READ_ONLY, local-python, SHA manifest. REUSE; next: не создавать второй Router.
06. **IFC QA:** есть ли готовый CLI? PR154 scripts/apa_external_readonly.py: ids-validate → ifctester -r Json; whitelist subprocess, new JSON output. REUSE; next: executed/skipped gate.
07. **XML read:** что доступно? v0.8.0 core/schemes.py:90–107 read_schedule_scheme(path) читает экспорт без PLN. ADAPTER; next: XML fixture+SHA.
08. **XML tree:** сохраняются ли комментарии? v0.8.0 schemes/xml_io.py:33–43 ET.TreeBuilder(insert_comments=True,insert_pis=True). SOURCE; next: unknown nodes.
09. **Byte roundtrip:** точность? schemes/xml_io.py:85–118 round_trips_exactly, UTF-8, byte compare. ADAPTER; next: LF/CRLF negative.
10. **Property GUID binding:** offline? schemes/spec.py:119–145 bind(property GUID) без connection, Group/Name требует resolver. ADAPTER; next: compare GUID with Tapir inventory.

Новые OFFLINE/BUILD/INSTALLED/LIVE/ACCEPTED: НЕ ПРОВОДИЛИСЬ.
