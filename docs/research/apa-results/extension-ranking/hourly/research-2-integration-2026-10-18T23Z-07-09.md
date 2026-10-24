# Проверки 07–09 — B2 isolation

07. **Версия пакетов?** PR167 строки 85–89: `importlib.metadata.version`, все `==0.8.5`. Вердикт pin подтверждён в коде, локальный runtime не проверен. Далее output gate.

08. **Можно ли перезаписать IFC?** строки 37–52: `not out.exists()`, output вне STABLE; строки 92–97: temporary `source.ifc` и hash. Вердикт REUSE private-copy. Далее GUID.

09. **Полнота ExtractElements?** строки 119–129: `expected <= readback GlobalId`, `geometryEquivalenceVerified=False`. Вердикт GUID subset ≠ геометрическая идентичность; далее BCF.

Источник: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-ifc-artifacts-b2-20261018/scripts/apa_ifc_artifacts_b2.py
