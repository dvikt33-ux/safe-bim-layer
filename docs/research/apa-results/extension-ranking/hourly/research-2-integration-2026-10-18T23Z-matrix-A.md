# Integration matrix A
IfcTester strict: APA V1→ifctester.ids.open(validate=True)→existing Json; 95, БЫСТРО, adapter; invalid XML and missing-property fixtures.
IfcFM: APA B2 private IFC copy→IfcFM cobie24→CSV; 89, АДАПТАЦИЯ, adapter; ifcfm/pandas/openpyxl missing in lock, duplicate_keys==0, GUID/units.
IfcClash: APA V1→ifcclash clearance/check_all→JSON; 87, БЫСТРО, adapter; three fixtures and unit guard.
IFC provenance: PR154 PDF SHA/page→B2 IFC copy→document API→IfcRelAssociatesDocument; 88, АДАПТАЦИЯ, adapter; GUID/revision readback.
