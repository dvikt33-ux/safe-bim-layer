"""Minimal regression for the live-observed Column -> ColumnSegment layout."""
import unittest
from apa_source_qualified_native_batch import verify_stud_bodies

class NativeColumnBodyRegression(unittest.TestCase):
    def test_owned_segment_is_the_physical_body_authority(self):
        root='root';child='segment';material='timber'
        item=dict(coordinates=dict(x=2,y=3,z=0),buildingMaterialId=dict(guid=material))
        vertices=[[x,y,z] for x in (1.95,2.05) for y in (2.975,3.025) for z in (0,2.9)]
        native=dict(elements=[dict(guid=root,type='Column',bodies=[]),dict(guid=child,type='ColumnSegment',relationships=dict(hostGuid=root),materialBindings=dict(buildingMaterial=dict(guid=material)),bodies=[dict(vertices=vertices)])])
        proof=verify_stud_bodies(native,[root],[item],{root:[child]})
        self.assertEqual(proof['elements'][0]['status'],'NATIVE_STUD_BODY_PASS')
        native['elements'][1]['relationships']['hostGuid']='foreign'
        with self.assertRaisesRegex(ValueError,'OWNER_MISMATCH'):
            verify_stud_bodies(native,[root],[item],{root:[child]})

if __name__=='__main__':unittest.main()
