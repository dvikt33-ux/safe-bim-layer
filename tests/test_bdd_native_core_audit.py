"""Offline guard checks for BDD read-only native geometry audit (no Archicad)."""
import importlib.util
from pathlib import Path
import unittest
P=Path(__file__).resolve().parents[1]/'scripts'/'apa_bdd_native_core_audit.py'
spec=importlib.util.spec_from_file_location('apa_bdd_native_core_audit',P)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class NativeGeometryAuditTests(unittest.TestCase):
    def test_readonly_fence(self):
        self.assertEqual(m.READ,{'GetProjectInfo','GetAllElements',
                                 'GetDetailsOfElements','Get3DBoundingBoxes','GetStories'})
        for cmd in ('CreateWalls','DeleteElements','OpenProject','SaveProject','CreateColumns'):
            with self.assertRaisesRegex(RuntimeError,'READ_ONLY_FENCE'):
                m.get(cmd)
    def test_structural_inputs(self):
        self.assertEqual(len(m.PILES),49)
        self.assertEqual(len(set(m.PILES)),49)
        self.assertEqual(sum(m.PHYSICAL.values()),125)
        self.assertEqual(m.MAIN[0],(0,0))
        self.assertNotEqual(m.WORKING,m.ORIGINAL)
    def test_detect_pile_coordinate_change(self):
        rows=[]
        def box(x,y,z):return {'xMin':x-.15,'xMax':x+.15,'yMin':y-.15,'yMax':y+.15,'zMin':z,'zMax':-.6}
        for i,(x,y) in enumerate(m.PILES):
            rows.append({'guid':'c'+str(i),'type':'Column',
                'details':{'origin':{'x':x,'y':y},'height':2.4,
                           'width':.3,'depth':.3,'zCoordinate':-3.0,'circleBased':True},
                'boundingBox3D':box(x,y,-3)})
        for i,(a,b) in enumerate(zip(m.MAIN,m.MAIN[1:]+m.MAIN[:1])):
            rows.append({'guid':'w'+str(i),'type':'Wall',
              'details':{'begCoordinate':{'x':a[0],'y':a[1]},
                         'endCoordinate':{'x':b[0],'y':b[1]}},
              'boundingBox3D':box(0,0,-.1)})
        for t,n in [('Beam',66),('Slab',3),('Roof',1)]:
            for i in range(n):
                rows.append({'guid':t+str(i),'type':t,'details':{},
                            'boundingBox3D':dict(box(0,0,3.3),zMax=6.3) if t=='Roof' else box(0,0,0)})
        problems,warnings,counts=m.evaluate(rows)
        self.assertFalse(problems,problems)
        self.assertEqual(counts,m.PHYSICAL)
        rows[0]['details']['height']=3.5
        problems,*_=m.evaluate(rows)
        self.assertTrue(any('invalid height' in p for p in problems))
if __name__=='__main__':
    unittest.main()
