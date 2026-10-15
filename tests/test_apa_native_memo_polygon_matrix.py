"""128 native Slab/Roof parameter-contour and omission scenarios (not 3D BREP)."""
from pathlib import Path
import sys
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from archicad_local_modules import memo_polygon_inputs


def native_polygon(guid, length, hole=False, native_type=8, story=0):
    outline = [(0, 0), (length, 0), (length, length), (0, length), (0, 0)]
    ring = [(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)] if hole else []
    coords = outline + ring
    return dict(elementId={"guid": guid}, nativeTypeId=native_type, homeStory=story,
                coordinates=[dict(index=i+1, x=float(x), y=float(y))
                             for i, (x, y) in enumerate(coords)],
                contourEnds=[5, 10] if hole else [5], arcs=[])


@pytest.mark.parametrize("case", range(128))
def test_slab_roof_memo_contours_and_fail_closed_omissions(case):
    side = 6 + case % 17
    good = native_polygon(f"VALID_{case}", side, bool(case & 1),
                          8 if case & 2 else 9, (case % 9) - 4)
    if case < 64:
        response = memo_polygon_inputs({"elements": [good]})
        assert len(response["polygons"]) == 1
        assert response["omitted"] == []
        polygon = response["polygons"][0]
        assert len(polygon["holes"]) == bool(case & 1)
        assert response["nativeBindings"][0]["homeStory"] == (case % 9) - 4
        assert (side * side - bool(case & 1)) == (
            side * side - sum(1 for _ in polygon["holes"]))
    else:
        bad = native_polygon(f"BAD_{case}", side, True)
        variant = case % 8
        if variant == 0:
            bad["nativeTypeId"] = 37   # Curtain Wall not a slab footprint
        elif variant == 1:
            bad["homeStory"] = "0"
        elif variant == 2:
            bad["arcs"] = [{"beginIndex": 1, "endIndex": 2, "angle": 0.5}]
        elif variant == 3:
            bad["contourEnds"] = [5, 9]
        elif variant == 4:
            bad["coordinates"][1]["x"] = float("inf")
        elif variant == 5:
            bad["coordinates"][2]["index"] = 99
        elif variant == 6:
            bad["coordinates"][4]["x"] = 1.0
        else:
            bad["elementId"]["guid"] = good["elementId"]["guid"]
        response = memo_polygon_inputs({"elements": [good, bad]})
        assert len(response["polygons"]) == 1
        assert response["polygons"][0]["id"] == f"VALID_{case}"
        assert len(response["omitted"]) == 1
        assert response["omitted"][0]["index"] == 1
    assert response["authority"] == "NATIVE_PARAMETER_POLYGONS_NOT_RESULTANT_BREP"
    assert response["engineering"] == "NOT_VERIFIED"
