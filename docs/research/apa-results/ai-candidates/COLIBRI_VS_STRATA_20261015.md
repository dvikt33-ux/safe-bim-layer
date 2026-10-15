# APA — Colibrì vs Strata (движки локального inference), 2026-10-15

**Статус:** official-source study, NOT_TESTED_APA, no installation. **Цель:** выбрать подходящий Windows runtime для Lenovo Legion Pro 5, RTX 4060 Laptop 8GB VRAM, 48GB RAM, SSD 1TB, Archicad 29. **Не перепутать Colibrì** `JustVugg/colibri` с недавно вышедшим `ColGrep-Agent-2B` от LightOn — совершенно разные программные продукты.

## Первоисточники / контрольные версии

- Colibrì: https://github.com/JustVugg/colibri @ commit `bf2442915d6e3dd4cdfd2eb9c2a3d2aa44a25850` (read via GitHub connector, official README + docs/qwen38.md + CHANGELOG + LICENSE). Apache-2.0 runtime. v2.0.0 released **2026-10-06** (не новая модель за неделю 08–15).
- Strata: https://github.com/Niko1221/Strata @ commit `296b59d2f73c8f04a805df29c2fa97655adace78` (official README). MIT runtime.
- Лицензии **самих весов** каждой запускаемой LLM могут отличаться от лицензии движка.

## Аппаратные факты

| Измерение/критерий | Colibrì | Strata |
|---|---|---|
| Назначение | Multi-family MoE runtime, CPU fallback, Vulkan GPU, disk-streamed expert weights; умеет 13 engines / several chat models | Высокоспециализированный Qwen3.8-Flash-Next 125B/6B (в том числе Coder/Swift fine-tunes), GPU+RAM+SSD |
| Windows + RTX 4060 8GB | Поддержан Vulkan 1.2; Windows setup uses Vulkan by default if CUDA toolkit unavailable; CUDA Windows package may be available on release, select only if verified | Official min **12GB VRAM**, 8GB GPU **NOT SUPPORTED in stated baseline**. Эксперименты 8GB возможны в форках/обходных путях, но не подтверждены на нашем ноутбуке |
| RAM | Qwen3-Coder-30B-A3B: 8GB min, 18GB recommended; Qwen3.6-35B: 10GB min, 20GB recommended; Qwen3.8 Flash Next FP8: 24GB min, 32GB recommended (с experts на SSD) | При 48GB RAM рекомендуется Q2_0 или IQ2_XS, если GPU ≥12GB; active process needs headroom for Windows + AC |
| Disk (Qwen3.8 Flash Next) | **186GB** official FP8 download; int4 sidecar 68GB additional (unless remove original copy after conversion, process not verified) | **~70–80GB** full download/install typical small quants (official README), Q2_0/IQ2_XS RAM+VRAM 37.6/39.2GB in model docs |
| Export API | OpenAI-compatible localhost:8000/v1 and Anthropic base localhost:8000 | OpenAI-compatible localhost:8080/v1; also Anthropic API |
| Concurrency | Official v2.0.0 allows up to 16 KV slots | Default single request, optional batch parallelism may hurt speed on small VRAM |
| Licence | Apache-2.0 engine | MIT engine |

## Производительность: **нельзя** выдавать чужие числа за A/B benchmark

From official readmes:
- **Colibrì Qwen3.8 Flash Next**, 3.99 tok/s **CPU-only** on Ryzen 7 PRO 8700GE desktop, int4 routed experts; baseline FP8 1.91–2.56 tok/s depending cached experts. **Не Ryzen9 7945HX, не RTX4060**.
- **Colibrì Qwen3.6-35B-A3B**, 30.0 tok/s on an **RTX 3070 8GB** desktop, separate model family.
- **Strata Qwen3.8 Flash Next IQ2_XS**, 79 tok/s on RTX 5070 **12GB**, 64GB RAM; **Q2_0** 94 tok/s (same GPU), official authors' results.
- Thus **NO DIRECT SAME MODEL, SAME QUANT, SAME HARDWARE** comparison is established; apparent 3.99 vs 79 tokens/s is INVALID as an apples-to-apples metric.
- For **GLM-5.2 744B Colibrì**, developer reports as low as 0.05–0.1 tok/s cold on ordinary 25GB laptop; even if it runs using SSD 429GB weights, this is not a practical autonomous reviewer for APA. Better use smaller MoE.
- Colibrì v2.0.0 (Oct06) added Qwen3-Coder, Qwen3.8-27B, GPU Vulkan all MoEs, Qwen3.8 speculative decoding/int4 experts; this is not a model launch on Oct15.

## Selection decision for APA

**Priority: PROMISING (for experimental local model hosting on the fixed 8GB GPU).** It supports **practical small MoEs** (Qwen3-Coder-30B-A3B, Qwen3.6-35B-A3B) as alternative to Strata, with published speed on **different** 8GB GPU, but experiments on this exact machine are required. **Do not bundle/launch 744B for background coding.**

Strata remains **PROMISING** with a critical block: official VRAM ≥12GB, below current hardware. Can evaluate on existing configuration only after demonstrating stable startup and free RAM with AC running; cannot promise 79/94 tok/s on RTX4060.

Best potential APA use: local code reviewer and tool-calling assistant with **read-only access**, not a second Archicad writer. Running model names/weights determines quality; the engines by themselves do not make an identical Qwen 125B more capable. The Python/JSON API contract, code bugs, and GUID readback must be checked independently.

### Fast test plan (NOT EXECUTED)

1. Source pin + hash + GPU/Windows compatibility and disk free check. **Avoid giant downloads** until user approves. Never run `START-HERE.bat` blindly; inspect it and release checksums.
2. Colibrì with a suitable **Qwen3-Coder-30B-A3B** (~19GB download, 18GB recommended RAM) and Qwen3.6-35B-A3B (~23GB download, 20GB RAM) tested **separately**, not simultaneously, with AC open.
3. Colibrì Qwen3.8 Flash Next FP8 186GB **only if** weight-download cost worth a like-for-like comparison; otherwise skip.
4. Strata Qwen3.8 Flash Next IQ2_XS only on officially supported GPU or separately acknowledged experimental install; would need 12GB+ GPU based on current README.
5. Same task suite for each tested model: 20 real APA code QA questions/bugs, JSON command schema correctness, correct target PLC/project/GUID, safe refusal to fabricate native tests. Count accuracy, false claims, runtime tok/s+TTFT, peak RAM/VRAM, disk bandwidth and time/job. DO NOT modify live Archicad.
6. Compare total **correctly completed tasks per hour**, not parameter count or reported tok/s on different GPUs.

**No runtime tests, PC installation, APA code modifications, purchases, or PLN edits occurred.** This is only source research, for independent verification and prioritization.
