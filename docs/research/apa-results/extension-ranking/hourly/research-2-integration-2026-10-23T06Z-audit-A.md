# Counteraudit A — mutation authority vs typed contracts (SOURCE-only)

Independent angle: inspect the WRITE path rather than trusting PR summaries.

1. SceneWriter `execute` authorizes each graph step with `approval_record.permission=command`; `CreateSlabs` is approved and SQLite intent committed before CREATE (scripts/archicad_scene_run.py, pinned blob 484c600a).
2. When `slabBasicMaterialGuid` exists, the same step creates a new `modify_intent` for `ModifySlabs` and persists `BASIC_MODIFY_ATTEMPTED` BEFORE calling `self.api("ModifySlabs",modify)`. This is a valuable crash-safe journal, but the inspected path has NO independent `ModifySlabs` permission check or separate approved graph step. Nested CREATE approval is not proof of separately scoped MODIFY permission.
3. PR149 `apa_ac29_existing_modify_verifiers.py` permits material-only modification of one pre-existing Basic Slab on floorIndex 0; it disallows thickness. It is NOT equivalent to PR74's compound new slab mutation with thickness and upper story.
4. Graph `compile_graph` validates typed host GUID and JSON schema, but not an explicit second mutation permission in this compound path.

**Counterfinding A-01:** G2/G3 authorization gap at SOURCE. Do NOT execute just to inspect schema. Minimum fix/decision: extend existing step authorization to explicitly include the exact second command, parameters, created GUID and plan hash; preserve original SceneWriter/SQLite. Owner BUILD-01 executor. READY only when independent policy audit proves both commands allowed and no replay on UNKNOWN. No code edited here.

Sources: https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/scripts/archicad_scene_run.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-existing-create-verifiers-20261017/scripts/apa_ac29_existing_modify_verifiers.py ; https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-automatic-group-routing-20261018/scripts/archicad_bim_graph.py

OFFLINE=0 BUILD=0 INSTALLED=0 LIVE=0 ACCEPTED=0.
