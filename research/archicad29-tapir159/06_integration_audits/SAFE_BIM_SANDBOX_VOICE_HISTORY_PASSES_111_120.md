# Safe BIM focused passes 111–120 — sandbox, voice, history, contextual assistance

Date: 2026-09-27
Research-only. No product changes. No Live BIM writes.

These passes follow the intermediate audit after pass 110 and target the ten highest-value unknowns.

---

## Pass 111 — dependency closure for a Design Option sandbox

**Finding: host/dependency graph is real and must be cloned explicitly.**

Examples from exact Archicad API structures:

- `API_WindowType.owner` is the GUID of the container wall.
- labels expose parent/association fields.
- dimension elements contain references to dimensioned points/elements.
- element memos can contain additional geometry/subelement information.

Therefore a sandbox implementation cannot simply duplicate arbitrary selected GUIDs independently.

### Proposed clone classes

**Class S1 — standalone**
- Morph;
- simple independent 2D elements;
- simple free-standing elements with no host relation.

**Class S2 — simple structural host**
- wall/slab/roof/mesh;
- clone base geometry first.

**Class S3 — hosted tree**
- wall + doors/windows/openings;
- host must be cloned first;
- children must be recreated against new host GUID.

**Class S4 — associative annotations**
- labels;
- dimensions;
- markers and similar dependents.

**Class S5 — graph/derived relations**
- SEO/trim relations;
- MEP topology;
- complex stairs/railings/curtain-wall subelements;
- other multi-object systems.

Initial sandbox prototype should support S1/S2 only, then wall+opening S3 after a dedicated live probe. Universal sandbox claim is prohibited until each class is certified.

Sources:
- Graphisoft `API_WindowType.owner`;
- Graphisoft Element Manager (`ACAPI_Element_Get`, `GetMemo`, `Create`, `CreateExt`).

---

## Pass 112 — sandbox proposal review through Mark-Up

**Finding: original ↔ modified pair is a first-class API concept.**

`ACAPI_Markup_AttachElements(..., APIMarkUpComponent_Modification, modificationElemTable)` explicitly accepts a table of original and modified element GUID pairs.

This is a strong fit for Safe BIM sandbox review because the system already needs exactly that mapping.

Recommended proposal record:

```yaml
stage_id: SB-184
sandbox_option: SAFE BIM SANDBOX / SB-184
markup_issue: SAFE BIM SB-184
pairs:
  original_guid_A: proposal_guid_A
  original_guid_B: proposal_guid_B
new_elements: [...]
deleted_candidates: [...]
```

The mapping can also live in SQLite and be mirrored in project-local Element Set/UserData.

Open UX question: exact appearance/usability in the Archicad Mark-Up palette needs a live UI prototype, but the mapping API itself is confirmed.

Source:
- Graphisoft Issue management / `ACAPI_Markup_AttachElements`.

---

## Pass 113 — accept/reject semantics for the sandbox

**Finding: deterministic replay is safer than silently replacing originals.**

Three theoretical acceptance strategies:

### A. Relink/replace originals with sandbox duplicates
Risk: high for dependent GUID relationships, annotations and external references.

### B. Delete original, move proposal to main model
Risk: original GUID identity is lost; downstream links may break.

### C. Replay the verified recipe against originals inside one native undoable Safe BIM command
Risk: still requires normal write safety, but preserves original identity where operation is a modify and allows exact verifier/readback.

**Preferred design: C.**

Sandbox is a visual and geometric proof environment. Accept compiles an explicit delta/recipe and applies it to original GUIDs under normal Safe BIM receipts/verifiers. Reject simply destroys proposal objects/option/issue after confirmation.

For operations where preserving original GUID is not relevant (new elements), Accept can create production elements from the verified proposal recipe rather than moving untrusted proposal GUIDs blindly.

---

## Pass 114 — checkpoint strategy: solo project vs Teamwork

**Finding: one checkpoint mechanism cannot safely cover both.**

### Solo PLN

Confirmed API:
- current project location/path is readable;
- `ACAPI_ProjectOperation_Save` can save project formats and is a complete operation outside command scopes.

Still to verify live:
- safest automatic backup-copy operation that does not unexpectedly switch active document/path.

Until certified, conservative plan:
1. save current PLN;
2. obtain exact file path;
3. create external filesystem copy only after Archicad Save succeeds and file handle behavior is verified on Windows;
4. store checksum/path in Safe BIM checkpoint ledger.

### Teamwork

Teamwork API provides reservation, ownership, online state and Send/Receive Changes. A local PLN copy is not an equivalent rollback checkpoint for a shared BIMcloud project.

Therefore Safe BIM must detect Teamwork and use a separate policy. No automated “restore whole project” should be promised until BIMcloud/Teamwork recovery semantics are explicitly designed and tested.

Source:
- Graphisoft Project Operations;
- Graphisoft Teamwork API.

---

## Pass 115 — Safe BIM history data model

**Finding: hybrid persistence is preferable.**

Use three layers:

### External SQLite — canonical execution ledger
Stores crash-recovery details:
- stage/job IDs;
- dispatch attempts;
- receipts;
- fingerprints;
- checkpoint path/hash;
- verification result;
- UNKNOWN_OUTCOME evidence.

### Project-local Add-On data / ModulData
Stores project identity + Safe BIM history index that should travel with the PLN.

### Element UserData / Element Sets
Stores optional links from actual elements to:
- stage ID;
- recipe ID/version;
- proposal set;
- known-fix provenance.

Element Sets automatically manage GUID lists across merge/paste ID collisions and accept custom user data, which is useful for a stage/proposal collection.

This architecture avoids relying on a single store for both crash durability and project portability.

Sources:
- Graphisoft Custom User Data;
- Graphisoft Element Set Manager.

---

## Pass 116 — passive contextual suggestions and EditNotificationInterface

**Finding: post-edit suggestions are feasible; native hover interception remains unproven.**

Archicad 29 introduces `ACAPI::EditNotificationInterface`, described as executing after element editing.

Safe BIM can therefore:

1. receive edit completion;
2. inspect edited GUIDs and local topology;
3. run fast deterministic matcher;
4. show a palette/notification suggestion such as:
   `Знакомый случай: junction_v7 — пересечь стены`;
5. temporarily highlight target elements/geometry;
6. execute only after user clicks.

This is better supported than trying to inject behavior into every native Wall-tool mouse move.

For active Safe BIM helper mode, custom user-input rubber lines and Pet Palette can provide the more interactive “bring wall to target” visual behavior.

Sources:
- Graphisoft Archicad 29 New Features / EditNotificationInterface;
- user-input rubber lines;
- API Pet Palette.

---

## Pass 117 — visible QA and proposal overlay

**Finding: use multiple visual mechanisms for different jobs.**

Recommended hierarchy:

1. **Temporary highlight** — immediate errors/selections; no model mutation.
2. **Rubber feedback line** — interactive proposed geometric continuation while Safe BIM owns input mode.
3. **Renovation graphic override** — persistent visual distinction for staged/new proposal elements.
4. **Mark-Up issue** — persistent reviewed change set/original↔modified mapping.
5. **Design Option** — actual geometry isolation.

Do not overload Renovation as isolation or temporary highlight as persistence.

This separation minimizes model contamination and makes visual semantics understandable.

---

## Pass 118 — Russian voice engine choice

Two strong CPU-oriented candidates remain:

### whisper.cpp tiny/base

Documented approximate memory:
- tiny: ~273 MB;
- base: ~388 MB;
- small: ~852 MB.

Advantages:
- mature C/C++;
- multilingual;
- quantization;
- Windows support;
- can be fully process-isolated.

### sherpa-onnx small Zipformer RU

Dedicated Russian model is documented and Windows executable/C/C++ API are supported. Example config uses `provider=cpu`, `num_threads=1`.

Advantages:
- dedicated Russian ASR model;
- streaming/non-streaming/VAD toolchain;
- stable native C API;
- potentially lower latency for short Russian commands.

**Decision:** no paper winner. Build a small benchmark harness on target Legion using 30–50 architectural utterances. Measure:
- cold start;
- first transcription latency;
- warm latency;
- CPU usage;
- RAM;
- exact slot accuracy for terms such as “толщина”, “конструкция”, “высота”, “штриховка”, “перекрытие”, “сопряжение”, “оси”.

General LLM must not be used unless deterministic parser rejects the transcript.

Sources:
- whisper.cpp README;
- sherpa-onnx Russian model docs.

---

## Pass 119 — BIBIM AI provider compatibility boundary

BIBIM public README confirms:

- direct BYOK providers: Anthropic/OpenAI/Google;
- local OpenAI-compatible Ollama/LM Studio/vLLM;
- Windows config location `%APPDATA%\BIBIM\rag_config.json`;
- keys protected with DPAPI;
- localhost bridge uses per-launch auth token from a handshake file;
- bridge exists between BIBIM add-on and its own desktop UI.

### Safe integration

**Local provider:** Safe BIM can point at the same OpenAI-compatible local endpoint. This achieves the user experience “the same AI works in both” without coupling to BIBIM internals.

**Cloud:** Safe BIM should allow explicit provider/model/base-url import if non-secret BIBIM config fields are proven stable. Secret key should be entered/imported explicitly into Safe BIM protected storage; no silent DPAPI extraction.

**BIBIM bridge:** do not make it a core dependency until the bridge endpoints/auth contract are audited in source. The README does not define a stable third-party API.

Source:
- `SquareZero-Inc/bibim-archicad/README.md`, Apache 2.0.

---

## Pass 120 — deterministic similar-fill and similar-wall selector

**Finding: sufficient API fields exist for deterministic filtering.**

For Fill/Hatch, API exposes fields including:

- `fillInd` (fill attribute);
- `fillPen`;
- `fillBGPen`;
- `foregroundRGB` / `backgroundRGB` where relevant;
- hatch subtype/category/orientation fields.

This supports the user case “выбрать одинаковые серые штриховки” without image similarity: criteria can explicitly match fill attribute + foreground/background pen/RGB.

For Walls, selector criteria can be built from exact semantic properties instead of length:

- element type;
- structure type;
- basic/composite/profile identity;
- thickness;
- height;
- story;
- layer;
- Building Material/priority if requested;
- renovation status.

Voice input only changes checkboxes; the selector shows the interpreted criteria before applying selection.

Sources:
- Graphisoft `API_HatchType` / fill-related members;
- `API_FilltypeType`;
- existing Wall API contracts.

---

# Result after pass 120

The remaining blockers are now narrow enough for a prefinal audit:

1. Design Option sandbox dependency closure must be certified incrementally by element class.
2. Solo checkpoint “backup copy without changing active file” needs a controlled Windows/Archicad probe.
3. Teamwork needs a distinct checkpoint/recovery design.
4. Native grouped Undo needs a Safe BIM-owned C++ executor; Tapir multi-call stages must not be advertised as single Undo yet.
5. Voice engine selection requires benchmark, not more documentation.
6. BIBIM direct bridge reuse remains optional and blocked on source/API stability audit.
7. Passive suggestions should start as post-edit notifications + Safe BIM helper mode; do not attempt invasive native-tool interception in v1.

No Live BIM writes were performed in passes 111–120.