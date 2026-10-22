# APA №1 BUILD-01 SOURCE 15–18

15. **Details→Create?** [Tapir PR866](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/866), MIT: дополнительные выходы Wall/Beam/Column/SlabDetails относятся к Grasshopper, не к JSON SceneWriter. №2: не добавлять GH в P0.

16. **Смешанные конструкции?** [PR866](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/866): Basic/Composite/Profile дают null в неприменимых полях, GH Create/Modify не принимают списки с null. №2: не считать roundtrip универсальным.

17. **Slab material при CREATE?** [PR785](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/785), MIT: новые поля upstream 1.7.2; PR отмечен unbuilt/unreviewed. №2: не переносить в локальную 1.5.10; сохранить CREATE→MODIFY+readback.

18. **Новые возможности от схем?** [PR1056](https://github.com/ENZYME-APD/tapir-archicad-automation/pull/1056): named schema definitions, без изменения accepted JSON. №2: не повышать статус G0 от рефакторинга схем.

4 SOURCE, 3 PR, 0 LIVE. MODEL_MODE_NOT_VERIFIABLE.
