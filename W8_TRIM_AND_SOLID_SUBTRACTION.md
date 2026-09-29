# W8 — Roof trim and Morph solid subtraction

Environment:
- Archicad 29
- Tapir 1.5.9
- sandbox `C:\Users\Admin\Downloads\Test_House_WriteSandbox.pln`

## Result

Overall verdict from the live probe: `TRIM_OR_SOLID_OPERATION_SEMANTICS_DIFFER`.

This is a partial PASS, not a total failure.

### A. Roof trim

Created:
- wall `98969D46-A212-4D25-830C-324B14BA5D4A`
- single-plane Roof `997EF6A5-046D-425D-801C-92D492ECA029`

`TrimElements` was called with the wall and Roof together in the `elements` list. A subsequent `GetElementTrims` query on the wall did not contain the Roof GUID.

Observed result: trim relation NOT CONFIRMED.

Important limitation: this invocation uses the Roof/Shell's own trim settings. The Tapir 1.5.9 command also supports an explicit `trimmingElement` and `trimType`, which maps to `ACAPI_Element_Trim_ElementsWith`. Therefore this result is not evidence that Archicad/Tapir cannot trim a wall with a Roof.

### B. Morph solid subtraction

Created:
- target wall `0BD8530D-83A0-4B49-B536-41F8F4737190`
- wedge Morph operator `D7D1E9CC-D497-4588-A41A-0A705FA6A7C3`

A `CreateSolidElementLinks` relation was created with operation `Subtraction`.

Readback before operator modification:
- target/operator relation found
- operation = `Subtraction`

The Morph body was then replaced with a larger wedge via `ModifyMorphs`.

Readback after operator modification:
- Morph vertex geometry changed
- returned vertices matched the requested replacement body
- target/operator relation still existed
- operation remained `Subtraction`

Conclusion: the solid subtraction relation is persistent and associative to the operator element GUID; editing the operator body does not destroy the SEO link.

## Safe BIM implication

Morph-based solid element operations can be modeled as explicit persistent dependencies. Safe BIM should preserve target/operator GUIDs and verify the link through `GetSolidElementLinks` after operator modifications.

Roof trim remains unresolved. W8B should reuse the existing wall/Roof and call `TrimElements` with an explicit `trimmingElement` and `trimType=KeepInside`, then inspect both the execution result and `GetElementTrims`.
