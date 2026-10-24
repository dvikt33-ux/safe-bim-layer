# APA №2 20Z — проверки 01–10 (SOURCE)

Каждая строка: вопрос → источник/контракт → контрааудит/следующий вопрос. Никаких новых LIVE.

01. Hotlink сохранён? [H] `44→69 GUID; importedElementsVerified=24; reopenVerified=true`. Да, прежний scratch; далее scope.
02. Узел виден до размещения? [HR] `GetHotlinks` пуст после успешного CreateHotlinkNodes. Нет; GUID ответа → затем readback.
03. Был replay? [H] `nativeCalls=2; saveCalls=1; nodeReplayCount=0`. По квитанции нет; далее журнал.
04. CloseProject закрыл? [R] success, проект остался открыт. Ответ недостаточен; далее no-open-project.
05. OpenProject без проекта? [R] code 4001, GUI reopen. Не доказан API путь; далее hash.
06. PR165 уже проверяет MEP? [P] `nativeMEPConnectionVerified=false`, только counts. Нет; далее порты.
07. Порты IFC4/2X3? [S] `get_ports` L91–108: `IsNestedBy/HasPorts`, `flow_direction`. Reader готов; далее peer.
08. Связанный порт? [S] `get_connected_port` L111–115: `ConnectedTo/From`, 0..1. Не PLN; далее owner.
09. Владелец порта? [S] `get_port_element` L118–127: `Nests/ContainedIn`. Нужен GUID; далее направление.
10. Соседи? [S] `get_connected_to/from` L130–156. Готовые списки; проверить reciprocity.

[H]: https://github.com/dvikt33-ux/safe-bim-layer/blob/b3a373243e10a4a6752b0b379c9b51005a663f73/docs/evidence/apa-ac29-hotlink-20261018/receipt.json
[HR]: https://github.com/dvikt33-ux/safe-bim-layer/blob/b3a373243e10a4a6752b0b379c9b51005a663f73/docs/evidence/apa-ac29-hotlink-20261018/README_RU.md
[R]: https://github.com/dvikt33-ux/safe-bim-layer/blob/b3a373243e10a4a6752b0b379c9b51005a663f73/docs/evidence/apa-ac29-hotlink-20261018/reopen-proof.json
[P]: https://github.com/dvikt33-ux/safe-bim-layer/blob/5c0dc009e729db9834301b4a369512490a205ef7/scripts/apa_high_density_readonly_v2.py#L170-L192
[S]: https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcopenshell-python/ifcopenshell/util/system.py#L91-L156
