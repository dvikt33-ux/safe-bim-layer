import copy
from contextlib import closing
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_connected_components as C
import archicad_connected_solver as SOLVER
import archicad_connected_ifc as IFC
from test_archicad_scene_run import FakeNative

GUID='00000000-0000-4000-8000-000000000001'
MAT='00000000-0000-4000-8000-000000000002'


class ConnectedComponentsTests(unittest.TestCase):
    def test_actual_details_fact_join_and_preserved_blockers(self):
        r=C.details_candidate(ROOT,'ARMO_SELFLOCK_ROOF__P0003',{'guid':GUID,'kind':'Roof','floorIndex':1})
        self.assertEqual(r['archiveSha256'],C.DETAILS_SHA)
        self.assertEqual(len(r['resolvedFacts']),2)
        self.assertEqual(len(r['missingDimensionEntities']),8)
        self.assertFalse(r['assemblyWriteAllowed'])
        first=r['resolvedFacts'][0]
        self.assertEqual((first['values']['value'],first['values']['value_2']),(25.,150.))
        self.assertEqual(first['fact']['normalized_unit'],'mm')
        self.assertEqual(r['host']['guid'],GUID)

    def test_details_unknown_id_fails(self):
        with self.assertRaisesRegex(ValueError,'NOT_UNIQUE'):C.details_candidate(ROOT,'INVENTED')

    def test_details_wrong_host_fails(self):
        with self.assertRaisesRegex(ValueError,'ROOF_HOST'):C.details_candidate(ROOT,'ARMO_SELFLOCK_ROOF__P0003',{'guid':GUID,'kind':'Wall'})

    def test_disabled_and_unknown_modules(self):
        self.assertEqual(C.adapters([]),{})
        with self.assertRaises(ValueError):C.adapters(['saf'])
        with self.assertRaises(ValueError):C.NativeAdapter('DeleteElements')
        with self.assertRaises(ValueError):C.RUN.SceneWriter(None,'unused',adapters={'DeleteElements':object()})

    def test_default_writer_does_not_enable_extended_commands(self):
        self.assertNotIn('CreateRoofs',C.RUN.SceneWriter(None,'unused').allowed_writes)
        self.assertIn('CreateRoofs',C.RUN.SceneWriter(None,'unused',adapters=C.adapters(['roof'])).allowed_writes)

    def test_strict_attribute_wrapper_accepts_observed_mep_shape(self):
        self.assertEqual(C.attribute_guid({'attributeId':{'guid':GUID}}),GUID)
        self.assertEqual(C.attribute_guid({'guid':GUID}),GUID)
        for invalid in ({'guid':GUID,'name':'extra'},{'attributeId':{'guid':'bad'}},None):
            with self.assertRaises(ValueError):C.attribute_guid(invalid)

    def test_box_rejects_nonfinite_zero_and_negative(self):
        for n in (0,-1,float('nan'),float('inf'),True):
            with self.assertRaises(ValueError):C.explicit_box_body({'x':1,'y':n,'z':1})

    def test_explicit_box_is_closed_by_edge_incidence(self):
        from collections import Counter
        body=C.explicit_box_body({'x':2,'y':.025,'z':.15});counts=Counter()
        for face in body['polygons']:
            ring=face['vertexIds']
            for i,left in enumerate(ring):counts[tuple(sorted((left,ring[(i+1)%len(ring)])))]+=1
        self.assertEqual((len(body['vertices']),len(body['polygons']),len(counts)),(8,6,12))
        self.assertEqual(set(counts.values()),{2})

    def test_face_keys_detect_missing_bottom_and_wrong_winding(self):
        body=C.explicit_box_body({'x':2,'y':.025,'z':.15})
        missing=copy.deepcopy(body);missing['polygons'].pop(0)
        self.assertNotEqual(C.body_face_keys(body),C.body_face_keys(missing))
        reversed_body=copy.deepcopy(body);reversed_body['polygons'][0]['vertexIds'].reverse()
        self.assertNotEqual(C.body_face_keys(body),C.body_face_keys(reversed_body))

    def test_face_keys_survive_polygon_rotation(self):
        body=C.explicit_box_body({'x':2,'y':.025,'z':.15});other=copy.deepcopy(body)
        other['polygons'].reverse()
        for p in other['polygons']:p['vertexIds']=p['vertexIds'][1:]+p['vertexIds'][:1]
        self.assertEqual(C.body_face_keys(body),C.body_face_keys(other))

    def test_morph_no_ambiguous_size_body(self):
        handler=C.NativeAdapter('CreateMorphs')
        for data in ({'size':{'x':1,'y':1,'z':1},'body':{}},{}):
            with self.assertRaises(ValueError):handler.resolve({'params':{'morphsData':[data]}},{},{})

    def test_mep_floor_is_active_story_not_z_guess(self):
        h=C.NativeAdapter('CreateMEPRoutingElements')
        self.assertEqual(h.floor({'routingElementsData':[{'nodeCoordinates':[{'z':20}]}]},{'binding':{'storyIndex':0}}),0)

    def route_fixture(self):
        data={'domain':'Ventilation','mepSystemId':{'guid':MAT},'nodeCoordinates':[{'x':0,'y':0,'z':2.5},{'x':6,'y':0,'z':2.5}],
            'crossSectionWidth':.2,'crossSectionHeight':.15,'crossSectionShape':'Rectangular'}
        row={'domain':data['domain'],'mepSystemId':{'attributeId':{'guid':MAT}},'polyline':data['nodeCoordinates'],
            'segments':[{'elementId':{'guid':GUID},'crossSectionWidth':.2,'crossSectionHeight':.15,'crossSectionShape':'Rectangular'}],
            'nodes':[{'elementId':{'guid':GUID},'position':p} for p in data['nodeCoordinates']]}
        return data,row

    def test_unknown_native_type_requires_dedicated_route_proof(self):
        data,row=self.route_fixture()
        h=C.NativeAdapter('CreateMEPRoutingElements');native={'type':'Unknown','floorIndex':0,'details':{'error':'Not supported'}}
        self.assertEqual(h.verify(lambda c,p:{'routingElements':[row]},GUID,{'routingElementsData':[data]},native,0,0),'MEPRouting')
        with self.assertRaises(ValueError):h.verify(lambda c,p:{'routingElements':[{'error':{}}]},GUID,{'routingElementsData':[data]},native,0,0)

    def test_mep_missing_segment_or_wrong_section_fails(self):
        data,row=self.route_fixture();h=C.NativeAdapter('CreateMEPRoutingElements');native={'type':'Unknown','floorIndex':0}
        bad=copy.deepcopy(row);bad['segments']=[]
        with self.assertRaises(ValueError):h.verify(lambda c,p:{'routingElements':[bad]},GUID,{'routingElementsData':[data]},native,0,0)
        bad=copy.deepcopy(row);bad['segments'][0]['crossSectionWidth']=.3
        with self.assertRaises(ValueError):h.verify(lambda c,p:{'routingElements':[bad]},GUID,{'routingElementsData':[data]},native,0,0)

    def test_mep_wrong_node_position_fails(self):
        data,row=self.route_fixture();row=copy.deepcopy(row);row['nodes'][0]['position']['z']=9
        with self.assertRaises(ValueError):C.NativeAdapter('CreateMEPRoutingElements').verify(lambda c,p:{'routingElements':[row]},GUID,{'routingElementsData':[data]},{'type':'Unknown','floorIndex':0},0,0)

    def test_ifc_map_rejects_loss_wrong_guid_and_duplicates(self):
        context={'elements':{'one':{'guid':GUID},'two':{'guid':MAT}}}
        for rows in ([],[{'elementId':{'guid':GUID},'ifcId':'X'*22}]*2,
            [{'elementId':{'guid':GUID},'ifcId':'X'*22},{'elementId':{'guid':MAT},'ifcId':'X'*22}]):
            with self.assertRaises(ValueError):C.ifc_map(lambda c,p:{'elementIFCIds':rows},context)

    def test_extra_inventory_guid_is_never_assigned_blindly(self):
        with self.assertRaises(ValueError):C.verify_inventory({'inventory':[GUID,MAT]},{'inventory':[GUID]},{},[])

    def test_hash_binds_modules_source_and_host_facts(self):
        base={'schemaSha256':'X','integrationBindings':{'enabled':['roof'],'host':GUID}}
        one=C.RUN.native_plan_hash(base,'graph')
        changed=copy.deepcopy(base);changed['integrationBindings']['host']=MAT
        self.assertNotEqual(one,C.RUN.native_plan_hash(changed,'graph'))
        changed=copy.deepcopy(base);changed['integrationBindings']['enabled']=[]
        self.assertNotEqual(one,C.RUN.native_plan_hash(changed,'graph'))

    def test_repair_timeout_is_durable_and_not_replayed(self):
        with tempfile.TemporaryDirectory() as temp:
            journal=Path(temp)/'state.sqlite3'
            with closing(sqlite3.connect(journal)) as db:
                db.execute('CREATE TABLE scenes(scene_id TEXT PRIMARY KEY,plan_hash TEXT,state TEXT,result TEXT)')
                db.execute('CREATE TABLE steps(scene_id TEXT,step_id TEXT,state TEXT,guid TEXT,output TEXT,PRIMARY KEY(scene_id,step_id))');db.commit()
            native=FakeNative();calls=[]
            def api(command,params):
                if command=='ModifyMorphs':calls.append(command);raise TimeoutError('unknown outcome')
                return native(command,params)
            writer=C.RUN.SceneWriter(api,journal,adapters=C.adapters(['morph']))
            plan={'sourcePlanHash':'OLD','binding':C.RUN.guarded_project(api)}
            params={'morphsWithDetails':[{'elementId':{'guid':GUID},'body':C.explicit_box_body({'x':1,'y':1,'z':1})}]}
            token=C.RUN.digest({'sceneId':'repair-timeout-test','sourcePlanHash':'OLD','command':'ModifyMorphs','parameters':params,'target':plan['binding']})
            result=writer.modify_morph_body(plan,'repair-timeout-test',params,token,lambda:None)
            self.assertEqual(result['status'],'PARTIAL_OR_UNKNOWN_OUTCOME')
            with self.assertRaises(ValueError):writer.modify_morph_body(plan,'repair-timeout-test',params,token,lambda:None)
            self.assertEqual(calls,['ModifyMorphs'])

    def test_repair_wrong_hash_performs_no_write(self):
        writer=C.RUN.SceneWriter(lambda *a:self.fail('must not dispatch'),'unused',adapters=C.adapters(['morph']))
        with self.assertRaises(ValueError):writer.modify_morph_body({'sourcePlanHash':'X','binding':{}},'test-repair-id',{},'WRONG',lambda:None)


class ConnectedSolverTests(unittest.TestCase):
    def context(self):
        return {'coordinateSystem':'ABSOLUTE_PROJECT_XYZ','units':'m','elements':{'column':{'kind':'Column','bounds':[[[2,3],[3.9,4.1],[0,3]]]}}}

    def test_solver_avoids_actual_blocker_and_uses_preference(self):
        r=SOLVER.choose_straight_route(self.context(),0,6,[2,4,6],2.5,.131,.106,6)
        self.assertEqual(r['status'],'OPTIMAL');self.assertEqual(r['selectedIndex'],2)
        self.assertEqual(r['candidates'][1]['blockedBy'],['column'])
        self.assertEqual(r['nativeCollisionAcceptance'],'NOT_VERIFIED')

    def test_solver_infeasible_and_invalid_units(self):
        r=SOLVER.choose_straight_route(self.context(),0,6,[4],2.5,.131,.106,4)
        self.assertEqual(r['status'],'INFEASIBLE');self.assertNotIn('nodeCoordinates',r)
        c=self.context();c['units']='mm'
        with self.assertRaises(ValueError):SOLVER.choose_straight_route(c,0,6,[6],2.5,.131,.106,6)

    def test_solver_no_nonfinite_or_duplicate_candidates(self):
        for ys in ([],[1,1],[float('nan')]):
            with self.assertRaises(ValueError):SOLVER.choose_straight_route(self.context(),0,6,ys,2.5,.131,.106,6)


class ConnectedIfcTests(unittest.TestCase):
    def test_export_prevents_overwrite_before_any_native_call(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'existing.ifc';path.write_text('original')
            with self.assertRaises(ValueError):IFC.export_once(lambda *a:self.fail('no native call'),{}, {},path,'translator',Path(temp)/'state.sqlite','export-id')
            self.assertEqual(path.read_text(),'original')


if __name__=='__main__':unittest.main()
