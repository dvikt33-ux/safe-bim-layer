# APA-CAND-20261015 — next nonduplicating verification work

**Status:** PENDING_AUDIT / NOT_IN_PROJECT_PLAN. No new authoritative task ID or work lease. Created after [1922-case offline JUnit verification](https://github.com/dvikt33-ux/safe-bim-layer/actions/runs/38728924457).

| Candidate | Priority | Nonduplicating test work | Acceptance evidence |
|---|---|---|---|
| CAND-NATIVE-CW-RAILING-HIERARCHY | HIGH | Compare 128 synthetic hierarchy cases to independently captured parent/root/membership SDK samples, including nested railings | Per-root actual GUID graph + readback; offline and LIVE statuses separate |
| CAND-OPENING-BREP-HOST | HIGH | Positive Generic Opening host-to-cut/reverse native links; check resultant void BREP in authorized copy | Native GUID host/cut graph and geometry snapshot after Save/Open; **LIVE only** |
| CAND-DYNAMIC-SESSION-GUARD | HIGH | Mutate source-reviewed operation effects, registered binary session identity, scope leases and replay; use source-only mock first | Negative tests prove fail-closed with 0 Archicad writes; live only with explicit authorization |
| CAND-SHELL-MEMO-BOUNDARIES | MEDIUM | Shell contour/hole and Revolved/Ruled source discriminants not covered by Slab/Roof parameter tests | SDK source/build/synthetic cases; live evidence must be separate |
| CAND-NAVIGATOR-AMBIGUOUS-MAP | MEDIUM | Audit trusted explicit view ID override vs mismatched map-identity results | Explicit adversarial ambiguity results and contract decision, with zero inferred physical GUIDs |

Do not replay 1922 passing cases without code changes or an explicit regression reason. Do not modify `control/PROJECT_PLAN.json` or claim DONE_PUBLISHED for controller tasks before independent audit. Reuse existing adapters and dynamic catalog instead of adding parallel executors.
