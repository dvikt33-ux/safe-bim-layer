# APA AC29 №2 17Z — source evidence 21–30

10 самостоятельных контрактных проверок готовых связующих, SOURCE only. Путь и поле указаны, LIVE не выполнялся.

21. **IfcDiff geometry** [L96-L102](https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-external-pdf-lossless-20261018/scripts/apa_external_readonly.py#L96-L102) — APA -r type property container aggregate classification; upstream default attributes/geometry не включены. **Вердикт/следующий вопрос:** два независимых режима QA; pinned 0.8.5 flags.

22. **IfcPatch overwrite** [L25-L45](https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifcpatch/ifcpatch/__main__.py#L25-L45) — -i/-r required, -o optional, если -o нет output=input. **Вердикт/следующий вопрос:** обязательный -o на копии; GUID/host/ports postcheck.

23. **Publisher selection** [L36-L102](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/NavigatorCommands.cpp#L36-L102) — publisherSetName required; selectedNavigatorItemIds=[] оставляет selectedLinksPtr=nullptr. **Вердикт/следующий вопрос:** fail-closed whitelist, output manifest.

24. **Hotlink** [L2189-L2229,L2344-L2415](https://github.com/ENZYME-APD/tapir-archicad-automation/blob/1.5.9/archicad-addon/Sources/ProjectCommands.cpp#L2189-L2229,L2344-L2415) — CreateHotlinkNodes sourceLocation .mod/.pln; CreateHotlinkInstances hotlinkNodeId+origin, rotationAngle radians, relinkWallOpenings. **Вердикт/следующий вопрос:** node/instance/child GUID, runtime command inventory.

25. **BCF2 exporter** [L844-L882](https://github.com/IfcOpenShell/IfcOpenShell/blob/b139fe1c355d6e29f36f430ad4e26f8910bc5958/src/ifctester/ifctester/reporter.py#L844-L882) — IfcTester reporter.Bcf imports bcf.v2.bcfxml.BcfXml, save_project. **Вердикт/следующий вопрос:** viewer roundtrip; issue #7152 viewpoint.bcfv/snapshot.png.

26. **STEP-to-JSON package** [L2-L38](https://github.com/aljoshakoecher/STEP-to-JSON/blob/master/package.json#L2-L38) — v4.0.0 MIT; Node, cli-progress/colors/rxjs/uuid/yargs; main dist/parser.cjs.js. **Вердикт/следующий вопрос:** новая Node среда; Windows/supply-chain gate.

27. **STEP parser** [L22-L80,L105-L130](https://github.com/aljoshakoecher/STEP-to-JSON/blob/master/src/parser.js#L22-L80,L105-L130) — parse() возвращает id/name/contains; split(';') и PRODUCT/NEXT_ASSEMBLY_USAGE_OCCURRENCE. **Вердикт/следующий вопрос:** нет placement/units; nested assembly fixture.

28. **STEP CLI** [L1-L16,L77-L96](https://github.com/aljoshakoecher/STEP-to-JSON/blob/master/cli/step-to-json.js#L1-L16,L77-L96) — реальный путь cli/step-to-json.js (README неверен); output split('.stp')[0]+'.json', fs.writeFileSync. **Вердикт/следующий вопрос:** может overwrite; безопаснее library wrapper.

29. **STEPhen dependencies** [L8-L25](https://github.com/antmicro/stephen/blob/main/pyproject.toml#L8-L25) — v0.0.1 Apache-2.0, Python>=3.9, cadquery/pandas/typer; Assembly допускает .step/.csv, не .stp. **Вердикт/следующий вопрос:** Windows CadQuery wheels/ABI NOT_VERIFIED.

30. **STEPhen transforms** [L74-L114](https://github.com/antmicro/stephen/blob/main/stephen/sourcefile.py#L74-L114) — cq.Assembly().load, traverse, loc.toTuple()→Location/Rotation; to_pos CSV и to_bom CSV. **Вердикт/следующий вопрос:** units/rotation convention/position reference fixture.

Дополнительные первоисточники: https://docs.ifcopenshell.org/ifcdiff.html (IfcDiff 0.9.0 docs НЕ pin 0.8.5); https://github.com/IfcOpenShell/IfcOpenShell/issues/7152 (BCF issue OPEN); https://github.com/antmicro/stephen/blob/main/stephen/assembly.py (STEPhen to_pos/to_bom); https://github.com/aljoshakoecher/STEP-to-JSON/blob/master/README.md (ошибка CLI пути). Источник не доказывает установленную сборку Windows/AC29.
