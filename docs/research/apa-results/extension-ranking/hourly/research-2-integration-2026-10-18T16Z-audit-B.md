# APA AC29 16Z — independent audit B

Architecture and engineering review: APA already contains Router, SceneWriter, BIM Graph, IFC reader, native group clone and external JSON evidence runner. A second writer or IFC engine is unnecessary. Native GUID and IFC GlobalId are different identifiers. IFC subset exports require host and port relationship checks. Publisher with an empty selection can publish a whole set. SplitByStorey may omit spanning elements. IFC postprocessing does not establish faster Archicad modelling.

Choices: reuse existing IfcDiff; prefer existing Tapir Publisher only after local command discovery; use ready IfcTester BCF2 for IDS after package review; adapt IfcPatch on separate IFC copies; defer SAF-to-PyNite and MEP mixed transition.

Status SOURCE only; no measured acceleration or model modifications.
