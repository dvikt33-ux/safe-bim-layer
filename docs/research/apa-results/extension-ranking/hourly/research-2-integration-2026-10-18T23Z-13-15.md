# Проверки 13–15 — IfcFM parser

13. **Как выбирается профиль?** IfcFM `__init__.py:78–99`: `Parser(preset="basic")`, `get_presets_configs`; `cobie24` явный. Вердикт использовать фиксированный preset; далее ключи.

14. **Как обрабатываются дубли?** `:100–128`: `duplicate_keys.append(...)`, затем `categories[category][key]=data` перезаписывает запись. Вердикт fail-closed при duplicates; далее federate.

15. **Federate lossless?** `:130–143`: повторный ключ → `continue`, пропуск строки. Вердикт не применять federate без отчёта конфликтов; далее Writer.

Источник: https://github.com/IfcOpenShell/IfcOpenShell/blob/ifcopenshell-python-0.8.5/src/ifcfm/ifcfm/__init__.py
