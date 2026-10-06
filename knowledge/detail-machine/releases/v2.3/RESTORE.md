# Restore detail-machine v2.3

The committed `detail-machine-v2.3-systematized.tar.gz` is the compact active machine state. It does not duplicate the raw manufacturer PDF/DXF/DWG files.

Verify:

```bash
sha256sum detail-machine-v2.3-systematized.tar.gz
# 7467739de818d111511e6965b0377ada00aeb956c2527db5c32ae40dda7ff9f2
```

Extract:

```bash
mkdir detail-machine-v2.3
# Linux/macOS
tar -xzf detail-machine-v2.3-systematized.tar.gz -C detail-machine-v2.3
```

The release contains active detail/IR records, parameter facts, component variants, source registry, ROCKFACADE PDF/DXF semantic evidence, and the inherited grammars for earlier processed sources.

Raw source binaries remain outside normal Git; their hashes are retained in source verification metadata.