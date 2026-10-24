# APA №2 — SOURCE 01–14 | 23.10.2026 09Z

**Метод:** 14 отдельных прямых вызовов GitHub `fetch_pr` (метаданные PR). Это проверка существования/состояния/HEAD, а не установленного API и не LIVE-тест. Все 14 PR в ответах OPEN, merged=false. Проверено в этом цикле.

| № | PR | HEAD commit | Что именно подтверждает metadata |
|---:|---|---|---|
| 01 | [#34](https://github.com/dvikt33-ux/safe-bim-layer/pull/34) | `e955ffb63d24d79e3068b27d16a89dfa9860f99f` | компилятор здания, BIM Graph |
| 02 | [#48](https://github.com/dvikt33-ux/safe-bim-layer/pull/48) | `976c19cecebe3f6bb4352365d9a59051d5b2b61b` | authored native/hosted openings |
| 03 | [#74](https://github.com/dvikt33-ux/safe-bim-layer/pull/74) | `5a3a9201a715a5528c93bed4a5318e2acb32eea7` | model-first building, Save/Open исторический |
| 04 | [#82](https://github.com/dvikt33-ux/safe-bim-layer/pull/82) | `1c27e7c4b66d5b225724e777719e6a675660494a` | Roof native |
| 05 | [#97](https://github.com/dvikt33-ux/safe-bim-layer/pull/97) | `8f134001ca0e3250eda587db61ac01dbd6357326` | CW/Railing/Shell/host |
| 06 | [#126](https://github.com/dvikt33-ux/safe-bim-layer/pull/126) | `f12aeba017ecd34a13989998f0b7700f6a0107d2` | native bulk, DynamicCommands |
| 07 | [#131](https://github.com/dvikt33-ux/safe-bim-layer/pull/131) | `75ae71dc60176225bb71928fb805e5adcc688b2e` | Wall/Slab batch и openings discovery |
| 08 | [#149](https://github.com/dvikt33-ux/safe-bim-layer/pull/149) | `4c119428e9b1c24bd00774c91a6f33cbf26f0369` | CREATE/MODIFY verifiers |
| 09 | [#150](https://github.com/dvikt33-ux/safe-bim-layer/pull/150) | `8fbb311fc2f25fb8b2b6ff432e74d4e31b4c93fc` | six verifiers release |
| 10 | [#151](https://github.com/dvikt33-ux/safe-bim-layer/pull/151) | `6d4487d6b4ef34a0573de694c179335827d3b1fc` | pinned deployment |
| 11 | [#154](https://github.com/dvikt33-ux/safe-bim-layer/pull/154) | `ca28e9b8003eeb3a38ca201ea96c0096e07b677f` | PDF vectors, вне P0 |
| 12 | [#159](https://github.com/dvikt33-ux/safe-bim-layer/pull/159) | `f13b1dcd70e9cb63f795e09fd25ada299e56f017` | mailbox group live bounded |
| 13 | [#160](https://github.com/dvikt33-ux/safe-bim-layer/pull/160) | `e8cbbf97335d454b7d253061319bcf354a4eaf99` | PDF/OpenBIM read-only |
| 14 | [#162](https://github.com/dvikt33-ux/safe-bim-layer/pull/162) | `f7c37b84b76c040c417ccd58a5543326e50f673a` | group-first selector/SceneWriter |

**Ограничение:** HEAD каждой PR — не installed build, не единая слитая ветка. Ветки независимы; нельзя механически объявлять, что все функции присутствуют в одном Windows runtime. Применение #154/#160 к BUILD-01 отложено. Дополнительные GitHub fetch_file и cross-read не включены в эти 14.
