# APA-P00.A02.S03 — GitHub forensic: 72 branch heads, exact aliases and 13 ancestor/difference checks

**План:** APA-P00 — объединение результатов.  
**Действие:** APA-P00.A02 — единый evidence map и дедупликация.  
**Подшаг:** APA-P00.A02.S03 (существующий, статус после прохода — PARTIAL).  
**Run:** `APA-RUN-20261010-235301Z-branch-evidence-dedup`; controller claim `APA-RUN-20261010T234936Z-branch-archive-dedup`.  
**Метод:** прямые GitHub `compare_commits` для 13 пар; чтение exact source Markdown/JSON по refs; сохранённый [исторический снимок 72 веток](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/BRANCH_HEADS_20261010.json).  
**Verification:** SOURCE_VERIFIED для Git ancestry/HEAD aliases, SOURCE_READ / REPORTED для технических заявлений исторических отчётов. Без запуска Archicad/PLN/APX.

## 1. Machine-readable audit asset

[BRANCH_DEDUP_MATRIX_20261011.json](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-verified-results-hub-20261010/docs/research/apa-results/inventories/BRANCH_DEDUP_MATRIX_20261011.json) содержит проверяемую матрицу: 72 записи snapshot, 69 различных SHA, 2 группы head-алиасов (5 указателей), 13 сравнений ancestry/различий, конкретные изменённые пути, `ahead_by`, `behind_by`, статус `identical|ahead|diverged`, границы покрытия. Файл опубликован отдельным коммитом и прочитан обратно. `BRANCH_HEADS_20261010.json` — исторический, не живое перечисление всех веток в этот момент.

### Тождественные HEAD-коммиты: точные алиасы, не отдельные исходники

1. Git SHA `bcac2e821a95f927fa6ae9f5fa5742b45d9ca2dd`: `feature/project-accelerator-integration-pr-20261009`, `research/apa-20261009-api-mep-batching-audit` и `research/apa-20261009-resource-mep-bridges-audit-v1`. Каждое сравнение с feature ref: `status=identical; ahead=0; behind=0; files_changed=0`. Поскольку ветви указывают на *тот же коммит*, два research-имени **не доказывают** наличия дополнительных опубликованных уникальных файлов. Содержимое branch-local несохранённых исследований вне GitHub здесь не наблюдаемо.
2. Git SHA `c6ab4749e8784cc65170167d166daa6cc219a931`: `arena/fix-house-offline-audit-f7d38af` и `arena/tapir159-compat-geometry-c6ab474`; `identical, 0/0`. Имена на один commit, но сами эти ветки не удалять: различия истории имен, external PR/проверок могут иметь provenance-значение.

**Числа:** 72 branch-head snapshots → 69 distinct SHA, 3 избыточных HEAD-алиаса в двух группах. Это **только exact SHA dedup**. Похожесть содержимого между другими 67 HEAD-коммитами не доказана; нельзя автоматически удалять/сливать.

## 2. Тринадцать проверенных сравнений GitHub ancestry/diff

В таблице `ahead/behind` считаются для `base...head`, а file count — список изменённых путей возвращённого compare API. Значение `ahead` отражает историю commit, **не техническую проверку работоспособности**.

| Пара | Статус | ahead/behind | Изменённых путей | API-доказательство |
| --- | --- | ---: | ---: | --- |
| `alias_mep` | identical | 0/0 | 0 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/feature%2Fproject-accelerator-integration-pr-20261009...research%2Fapa-20261009-api-mep-batching-audit) |
| `alias_resource` | identical | 0/0 | 0 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/feature%2Fproject-accelerator-integration-pr-20261009...research%2Fapa-20261009-resource-mep-bridges-audit-v1) |
| `alias_arena` | identical | 0/0 | 0 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/arena%2Ffix-house-offline-audit-f7d38af...arena%2Ftapir159-compat-geometry-c6ab474) |
| `detail_v2_2_to_v2_3` | ahead | 1/0 | 10 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/chatgpt%2Fdetail-machine-v2.2...chatgpt%2Fdetail-machine-v2.3) |
| `detail_db_v2_2_to_v2_3` | diverged | 5/2 | 43 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/chatgpt%2Fdetail-machine-db-v2.2-20261006...chatgpt%2Fdetail-machine-db-v2.3-20261006) |
| `kaiman_parent` | ahead | 1/0 | 8 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/chatgpt%2Fdetail-machine-v2.3...chatgpt%2Fkaiman-exact-v2.4) |
| `kaiman_v2_4_to_v2_5` | ahead | 1/0 | 3 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/chatgpt%2Fkaiman-exact-v2.4...chatgpt%2Fkaiman-exact-v2.5) |
| `detail_machine_vs_db_v2_3` | diverged | 5/33 | 43 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/chatgpt%2Fdetail-machine-v2.3...chatgpt%2Fdetail-machine-db-v2.3-20261006) |
| `gdl_checkpoint_to_blocker` | ahead | 1/0 | 1 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/research%2Fapa-tn-gdl-create-01-checkpoint-20261009...research%2Fapa-tn-gdl-create-01-blocker1-audit-20261009) |
| `gdl_blocker_to_native` | ahead | 1/0 | 5 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/research%2Fapa-tn-gdl-create-01-blocker1-audit-20261009...research%2Fapa-tn-gdl-create-01-native-probe-20261009) |
| `stage4_hardening_to_performance` | ahead | 31/0 | 12 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/work%2Fstage4-live-hardening...work%2Fstage4-performance-pass) |
| `stage4_performance_to_stage5_window` | ahead | 40/0 | 19 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/work%2Fstage4-performance-pass...work%2Fstage5-hosted-window) |
| `whole_scene_to_integration` | ahead | 2/0 | 19 | [GitHub compare](https://github.com/dvikt33-ux/safe-bim-layer/compare/chatgpt%2Fwhole-scene-v1-20261009...feature%2Fproject-accelerator-integration-pr-20261009) |

Итого 13: **3 identical, 8 ahead, 2 diverged**. Ни одно сравнение не выдаётся за полный аудит 72×72 пар веток, тем более не за установленный runtime.

## 3. Уникальные артефакты, которые нельзя потерять при дедупликации

**A. Stage 4 Performance → Stage 5 Hosted Window:** `work/stage4-performance-pass...work/stage5-hosted-window`: **ahead=40, behind=0, changed_files=19**. В Stage 5 добавлены `closed_loop/live_window.py`, `closed_loop/window_attempts.py`, независимые проверки и [STAGE5_HOSTED_WINDOW.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/work%2Fstage5-hosted-window/docs/STAGE5_HOSTED_WINDOW.md). Следовательно Stage 5 — последовательное расширение, а не независимый полностью альтернативный Stage 4 runtime. [Stage 4 acceptance JSON](https://github.com/dvikt33-ux/safe-bim-layer/blob/work%2Fstage4-performance-pass/outputs/closed-loop-stage4/stage4-performance-acceptance.json) заявляет **58 focused PASS**, `offlineProofSpeedup=8.75` и retained verifier speedup `4.96` на сохранённых данных; **не воспроизводилось в данном проходе**. [Stage 5 offline acceptance](https://github.com/dvikt33-ux/safe-bim-layer/blob/work%2Fstage5-hosted-window/outputs/closed-loop-stage5/stage5-offline-acceptance.json) подтверждает запись опубликованного результата `51 tests PASS`, `physicalMutationCalls=0`, `W01–W07 PASS`, `W08–W10 PENDING`, `stage5Status=NOT_VERIFIED`. **Не повышать Stage 5 до LIVE_PASS**. Связать с существующими `APA-P70.A03.S02` / `APA-P70.A03.S03`.

**B. GDL / ТЕХНОНИКОЛЬ:** `research/apa-tn-gdl-create-01-checkpoint-20261009` → `blocker1-audit` → `native-probe` — **две последовательные однокоммитные ступени**; в конечной добавлены `docs/research/patches/tapir-1.5.10-blocker1-readonly-diagnostic.patch`, `scripts/verify_apa_blocker1_patch.py`, `tests/test_apa_blocker1_patch.py` и обновления отчёта. [Конечный audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/research%2Fapa-tn-gdl-create-01-native-probe-20261009/docs/research/APA_TN-GDL-CREATE-01_BLOCKER1_AUDIT_2026-10-09.md) документирует focused offline contract/translation-unit compilation, но **полный APX не собран и не установлен**, resolver readback и блокер 92 ошибок НЕ закрыты. Это не основание заново писать тот же диагностикум; использовать опубликованный патч после отдельного gate. Привязка `APA-P10.A02.S02`.

**C. KAIMAN/Detail Machine, похожее имя v2.3 НЕ доказывает дубликат:** `chatgpt/detail-machine-v2.3` и `chatgpt/detail-machine-db-v2.3-20261006` **diverged (5 ahead/33 behind)**, 43 changed paths. Первый `details/machine-db/releases/v2.3/` имеет фокус **KAIMAN/KERAKAM WT1.1**, [точные dimension bindings](https://github.com/dvikt33-ux/safe-bim-layer/blob/chatgpt%2Fdetail-machine-v2.3/details/machine-db/releases/v2.3/README_v2.3.md) — 196 binding на 21 sheet; второй `knowledge/detail-machine/releases/v2.3/` — **ROCKFACADE**: [аудит](https://github.com/dvikt33-ux/safe-bim-layer/blob/chatgpt%2Fdetail-machine-db-v2.3-20261006/knowledge/detail-machine/releases/v2.3/AUDIT_v2.3.json), 101 sheets с DXF evidence. **Нельзя объявлять их версиями одной ветки и удалять один источник без content-level inventory**. Оба `commit_allowed=true` имеют значение 0 в исторических evidence, нет доказанного BIM write.

**D. KAIMAN exact series:** `chatgpt/detail-machine-v2.3→kaiman-exact-v2.4→kaiman-exact-v2.5` даёт две последовательные one-commit ветви; v2.5 добавляет 3 файла в `details/machine-db/releases/kaiman-v2.5/`. [v2.5 audit](https://github.com/dvikt33-ux/safe-bim-layer/blob/chatgpt%2Fkaiman-exact-v2.5/details/machine-db/releases/kaiman-v2.5/AUDIT_KAIMAN_v2.5.json) фиксирует **139 новых source-printed bindings / 8 листов**, итого **47/227 sheets, 536 bindings**, 180 sheets ещё не обработаны. Сохранена несовместимость 80 и 150 мм между парными источниками; данные не нормативная экспертиза. `commit_allowed_true=0`. Привязка `APA-P70.A04.S01` и `APA-P70.A04.S03`, без автоматической генерации узлов.

**E. Интеграция APA:** `chatgpt/whole-scene-v1-20261009→feature/project-accelerator-integration-pr-20261009` — **2 commits впереди, 19 изменённых путей**, включает `scripts/archicad_accelerator_integration.py`, `scripts/archicad_project_accelerator.py`, схемы Tapir, испытания и [PROJECT_ACCELERATOR_INTEGRATION.md](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature%2Fproject-accelerator-integration-pr-20261009/docs/PROJECT_ACCELERATOR_INTEGRATION.md). Это полноценное отдельное семейство артефактов, не доказанное текущим именем research branch-алиасов; не переписывать схему адаптеров повторно. Synthetic/read-only результаты из README оставлять `REPORTED` до отдельного test gate. Привязка `APA-P70.A01.S02`, `APA-P70.A03.S02`.

## 4. Рабочая карта superseded_by / KEEP — не команда удаления

| Объект | Решение и каноническая ссылка | Доказательство |
| --- | --- | --- |
| `research/apa-20261009-api-mep-batching-audit` | `EXACT_HEAD_ALIAS_OF feature/project-accelerator-integration-pr-20261009@bcac2e8`; **KEEP pointer** | identical; HEAD Git SHA |
| `research/apa-20261009-resource-mep-bridges-audit-v1` | `EXACT_HEAD_ALIAS_OF feature/project-accelerator-integration-pr-20261009@bcac2e8`; **KEEP pointer** | identical |
| `arena/tapir159-compat-geometry-c6ab474` | `EXACT_HEAD_ALIAS_OF arena/fix-house-offline-audit-f7d38af@c6ab474`; **KEEP pointer** | identical |
| `work/stage4-performance-pass` | **KEEP independently accepted performance milestone**; Stage5 is a descendant, not an accepted replacement | 40 commits ahead, Stage5 W08–W10 pending |
| `research/apa-tn-gdl-create-01-native-probe-20261009` | **KEEP most advanced diagnostic source**; source report/patched code over earlier checkpoint | ahead chain / full APX still absent |
| `chatgpt/detail-machine-v2.3` vs `chatgpt/detail-machine-db-v2.3-20261006` | **KEEP BOTH** — distinct manufacturers/source corpora and diverged history | source readback + compare |
| `chatgpt/kaiman-exact-v2.5` | **KEEP latest appended WT1.3 exact source facts**, not normative or generation-ready | v2.5 audit / unchanged fail-closed gate |

## 5. Unverified gaps & next measured gate

- This is a **snapshot-based exact SHA and 13-pair ancestry audit**, not full 72-branch unique file inventory. Every untouched branch remains UNCLASSIFIED for unique artifacts. No historical branch was deleted, merged, renamed or reset.
- The legacy claim **“six requested research summary filenames missing”** still lacks the six exact names in the examined Slack audit. Without explicit names plus exhaustive branch tree search, global-absence claim **NOT_VERIFIED**. Do not announce those six reports irretrievable.
- Source assertions inside retained engineering acceptance JSON are **read and attributed**, not newly rerun. Latest installed binary/runtime equivalence remains unverified.
- Next within `APA-P00.A02.S03` / `APA-P00.A01.S03`: enumerate unique paths/blobs in the remaining 69 distinct snapshot HEAD trees, group evidence by *Git blob SHA* and S-ID, map more semantically same findings, and retain source SHA. Scope each run, do not start 69 repeated tiny tests.
- Existing `APA-P50.A01.S01` cross-task evidence map and `APA-P70.A01.S02` product capability trace should reference this machine matrix. Avoid creating duplicate work_keys, run claims and fake DONE states.

**Task outcome:** `PARTIAL`, with new verified machine inventory, not `DONE_PUBLISHED` for the full legacy dedup task. No Deep Research, paid runtime, PLN/APX or main/master modifications.
