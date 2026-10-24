# APA №2 04Z — проверки 11–14

11. Tapir upstream PR553: чужой AC29 тест cross-set опубликовал 23 вместо 7 PDF; fix 1.5.9. DENY чужие GUID; далее membership.
12. SDK29 API_NavigatorItem: guid и sourceGuid различны. REUSE оба; далее provenance.
13. Tapir1.5.9 ProjectCommands.cpp L638–695: GetHotlinks возвращает nodeId,name,type,location,children. REUSE.
14. hotlink_instances.py L17–19: GetHotlinks охватывает placed, не unplaced. PARTIAL; далее SDK29 cached.
