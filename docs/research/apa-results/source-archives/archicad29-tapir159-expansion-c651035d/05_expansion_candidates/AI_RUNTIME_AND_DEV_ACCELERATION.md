# AI runtime + development acceleration research track

Status: active research. This document stores only confirmed or explicitly marked provisional findings. Product code and `main` are not changed by this research.

## Goal

Integrate local AI into Safe BIM so that AI is demand-loaded, releases RAM/VRAM promptly when idle, cannot contend with Archicad/Twinmotion during interactive work, and accelerates development without weakening the deterministic Safe BIM safety kernel.

## Research program

### A. AI resource isolation — 10–20 passes
1. Ollama unload/keep-alive semantics.
2. Ollama concurrency and max-loaded-model controls.
3. Ollama context/KV-cache/Flash-Attention memory controls.
4. llama.cpp idle sleep / unload behavior.
5. llama.cpp GPU-layer / KV-cache / mmap / lazy-load controls.
6. LM Studio JIT + Idle TTL + Auto-Evict.
7. LM Studio explicit unload and resource estimation.
8. vLLM sleep mode and platform fit for this Windows laptop.
9. Windows process-priority / process-lifetime isolation options.
10. GPU ownership / race conditions with Archicad/Twinmotion and local inference.
11–20. Follow-up passes on any unresolved memory, latency, or reliability issues.

### B. Development acceleration — 10–20 passes
1. Generate typed wrappers/validators from Tapir 1.5.9 schemas rather than hand-copying commands.
2. Progressive command discovery instead of exposing hundreds of tools to the model at once.
3. Split offline/schema tests from live Archicad tests.
4. Parallelize only isolation-safe offline tests.
5. Re-run failed tests first during edit cycles.
6. Property-based/fuzz tests for geometry/payload validators.
7. Schema-diff CI between pinned Tapir snapshot and target Tapir release.
8. Capability matrix generated from source/schema evidence.
9. Read-only probe suite before any write-capability promotion.
10. Risk-based test tiers and changed-file test selection.
11–20. Follow-up passes on profiling, CI cache, generated evidence, and bottlenecks.

## Confirmed findings so far

### Local model residency

**Ollama**
- API supports per-request `keep_alive`; `keep_alive: 0` with an empty chat/generate payload explicitly unloads a model from memory.
- Current server configuration exposes `OLLAMA_KEEP_ALIVE`, `OLLAMA_MAX_LOADED_MODELS`, `OLLAMA_NUM_PARALLEL`, `OLLAMA_MAX_QUEUE`, `OLLAMA_GPU_OVERHEAD`, Flash Attention and KV-cache settings.
- `OLLAMA_NUM_PARALLEL` multiplies KV/context memory pressure; for a single-user Safe BIM assistant the safe default candidate is therefore `1`, subject to benchmark.
- A known 2026 Ollama issue reported that `keep_alive=0` can fail to unload correctly under concurrent requests. This reinforces the design rule: Safe BIM should serialize local-LLM jobs and should verify unload state rather than assume it.

**llama.cpp**
- Current `llama-server` supports `--sleep-idle-seconds`; when idle, the model and KV cache are unloaded from RAM and a later request reloads them automatically.
- It exposes explicit controls for GPU layers, device selection, Flash Attention, K/V cache type, mmap/load mode, lazy tensor loading, and parallel sequence count.
- This is a strong candidate for a dedicated on-demand inference worker because the server itself can sleep without keeping model memory resident.

**LM Studio**
- Supports JIT model loading, Idle TTL, Auto-Evict, explicit unload, and resource estimation before load.
- Auto-Evict keeps at most one JIT-loaded model resident by default; Idle TTL unloads inactive models.
- This is operationally attractive but Safe BIM should not rely on GUI state; if adopted, the integration should use the documented API/CLI and verify model residency.

**vLLM**
- Has a sleep mode that frees most GPU memory while keeping the server/container alive.
- It is currently a secondary candidate for this Windows laptop because its main strength is high-throughput serving; Safe BIM is primarily a single-user, low-concurrency workload and must protect RTX 4060 VRAM for Archicad/Twinmotion.

### Preliminary architecture rule

The local AI must remain outside the deterministic write kernel:

`user intent -> optional AI planner -> structured intent -> deterministic validator/planner -> SafeBIMOperations -> Tapir -> exact-GUID readback/reconciliation`

AI must never decide ownership, APPLIED/NOT_APPLIED, retry-after-unknown-outcome, project identity, capability promotion, or safety policy.

### Candidate resource-manager architecture

A small `AIResourceBroker` (future design; not implemented) should own model-process lifecycle:

1. Receive a semantic/planning request.
2. Check that no protected high-VRAM activity policy is active.
3. Start/load exactly one approved model on demand.
4. Use concurrency = 1 for the large local model.
5. Use the minimum context needed for the task.
6. Return structured output only.
7. Explicitly unload/sleep the model after the request or after a short idle TTL.
8. Verify that the model is no longer resident before marking the AI lease released.
9. Never hold a model indefinitely in the background.

The broker must be advisory to inference only; it must not become a second Safe BIM execution path.

### Candidate priority order for the user's laptop

Provisional, pending benchmark/audit:
1. `llama.cpp llama-server` with idle sleep — strongest direct resource-release semantics.
2. Ollama with serialized requests + short keep-alive + explicit unload verification — easiest with the user's existing Ollama setup.
3. LM Studio JIT + TTL + Auto-Evict — strong operational controls, but adds another runtime/app layer.
4. vLLM — likely unnecessary for the single-user RTX 4060 workflow unless future throughput needs justify it.

## Development acceleration findings

- Tapir/MCP projects demonstrate that command tools can be generated dynamically from Tapir + official Archicad schemas rather than maintained manually. Safe BIM should reuse this idea only for **discovery/schema generation**; production write admission must stay on an explicit certified allowlist.
- A progressive discovery pattern (`list commands` -> `get exact command schema`) reduces prompt/tool bloat compared with exposing 191+ tools simultaneously.
- `pytest-xdist` can parallelize independent offline tests. Live Archicad and runtime single-flight tests must remain serialized.
- pytest `--last-failed` / `--failed-first` can shorten edit-test cycles; the full safety suite remains mandatory before capability promotion.
- Property-based testing (Hypothesis) is a good fit for finite-number validation, malformed geometry, story/Z transforms, schema payloads, receipt binding, and fail-closed invariants.
- GitHub Actions Python dependency caching can shorten CI setup time; this affects build/test latency only and does not alter safety semantics.

## Hard constraints

- No AI model may remain loaded merely because Safe BIM is running.
- No background inference polling.
- No more than one heavyweight local generation at a time unless a later benchmark proves parallel execution does not degrade Archicad/Twinmotion or memory safety.
- No automatic fallback that silently shifts a large model to CPU and consumes most of the 48 GB RAM.
- No AI-generated raw Tapir write command may bypass `SafeBIMOperations`.
- Live Archicad writes require the existing receipt/checkpoint/project-identity/reconciliation chain.

## Evidence sources reviewed in this track

- Ollama current API/docs and source configuration (`keep_alive`, scheduler/concurrency, Flash Attention/KV cache).
- llama.cpp current server and CLI documentation (idle sleep, offload, KV cache, mmap/lazy mode).
- LM Studio current developer documentation (Idle TTL, Auto-Evict, unload, resource estimates).
- vLLM current Sleep Mode documentation.
- pytest / pytest-xdist / Hypothesis / GitHub Actions documentation.
- Archicad MCP implementations that autogenerate tools from Tapir + official schemas.

Exact source URLs/commits will be normalized into `08_sources_evidence` during the final evidence pass.
