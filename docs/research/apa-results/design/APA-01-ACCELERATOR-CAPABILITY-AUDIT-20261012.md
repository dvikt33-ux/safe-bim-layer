# APA capability audit for APA-01 Kazan house
Date 2026-10-12. Evidence: canonical PROJECT_PLAN.json revision 108 and PR #56 description, read from GitHub. This is a repository-level capability audit, NOT a new live Archicad test.

## Verified controller summary
25 DONE_PUBLISHED, 16 PARTIAL, 13 BLOCKED, 36 READY, 1 IN_PROGRESS (91 tasks total). APA-P70.A04.S02 is IN_PROGRESS by another executor: do not take it over. APA-P70.A11.S03 PARTIAL. Do not alter canonical controller from this isolated design PR.

## Mapping to the Kazan house
- Storeys, walls, editable native elements, hosted openings, story/material/GUID readback: historical integrated tests, supported for bounded cases. A03.S01-S04 and A08.S04 DONE_PUBLISHED. Full house not demonstrated.
- Native slab writing: demonstrated in limited copy/create scenarios; not evidence of product-specific hollow-core plate selection, accurate two-end bearing, plate family catalog, slab voids or staircase cutouts. Kazan requirement = CONDITIONAL.
- Native Beam writer: bounded timber detail in PR #56 is reported, with actual source-bound 25x150 mm example. This is NOT proof that ~4.7m intermediate floor joists pass structural design, nor proof of full roof frame creation. Need Beam create, transform, rotation, material, cross-section and story readback; verify support contacts. Kazan requirement = PARTIAL.
- Composite/profile/material reading and selected materials: A02.S04 DONE_PUBLISHED. Full warm ceramic + self-supporting face brick + interior finish with actual hygrothermal validation = NOT VERIFIED.
- Native Roof and Morph creation: bounded tests; correct ridge/rafters/columns/truss/roof connection and structural verification = NOT VERIFIED.
- MEP: PR #56 reports seven routes, nine segments, twelve physical elements, 11 reciprocal connections; one terminal open, circular preference mismatch (0.2m request vs 0.8m actual). Not essential to initial structural shell.
- IFC: PR #56 reports 37/37 geometry bounds, 44 elements, 26 ports and 11 links; not proof of SAM/SAF structural load transfer or design approval.
- Save/reopen: PR #56 reports 95 GUID preserved, 95 geometry signatures match, isolated PLN. This is positive integration evidence for that TEST PLN, not a Kazan house file.
- Construction details: A04.S02 currently IN_PROGRESS, avoid overlapping writes. A04.S03 READY. Structural calculation A05.S01-S03 READY, no accepted Kazan loads or engineer calculations. Full house acceptance A08.S01 READY. Installer A11.S05 READY; not ready to promise one-click installed package.
- Shell/edit Opening, SAM/SAF, Twinmotion semantic integration, native MEP terminal preference are BLOCKED by controller. Avoid making these mandatory for first structural shell.

## Safe next verification batch (requires local Archicad executor)
1. On an isolated copy of a verified active test PLN, create 3 native stories, native loadbearing walls, 2 separate native Slab units representing individual two-end-supported precast units; verify bearing face geometry and no side-bearing; do not claim actual manufacturer slab specification.
2. Create >= 3 native Beam joists with material/section/story, one native Slab deck, save/reopen; compare GUIDs, positions, cross sections and materials; zero Morph.
3. Create a native gable Roof and >= 2 correctly placed Beam rafters plus an actual ridge bearing scheme; verify true 3D support contact and all transforms after save/reopen; this tests geometric API only, not structural adequacy.
4. Produce audit JSON: expected/observed types, GUIDs, story, material, 3D contacts, two-end-bearing, no Morph, and repeatability. Compare against native dump.
5. Stop and label BLOCKED if API does not expose required writer. Never silently substitute Morph or invented structural members.
6. Record actual runtime build, test and save/reopen evidence in a new branch/PR, not chat-only. Do not touch other executor's in-progress A04.S02 or the canonical controller without lease/CAS.

## Result
Repository capability = partial but sufficient to attempt a limited native geometric Kazan skeleton after local runtime preflight. Engineer-approved masonry, product-marked precast layout and load-rated rafter system are NOT currently proven. No PLN was created or modified by this audit.
Sources: canonical docs/research/apa-results/control/PROJECT_PLAN.json rev 108; https://github.com/dvikt33-ux/safe-bim-layer/pull/56.
