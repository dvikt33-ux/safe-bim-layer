# W7 — Arbitrary Morph geometry

Environment:
- Archicad 29
- Tapir Archicad Automation 1.5.9
- sandbox project: `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`

## Result

**PASS — `PASS_ARBITRARY_MORPH_CREATE_READ_MODIFY`**

Three non-box Morph bodies were created with the stock Tapir `CreateMorphs` command and immediately read back through `GetDetailsOfElements`:

| Specimen | GUID | Vertices | Faces | Vertex coordinates round-tripped |
|---|---|---:|---:|---|
| Pyramid | `3B9BBC81-9482-49CF-A24B-5090DB4F83E6` | 5 | 5 | PASS |
| Wedge | `EECE2D90-72AA-44F0-857D-F24D8B888D23` | 6 | 5 | PASS |
| Octahedron | `02A4BECC-93C2-4D64-9323-8F4F6F873131` | 6 | 8 | PASS |

The Wedge was then modified with `ModifyMorphs` by replacing its complete `body`.

Verified after modification:
- GUID preserved: PASS
- geometry actually changed: PASS
- returned vertex set equals the requested new body: PASS
- final vertex count: 6
- final face count: 5

## Implication for Safe BIM

Stock Tapir 1.5.9 can round-trip arbitrary controlled Morph bodies through the shared `body` structure (`vertices` + `polygons`). This is strong enough for:
- non-box custom geometry;
- deterministic reconstruction/modification;
- use of Morphs as later solid-element-operation operators.

This does **not** yet prove fillets/chamfers or curved Morph faces. Those require tessellated geometry supplied explicitly; W7 only proves arbitrary polyhedral bodies.

## Safety notes

- Project identity was checked before writes.
- No `DeleteElements` call.
- No `SaveProject` call.
- Evidence JSON produced by the live probe at:
  `C:\Users\Admin\AppData\Local\Temp\safe-bim-w7-morph-geometry\w7_morph_geometry_result.json`
