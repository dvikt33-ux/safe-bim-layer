# Integration backlog — prioritized from final research

This is a research-derived implementation backlog. It does not itself production-enable any capability.

## P0 — compatibility foundation

1. Replace/augment pinned `tapir-1.5.8.json` with a reproducible Tapir 1.5.9 schema/source artifact tied to upstream tag commit `d0dbb11b13942e014661e1402b07958b70cd9dba`.
2. Add runtime compatibility gate: Archicad version/build, Tapir add-on version, Safe BIM capability manifest version.
3. Correct offline Arc/Mesh/Morph/Roof contracts against Tapir 1.5.9 source.
4. Independent offline adversarial re-audit after those corrections.

## P1 — compiler / reusable-project foundation

5. Create machine-readable capability/evidence registry.
6. Create typed/versioned `ProjectRecipe` schema.
7. Deterministic recipe-to-DAG compiler.
8. Project Profile manifest + hash + preflight/resolver.
9. Persist recipe/profile/capability versions with every job.
10. Add filtered multi-GUID `GetDetailsOfElements` adapter for read-only verification batching.

## P2 — highest immediate productivity

11. Selection-first exact-target adapter (`GetSelectedElements`).
12. Highlight preview adapter (`HighlightElements`) + clear lifecycle.
13. ScriptUI WAITING_USER form for one-shot parameter/approval collection.
14. Isolated point-pick adapter; never background/prefetch.
15. Favorite inventory/capture/use flow:
    - list/preflight;
    - `CreateFavoritesFromElements` from approved exemplar;
    - `favoriteName` at create;
    - dependency checks in Project Profile.
16. Hotlink module catalog:
    - `SaveAsModuleFile`;
    - immutable/versioned module path;
    - `CreateHotlinkNodes`;
    - exact instance create/readback verifier.
17. First parameterized project-archetype recipes.

## P3 — geometry certification

18. Arc wall one-write orientation/sign probe after 1.5.9 offline correction.
19. Mesh one-write flat-Z probe after correcting `level + meshPolyZ` semantics.
20. Morph one-write box/body probe after real origin/axes/body verifier.
21. Single-plane Roof one-write pivot/positive-side probe.
22. Deterministic gable = two separately verified single-plane roof steps.

## P4 — incremental QA and documentation

23. Project-keyed read cache + explicit cache domains.
24. Element notification adapter as dirty hint only.
25. Incremental dirty dependency graph.
26. BBox/relations/collision read adapters.
27. Zone create/read/update operation family with global `UpdateZones` isolated.
28. Sections/interior elevations/details/worksheets.
29. Dimensions/text/labels/autotext.
30. Views/view settings/layouts/drawings.
31. Publisher/export as X1 external-output capability.
32. Phase/save checkpoint policy.

## P5 — advanced functionality

33. SEO exact relation receipt/reconcile.
34. Trim exact relation receipt/reconcile.
35. Attributes/profiles/property/classification profile operations.
36. Design Option variant workflow.
37. Object/Lamp placement with library Main-GUID preflight and exact readback.
38. GDL/HSF component factory around fixed-path `LP_XMLConverter` wrapper.
39. Stairs after hierarchy verifier.
40. Teamwork reservation lifecycle design.
41. MEP single-element operations, then separate W5 multi-object topology design for connect/merge/split.

## P6 — optional AI acceleration

42. AI broker in a separate subprocess/process tree.
43. Deterministic recipe/rule fast path before AI.
44. Progressive discovery generated from certified Safe BIM capabilities only.
45. Strict structured planner output; no raw Tapir command authority.
46. Resource admission snapshot, one model/one request, explicit unload before BIM write/reconcile.
47. Compare Ollama and llama.cpp cold-start/wake/unload on the user's laptop.

## P7 — performance/evidence tooling

48. Generic controlled one-write probe harness.
49. Golden raw readback fixture format.
50. Trace/replay fake backend with post-dispatch fault injection.
51. Evidence ledger linking source/offline/live/audit proof to capability promotion.
52. End-to-end performance suite: model, repeated modules, docs, save/publish, AI planning/unload.
53. Benchmark filtered readback batch sizes (1/4/8/16/32/64) rather than hard-coding a guess.

## Global implementation rule

No item in this backlog may bypass the existing Safe BIM safety model merely because it improves throughput. Optimize reuse, planning, reads, caching and dependency scheduling; keep mutating ownership/reconciliation conservative.
