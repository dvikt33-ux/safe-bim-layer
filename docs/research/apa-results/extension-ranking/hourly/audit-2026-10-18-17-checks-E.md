# Checks 21-25

21. PR165 V2 runtime requires existing V1 venv, installation.json, three source hashes (L334-349).
22. V2 subprocess timeout 1200s; output <200MiB checked after writing, partial-file cleanup not explicit (L353-378).
23. PR165 CI run 39150691598: 2/2 Windows jobs success on head 2e355dd8; acceptance states 21/21 tests each.
24. V1 IfcDiff -r selects relationships, not default geometry/attributes (apa_external_readonly.py L96-102).
25. Tapir 1.5.9 Publisher empty selection yields null pointer (NavigatorCommands.cpp L83-102).
