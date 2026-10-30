"""Offline acceptance for delivered VIS-01 scene, preserving source semantics."""
import json,struct,unittest,sys,hashlib
import numpy as np
import trimesh
from collections import Counter
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'outputs/moag-vis-01/generated'
sys.path.insert(0,str(ROOT/'tools/moag_topology'))
import solver_r11 as r11
import physical_connectivity_r22 as r22
class VIS01(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.scene=json.loads((OUT/'scene.json').read_text(encoding='utf-8'))
  cls.proof=json.loads((OUT/'validation.json').read_text(encoding='utf-8'))
 def test_r22_and_all_sources_and_route_occurrences_survive(self):
  s=self.scene
  self.assertEqual(s['base_R22'],'b6b333d62cd9a4de6afcd8262d5882bf668086f8')
  self.assertEqual(len(s['objects']),196)
  self.assertEqual(len(s['route_occurrences']),378)
  self.assertEqual(len(s['gap_nodes']),18)
  self.assertEqual(len(s['original_typed_edges']),845)
  self.assertEqual(sum(bool(e.get('proves_direct_access')) for e in s['original_typed_edges']),25)
  self.assertEqual(s['new_doors'],0)
 def test_actual_original_graph_and_r22_qualified_edges_match(self):
  graph=r11.inputs()[-1]
  self.assertEqual(self.scene['R09_fingerprint'],r11.digest(graph))
  self.assertEqual(self.scene['original_typed_edges'],graph['edges'])
  self.assertEqual(self.scene['route_occurrences'],[n for n in graph['nodes'] if n['layer']=='ROUTE_OCCURRENCE'])
  self.assertEqual(self.scene['R22_edge_dispositions'],r22.qualified_edges(graph)[1])
 def test_only_one_hall_and_uncertain_is_not_fixed(self):
  s=self.scene;found=[o for o in s['objects'] if o['id']=='M-L1-AH-OLD-001']
  self.assertEqual(len(found),1);self.assertEqual(found[0]['aliases'],['M-L1-CH-001'])
  self.assertEqual(found[0]['sample_shape'],'ELLIPTICAL_CYLINDER_SCENARIO')
  self.assertEqual(found[0]['size'][0],found[0]['size'][1])
  for ident in ['MOAG-G-0009','MOAG-G-0036']:
   self.assertEqual(next(o for o in s['objects'] if o['id']==ident)['sample_shape'],'ELLIPTICAL_CYLINDER_SCENARIO')
  self.assertEqual(s['confirmed_placements'],0);self.assertEqual(s['scenario_placements'],13)
  self.assertEqual(Counter(o['placement'] for o in s['objects']),{'SCENARIO':13,'UNPLACED_UNKNOWN':183})
  self.assertTrue(all(not o['coordinates_known'] for o in s['objects']))
 def test_scenario_boxes_fit_circular_level_envelopes(self):
  shells={s['global_level']:s for s in self.scene['shells']}
  self.assertEqual(set(shells),{1,2,3})
  for o in self.scene['placed_volumes']:
   shell=shells[o['global_level']];hx,hy,hz=shell['origin'];w,d,h=shell['size']
   x,y,z=o['origin'];dx,dy,dz=o['size']
   self.assertGreaterEqual(z,hz);self.assertLessEqual(z+dz,hz+h)
   for px in (x,x+dx):
    for py in (y,y+dy):
     self.assertLessEqual(((px-hx-w/2)/(w/2))**2+((py-hy-d/2)/(d/2))**2,1+1e-10)
 def test_solvers_and_geometric_checks(self):
  p=self.proof
  for k in ['python_cp_sat','minizinc','minizinc_python_witness_replay']:
   self.assertEqual(p[k],'SAT')
  for k in ['false_hall_split_python','false_hall_split_minizinc','false_boat_merge_python','false_boat_merge_minizinc']:
   self.assertEqual(p[k],'INFEASIBLE')
  self.assertEqual(p['actual_nonparent_aabb_intersections'],[])
  self.assertEqual(p['hall_ellipse_control_and_bound_points'],'PASS')
  self.assertEqual(p['parent_aabb_containment'],'PASS')
  self.assertEqual(p['partial_gallery_containment'],'PASS')
  self.assertEqual(len(p['APA_scene_graph_topological_order']),13)
 def test_partial_gallery_is_one_scenario_child_of_the_round_hall(self):
  o=next(o for o in self.scene['placed_volumes'] if o['id']=='M-L1-CH-GAL-001')
  self.assertEqual(o['parent'],'M-L1-AH-OLD-001')
  self.assertEqual(o['sample_shape'],'HALF_ANNULAR_GALLERY_SCENARIO')
  self.assertTrue(any(x['id']=='P-220' for x in o['sources']))
  glb=trimesh.load(OUT/'station.glb',force='scene');_,name=glb.graph[o['id']];mesh=glb.geometry[name]
  self.assertTrue(mesh.is_watertight);self.assertTrue(mesh.is_winding_consistent)
 def test_r05_profile_scale_is_possible_without_selecting_real_dimensions(self):
  c=self.scene['R05_symbolic_scale_check'];lo,hi=c['scale_interval_modules_per_scenario_unit']
  self.assertEqual(c['status'],'SYMBOLIC_COMMON_SCALE_EXISTS_NOT_SELECTED')
  self.assertGreater(lo,0);self.assertLessEqual(lo,hi)
  self.assertEqual({x['object_id'] for x in c['checks']},{x['id'] for x in self.scene['placed_volumes']})
  profiles={x['profile_id'] for x in c['checks']}
  self.assertTrue({'M-L1-CH-001','M-L1-AH-OLD-001'}<=profiles)
 def test_all_views_decode_and_have_pixels(self):
  for name in ['station-axon.png','level-1-axon.png','level-1.png','level-2.png','level-3.png','vertical-section.png']:
   with Image.open(OUT/name) as im:
    im.load();self.assertGreater(im.width,600);self.assertGreater(im.height,500)
 def test_glb_has_translucent_geometry_for_all_objects_and_levels(self):
  raw=(OUT/'station.glb').read_bytes();self.assertEqual(raw[:4],b'glTF')
  self.assertEqual(struct.unpack_from('<I',raw,8)[0],len(raw))
  length=struct.unpack_from('<I',raw,12)[0];gltf=json.loads(raw[20:20+length])
  names={n.get('name') for n in gltf['nodes']}
  self.assertTrue({o['id'] for o in self.scene['placed_volumes']}<=names)
  self.assertTrue({'LEVEL-1','LEVEL-2','LEVEL-3'}<=names)
  self.assertTrue(all(m.get('alphaMode')=='BLEND' for m in gltf['materials']))
 def test_glb_roundtrip_has_scene_geometry_bounds(self):
  glb=trimesh.load(OUT/'station.glb',force='scene')
  for obj in self.scene['shells']+self.scene['placed_volumes']:
   transform,name=glb.graph[obj['id']]
   points=trimesh.transform_points(glb.geometry[name].vertices,transform)
   actual=np.array([points.min(axis=0),points.max(axis=0)])
   expected=np.array([obj['origin'],np.array(obj['origin'])+obj['size']])
   self.assertTrue(np.allclose(actual,expected,atol=1e-4),obj['id'])
 def test_manifest_matches_all_delivered_artifacts(self):
  manifest=json.loads((OUT/'manifest.json').read_text(encoding='utf-8'))
  self.assertEqual(manifest['base_R22'],'b6b333d62cd9a4de6afcd8262d5882bf668086f8')
  self.assertEqual(manifest['generator_sha256'],hashlib.sha256((ROOT/'tools/moag_vis/generate_vis01.py').read_bytes()).hexdigest())
  self.assertGreaterEqual(len(manifest['files']),17)
  for row in manifest['files']:
   data=(OUT/row['path']).read_bytes()
   self.assertEqual(len(data),row['bytes']);self.assertEqual(hashlib.sha256(data).hexdigest(),row['sha256'])
 def test_html_is_self_contained_and_declares_controls(self):
  html=(OUT/'station.html').read_text(encoding='utf-8')
  self.assertIn('plotly.js',html.lower())
  for token in ['id=v1','id=v2','id=v3','id=vs','id=vo','Plotly.restyle']:
   self.assertIn(token,html)
  self.assertNotIn('src="https://cdn.plot.ly',html)
if __name__=='__main__':unittest.main()
