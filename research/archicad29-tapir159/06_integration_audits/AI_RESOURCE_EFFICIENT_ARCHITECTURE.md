# Resource-efficient AI integration audit — 18 passes

Goal: integrate AI into Safe BIM without leaving a heavy model resident in RAM/VRAM and without slowing Archicad, Twinmotion or deterministic Safe BIM execution. Research only; no production code changed.

## Design invariant

The AI is **not** the safety kernel and is never a direct model writer.

Trusted path:

`user text -> optional AI planner -> strict IntentPlan JSON -> deterministic validation/compilation -> immutable Safe BIM plan -> unload AI -> Safe BIM runtime -> Tapir -> exact-GUID read-back/reconciliation`

The model must not decide:

- `APPLIED` / `NOT_APPLIED` / `DONE`,
- ownership,
- whether an unknown-outcome write should be retried,
- project identity switching,
- safety policy or capability promotion,
- reconciliation result.

This preserves the existing fail-closed runtime even if the model hallucinates.

## Pass 01 — process boundary

Do not import an inference engine into `safe_bim_service.py`, `launcher.py` or the controller process. The current launcher starts only the Safe BIM runtime/controller; keep AI as an optional child/service reached over loopback.

Reason: process separation makes model RAM/VRAM reclaimable by unloading/terminating the inference worker without touching the runtime or SQLite executor.

Safe BIM sources:
- `launcher.py` at `c6ab4749...`
- `safe_bim_service.py` at `c6ab4749...`

## Pass 02 — plan-then-unload execution model

The strongest anti-contention design is not merely short TTL. It is a phase boundary:

1. AI produces a proposed structured plan.
2. Deterministic compiler validates all fields/capabilities/project assumptions.
3. User confirmation is obtained when required.
4. AI process/model is explicitly unloaded.
5. Only then may physical BIM execution begin.

This guarantees that local LLM VRAM is not needed while Tapir/Archicad is in the critical write/read-back/reconcile section.

Any later clarification opens a new planning phase; it does not keep the model resident throughout execution.

## Pass 03 — Ollama unload behavior

Ollama has an explicit memory residency control. API `keep_alive` controls how long a model remains loaded; default is 5 minutes. Sending an empty prompt with `keep_alive: 0` unloads the model. `OLLAMA_KEEP_ALIVE` sets a server default, while request-level `keep_alive` overrides it.

Source:
- https://github.com/ollama/ollama/blob/main/docs/api.md
- https://github.com/ollama/ollama/blob/main/docs/faq.mdx

Recommended Safe BIM mode if Ollama is used:

- request `keep_alive: "30s"` or a similarly short burst window during iterative planning;
- after the plan is frozen, explicitly unload with `keep_alive: 0` rather than waiting for TTL;
- if strict zero background service use is wanted, disable Ollama auto-start and start/stop it on demand as a separate optimization later.

## Pass 04 — Ollama concurrency/memory guard

Ollama documents that parallel requests multiply effective context allocation and RAM requirements. It exposes:

- `OLLAMA_MAX_LOADED_MODELS`,
- `OLLAMA_NUM_PARALLEL`,
- `OLLAMA_MAX_QUEUE`.

Source:
https://github.com/ollama/ollama/blob/main/docs/faq.mdx

Safe BIM profile:

- `OLLAMA_MAX_LOADED_MODELS=1`
- `OLLAMA_NUM_PARALLEL=1`
- low queue (fail/route elsewhere rather than queue a large local workload while BIM work is active)

This prevents a harmless second request from unexpectedly doubling KV/context memory or loading another model.

## Pass 05 — context and KV-cache budget

Long context is a direct memory cost. Ollama supports Flash Attention and quantized KV cache. Its docs state `q8_0` KV uses approximately half the memory of f16 with usually very small quality impact, while q4 uses about one quarter with greater quality risk.

Sources:
https://github.com/ollama/ollama/blob/main/docs/faq.mdx

Recommended planning profile:

- context 4k–8k by default, expanded only for a measured need;
- Flash Attention when backend/device supports it;
- q8 KV cache as a candidate after correctness benchmark;
- do not make q4 KV the default for safety-sensitive structured planning without an evaluation set.

## Pass 06 — llama.cpp sleep/unload option

`llama-server` supports OpenAI-style chat/tool calls and `--sleep-idle-seconds`, which places the server into sleep after inactivity. Current server also supports lazy multi-model presets (`load-on-startup: false`) and model unload facilities.

Source:
https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md

This is a stronger architectural fit than a permanently loaded model when the goal is a tiny resident control process with heavy model resources absent while idle.

Recommended candidate profile:

- one model,
- one inference slot,
- 4k–8k context,
- `--sleep-idle-seconds 30` to `60`,
- explicit server/model shutdown after plan freeze if measured sleep does not release enough memory on Windows/NVIDIA.

## Pass 07 — llama-swap for several local specialists

`llama-swap` is a small Go proxy that starts compatible inference servers on demand, supports per-model TTL, exposes explicit model unload endpoints, and can keep only the control proxy resident while model workers disappear.

Source:
https://github.com/mostlygeek/llama-swap

Use only if Safe BIM eventually needs several local specialists (planner, coder, vision). For one model it adds unnecessary moving parts; direct Ollama/llama.cpp is simpler.

## Pass 08 — LM Studio alternative

LM Studio supports JIT loading, per-model Idle TTL, Auto-Evict/keep-last-model behavior, explicit unload, controllable context/GPU offload and memory estimation before loading.

Sources:
- https://lmstudio.ai/docs/developer/core/ttl-and-auto-evict
- https://lmstudio.ai/docs/cli/local-models/load
- https://lmstudio.ai/docs/developer/core/headless

It is operationally friendly, but for this project it is an alternative rather than a required dependency. A direct lightweight server (Ollama or llama.cpp) is easier to isolate and reproduce in a developer setup.

## Pass 09 — TabbyAPI / ExLlama path

TabbyAPI exposes fast NVIDIA-focused ExLlamaV3 inference, OpenAI compatibility, model load/unload, schema/grammar constraints and tool calling. It is AGPLv3 and its own README describes it as a rolling-release hobby project, not intended as a production server.

Source:
https://github.com/theroyallab/tabbyAPI

Judgment: useful benchmarking candidate for throughput, not the default Safe BIM AI broker. Its dependency/upgrade surface and licensing complexity are unnecessary until speed measurements show a clear benefit over llama.cpp/Ollama.

## Pass 10 — no permanent embedding/RAG daemon

The project does not need a resident embedding model merely to expose its command catalog/docs to the planner.

Prefer in this order:

1. deterministic capability registry + exact command IDs;
2. progressive discovery by keyword/category;
3. SQLite FTS5 / lexical search over research and schemas;
4. on-demand embedding model only if lexical retrieval quality is shown insufficient.

The `tapir-archicad-MCP` project demonstrates the useful idea of progressive command discovery (`list -> get schema -> call`) instead of stuffing 191+ tool schemas into every model context.

Source:
https://github.com/SzamosiMate/tapir-archicad-MCP

Safe BIM should copy the discovery pattern, not expose direct write authority to the model.

## Pass 11 — AI tool surface must be capability-filtered

The model should never see every Tapir write command just because Tapir exposes it. Generate the AI-visible registry from Safe BIM's certified capability matrix only.

Suggested tool classes:

- `READ`: safe read adapters certified for current project/version;
- `PLAN`: pure geometry/parameter builders with zero writes;
- `PROPOSE`: creates an immutable Safe BIM plan draft;
- no raw `Create*`, `Modify*`, `Delete*`, `SetStories`, project open/close, or unrestricted MCP gateway.

This prevents prompt injection/model error from bypassing the safety kernel.

## Pass 12 — resource admission gate

Local inference should be admitted only at planning time. Before starting/loading a model, take a one-shot resource snapshot (not a background poller):

- available system RAM,
- GPU VRAM used/total,
- GPU utilization,
- whether an Archicad physical dispatch/reconcile section is active,
- optionally presence/activity of GPU-heavy visualization processes.

On NVIDIA/Windows, `nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv,noheader,nounits` is adequate for a low-frequency preflight and avoids another resident Python GPU library.

If the guard fails, choose cloud AI or deterministic/manual planning; do not steal resources from Archicad/Twinmotion.

## Pass 13 — Windows process scheduling

Microsoft documents `BELOW_NORMAL_PRIORITY_CLASS` and background processing mode. Job Objects can constrain process priority/CPU and can terminate an entire child process tree when the controlling job handle closes (`JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE`).

Sources:
- https://learn.microsoft.com/windows/win32/api/processthreadsapi/nf-processthreadsapi-setpriorityclass
- https://learn.microsoft.com/windows/win32/procthread/job-objects
- https://learn.microsoft.com/windows/win32/api/winnt/ns-winnt-jobobject_basic_limit_information

Recommended broker behavior:

- launch local inference worker at Below Normal CPU priority;
- put worker tree in a Windows Job Object with kill-on-close so a broker/controller crash cannot leave `llama-server`/helpers consuming RAM/VRAM;
- do **not** use a hard memory cap initially: failing model allocations unpredictably is worse than declining to start based on resource preflight;
- do not use realtime/high priority.

`PROCESS_MODE_BACKGROUND_BEGIN` is appropriate only for genuinely background tasks; interactive LLM generation may become too sluggish. Prefer Below Normal for the inference worker and zero background inference.

## Pass 14 — no inference during write/reconcile

A mutex/admission policy should make these states mutually exclusive:

- `AI_PLANNING_LOCAL`
- `BIM_PHYSICAL_DISPATCH`
- `BIM_RECONCILIATION`

Local model load/inference is prohibited during the latter two. AI cannot be invoked by an exception handler inside an unknown-outcome reconciliation path. All decisions in that path must be deterministic.

This is more important than micro-optimizing tokens because it protects latency and safety at the point Archicad is mutating.

## Pass 15 — structured outputs and tiny prompts

The planner should emit one versioned schema, e.g. `IntentPlanV1`, with strict `additionalProperties=false` and finite numeric checks. It should reference capability IDs rather than raw Tapir command names.

Instead of feeding all APIs on every turn:

1. deterministic router identifies domain (`wall`, `roof`, `zone`, `docs`, etc.);
2. registry returns only a few certified capabilities and field schemas;
3. LLM emits structured intent;
4. deterministic compiler resolves story elevations, attributes/Favorites, exact parameters and safety gates.

This reduces prompt tokens, KV memory, inference latency and hallucination surface simultaneously.

## Pass 16 — local model role and size

The local model should be optimized for **intent extraction / planning / explanation**, not for being a second safety runtime. A compact model that fits comfortably under the resource guard is preferable to a very large MoE whose weights/CPU offload compete with CAD.

Large SSD-streamed/MoE models may be interesting for offline research, but they are a poor default for interactive Safe BIM orchestration because their cold-start/I/O/RAM footprint conflicts with the stated requirement not to slow other work.

Use cloud reasoning for rare difficult planning/coding tasks if desired; execution still uses the same deterministic plan compiler and safety kernel, so provider choice does not alter write authority.

## Pass 17 — caching policy

Caching must be bounded and disposable:

- model weight cache on disk: fine;
- prompt/KV cache in RAM/VRAM: only during a short planning burst;
- controller stores only compact conversation/plan summaries needed for the next turn;
- no persistent in-memory full source/index cache in the Safe BIM runtime;
- after plan freeze, discard AI session and unload model.

A cold reload costs latency, but zero-idle resource use is a deliberate requirement. Use a 30–60 s warm burst window only if benchmark data shows repeated reload dominates UX.

## Pass 18 — acceptance benchmark / final audit

AI integration is not production-ready until an automated benchmark compares `AI disabled` versus `AI broker installed but idle` and `AI planning active`.

Required metrics:

### Idle acceptance

- Safe BIM startup time: no material regression;
- idle controller/runtime RAM: no model-sized increase;
- GPU VRAM after AI unload: returns to baseline within tolerance;
- GPU utilization idle: baseline;
- no inference/embedding process survives broker shutdown.

### Planning acceptance

- one local model max;
- one parallel request max;
- no BIM physical dispatch/reconcile overlaps local generation;
- AI output rejected if schema/capability/version invalid;
- cancel/unload frees resources deterministically.

### Execution acceptance

- local AI already unloaded before first Tapir write;
- all existing Safe BIM safety tests pass with AI package absent and with broker configured;
- killing AI worker during planning cannot mutate Archicad or corrupt runtime state.

## Architecture verdict

### Recommended V1

`optional AI broker subprocess + Ollama OR llama.cpp -> strict IntentPlan -> deterministic compiler -> explicit unload -> existing Safe BIM runtime`

Preference order for the initial implementation:

1. **Ollama** if reusing the already familiar local-model setup is the priority. Enforce `MAX_LOADED_MODELS=1`, `NUM_PARALLEL=1`, short keep-alive and explicit unload.
2. **llama.cpp server** if the strongest minimal-idle/process-isolation control is the priority. Use sleep/explicit process termination.
3. **llama-swap** only when multiple local model backends are actually needed.
4. LM Studio as an optional user-friendly provider.
5. TabbyAPI only after a benchmark demonstrates a compelling throughput advantage.

### Integration status

- Safe to design offline: **YES**
- Safe to put AI into the existing trusted write path: **NO**
- Safe to add as optional planner with zero write authority: **YES, after schema/compiler tests**
- Safe to run local inference concurrently with physical BIM writes: **NO by design**

The central optimization is simple: **think first, freeze the plan, unload the model, then touch Archicad.**
