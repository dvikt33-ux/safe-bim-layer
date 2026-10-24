# APA №2 05Z — контрааудит A

Источник: PR #162, `archicad_project_accelerator.py`, функция `run_project`. Для `apa-authored-project/1` разрешены только `preflight` и `execute`; `offline` отклоняется до компиляции. Поэтому G1 не может получить OFFLINE_PASS через обычный CLI offline без дополнительного fixture/адаптера. `preflight` требует только чтение живого Archicad и не даёт LIVE-модель. Статус SOURCE_ONLY, G1 NOT_RUN.
