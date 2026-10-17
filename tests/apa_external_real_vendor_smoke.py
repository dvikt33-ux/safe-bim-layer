"""New external vendor path smoke; Python 3.11/3.12 isolated venv, no Archicad.

Exercises actual ifcdiff, pdfplumber and ezdxf on self-generated ephemeral
fixtures, not mocks or write permissions in a PLN.
"""
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import apa_external_readonly as E
import apa_external_router_activation as R

import ezdxf
import ifcopenshell
import ifcopenshell.guid


def main():
    with tempfile.TemporaryDirectory(prefix="apa-new-tools-smoke-") as temp:
        folder = Path(temp)
        dxf = folder / "draw.dxf"
        d = ezdxf.new("R2013")
        d.modelspace().add_line((0, 0), (1, 2))
        d.saveas(dxf)
        dxf_result, sources = E.dxf_vectors(SimpleNamespace(a=str(dxf)))
        assert sources == [dxf.resolve()]
        assert dxf_result["primitiveCount"] == 1, dxf_result

        pdf = folder / "drawing.pdf"
        R.make_pdf(pdf)
        pdf_result, sources = E.pdf_vectors(SimpleNamespace(a=str(pdf)))
        assert sources == [pdf.resolve()]
        assert pdf_result["pages"][0]["lineCount"] >= 1, pdf_result

        model = ifcopenshell.file(schema="IFC4")
        model.create_entity("IfcProject", GlobalId=ifcopenshell.guid.new(),
                            Name="APA vendor smoke")
        before, after = folder / "before.ifc", folder / "after.ifc"
        model.write(before)
        model.write(after)
        diff, sources = E.ifc_diff(SimpleNamespace(
            a=str(before), b=str(after), output=str(folder / "not-used.json")))
        assert sources == [before.resolve(), after.resolve()]
        assert diff["vendor"] == "ifcdiff", diff
        assert isinstance(diff["vendorOutput"], (dict, list)), diff

    print(json.dumps({
        "status": "REAL_VENDOR_SOURCE_READ_ONLY_PASS",
        "operations": ["PDFVectors", "DXFVectors", "IFCDiff"],
        "archicadNativeCalls": 0, "plnWrites": 0}, indent=2))


if __name__ == "__main__":
    main()
