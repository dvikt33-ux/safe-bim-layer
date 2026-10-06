# Restore detail-machine v2.4

The committed `detail-machine-v2.4-systematized.tar.gz` is the compact active machine state. It does not duplicate the raw manufacturer PDF/DXF/DWG files.

Verify:

```bash
sha256sum detail-machine-v2.4-systematized.tar.gz
# f13b414d13cf070dedcf29af6524a65a7fdaaf50e426dc8fa099ae2b8378439a
```

Extract:

```bash
mkdir detail-machine-v2.4
tar -xzf detail-machine-v2.4-systematized.tar.gz -C detail-machine-v2.4
```

The release contains active detail/IR records, parameter facts, component variants, source registry, BRAAS roof-detail semantics, and inherited grammars for previously processed sources.

Raw source binaries remain outside normal Git; their hashes are retained in source verification metadata.