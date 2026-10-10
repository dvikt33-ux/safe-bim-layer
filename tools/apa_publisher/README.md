# APA Research OS — GitHub Actions publisher

**Status:** GitHub Actions workflow installed on canonical research branch. The workflow triggers on a push changing an inbox JSON, publisher code, or the workflow file. It does **not** autonomously perform research or schedule ChatGPT. See Actions run results for operational status.

- Workflow: [apa-research-publisher.yml](../../.github/workflows/apa-research-publisher.yml)
- Input: [PUBLISH_REQUEST_V1.schema.json](../../docs/research/apa-results/protocol/PUBLISH_REQUEST_V1.schema.json)
- Implementation: [publisher.py](publisher.py)
- Tests: [test_publisher.py](tests/test_publisher.py)
- Generated index: [generated/INDEX.md](../../docs/research/apa-results/generated/INDEX.md)

## How to submit a run

1. Complete one APA-Pxx.Ayy.Szz research substep in an ordinary ChatGPT conversation.
2. Build one JSON object matching PUBLISH_REQUEST_V1. Include full report in report_markdown, real source references and evidence statuses, a unique run_id, and all safety flags false.
3. Commit it to **research/apa-verified-results-hub-20261010** at:
   docs/research/apa-results/inbox/<run_id>.json
4. GitHub push triggers the workflow. It runs offline tests, checks the schema/safety, creates immutable REPORT.md, manifest.json, evidence.json, updates generated index, commits, reads every file back through GitHub REST, commits receipt, reads receipt back.
5. Confirm GitHub Actions run success and receipt under docs/research/apa-results/receipts/<run_id>.json. If the workflow fails, publication is NOT DONE.

All existing flat legacy reports are preserved. The generated V2 index does not overwrite manual CURRENT_STATUS, ARTIFACT_REGISTER, MASTER_PLAN or RESEARCH_QUEUE. Those remain manually maintained until a separate index-builder migration gate.

## Safety and recovery

- Only canonical research branch; never main/master, PLN, APX or tested code branches.
- No secrets or commercial library payloads in inbox. No external paid API, Work, Codex or Deep Research.
- Same run_id and identical payload are idempotent; a changed report under the same run_id fails IMMUTABLE_CONFLICT.
- A crash after report commit but before receipt can be recovered by rerunning the workflow. An existing immutable report is verified, not overwritten.
- GitHub REST readback validates SHA-256 content and Git blob SHA-1. Receipt includes the report commit SHA from the first commit.
- A failed API readback fails the workflow. GitHub Actions success is the final confirmation; do not infer success from a workflow file merely existing.
- This is a **push-triggered publisher**, not an autonomous 24/7 research agent. There is no scheduled ChatGPT research, heartbeat or 24-hour operational proof.

## Manual offline tests

    python -m unittest discover -s tools/apa_publisher/tests -v

## Expected smoke test

Submit a SYNTHETIC run with NOT_VERIFIED claims (not a fake Archicad live test); check generated/STATE.json run_count and receipt readback. Do not mark Archicad source/build/live PASS from this smoke test.
