# Detail Machine DB v2.2 — repository package

This directory stores the compact, systematized active machine state for the Archicad construction-detail database.

## Restore

```bash
tar -xzf detail-machine-v2.2-systematized.tar.gz
cd detail_release_v2.2
```

The archive contains the active JSON/JSONL machine state, assembly grammars, source registry, audit data, dimension-binding queue and source-verification metadata. It intentionally does **not** duplicate the raw source PDFs in Git.

Archive SHA-256:

`57edcbfef8f1bf4b9d946e212c7a2c3e0c1a0a12f285e1aa3f974c178dcdf16e`

Safety policy remains fail-closed: source/manufacturer claims are not silently promoted to current normative requirements, raster pixels are not dimensions, and unresolved detail/project parameters keep Archicad commit disabled.
