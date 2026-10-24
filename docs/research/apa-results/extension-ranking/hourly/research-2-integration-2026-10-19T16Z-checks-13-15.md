# APA №2 16Z — SOURCE проверки 13–15
13. GraphicOverrideCriterion.cpp L1123: elementType early return can ignore layer in same object. ADAPTER: reject multi-key leaf; next OFFLINE fixture. SOURCE https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicOverrideCriterion.cpp
14. GraphicOverrideCommands.cpp L229: criterion and criterionXML together rejected; neither uses default. ADAPTER: exactly one required; next two negative fixtures. SOURCE https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.7.2/archicad-addon/Sources/GraphicOverrideCommands.cpp
15. Same source L319: GetGraphicOverrideRules silently skips failed GetOverrideRuleById. ADAPTER: count/ID reconciliation; next missing-rule fixture.
