# T0 results

**Status: PENDING — no live Archicad run has been performed from this repository.**

Everything below is the contract for the live run. Nothing here is measured
evidence about a real Archicad 29 build yet. The only measured artefacts that
exist today were produced against the in-memory doubles in
`bimexec/tests/fakes/`; they validate probe logic, not Archicad behaviour.

| Item | Value |
|---|---|
| Committed kit | `bimexec/probes/` (`probe_t0a.py`, `probe_t0b.py`, `backends.py`, `T0_PLAN.md`, `README_RUN_WINDOWS.txt`, `SHA256SUMS.txt`) |
| Branch | `arena/t0-probes`, base `main` @ `72e9be1` (Arena never writes to `main`) |
| Commit SHA | see `bimexec/HANDOFF_ARENA.md` |
| T0A status | **not run on Windows** |
| T0B status | **not run, not authorised.** No write to Archicad from this repository. |
| `create_wall` | `production_safe = false`, not implemented, hard-blocked by `backends.py` |

## docs/ vs results/

- `bimexec/docs/` — this file is a **contract**: what a run must produce, how to
  read it, and when T0B may be attempted. No live data belongs here.
- `bimexec/results/` — **live artefacts** of real runs:
  `WORK_LIVE_BASELINE_2026-09-26.md`, `GetDetailsOfElements_wall_sample.json`,
  `capability_matrix.json`. Template: `bimexec/results/TEMPLATE_T0A_RUN.md`.

---

## 1. Exact Windows command for T0A

From the folder that contains `probe_t0a.py` (read-only, no write to the model):

```
python probe_t0a.py --out capability_matrix.json --ports 19723,19724 --mcp-url http://127.0.0.1:8001/mcp --expect-project "C:\PLN\MCP_TEST.pln"
```

Prerequisites in `MCP_TEST.pln` (manual, once):

1. Archicad 29 open with the Tapir Add-On loaded.
2. User-defined property created by hand: group `BIMEXEC`, name
   `BIMEXEC_MARKER`, type String. The official JSON API cannot create
   properties, only set values.
3. The test wall has an Element ID, e.g. `W-TEST-001` — needed as the positive
   control for the search scan.
4. No value in the project starts with `BX:PROBE:`.

Exit codes: `0` = probe executed (**not** a go decision), `2` = no backend
answered (fail closed: nothing is certified).

---

## 2. What T0A must produce

**Files**

- `capability_matrix.json` — the matrix, conforming to
  `bimexec/specs/capability_matrix.schema.json`.

**Console output**

- One line per capability with `[OK]` / `[NO]` / `[??]` and `backend=...`.
- `readable marker carriers : [...]` — which of `element_id`, `property` can be
  read.
- `duplicate detection      : SCAN_PREFIX` (or `EMPTY_SCOPE_FALLBACK`).
- `create_wall production_safe: False` + `blocked by: [...]`.
- `element_id address (для T0B --element-id-address): ...`
- `GUID candidates for T0B (стены):` with GUID + Element ID per wall.
- `T0A GO` or `T0A NO-GO`, then `next: ...`.

**Mandatory content of the JSON**

- every `capabilities.<name>` carries `backend` (attribution) and a tri-state
  `supported`;
- `raw_dumps.GetDetailsOfElements_sample` is present and holds the untouched
  response (this is the evidence for wall endpoints);
- `operations.create_wall.production_safe == false` and
  `implemented_here == false`;
- `verdicts.executed` and `verdicts.t0a_go` are both present;
- `t0b_candidates` lists wall GUIDs to feed T0B.

Bring back: `capability_matrix.json`, the full console output, the exit code,
which backend answered, and the live Tapir add-on version if reported.

---

## 3. Go / no-go for T0B

**GO only if all of these are true:**

1. `capabilities.project_identity.supported = true` — the project path matches
   `--expect-project`, `is_untitled = false`, `is_teamwork = false`.
2. `capabilities.list_guids.supported = true`.
3. `capabilities.wall_geometry_endpoints.supported = true` — the raw response
   really contains `begCoordinate` / `endCoordinate`.
4. At least one marker carrier is readable:
   `capabilities.read_element_id.supported = true` **or**
   `capabilities.read_custom_property.supported = true`.
5. `capabilities.search_scan.supported = true` — the positive control found the
   probe value and the random sentinel negative control found nothing.
6. `duplicate_detection` is `SCAN_PREFIX` (client scan + prefix match is
   available). If it is `EMPTY_SCOPE_FALLBACK`, no marker round-trip is
   possible and T0B must not be attempted at all.
7. `verdicts.t0a_go = true`.

**NO-GO, and do not start T0B, if any of these hold:**

- any of the five capabilities above is `false` or `null` (`null` = UNKNOWN,
  fail closed);
- `duplicate_detection = EMPTY_SCOPE_FALLBACK`;
- the project reported at run time is not the disposable `MCP_TEST.pln`;
- the add-on version is unknown, or read commands behave inconsistently between
  calls;
- T0A exited `2`.

Even on GO, T0B is a **separate, explicit authorisation** recorded in this file
or in `COORDINATION.md` before anyone runs it. T0B is then run only:

- on `MCP_TEST.pln`;
- on one element with a known GUID;
- with `--carrier property` first;
- with both keys `--allow-write --i-understand-this-writes-to-archicad`;
- one attempt per stage, no retries.

---

## 4. Still UNKNOWN until the live run

1. Live Tapir Add-On version (`GetAddOnVersion` was never observed on the real
   stack; earlier inventory did not confirm it).
2. Which Element ID address actually resolves on AC29 (`General_ElementID`,
   `General/Element ID`, …). T0A records the first one that returns values.
3. Whether `GetDetailsOfElements` returns wall coordinates inside
   `details.wall` for **this** build — T0A dumps the raw response as evidence.
4. Whether the MCP endpoint on port 8001 answers `initialize` and what
   `tools/list` reports (mode `verdicts` vs `full`). Until this is measured, the
   write path is planned via Tapir, not MCP.
5. Whether `API.SetPropertyValuesOfElements` can write a user-defined property
   that was created by hand — **this is exactly what T0B exists to test**.
6. Whether `floorIndex` → story name mapping is complete for all stories.
7. Whether BIBIM offers anything this stack needs (out of scope for v1; no local
   package or schemas were found).

---

## 5. Where the live record goes

Use `bimexec/results/TEMPLATE_T0A_RUN.md`. Commit the filled copy as
`bimexec/results/T0A_RUN_YYYY-MM-DD.md` (and, if T0A ran,
`bimexec/results/capability_matrix.json` next to it).

If Work/Codex runs the read-only baseline from `bimexec/HANDOFF_WORK.md` first,
its record goes to `bimexec/results/WORK_LIVE_BASELINE_2026-09-26.md` with the
summary fields `PROBES_PRESENT`, `ACTIVE_PORT`, `PROJECT`, `TAPIR_VERSION`,
`MCP_OK`, `MCP_MODE`, `WALL_SAMPLE_OK`, `MUTATIONS=0`, `BLOCKERS`.

Do not fill this in from memory or from documentation. Only from a run.
