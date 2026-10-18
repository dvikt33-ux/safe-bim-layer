# APA AC29 16Z — appendix C1: Split and BCF

SOURCE-only technical checks 21–25.

21. IfcPatch SplitByBuildingStorey names files '{i}-{storey.Name}.ifc' using the raw storey name, including in Windows output path. Source: https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifcpatch/ifcpatch/recipes/SplitByBuildingStorey.py#L21-L51 . Need sanitized filenames and isolated directory.
22. SplitByBuildingStorey is_in_storey tests ContainedInStructure[0].RelatingStructure.GlobalId only. Same source L79-L84. Spanning stairs/walls and indirect containment require explicit GUID coverage.
23. Split recipe uses copyfile(src,dest), opens dest, removes non-storey elements and writes dest. Same source L42-L77. It is not intrinsically read-only; only use permitted IFC copies.
24. IfcTester CLI accepts -r Json or Bcf and -o path; both call engine.to_file. Source: https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifctester/ifctester/__main__.py#L31-L66 . Existing APA runner expects JSON; BCF ZIP requires a different output reader.
25. IfcTester reporter.Bcf.to_file imports bcf.v2.bcfxml.BcfXml, creates topic and viewpoint from IFC GlobalId and placement. Source: https://github.com/IfcOpenShell/IfcOpenShell/blob/master/src/ifctester/ifctester/reporter.py#L425-L466 . This is BCF2, not BCF3.

Alternatives: Split A native Archicad per-storey export (callable SDK29 contract not verified), B IfcPatch Split (spanning/path risks): DEFER. BCF A IfcTester→BCF2 for IDS, B BCF3 for generic QA: prefer A for IDS after licensing review. SOURCE only, no installs or live runs.
