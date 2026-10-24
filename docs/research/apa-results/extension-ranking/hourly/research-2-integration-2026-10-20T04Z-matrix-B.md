# APA №2 04Z — матрица I04-04..06

| ID/польза | Путь | Решение/риск/ГОТОВО |
|---|---|---|
| I04-04 Hotlink placed/99 | Router→Tapir1.5.9 GetHotlinks+GetDetails→BIM Graph | REUSE/БЫСТРО; node/instance/owner GUID раздельно; MEDIUM |
| I04-05 Hotlink cached/99 | SDK29 Bridge→GetHotlinkNodes(unplaced)+Tree/Instances→Graph | ADAPTER/HIGH; ABI проверить; cached/placed/proxy/status и ошибки |
| I04-06 DXF visible/99 | PR189→PR168→ezdxf1.4.5 XClip+clipping | ADAPTER/HIGH; RAW/VISIBLE_2D/UNSUPPORTED, WCS/units/handles; end-to-end NOT_FOUND |
