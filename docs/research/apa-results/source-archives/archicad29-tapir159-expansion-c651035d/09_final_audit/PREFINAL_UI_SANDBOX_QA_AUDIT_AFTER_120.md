# Prefinal Audit — Safe BIM Palette / Sandbox / History / QA after pass 120

Date: 2026-09-27
Status: prefinal architecture audit, research-only.

## User goals frozen for this audit

1. Russian compact palette, minimal workspace occupation.
2. One expandable main area.
3. Code panel may auto-collapse after execution.
4. AI panel opens/closes only by user toggle; never auto-closes after answer.
5. No PowerShell / separate visible AI application in normal workflow.
6. Pre-stage checkpoint.
7. One-stage Undo where technically guaranteed.
8. Safe BIM History with restore-to-stage capability.
9. Optional visual staging via Renovation.
10. Deep native sandbox research.
11. Continuous QA and visible model highlighting.
12. Similar-element checkbox selector.
13. Wall-junction/priority QA as a first-class requirement.
14. Voice can set selector/command fields using lightweight local recognition.
15. BIBIM-compatible AI provider reuse if it can be done without brittle secret/config coupling.
16. “Learn without ML”: verified recipes remembered and offered contextually.
17. One-click in-model/context suggestions for familiar corrections.

## Prefinal architecture verdict

The most coherent architecture is now:

```text
Russian Safe BIM Palette (collapsed by default)
             │
             ├── Deterministic UI actions
             │      ├─ Similar selector
             │      ├─ QA
             │      ├─ History
             │      └─ Known recipes
             │
             ├── Optional AI / voice broker
             │      └─ outputs typed intent/recipe only
             │
             └── Safe BIM Compiler / Runtime
                    │
                    ├─ Preflight
                    ├─ Checkpoint
                    ├─ Sandbox optional
                    ├─ Native grouped command where supported
                    ├─ exact receipt + readback
                    ├─ incremental QA
                    └─ History entry
```

The UI must never make AI the execution core.

---

# Protection stack verdict

## Layer 1 — checkpoint: REQUIRED for large stages

- Save must complete before model mutation.
- Solo and Teamwork need distinct checkpoint implementations.
- Exact solo backup-copy method remains a controlled implementation probe, not a documentation assumption.

## Layer 2 — native one-stage Undo: REQUIRED TARGET

- Confirmed possible when a Safe BIM C++ executor owns one `ACAPI_CallUndoableCommand` scope.
- Not guaranteed across arbitrary independent Tapir JSON calls.
- Future executor work should preserve Safe BIM durable receipt semantics around this command boundary.

## Layer 3 — sandbox: OPTIONAL but high-value

Best native candidate is **Design Options**.

Recommended v1 sandbox scope:
- standalone/simple elements first;
- wall/slab/mesh/morph/roof candidates after type certification;
- host trees only after dedicated dependency-clone probes.

Sandbox proposals should be paired with:
- Mark-Up original↔proposal mapping;
- Renovation/highlight for visual contrast;
- Safe BIM stage ledger.

## Layer 4 — visual staging: ALWAYS AVAILABLE

Use temporary highlights for ephemeral QA/targets; Renovation/Mark-Up for persistent proposal visibility.

---

# History verdict

A Photoshop-like experience is achievable for **Safe BIM-controlled stages**, not yet for the entire arbitrary Archicad native Undo history.

History entry must know:

- timestamp;
- project identity/modification stamp;
- stage/job ID;
- user-visible description;
- checkpoint ID/path/hash;
- exact original/created/modified GUIDs;
- recipe ID/version;
- native Undo label/availability;
- sandbox option/markup IDs if used;
- QA before/after;
- final verification state.

Restore UI should expose only operations that are actually available:

- `Undo stage` when native stage is still undoable;
- `Restore checkpoint` when a checkpoint exists and restore semantics are safe;
- `Reject sandbox` when proposal is isolated;
- never show fake rollback controls.

---

# Continuous QA verdict

Continuous deterministic QA should become a permanent service of the add-on, but it must be incremental and debounced.

Priority QA v1:

1. wall junction relation / priority / sequence / layer intersection group;
2. wall endpoint microgap / near miss;
3. host/opening consistency;
4. invalid/unverified Safe BIM receipt state;
5. duplicated/overlapping new proposal elements;
6. unclosed model contours where a type-specific deterministic check exists.

Processing rule:

`notification → changed GUID queue → debounce → local relation graph → checks → highlight/update issue count`

No heavy AI in this loop.

---

# Voice verdict

Use ASR + deterministic parser, not “a small chat AI”.

Candidate benchmark set:
- whisper.cpp tiny/base;
- sherpa-onnx small Russian Zipformer.

Voice result must update visible UI fields/checkboxes first. Destructive actions require normal Safe BIM confirmation policy.

---

# BIBIM compatibility verdict

Confirmed useful compatibility layer:

- same cloud provider families;
- same local OpenAI-compatible server family;
- BIBIM is Apache-2.0 and useful as source/reference.

Recommended implementation:
- Safe BIM has its own AI Broker;
- shared local Ollama/LM Studio/vLLM endpoint is first-class;
- optional explicit import of proven non-secret BIBIM settings later;
- no silent decryption of BIBIM DPAPI keys;
- no dependency on undocumented per-launch BIBIM bridge API.

This satisfies the user goal “the AI selected for BIBIM should be easy to reuse” without making Safe BIM fragile.

---

# Contextual assistance verdict

Two different mechanisms are required:

### Post-edit familiar-case suggestion
`EditNotificationInterface` → detect context → palette/bubble suggestion → click recipe.

### Interactive helper mode
Safe BIM owns user input → rubber line / custom pet palette → one-click geometric recipe.

Do not promise passive hover augmentation of every native Archicad tool in v1.

---

# Remaining uncertainties before final assembly audit

Only these topics still justify another short pass series:

1. finalize Safe BIM protection-mode state machine;
2. define stage history data model and rollback precedence;
3. specify sandbox v1 supported element classes and refusal rules;
4. specify wall-junction QA algorithm and tolerance calibration plan;
5. specify continuous QA scheduler so it cannot slow Archicad;
6. specify exact palette state machine/collapse behavior;
7. define voice benchmark protocol and timeout/resource policy;
8. define AI provider broker contract and BIBIM compatibility boundary;
9. define known-recipe match scoring/refusal behavior;
10. create implementation backlog/order so safety foundations land before visual sugar.

No further broad ecosystem research is required for the final audit. The next passes should synthesize implementation contracts.