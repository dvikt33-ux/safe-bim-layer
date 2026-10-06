# Restore v2.6

1. Decode `detail-machine-v2.6-systematized.tar.gz` if stored through a base64 transport layer.
2. Verify SHA-256 against `SYSTEMATIZED_ARCHIVE_SHA256.txt`.
3. Extract the archive and use `detail_machine_v2.6.sqlite` as the active DB.
4. `detail_units_v2.6.jsonl` and `archicad_ir_v2.6.jsonl` are the active exports.
5. POROTHERM v2.6 uses physical PDF sheet footers as canonical source identity; 11 previously omitted physical technical sheets were restored.
6. Raw manufacturer sources remain outside normal Git; `POROTHERM_LOWRISE_SOURCE_VERIFY_v2.6.json` and the full-package source verification preserve hashes.