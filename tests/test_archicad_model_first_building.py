import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import archicad_project_accelerator as A
import archicad_authored_extension as E
import archicad_authored_geometry as G
import archicad_bim_documentation as D
from test_archicad_isolated_authored_execution import IsolatedNative
from test_archicad_scene_run import FakeNative

OLD='00000000-0000-4000-8000-000000000001'
NEW='00000000-0000-4000-8000-000000000009'


class ModelFirstTests(unittest.TestCase):
    def setUp(self):
        self.intent=json.loads((ROOT/'examples/accelerator/model-first-building.json').read_text(encoding='utf8'))
        self.api=IsolatedNative()
        p=patch.object(A.RUN,'EXPECTED_PATH',A.RUN.APPROVED_ISOLATED_WRITER_PATH)
        p.start();self.addCleanup(p.stop)

    def compiled(self):
        return A.compile_authored_intent(self.intent,A.RUN.DEFAULT_SCENE_SCHEMA,self.api)

    def test_complete_source_compiles_21_native_elements_through_existing_graph(self):
        result=self.compiled()
        self.assertEqual(len(result['graph']['operations']),21)
        counts=result['metrics']['nativeCommands']
        self.assertEqual(counts,{'CreateSlabs':2,'CreateWalls':10,'CreateDoors':2,'CreateWindows':6,'CreateRoofs':1})
        self.assertEqual({v['executor'] for v in result['routes'].values()},{'SceneWriter'})
        self.assertNotIn('CreateMorphs',counts)

    def test_slab_supports_entire_wall_width_and_lower_wall_stops_at_underside(self):
        ops={x['id']:x for x in self.compiled()['graph']['operations']}
        slab=ops['native-slab-level-1']['params']['slabsData'][0]
        self.assertAlmostEqual(min(p['x'] for p in slab['polygonCoordinates']),141.85)
        self.assertAlmostEqual(max(p['x'] for p in slab['polygonCoordinates']),152.15)
        self.assertAlmostEqual(ops['native-wall-east-level-1']['params']['wallsData'][0]['height'],2.8)
        self.assertAlmostEqual(ops['native-slab-level-2']['params']['slabsData'][0]['level'],3)

    def test_policy_is_explicit_and_default_historical_geometry_is_retained(self):
        self.intent.pop('junctionPolicy');ops={x['id']:x for x in self.compiled()['graph']['operations']}
        self.assertEqual(ops['native-wall-east-level-1']['params']['wallsData'][0]['height'],3)
        self.assertEqual(min(p['x'] for p in ops['native-slab-level-1']['params']['slabsData'][0]['polygonCoordinates']),142)

    def test_invalid_junction_policy_and_outside_partition_fail_before_writes(self):
        self.intent['junctionPolicy']['slabFootprint']='GUESS'
        with self.assertRaises(ValueError):self.compiled()
        self.intent['junctionPolicy']['slabFootprint']='OUTER_WALL_FACE'
        next(x for x in self.intent['nativeComponents'] if x['id']=='test-partition-0')['params']['wallsData'][0]['begCoordinate']['x']=1000
        with self.assertRaisesRegex(ValueError,'OUTSIDE_DECLARED'):self.compiled()
        self.assertFalse(self.api.writes)

    def test_missing_roof_material_and_unsupported_morph_are_denied(self):
        roof=next(x for x in self.intent['nativeComponents'] if x['id']=='test-roof')
        roof['params']['roofsData'][0].pop('buildingMaterialId')
        with self.assertRaisesRegex(ValueError,'TYPED_BASIC'):self.compiled()
        roof['command']='CreateMorphs'
        with self.assertRaisesRegex(ValueError,'UNSUPPORTED_AUTHORED'):self.compiled()

    def test_structural_function_cannot_be_assigned_to_an_opening(self):
        self.intent['structuralFunctions']['authored-entry-door']='LoadBearingElement'
        with self.assertRaisesRegex(ValueError,'STRUCTURAL_FUNCTIONS'):self.compiled()

    def test_saved_copy_preview_requires_current_exact_hash_and_explicit_binding(self):
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/'test.pln');Path(path).write_bytes(b'original')
            record={'path':path,'sha256':hashlib.sha256(b'original').hexdigest(),'authorizationRef':'test'}
            with patch.object(A.RUN,'EXPECTED_PATH',path),patch.object(A.RUN,'_SAVED_COPY_AUTHORIZATION',record):
                self.assertTrue(A.RUN.authorized_authored_target(path))
                Path(path).write_bytes(b'changed')
                self.assertFalse(A.RUN.authorized_authored_target(path))

    def scope(self,command,params,owned=(NEW,),retained=(OLD,)):
        return E.model_operation_scope(command,params,'source',owned,retained,'explicit test')

    def test_roof_move_preserves_guid_and_protected_targets_are_denied(self):
        params={'elementsWithMoveVectors':[{'elementId':{'guid':NEW},'moveVector':{'x':0,'y':0,'z':.2},'copy':False}]}
        self.scope('MoveElements',params)
        params['elementsWithMoveVectors'][0]['elementId']['guid']=OLD
        with self.assertRaises(ValueError):self.scope('MoveElements',params)
        params['elementsWithMoveVectors'][0]['elementId']['guid']=NEW
        params['elementsWithMoveVectors'][0]['copy']=True
        with self.assertRaises(ValueError):self.scope('MoveElements',params)

    def test_malformed_dimensions_and_scope_tamper_are_denied(self):
        params={'windowsWithDetails':[{'elementId':{'guid':NEW},'width':1.4}]}
        scope=self.scope('ModifyWindows',params)
        changed=copy.deepcopy(params);changed['windowsWithDetails'][0]['width']=1.5
        with self.assertRaisesRegex(ValueError,'SCOPE_MISMATCH'):E.qualify_model_operation(scope,'ModifyWindows',changed,'source')
        params['windowsWithDetails'][0]['width']=float('nan')
        with self.assertRaises(ValueError):self.scope('ModifyWindows',params)

    def test_seo_requires_owned_operator_exact_upwards_and_explicit_flags(self):
        roof='00000000-0000-4000-8000-000000000010'
        params={'solidLinks':[{'targetId':{'guid':NEW},'operatorId':{'guid':roof},'operation':'SubtractionUpwards',
            'linkFlags':{'inheritOperatorAttributes':False,'skipPolygonHoles':True}}]}
        self.scope('CreateSolidElementLinks',params,(NEW,roof))
        params['solidLinks'][0]['operatorId']['guid']=OLD
        with self.assertRaises(ValueError):self.scope('CreateSolidElementLinks',params,(NEW,roof))

    def test_bearing_metadata_uses_real_localized_native_definition(self):
        definition={'propertyId':{'guid':NEW},'isEditable':True,'type':'singleEnum','possibleEnumValues':[
            {'enumValue':{'nonLocalizedValue':r,'displayValue':label}} for r,label in
            [('LoadBearingElement','Bearing native label'),('NonLoadBearingElement','Partition native label')]]}
        def api(c,p):
            return {'properties':[{'propertyId':{'guid':NEW}}]} if c=='API.GetPropertyIds' else {'propertyDefinitions':[{'propertyDefinition':definition}]}
        result=E.resolve_structural_function(api)
        self.assertEqual(result['displayValues']['NonLoadBearingElement'],'Partition native label')
        self.assertEqual(result['engineeringCapacity'],'NOT_VERIFIED')
        definition['isEditable']=False
        with self.assertRaises(ValueError):E.resolve_structural_function(api)

    def test_parameter_diff_edits_roof_only_without_recreation(self):
        compiled=self.compiled();old={**compiled,'binding':{'path':'test'},'slabBasicMaterialGuid':NEW,
            'integrationBindings':{'dependencies':{'authoredRoofJunctions':{'targetStepIds':['wall']}}}}
        proposed=copy.deepcopy(compiled)
        next(x for x in proposed['graph']['operations'] if x['id']=='test-roof')['params']['roofsData'][0]['level']+=.2
        created={x['id']:{'guid':NEW,'kind':x['command'][6:-1],'floorIndex':0} for x in old['graph']['operations']}
        with patch.object(E,'verify_model',return_value=created),patch.object(A,'compile_authored_intent',return_value=proposed):
            result=E.prepare_building_parameter_edit(self.api,old,created,self.intent,A.RUN.DEFAULT_SCENE_SCHEMA)
        self.assertEqual(result['newCreates'],0)
        self.assertEqual(result['operations'][0]['command'],'MoveElements')
        self.assertAlmostEqual(result['operations'][0]['parameters']['elementsWithMoveVectors'][0]['moveVector']['z'],.2)
        self.assertEqual(result['newPlan']['binding'],old['binding'])
        self.assertEqual(result['newPlan']['integrationBindings'],old['integrationBindings'])

    def test_unchanged_parameters_and_removed_elements_cannot_dispatch(self):
        compiled=self.compiled();created={x['id']:{'guid':NEW} for x in compiled['graph']['operations']}
        with patch.object(E,'verify_model',return_value=created),patch.object(A,'compile_authored_intent',return_value=compiled):
            with self.assertRaisesRegex(ValueError,'NO_PARAMETER_CHANGE'):
                E.prepare_building_parameter_edit(self.api,compiled,created,self.intent,A.RUN.DEFAULT_SCENE_SCHEMA)
        proposed=copy.deepcopy(compiled);proposed['graph']['operations'].pop()
        with patch.object(E,'verify_model',return_value=created),patch.object(A,'compile_authored_intent',return_value=proposed):
            with self.assertRaisesRegex(ValueError,'CANNOT_ADD_REMOVE'):
                E.prepare_building_parameter_edit(self.api,compiled,created,self.intent,A.RUN.DEFAULT_SCENE_SCHEMA)

    def test_native_segment_sentinel_uses_resultant_brep_not_fabricated_bounds(self):
        raw={'regenerated3D':True,'coordinateSystem':'ABSOLUTE_PROJECT_XYZ','nativeBodySlots':1,
             'bodies':[{'nativeBodyIndex':1}],'deletedBodySlots':[],'geometryScope':'active native filters'}
        normal={'elements':[{'guid':OLD,'nativeTypeId':70,'bodies':[{'vertices':[[100,1,0],[101,2,1]]}]}]}
        def api(c,p):
            if c=='GetAllElements':return {'elements':[{'elementId':{'guid':OLD}}]}
            if c=='Get3DBoundingBoxes':return {'boundingBoxes3D':[{'boundingBox3D':
                {'xMin':1e35,'xMax':-1e35,'yMin':1e35,'yMax':-1e35,'zMin':0,'zMax':0}}]}
            return raw
        with patch.object(G,'normalize_dump',return_value=normal):
            result=A.RUN.scan_for_existing_geometry(api,0,0)
            self.assertEqual(result['resultantBodyBoundsFallbackGuids'],[OLD])
            with self.assertRaisesRegex(ValueError,'SPATIAL_COLLISION'):A.RUN.scan_for_existing_geometry(api,100,1)

    def test_missing_native_body_slots_cannot_bypass_spatial_gate(self):
        def api(c,p):
            if c=='GetAllElements':return {'elements':[{'elementId':{'guid':OLD}}]}
            if c=='Get3DBoundingBoxes':return {'boundingBoxes3D':[{'boundingBox3D':
                {'xMin':1e35,'xMax':-1e35,'yMin':1e35,'yMax':-1e35,'zMin':0,'zMax':0}}]}
            return {'regenerated3D':True,'coordinateSystem':'ABSOLUTE_PROJECT_XYZ','nativeBodySlots':2,
                'bodies':[{'nativeBodyIndex':1}],'deletedBodySlots':[]}
        with self.assertRaisesRegex(ValueError,'incomplete native body slots'):A.RUN.scan_for_existing_geometry(api,0,0)


if __name__=='__main__':unittest.main()
