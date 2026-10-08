# Archicad 29 Template — Live Execution Runbook v0.1

> Current installed Archicad version (confirmed 2026-10-09): **Archicad 29.2.1 (5101) RUS FULL (x86-64)**. `Archicad 29` elsewhere in this runbook refers to the AC29 compatibility generation. See [current runtime record](../ARCHICAD_RUNTIME_CURRENT.md). Historical checks are not retroactively reclassified as build 5101.


This runbook converts the existing fail-closed builder actions into a reproducible live sequence for a clean Archicad 29 candidate project.

It does **not** claim that Archicad has already been executed from GitHub or from ChatGPT. The launcher must run on the Windows machine where Archicad 29 and the Tapir/native overlay are available.

## Launcher

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage preflight
```

Default Tapir port: `19723`.

Every stage writes one JSON evidence file per builder action plus `summary.json` under:

```text
outputs/archicad-template-live/<timestamp>/
```

The launcher stops immediately when:
- Python exits non-zero;
- the expected JSON evidence file is missing;
- builder result status is anything other than `PASS`.

This means `BLOCKED_ADDON_REBUILD`, `FAIL`, platform blocks, registry mismatches, non-empty-project write refusal, or other explicit gates cannot be silently bypassed.

## Stages

### 1. preflight

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage preflight
```

Runs:
1. `font-preflight`
2. `validate`
3. `inspect`
4. `plan`

No Archicad writes are expected.

### 2. core

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage core
```

Runs:
1. `apply-core`
2. `inspect`

Expected write scope: Project Info, Layers, Pen Tables, simple Line Types, Layer Combinations only.

### 3. materials-data

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage materials-data
```

Runs:
1. `apply-surfaces`
2. `plan-materials`
3. `apply-ready-materials`
4. `plan-data-schema`
5. `apply-data-schema`

### 4. navigator-master

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage navigator-master
```

Runs:
1. `plan-navigator`
2. `apply-navigator-shell`
3. `plan-master-layouts`
4. `apply-master-layout-shell`
5. `inspect`

The Master Layout stage must leave model-element count unchanged and must remove any temporary `__SBIM_MASTER_SEED_` Layout used by the builder.

### 5. all-safe

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage all-safe
```

Runs stages 1–4 in order. It intentionally does **not** run `plan-autotext`, because AutoText requires the rebuilt native overlay containing `GetAutoTextsV1`.

### 6. autotext gate

After rebuilding/loading the overlay:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage autotext
```

This runs only `plan-autotext`.

If the overlay is stale, the launcher must stop on `BLOCKED_ADDON_REBUILD`.

## Stop conditions before titleblock drawing

Do not proceed to full GOST R 21.101-2026 Form 3 geometry until all of the following are true:

- `all-safe` returns PASS;
- `autotext` returns PASS after overlay rebuild;
- one sacrificial Master Layout line is created and read back at the expected coordinates;
- one Text element is created and read back;
- one AutoText element is created and resolves to a real Archicad value;
- no model geometry count changes during any Master Layout test.

Only after those gates pass should full Form 3 line/text/AutoText generation be implemented.

## Deliberately excluded

This launcher does not:
- pass `--allow-nonempty`;
- create production model geometry;
- create or edit MVO, GO, Dimension Style, Publisher, DWG or IFC presets unsupported by the current API path;
- save a final `.tpl`;
- bypass any builder gate.


## 7. Master Layout smoke gate

After `autotext` passes:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage master-smoke
```

This activates `A4_P` and creates three sacrificial document elements:

- one 40 mm Line from 20/20 mm to 60/20 mm;
- one static Text at 20/30 mm;
- one Text containing `<BUILDING_NAME>` at 20/40 mm.

The test verifies that the created GUIDs are present in the `A4_P` Master Layout database and then deletes all three elements in a `finally` cleanup path.

A PASS now proves database targeting, exact Line/Text coordinates, 2.5 mm text height, raw text content, interpreted project-level AutoText value, GUID read-back and cleanup via the native `GetCurrent2DDocumentV1` overlay command.

The remaining AutoText gate is **layout-scoped context** such as `<LAYOUTNAME>`. That must be tested on a sacrificial real Layout using `A4_P`, because a Master Layout itself is not a concrete sheet and therefore is not a valid final proof of layout-specific values.


## 8. Layout-scoped AutoText smoke gate

After `master-smoke` passes:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage layout-autotext-smoke
```

This creates a disposable subset `__SBIM_AUTOTEXT_SMOKE_SUBSET__` and a disposable Layout `__SBIM_AUTOTEXT_SMOKE_LAYOUT__` based on `A4_P`.

On that real Layout it verifies:

- `<LAYOUTNAME>`;
- `<LAYOUTNUMBERINCURRENTSUBSET>`;
- `<NUMBEROFLAYOUTSINCURRENTSUBSET>`.

The gate reads both raw and interpreted Text content through `GetCurrent2DDocumentV1`. It requires the layout name to resolve exactly to the temporary Layout name, the number-in-subset to be non-empty, and the number-of-layouts-in-current-subset to resolve to exactly `1`.

Cleanup is mandatory and ordered:

1. delete sacrificial Text elements;
2. delete sacrificial Layout;
3. delete sacrificial subset;
4. verify neither navigator item remains;
5. verify model-element count is unchanged.

A pre-existing navigator item with either smoke name causes `BLOCKED_RESIDUAL_SMOKE_ITEMS`; the builder will not silently delete it.

After this gate passes, the titleblock AutoText contract for Form 3 fields 4, 7 and 8 is considered live-verified. The next implementation stage is full Form 3 titleblock geometry generation.


## 9. Master Layout coordinate calibration

After both smoke gates pass:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage coordinate-calibration
```

The command activates `A4_P` and draws both paper-space hypotheses at once:

- `H1`: origin at bottom-left, +X right, +Y up;
- `H2`: origin at top-left, +X right, -Y down.

Each hypothesis places four labeled cross marks 10 mm inside the candidate paper corners. While the marks are visible, the command waits for an explicit terminal answer:

- `H1`
- `H2`
- `ABORT`

No convention is selected automatically. All calibration Line/Text elements are deleted in a `finally` cleanup path after the answer, and model-element count must remain unchanged.

A PASS from this stage proves only the convention selected by visual inspection. The returned JSON contains `confirmedConvention`; that convention must then be persisted in the coordinate-calibration registry before `apply-form3-core-geometry` is enabled.


## 10. Form 3 core geometry

This stage remains fail-closed until the coordinate calibration result is persisted:

```yaml
confirmed_convention: H1
```

or

```yaml
confirmed_convention: H2
```

Then run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage form3-core
```

The writer targets every registered A4-A0 Master Layout and places only the verified 185×55 mm Form 3 **line grid**. Static labels and AutoText are deliberately excluded from this stage.

Before writing each master it reads current 2D Lines through `GetCurrent2DDocumentV1`:

- complete expected grid already present -> PASS, no duplicate creation;
- only some expected segments present -> `BLOCKED_PARTIAL_FORM3_GEOMETRY`;
- none present -> create all registered segments and read them back.

The titleblock origin is calculated from the verified sheet size plus the normative 5 mm right/bottom frame insets. The Y formula depends exclusively on the persisted H1/H2 convention; no coordinate convention is guessed at runtime.

The stage also requires model-element count to remain unchanged.


## 11. Form 3 static labels

After `form3-core` passes:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage form3-static
```

This stage writes only non-dynamic Form 3 labels:

- `Разраб.`
- `Н. контр.`
- `Стадия`
- `Лист`
- `Листов`
- change-table headers `Изм.`, `Кол.уч`, `Лист`, `№ док.`, `Подп.`, `Дата`

The change-table labels are derived directly from the registered `change_header.columns` geometry, not duplicated in another source of truth.

Before writing, each Master Layout must already contain the complete verified Form 3 line grid. Text read-back uses `GetCurrent2DDocumentV1` and compares raw text, anchor coordinates and text height.

Safety behavior:

- complete expected static-label set -> PASS, no duplicates;
- only part of the set -> `BLOCKED_PARTIAL_FORM3_STATIC_LABELS`;
- different Text at an expected anchor -> `BLOCKED_FORM3_TEXT_CONFLICT`;
- incomplete line grid -> `BLOCKED_FORM3_CORE_GEOMETRY`.

No dynamic project/layout data is written in this stage. AutoText remains a separate gate.


## 12. Master-context AutoText smoke

Before production AutoText is written onto Master Layouts:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/run_archicad_template_live.ps1 -Stage master-context-autotext-smoke
```

This gate creates a disposable subset and Layout based on `A4_P`, switches to the `A4_P` Master Layout, and sets that Layout as the Master Layout rendering context through the native `SetMasterLayoutContextV1` command.

Three layout-scoped AutoText tokens are then created **on the Master Layout itself**:

- `<LAYOUTNAME>`
- `<LAYOUTNUMBERINCURRENTSUBSET>`
- `<NUMBEROFLAYOUTSINCURRENTSUBSET>`

Their raw and interpreted values are read back through `GetCurrent2DDocumentV1`.

PASS requires:

- `LAYOUTNAME` resolves exactly to the disposable Layout name;
- layout number in subset is non-empty;
- number of layouts in current subset resolves to exactly `1`.

Cleanup always clears the Master Layout context first, then deletes sacrificial Texts, Layout and subset. Model-element count must remain unchanged.

This gate is the production-equivalent proof required before layout-scoped AutoText is added to the real Form 3 Master Layout.


## 13. Active-project write safeguard

Write stages now pin themselves to one explicitly confirmed Archicad project.

At the start of any stage that can create/change Archicad data, the runner calls:

```text
confirm-project
```

It displays the active project name and exact `projectPath`, then requires the literal answer:

```text
YES
```

The returned `projectPath` is stored only for that live run. Every subsequent `apply-*` action independently calls `GetProjectInfo` again and compares the currently active project path with the confirmed path.

Fail-closed states:

- unsaved/untitled project -> `BLOCKED_UNTITLED_PROJECT`;
- Archicad returned no stable path -> `BLOCKED_PROJECT_IDENTITY`;
- user did not type `YES` -> `BLOCKED_PROJECT_CONFIRMATION`;
- active project changed after confirmation -> `BLOCKED_ACTIVE_PROJECT_CHANGED`.

This allows other PLN projects to remain open in parallel while preventing a write stage from silently continuing after the user switches to another project.

Direct `apply-*` calls outside the runner must supply the exact path using `--expected-project-path`; otherwise they fail closed.


## 14. Promote live evidence into release gates

Do not edit `confirmed_convention` or `production_master_context_verified` by hand after a live test. Use the evidence-promotion helper.

After a successful coordinate calibration:

```powershell
python .\scripts\promote_archicad_template_gate.py coordinate --evidence <path-to-apply-master-coordinate-calibration.json>
```

The helper requires:

- `status == PASS`;
- `confirmedConvention` is exactly `H1` or `H2`;
- cleanup succeeded;
- model-element count remained unchanged.

It then changes only:

```yaml
confirmed_convention: H1
```

or `H2`. If the registry already contains the opposite convention, promotion stops instead of replacing it.

After a successful Master-context AutoText smoke:

```powershell
python .\scripts\promote_archicad_template_gate.py master-context-autotext --evidence <path-to-apply-master-context-autotext-smoke.json>
```

The helper requires:

- `status == PASS`;
- `masterContextAutoTextVerified == true`;
- Master Layout context was cleared;
- temporary Layout and subset were deleted;
- model-element count remained unchanged.

Only then does it change:

```yaml
production_master_context_verified: true
```

The helper does not connect to Archicad and does not modify PLN data. Its sole purpose is to promote already-proven live evidence into the repository release gates.
