# Existing TDK source slice

This directory mounts 28 byte-exact files from `dvikt33-ux/tdk-course-project`,
branch `normative-recovery-2026-10-06`, commit
`67f17d407d14aebb091daaf79f11c10178b87440`.
`SOURCE_LOCK.json` records original paths, Git blobs and SHA256 hashes.

The source governance, rule text, schemas, routes, aliases, release set, source
passports, compiled blocks and two Python modules are unchanged. This is a
bounded existing source snapshot for reproducible offline execution and CI,
not a new rule catalog. Source files remain owned by the upstream repository.

Read `NORMATIVE_WORK_PROTOCOL.md` first. The existing branch is quarantined;
all routes/blocks remain design_only. Stored evidence field validation is not
independent verification of a primary normative text or engineering acceptance.

The first APA package opens only the exact object route and the selected roof
block closure. It reads just `rules/roofing_2026.yaml`, with nine IDs authorized
by the existing Central release whitelist. Inactive fire, engineering, loads,
accessibility and thermal rule libraries are not loaded. Exact MKD/TRC routes
are included to fail closed, without borrowing the IZHS roof route.

The Python resolver and evidence validator execute directly from this source
snapshot. The APA facade narrows the resolver's eager catalog load; it does not
replace its dependency, guard or release implementation. Roof calculators are
only declared upstream; no executable roof calculator exists in this slice.
Missing project inputs do not trigger library-wide retrieval.

To extend another module, supply a reviewed exact-object block/source slice and
a new verified source lock, retain the same profile/facts/result interface, and
qualify the corresponding existing upstream evaluator. Do not enable another
library merely because the project stage is working documentation.
