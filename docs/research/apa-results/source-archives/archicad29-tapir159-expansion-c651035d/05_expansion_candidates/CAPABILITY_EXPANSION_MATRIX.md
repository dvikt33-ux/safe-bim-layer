# Capability expansion matrix — AC29 / Tapir 1.5.9 / Safe BIM

States used here are research/integration states, not production permission.

- `EXISTING_PATH` — already present in the known Safe BIM dispatcher/runtime lineage; this research did not recertify it against 1.5.9.
- `SOURCE_READY` — source/schema contract is strong enough to design an offline Safe BIM operation.
- `OFFLINE_FIX_REQUIRED` — existing offline implementation contradicts/newer source semantics and must be corrected first.
- `PROBE_REQUIRED` — narrow controlled live evidence is still required.
- `DESIGN_REQUIRED` — ownership/reconciliation model must be designed before implementation.
- `READ_ONLY_CANDIDATE` — useful broadly but does not require write ownership.
- `GLOBAL_HIGH_RISK` — project/global side effect; separate risk class.

| Domain | Capability | Research state | Productivity value | Main remaining gate |
|---|---|---:|---:|---|
| Core geometry | straight Wall / plinth | EXISTING_PATH | High | recertify transport/schema baseline against 1.5.9 before broader changes |
| Core geometry | basic Slab | EXISTING_PATH | High | same version-baseline recertification |
| Openings | Window / Door | EXISTING_PATH | High | 1.5.9 has important floor-plan DB/default/Favorite reliability behavior; re-audit current adapter |
| Core geometry | Arc Wall | OFFLINE_FIX_REQUIRED + PROBE_REQUIRED | Medium | 1.5.9 readback contract + one sign/orientation probe |
| Site | Mesh | OFFLINE_FIX_REQUIRED + PROBE_REQUIRED | High | fix level/meshPolyZ semantics, then one controlled Z probe |
| Freeform | Morph box/body | OFFLINE_FIX_REQUIRED + PROBE_REQUIRED | Medium | rewrite verifier to real origin/axes/body, then probe |
| Roof | single-plane Roof | SOURCE_READY + PROBE_REQUIRED | High | pivot/positive-side probe + strict RoofDetails verifier |
| Roof | gable Roof | SOURCE_READY + PROBE_REQUIRED | High | implement as two verified single-plane roofs |
| Reuse | Favorites at Create | SOURCE_READY | Very high | Project Profile dependency preflight + operation wrappers |
| Reuse | Create Favorite from exemplar | SOURCE_READY | Very high | exact naming/version policy and controlled write wrapper |
| Reuse | Hotlink node | SOURCE_READY | Very high | immutable/versioned source-path policy |
| Reuse | Hotlink instance | SOURCE_READY + PROBE_REQUIRED | Very high | exact instance detail fixture/reconciliation probe |
| Reuse | SaveAsModuleFile | SOURCE_READY | Very high | external-file receipt/path policy |
| Parametric content | GDL/HSF -> GSM factory | DESIGN_REQUIRED | High | deterministic source skeleton/Main-ID + converter wrapper + first generated-object probe |
| Objects | Create/Modify Object/Lamp | SOURCE_READY + PROBE_REQUIRED | High | library Main-GUID preflight + strict placed-object/GDL verifier |
| Libraries | Get/Add/Set/Reload libraries | SOURCE_READY / GLOBAL_HIGH_RISK | High | classify Add vs Set; version/profile policy; reload timing |
| Resources | Attributes / Profiles | SOURCE_READY / GLOBAL_HIGH_RISK | High | semantic fingerprint and overwrite policy |
| Spatial | Zones | SOURCE_READY + PROBE_REQUIRED | High | geometry/area/boundary verifier; UpdateZones global node |
| Structural | Columns / Beams | SOURCE_READY + PROBE_REQUIRED | High | type-specific verifier/live fixture |
| Circulation | Stairs | SOURCE_READY + DESIGN_REQUIRED | Medium | hierarchy/baseline verifier; Favorite geometry caveats |
| Relations | SEO | SOURCE_READY + PROBE_REQUIRED | High | relation-tuple reconciliation live fixture |
| Relations | Trim elements | SOURCE_READY + PROBE_REQUIRED | High | exact trim relation readback fixture |
| Variants | Design Options | SOURCE_READY | High | lifecycle/migration policy; not transactional rollback |
| UX | GetSelectedElements | READ_ONLY_CANDIDATE | Very high | integrate exact-target adapter |
| UX | HighlightElements | READ_ONLY_CANDIDATE | High | preview lifecycle/clear policy |
| UX | ScriptUI | SOURCE_READY | High | WAITING_USER adapter + typed result schema |
| UX | GetPointFromUser | SOURCE_READY | High | isolate because JSON queue blocks until click/Escape |
| QA | Get3DBoundingBoxes | READ_ONLY_CANDIDATE | High | cheap spatial QA adapter |
| QA | GetCollisions | READ_ONLY_CANDIDATE | High | target-group policy; never ownership evidence |
| QA | Relations / Connected / Subelements | READ_ONLY_CANDIDATE | High | cache/adapters |
| Cache | Element notifications | READ_ONLY_CANDIDATE | High | dirty-hint only; never transaction evidence |
| Metadata | Properties / Classifications | SOURCE_READY | Very high | schema-specific exact value verifier and profile definitions |
| Metadata | Keynotes | SOURCE_READY | Medium | docs/semantic workflow integration |
| Docs | Sections / Interior Elevations / Details / Worksheets | SOURCE_READY + PROBE_REQUIRED | Very high | per-command identity/readback classification |
| Docs | Dimensions | SOURCE_READY + PROBE_REQUIRED | Very high | witness-point/section-ID verifier fixtures |
| Docs | Text / Labels / AutoText | SOURCE_READY + PROBE_REQUIRED | High | content/style readback subset |
| Docs | Views / View Settings | SOURCE_READY | Very high | navigator-ID readback + dirty graph |
| Docs | Layouts / Drawings | SOURCE_READY + DESIGN_REQUIRED | Very high | distinguish local modify vs replace identity transitions |
| Output | Publisher | GLOBAL_HIGH_RISK | High | filesystem/output receipt + no-blind-retry policy |
| Output | SaveProject | GLOBAL_HIGH_RISK | Medium | checkpoint policy + benchmark |
| Project | SetStories | GLOBAL_HIGH_RISK | Medium | destructive story deletion semantics; dedicated project-structure operation only |
| Project | GeoLocation | GLOBAL_HIGH_RISK | Medium | global-state verifier |
| Groups | Create/read groups | SOURCE_READY | Medium | group-ID + exact membership verifier |
| Teamwork | reserve/release/send/receive | DESIGN_REQUIRED | High in Teamwork | reservation state + conflicts + multi-user reconciliation |
| Interop | IFC reads/writes | DESIGN_REQUIRED | Medium | keep IFC identity separate from Archicad transaction ownership |
| Review | Issues / BCF | SOURCE_READY | High | external review workflow; not BIM ownership |
| MEP | routing/elements | DESIGN_REQUIRED | High | per-element contracts |
| MEP | connect/merge/split | DESIGN_REQUIRED | High | multi-object topology receipt/reconciliation design |
| AI | progressive certified tool discovery | SOURCE_READY | High | expose Safe BIM registry only, never raw writes |
| AI | optional local planner | SOURCE_READY | High | broker/resource benchmark/schema compiler tests |

## Priority conclusion

Highest payoff before widening element coverage:

1. Tapir 1.5.9 pin/version gate.
2. ProjectRecipe + Project Profile + capability/evidence registry.
3. Favorites / selection / highlight / ScriptUI.
4. Hotlink modules.
5. Filtered batched readback and cache/dirty graph.
6. Arc/Mesh/Morph/Roof corrected contracts/probes.
7. Model-to-document automation.
8. SEO/trims + GDL component factory.
9. Advanced structural/MEP/global operations only after dedicated safety designs.
