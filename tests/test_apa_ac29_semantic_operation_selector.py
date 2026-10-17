"""Focused decision-quality tests: no Archicad runtime calls, no native writes.

Synthetic BDD-shaped scenarios: 49 structural pile locations, timber stud
runs, verified axes, incomplete raster, isolated walls, hosted openings.
These are decision fixtures, not claims about actual PDF dimensions or timings.
"""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from apa_ac29_semantic_operation_selector import analyze, topology

COLUMN="Column"
FAM_A="TIMBER_100x50_SAME_MATERIAL_STORY0"
FAM_B="STEEL_BEAM_SECTION_VERIFIED_STORY0"
FAM_C="WALL_CUSTOM_SECTION_VERIFIED_STORY0"
GUID_C="b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
GUID_B="26d80ca1-e33e-4983-9948-18f7b2279957"


def row(kind,x,y,z=0,family=FAM_A,**additional):
    return dict(type=kind,familySignature=family,storyIndex=0,
                anchor=dict(x=x,y=y,z=z),
                sourceRef="SYNTHETIC_DRAWING_KR_AXIS_AND_MEMBER_PLAN",
                **additional)


def prototype(kind,guid,family=FAM_A,x=0,y=0,z=0):
    value=row(kind,x,y,z,family)
    del value["sourceRef"]
    value.update(guid=guid,nativeReadbackVerified=True)
    return value


def source_axes(xs,ys,native=True):
    return dict(status="SOURCE_VERIFIED",
                sourceRef="SOURCE_REVIEWED_EXPLICIT_AXIS_LABELS_AND_COORDINATES",
                X=[dict(id=f"X{i+1}",coordinate=x) for i,x in enumerate(xs)],
                Y=[dict(id=f"Y{i+1}",coordinate=y) for i,y in enumerate(ys)],
                requiresNativeAxisObjects=native)


class NativeSelectionDecisions(unittest.TestCase):
    def test_one_off_custom_wall_uses_single_create_and_not_grid(self):
        data=[row("Wall",25,6,family=FAM_C,
                  nativeCreateData={"complete":"TEST_ONLY"})]
        result=analyze([],data)
        self.assertEqual(result["creates"][0]["method"],"NATIVE_CREATE_SINGLE")
        self.assertEqual(result["creates"][0]["nativeCommand"],"CreateWalls")
        self.assertEqual(result["creates"][0]["arrangement"]["pattern"],"SINGLE")
        self.assertEqual(result["sourceAxes"]["status"],
                         "NO_SOURCE_QUALIFIED_AXIS_GRID_REQUEST")
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],0)

    def test_12_identical_columns_full_rectangular_array_no_axes_inferred(self):
        existing=[prototype(COLUMN,GUID_C,x=1,y=1)]
        positions=[row(COLUMN,x,y) for x in (21,22,23) for y in (11,12,13,14)]
        result=analyze(existing,positions)
        self.assertEqual(result["copies"][0]["arrangement"]["pattern"],
                         "RECTANGULAR_ARRAY")
        self.assertEqual(result["copies"][0]["arrangement"]["gridShape"],[3,4])
        self.assertEqual(result["copies"][0]["count"],12)
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],1)
        self.assertEqual(result["sourceAxes"]["status"],
                         "NO_SOURCE_QUALIFIED_AXIS_GRID_REQUEST")

    def test_49_studs_on_grid_are_separate_from_true_semantic_axes(self):
        existing=[prototype(COLUMN,GUID_C,x=0,y=0)]
        xs=[20+i*2 for i in range(7)]
        ys=[10+j*1.5 for j in range(7)]
        targets=[row(COLUMN,x,y) for x in xs for y in ys]
        result=analyze(existing,targets,source_axes=source_axes(xs,ys))
        self.assertEqual(result["copies"][0]["count"],49)
        self.assertEqual(result["copies"][0]["arrangement"]["pattern"],
                         "RECTANGULAR_ARRAY")
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],1)
        self.assertEqual(result["sourceAxes"]["sourceAxesX"],7)
        self.assertEqual(result["sourceAxes"]["sourceAxesY"],7)
        self.assertEqual(result["sourceAxes"]["status"],
                         "NATIVE_GRID_ELEMENTS_REQUIRE_INDEPENDENT_RUNTIME_AND_LIBRARY_PROOF")
        self.assertFalse(result["sourceAxes"]["nativeAxisCallsAuthorized"])

    def test_hole_in_column_grid_requires_exact_explicit_placements(self):
        existing=[prototype(COLUMN,GUID_C,x=1,y=1)]
        xs=[21,22,23]
        ys=[11,12,13,14]
        targets=[row(COLUMN,x,y) for x in xs for y in ys if (x,y)!=(22,12)]
        result=analyze(existing,targets,source_axes=source_axes(xs,ys))
        self.assertEqual(result["copies"][0]["count"],11)
        self.assertEqual(result["copies"][0]["arrangement"]["pattern"],
                         "EXPLICIT_POSITIONS")
        self.assertEqual(result["sourceAxes"]["occupiedIntersections"],11)

    def test_straight_regular_and_irregular_studs_use_different_patterns(self):
        prototype_=[prototype(COLUMN,GUID_C)]
        regular=analyze(prototype_,[row(COLUMN,2*i,3) for i in range(1,7)])
        irregular=analyze(prototype_,[row(COLUMN,x,3) for x in (2,3.1,7,12)])
        self.assertEqual(regular["copies"][0]["arrangement"]["pattern"],
                         "LINEAR_ARRAY")
        self.assertEqual(irregular["copies"][0]["arrangement"]["pattern"],
                         "EXPLICIT_POSITIONS")
        self.assertEqual(irregular["copyNativeCallsIfIndependentlyAuthorized"],1)

    def test_explicit_even_distribution_requires_real_endpoint_source(self):
        e=[prototype(COLUMN,GUID_C)]
        targets=[row(COLUMN,x,0) for x in (2,4,6,8)]
        key=(COLUMN,FAM_A,0)
        rules={key:dict(mode="EVEN_BETWEEN",
                        sourceRef="VERIFIED_END_POINTS_AND_SPACING",
                        path=[dict(x=2,y=0,z=0),dict(x=8,y=0,z=0)])}
        result=analyze(e,targets,distribution_rules=rules)
        self.assertEqual(result["copies"][0]["arrangement"]["pattern"],
                         "EVEN_DISTRIBUTION")
        bad=copy.deepcopy(rules)
        bad[key]["path"][1]["x"]=8.5
        with self.assertRaisesRegex(ValueError,"MUST_PRESERVE_ALL_EXACT_POINTS"):
            analyze(e,targets,distribution_rules=bad)

    def test_verified_polyline_equal_arc_length_is_not_a_straight_array(self):
        e=[prototype(COLUMN,GUID_C)]
        p=[row(COLUMN,1,0),row(COLUMN,2,0),row(COLUMN,2,1),
           row(COLUMN,2,2)]
        rule={(COLUMN,FAM_A,0):dict(mode="ALONG_POLYLINE",
             sourceRef="SOURCE_VERIFIED_POLYLINE_POINTS",
             path=[dict(x=1,y=0,z=0),dict(x=2,y=0,z=0),
                   dict(x=2,y=2,z=0)])}
        result=analyze(e,p,distribution_rules=rule)
        self.assertEqual(result["copies"][0]["arrangement"]["pattern"],
                         "POLYLINE_DISTRIBUTION")

    def test_two_prototypes_different_types_share_one_copy_call(self):
        e=[prototype(COLUMN,GUID_C),prototype("Beam",GUID_B,FAM_B)]
        targets=[row(COLUMN,x,0) for x in (5,7)]
        targets+=[row("Beam",15,18,family=FAM_B)]
        result=analyze(e,targets)
        self.assertEqual(len(result["copies"]),2)
        self.assertEqual(sum(r["count"] for r in result["copies"]),3)
        self.assertEqual(result["copyMethod"],
                         "ONE_NATIVE_MULTI_PROTOTYPE_COPY_CALL")
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],1)

    def test_verified_object_copy_single_and_batched_not_unqualified_create(self):
        obj="LIBPART_OBJECT_IDENTICAL_LIBRARY_PARAMETERS"
        prototype_obj=prototype("Object",GUID_C,family=obj)
        one=analyze([prototype_obj],[row("Object",3,2,family=obj)])
        self.assertEqual(one["copies"][0]["method"],"NATIVE_COPY_SINGLE")
        self.assertEqual(one["copyMethod"],"ONE_NATIVE_COPY_CALL")
        several=analyze([prototype_obj],[
            row("Object",3,2,family=obj),row("Object",6,2,family=obj)])
        self.assertEqual(several["copyMethod"],"ONE_NATIVE_BATCH_COPY_CALL")
        no_verified_prototype=analyze([],[row("Object",3,2,family=obj)])
        self.assertEqual(no_verified_prototype["creates"][0]["state"],
                         "BLOCKED_OBJECT_CREATE_REQUIRES_VERIFIED_LIBRARY_PART")
        self.assertIsNone(no_verified_prototype["creates"][0]["nativeCommand"])

    def test_hosted_windows_batch_creates_not_free_floating_copy(self):
        e=[prototype("Window",GUID_C)]
        targets=[row("Window",x,0,
                     nativeCreateData={"ownerWallId":{"guid":"sourcewall"}})
                 for x in (4,6)]
        result=analyze(e,targets)
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],0)
        self.assertEqual(result["creates"][0]["nativeCommand"],"CreateWindows")
        self.assertEqual(result["creates"][0]["method"],"NATIVE_CREATE_BATCH")

    def test_unique_roof_is_single_create_not_an_array(self):
        result=analyze([],[row("Roof",55,10,family=FAM_C,
                               nativeCreateData={"polygonCoordinates":[]})])
        self.assertEqual(result["creates"][0]["nativeCommand"],"CreateRoofs")
        self.assertEqual(result["creates"][0]["method"],"NATIVE_CREATE_SINGLE")

    def test_repeated_columns_without_prototype_require_batch_create_source(self):
        targets=[row(COLUMN,x,0,nativeCreateData={"section":"TEST"})
                 for x in (20,22,24,26)]
        result=analyze([],targets)
        self.assertEqual(result["creates"][0]["method"],"NATIVE_CREATE_BATCH")
        self.assertEqual(result["creates"][0]["arrangement"]["pattern"],
                         "LINEAR_ARRAY")
        self.assertEqual(result["copies"],[])

    def test_no_source_geometry_cannot_become_eligible_create(self):
        result=analyze([],[row(COLUMN,30,40)])
        self.assertEqual(result["creates"][0]["state"],
                         "BLOCKED_NATIVE_SOURCE_DATA_MISSING")
        self.assertEqual(result["nativeModelWrites"],0)

    def test_axis_with_mismatched_coordinates_is_denied(self):
        existing=[prototype(COLUMN,GUID_C)]
        with self.assertRaisesRegex(ValueError,"NOT_AT_SOURCE_AXIS_INTERSECTION"):
            analyze(existing,[row(COLUMN,20,10)],
                    source_axes=source_axes([20,30],[11,15]))

    def test_duplicate_placement_fails_before_any_candidate(self):
        existing=[prototype(COLUMN,GUID_C)]
        with self.assertRaisesRegex(ValueError,"DUPLICATED"):
            analyze(existing,[row(COLUMN,3,4),row(COLUMN,3,4)])

    def test_all_fulfilled_requires_no_copy_or_create(self):
        existing=[prototype(COLUMN,GUID_C,x=2,y=3)]
        result=analyze(existing,[row(COLUMN,2,3)])
        self.assertEqual(result["copies"],[])
        self.assertEqual(result["creates"],[])
        self.assertEqual(result["alreadyPresent"],1)
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],0)



class NativeBddSourceEvidence(unittest.TestCase):
    """The actual 261-GUID native read, NOT a claim about 298-GUID LIVE state."""
    @classmethod
    def setUpClass(cls):
        import json
        cls.fixture=json.loads((Path(__file__).parent/"fixtures"/
            "apa_ac29_bdd_261_verified_native_positions.json"
        ).read_text(encoding="utf8"))

    def test_49_real_piles_are_not_a_7_by_7_axis_grid(self):
        rows=self.fixture["piles"]
        self.assertEqual(len(rows),49)
        xyz=[tuple(row["anchor"][k] for k in ("x","y","z")) for row in rows]
        self.assertEqual(len({p[0] for p in xyz}),31)
        self.assertEqual(len({p[1] for p in xyz}),21)
        self.assertEqual(topology(xyz)["pattern"],"EXPLICIT_POSITIONS")
        # Two separate phenomena: spatial element placement and semantic
        # native GridElements. The source does not contain named grid axes.
        source=row(COLUMN,1,0,family=FAM_A)
        self.assertIsNone(None if "axisSource" not in source else source["axisSource"])

    def test_true_native_49_pile_copy_plan_uses_one_call_without_axes(self):
        piles=self.fixture["piles"]
        family="BDD_NATIVE_PILE_300_DIAMETER_2400_HIGH_MATERIAL"
        first=piles[0]
        source=prototype("Column",first["guid"],family,
                         **first["anchor"])
        targets=[row("Column",r["anchor"]["x"],r["anchor"]["y"],
                     r["anchor"]["z"],family) for r in piles]
        result=analyze([source],targets)
        self.assertEqual(result["alreadyPresent"],1)
        self.assertEqual(len(result["copies"]),1)
        self.assertEqual(result["copies"][0]["count"],48)
        self.assertEqual(result["copies"][0]["layoutTargetCount"],49)
        self.assertEqual(result["copies"][0]["arrangement"]["pattern"],
                         "EXPLICIT_POSITIONS")
        self.assertEqual(result["copyMethod"],"ONE_NATIVE_BATCH_COPY_CALL")
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],1)
        self.assertEqual(result["sourceAxes"]["status"],
                         "NO_SOURCE_QUALIFIED_AXIS_GRID_REQUEST")
        self.assertEqual(result["nativeModelWrites"],0)

    def test_real_48_joists_reuse_two_verified_native_prototypes(self):
        beams=self.fixture["floorJoists"]
        def family(beam):
            d=round(beam["end"]["y"]-beam["start"]["y"],3)
            return "BDD_NATIVE_JOIST_LEN_" + str(d) + "_SAME_ATTRIBUTES"
        prototypes={}
        targets=[]
        for beam in beams:
            sig=family(beam)
            if sig not in prototypes:
                prototypes[sig]=prototype("Beam",beam["guid"],sig,
                    beam["start"]["x"],beam["start"]["y"],beam["z"])
            targets.append(row("Beam",beam["start"]["x"],
                               beam["start"]["y"],beam["z"],sig))
        self.assertEqual(len(prototypes),2)
        result=analyze(list(prototypes.values()),targets)
        self.assertEqual(result["alreadyPresent"],2)
        self.assertEqual(sum(g["count"] for g in result["copies"]),46)
        self.assertEqual(result["copyMethod"],
                         "ONE_NATIVE_MULTI_PROTOTYPE_COPY_CALL")
        arrangements={g["arrangement"]["pattern"]:g for g in result["copies"]}
        self.assertEqual(arrangements["LINEAR_ARRAY"]["layoutTargetCount"],9)
        self.assertEqual(arrangements["PARALLEL_LINEAR_RUNS"]["layoutTargetCount"],39)
        self.assertEqual(arrangements["PARALLEL_LINEAR_RUNS"]["arrangement"]["runCount"],2)
        self.assertEqual(sorted(x["count"] for x in
                         arrangements["PARALLEL_LINEAR_RUNS"]["arrangement"]["runs"]),
                         [15,24])
        self.assertEqual(result["copyNativeCallsIfIndependentlyAuthorized"],1)
        self.assertEqual(result["nativeModelWrites"],0)

    def test_real_48_joists_have_three_600mm_runs_two_native_lengths(self):
        rows=self.fixture["floorJoists"]
        self.assertEqual(len(rows),48)
        spans={}
        for item in rows:
            a,b=item["start"],item["end"]
            key=(round(a["y"],3),round(b["y"],3),
                 round(b["y"]-a["y"],3))
            spans.setdefault(key,[]).append((a["x"],a["y"],item["z"]))
        self.assertEqual(
            sorted((len(v), round(k[2],3)) for k,v in spans.items()),
            [(9,5.085),(15,3.995),(24,3.995)])
        for coords in spans.values():
            self.assertEqual(topology(coords)["pattern"],"LINEAR_ARRAY")
            sorted_x=sorted(v[0] for v in coords)
            gaps=[round(sorted_x[i+1]-sorted_x[i],3)
                  for i in range(len(sorted_x)-1)]
            self.assertEqual(set(gaps),{0.6})
        by_family={}
        for (y1,y2,length),arr in spans.items():
            by_family.setdefault(length,[]).extend(arr)
        self.assertEqual(topology(by_family[3.995])["pattern"],
                         "PARALLEL_LINEAR_RUNS")
        self.assertEqual(topology(by_family[3.995])["runCount"],2)

    def test_real_18_grillage_members_have_many_different_lengths(self):
        rows=self.fixture["grillageBeams"]
        self.assertEqual(len(rows),18)
        import math
        lengths=[round(math.hypot(r["end"]["x"]-r["start"]["x"],
                                  r["end"]["y"]-r["start"]["y"]),3)
                 for r in rows]
        self.assertGreaterEqual(len(set(lengths)),10)
        # Shared material and cross section are insufficient for safe copy:
        # a beam prototype must preserve its verified native length.
        self.assertEqual({(x["width"],x["height"]) for x in rows},{(0.4,0.3)})
        self.assertEqual(len({x["materialId"] for x in rows}),1)

if __name__=="__main__":
    unittest.main()
