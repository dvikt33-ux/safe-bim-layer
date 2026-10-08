## Scope

Describe the smallest behavior change in this PR.

## Safety checklist

- [ ] No credentials, personal data, local logs, GGUFs, or Archicad projects are included.
- [ ] No direct change was made to `main`.
- [ ] CHAT-FIRST / WORK-MINIMAL followed: main work in ChatGPT (90–95%); Work limited to small PC/file/run/build/test actions (5–10%), with results returned to chat. See [operating model](../docs/OPERATING_MODEL.md#chat-first--work-minimal).
- [ ] The change does not make a live Archicad call during tests.
- [ ] Tapir payloads remain schema-validated and fail closed.
- [ ] A failed read-back cannot be reported as success.

## Verification

List the offline/unit tests run and their results. State clearly if live-copy
validation is still required.

## Arena hand-off

If Arena authored this PR, include the Arena task link or task identifier and
list every assumption it made about Tapir or Archicad.
