# APA №2 | 2026-10-24 08Z | Два документарных контрааудита

## A. Ложное равенство GH Roof и APA Roof по Favorite

Гипотеза: одинаковые Favorite, Building Material и Roof Pitch означают одинаковую native Roof геометрию и идентичную синхронизацию.

Фальсификация: Graphisoft AC29 GC.pdf стр.28 задаёт GH Roof pitch/elevation **входной плоскостью polygon** и прямо исключает влияние Favorite Pitch/Offset. Pinned PR74 CreateRoofs принимает Basic/pivotLine/material/story, polygon ограничен outline+0.35m; это не эквивалентный интерфейс. После изменения уклона двух Single-plane Roof Graphisoft Support (15.10.2025) описывает не обновившийся конёк и ручной rejoin. Совпадение Favorite не проверяет BREP ridge, normal, absolute Z, SEO или GUID.

Вердикт: FAVORITE_MATCH ≠ BIM_EQUIVALENCE. Требуется readback plane/normal/pitch/Z/pivot/story/GUID/material/BREP, пересечение конька и разрез, Save/Close/Reopen. Unattended rejoin без нового writer/ручного действия: NOT_FOUND.
Источники: https://help.graphisoft.com/AC/29/INT/GC.pdf ; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py ; https://support.graphisoft.com/hc/en-us/articles/24479784963089-My-roof-s-apex-connection-is-no-longer-clean-in-section.

## B. Ложная готовность G0 по static schema и Connected

Гипотеза: локальный файл Tapir schema и статус GH Connected достаточны для preflight и записи.

Фальсификация: PR74 catalog_with_provenance проверяет live origin, provider_version, SHA256 двух исходных JS и exact regenerated catalog; RUN.guarded_project проверяет реальный PLN/stories; отдельный GH port/document не гарантирует правильный .gh/.3dm/PLN. Аудитор №3 20.10 18Z отдельно предупреждает, что IsAlive не доказывает идентичность PLN. bind_authorized_saved_copy требует saved SHA256 и authorization_ref; наличие функции не означает разрешение G3.

Вердикт: G0 BLOCKED_RUNTIME, G1 NOT_RUN, G3 NOT_AUTHORIZED. Следующий шаг: read-only G0 manifest с фактическим APX/PLN/port/commands/materials/libraries; без fake transport и без LIVE.
Источники: https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_project_accelerator.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/5a3a9201a715a5528c93bed4a5318e2acb32eea7/scripts/archicad_scene_run.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-A.md ; https://github.com/dvikt33-ux/safe-bim-layer/blob/research/apa-extension-ranking-hub-20261018/docs/research/apa-results/extension-ranking/hourly/audit-2026-10-20-18-B.md.

**Ограничение:** это два внутренних документарных контрааудита, не независимый аудит №3 и не строительная экспертиза. MODEL_MODE_NOT_VERIFIABLE.
