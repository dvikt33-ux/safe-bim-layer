# APA AC29 — два перекрёстных аудита, 2026-10-19 14Z

## А. Доказательства и совместимость
Пересчитаны канон rev182 (91 задача), матрица и реестр (по 61 уникальному ID), прочитаны №1 09Z, №2 14Z, pinned Tapir 1.7.2, ezdxf 1.4.5, IfcOpenShell 0.8.5 и Graphisoft SDK29 LICENSE. Source tag не доказывает наличие релизного APX в локальном AC29 5101. Обнаружены: необязательный ruleGroupName в rich schema, молчаливый пропуск unreadable rules, некорректность переноса AC30 active override на AC29. Вердикт SOURCE_PASS_WITH_GATES; installed/live NOT_VERIFIED.

## Б. Инженерная применимость и дублирование
Прочитаны PR #154 PDFVectors, #159 native groups, #160 hosted PDF preflight, #162 group-first через SceneWriter, #165 IFC ports, #168 DXF recursive_decompose, #170 IFC OBJ/GLB. Не нужен второй CloneNativeGroupV1, SceneWriter, DXF parser или IFC serializer. Нужны узкие adapters: override schema+per-item error, DXF XCLIP provenance, IFC validation, безопасный read-only inventory. SaveProject(projectPath), DeleteElements и legacy override upsert — потенциальные writes, не запускались. Вердикт ADAPTER_AFTER_GATES.

Статусы: SOURCE 30; OFFLINE 0; BUILD 0; INSTALLED 0; LIVE 0; ACCEPTED 0. Числа 0 означают новые запуски в этом аудите. MODEL_MODE_NOT_VERIFIABLE.
