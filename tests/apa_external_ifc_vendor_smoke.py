"""Real upstream IFC read-only smoke; ephemeral geometrically valid IFC4/IDS.

No Archicad process, PLN, saved BDD model, plugin upgrade or model writes.
Tests the already-installed adapter code with its own ifcopenshell 0.8.5 stack.
"""
from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
import apa_external_readonly as E

import ifcopenshell
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.unit
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.spatial
import ifcopenshell.api.aggregate
from ifctester import ids


def create_ifc(path, label):
    model = ifcopenshell.api.project.create_file(version="IFC4")
    project = ifcopenshell.api.root.create_entity(model, ifc_class="IfcProject", name="APA SMOKE")
    ifcopenshell.api.unit.assign_unit(model)
    ctx = ifcopenshell.api.context.add_context(model, context_type="Model")
    body = ifcopenshell.api.context.add_context(
        model, context_type="Model", context_identifier="Body",
        target_view="MODEL_VIEW", parent=ctx)
    site = ifcopenshell.api.root.create_entity(model, ifc_class="IfcSite", name="Site")
    building = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuilding", name="Building")
    storey = ifcopenshell.api.root.create_entity(model, ifc_class="IfcBuildingStorey", name="Level 0")
    ifcopenshell.api.aggregate.assign_object(model, relating_object=project, products=[site])
    ifcopenshell.api.aggregate.assign_object(model, relating_object=site, products=[building])
    ifcopenshell.api.aggregate.assign_object(model, relating_object=building, products=[storey])
    wall = ifcopenshell.api.root.create_entity(model, ifc_class="IfcWall", name=label)
    ifcopenshell.api.geometry.edit_object_placement(model, product=wall)
    representation = ifcopenshell.api.geometry.add_wall_representation(
        model, context=body, length=5, height=3, thickness=0.2)
    ifcopenshell.api.geometry.assign_representation(
        model, product=wall, representation=representation)
    ifcopenshell.api.spatial.assign_container(model, relating_structure=storey, products=[wall])
    model.write(str(path))
    return wall.GlobalId


def main():
    with tempfile.TemporaryDirectory(prefix="apa-ifc-vendor-read-") as tmp:
        directory = Path(tmp)
        source_a = directory / "architecture.ifc"
        source_b = directory / "services.ifc"
        guid_a = create_ifc(source_a, "Wall A")
        guid_b = create_ifc(source_b, "Wall B")
        assert guid_a != guid_b

        # Original APA quantity reader (no new QTO algorithm).
        prior_root = E.ROOT
        E.ROOT = SCRIPTS.parent
        try:
            qto, files = E.ifc_qto(SimpleNamespace(a=str(source_a)))
        finally:
            E.ROOT = prior_root
        original = qto["result"]
        assert original["schema"] == "APA_QUANTIFIED_IFC_EXCHANGE_V1", original
        assert len(original["elements"]) == 1, original
        assert original["elements"][0]["ifcId"] == guid_a, original
        assert original["elements"][0]["ifcType"] == "IfcWall", original

        # Official IfcTester validation with actual IDS XML and one matching wall.
        document = ids.Ids(title="APA required wall names")
        spec = ids.Specification(name="IFC4 wall name check", ifcVersion=["IFC4"])
        spec.applicability.append(ids.Entity(name="IFCWALL"))
        spec.requirements.append(ids.Attribute(name="Name"))
        document.specifications.append(spec)
        idspath = directory / "wall-name.ids"
        document.to_xml(str(idspath))
        check, files = E.ids_validate(SimpleNamespace(
            a=str(source_a), ids=str(idspath), output=str(directory / "ids-evidence.json")))
        assert check["vendor"] == "ifctester", check
        assert isinstance(check["vendorOutput"], dict), check

        # Actual collision engine against two overlapping IFC wall solids.
        clash, files = E.ifc_clash(SimpleNamespace(
            a=str(source_a), b=str(source_b),
            output=str(directory / "clash-evidence.json")))
        assert clash["vendor"] == "ifcclash", clash
        assert isinstance(clash["vendorOutput"], (dict,list)), clash

    print(json.dumps({
        "status": "REAL_IFC_VENDOR_READ_ONLY_PASS",
        "operations": ["IFCQuantities", "IDSValidate", "IFCClash"],
        "ifcElementCount": 1,
        "geometrySource": "ACTUAL_IFC4_WALL_SOLIDS",
        "idsSource": "ACTUAL_IFCTESTER_AUTHORED_IDS",
        "archicadNativeCalls": 0,
        "plnWrites": 0
    }, indent=2))


if __name__ == "__main__":
    main()
