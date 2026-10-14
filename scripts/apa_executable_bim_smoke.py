"""Authorized existing-PLN functional scenario; one BIM Graph and SceneWriter.

Run only with private baseline, actual attribute/library inputs and explicit
test authorization. No APX installation, fixture building or automatic retry.
The source policies and selected schemas are consumed by the core router.
"""
import json,sys,hashlib,time,copy
from pathlib import Path
import archicad_project_accelerator as A
import archicad_connected_components as C
import archicad_bim_documentation as D
from archicad_connected_ifc import native_body_quantities
from archicad import ACConnection

def run(baseline,inputs,output,journal,effects,authorization,prepare_only=False,reconciled_wall=None,reconciled_window=None,reconciled_classification=None):
    if not authorization or Path(baseline['project']['projectPath']).stem!='APA_Stories_Grid_Stair_Test_01':raise ValueError('EXACT_AUTHORIZED_TEST_PROJECT_REQUIRED')
    b=baseline;out=Path(output);out.mkdir();api=A.EvidenceAPI(A.native_transport,out);A.RUN.PORT=b['port']
    assert api('GetProjectInfo',{})==b['project'];saved=lambda:hashlib.sha256(Path(b['project']['projectPath']).read_bytes()).hexdigest()
    assert saved()==b['savedSHA256'];A.RUN.bind_authorized_saved_copy(b['port'],b['project']['projectPath'],b['project']['projectName'],saved(),authorization)
    router=A.native_command_router(b['schemaFile'],ACConnection.connect(b['port']).commands);router.load_policies(effects)
    router.index(out/'selected-tool-index.md',out/'selected-tool-index.sqlite3')
    request='Create a native Wall with a hosted Window in a free test region; edit height, material, surface, classification and ElementID; move and copy; verify IFC/MEP, Save/Open, remove only temporary elements.'
    selection=A.native_task_tools(router,out/'selected-tool-index.sqlite3',request,limit=10);A.write_json(out/'gpt-tool-selection.json',selection)
    selected=['CreateWalls','ModifyWalls','CreateWindows','MoveElements','DeleteElements','SetClassificationsOfElements','SetPropertyValuesOfElements'];A.write_json(out/'selected-schemas.json',{n:router.select(n) for n in selected})
    existing_wall=(reconciled_wall or {}).get('guid','').lower()
    existing_window=(reconciled_window or {}).get('guid','').lower()
    if reconciled_wall and (reconciled_wall.get('status')!='LIVE_RECONCILED_NO_REPLAY_PASS' or not reconciled_wall.get('originalSceneId')):raise ValueError('MANUAL_RECONCILIATION_REQUIRED')
    if reconciled_window and (reconciled_window.get('status')!='LIVE_RECONCILED_NO_REPLAY_PASS' or not reconciled_window.get('originalSceneId')):raise ValueError('MANUAL_WINDOW_RECONCILIATION_REQUIRED')
    writer=A.RUN.SceneWriter(api,journal,b['schemaFile']);owned={g for g in [existing_wall,existing_window] if g};records=[];current={};protected=b['signatures'];steps=0;preparation=[];execution=[]
    def capture():
        ids=A.inventory_guids(api);model=D.capture_full_model(api,ids);signatures=C.retained_geometry_signatures(model,ids)
        if C.retained_geometry_signatures(model,list(protected))!=protected:raise ValueError('ORIGINAL258_CHANGED')
        return ids,model,signatures
    def detail(g):return A.RUN.requested_details(api,g)
    def by_id(model):return {e['guid'].lower():e for e in model['elements']}
    initial=capture();assert set(initial[0])==set(b['inventory'])|owned
    # Explicit test dimensions, checked against actual accepted geometry.
    region=dict(xMin=110,xMax=117,yMin=29.5,yMax=33.5,zMin=-.01,zMax=3.11)
    for e in by_id(initial[1]).values():
        if e['guid'].lower() in owned:continue
        vertices=[v for body in e.get('bodies',[]) for v in body['vertices']]
        if vertices and all(max(v[i] for v in vertices)>region[k+'Min'] and min(v[i] for v in vertices)<region[k+'Max'] for i,k in enumerate('xyz')):raise ValueError('TEST_REGION_OCCUPIED')
    material=inputs['materialFacts']['buildingMaterials'][0];other=inputs['materialFacts']['buildingMaterials'][1];surface=inputs['surfaces']['attributeIds'][0]['attributeId'];lib=inputs['windows']['detailsOfElements'][0]['details']['libPart']['name']
    system=inputs['classifications']['classificationSystems'][0]
    def flatten(items):
        for row in items:
            item=row['classificationItem'];yield item;yield from flatten(item.get('children',[]))
    cls=next(c for c in flatten(system['tree']['classificationItems']) if c.get('id','').casefold() in {'стена','wall'})
    wall_data=dict(begCoordinate=dict(x=110,y=30),endCoordinate=dict(x=116,y=30),floorIndex=0,zCoordinate=0,height=2.8,thickness=.25,referenceLineLocation='Center',structureType='Basic',buildingMaterialId=material['attributeId'])
    ref=lambda sid,pointer:{'$result':dict(step=sid,pointer=pointer)}
    element=lambda sid:dict(guid=existing_wall) if sid=='wall' and existing_wall else dict(guid=existing_window) if sid=='window' and existing_window else ref(sid,'/elements/0/elementId')
    prop=router.read(api,router.prepare('API.GetPropertyIds',dict(properties=[dict(type='BuiltIn',nonLocalizedName='General_ElementID')])),True)['properties'][0]['propertyId']
    def check_wall(g,height,x=110,material_id=None,face=None):
        row=detail(g);d=row['details'];assert row['type']=='Wall' and row['floorIndex']==0
        for key,value in [('height',height),('begThickness',.25),('endThickness',.25)]:assert A.RUN.close(d[key],value),(key,d[key],value)
        begin=d.get('begCoordinate',d.get('beginCoordinate'));end=d.get('endCoordinate');assert A.RUN.close(begin['x'],x) and A.RUN.close(end['x'],x+6)
        if material_id:assert d['buildingMaterialId']['guid'].lower()==material_id['guid'].lower()
        if face:assert d['referenceMaterial']['overridden'] and d['referenceMaterial']['attributeId']['guid'].lower()==face['guid'].lower()
        return row
    def check_window(g,host):
        row=detail(g);d=row['details'];assert row['type']=='Window' and row['floorIndex']==0 and d['ownerElementId']['guid'].lower()==host
        for key,value in [('width',1.2),('height',1.2),('sillHeight',1),('centerOffset',3)]:assert A.RUN.close(d[key],value),(key,d[key])
        assert d['libPart']['name']==lib;return row
    def scoped(step,ticket,results):
        nonlocal steps
        sid=step['id'];before_ids,before_model,before_signatures=capture();affected=[]
        wall=existing_wall or results.get('wall',{}).get('elements',[{}])[0].get('elementId',{}).get('guid','').lower();window=existing_window or results.get('window',{}).get('elements',[{}])[0].get('elementId',{}).get('guid','').lower()
        if sid in {'edit','classify','property'}:affected=[wall]
        elif sid in {'window','move','copy'}:affected=[wall]+([window] if window else [])
        elif sid=='cleanup':affected=sorted(owned)
        assert set(affected)<=owned
        expected_before=set(b['inventory'])|owned;assert set(before_ids)==expected_before,'UNTRACKED_GUIDS_STOP'
        retained={g:s for g,s in before_signatures.items() if g not in affected}
        def verify_before(_):return dict(status='EXACT_TEMPORARY_SCOPE_PASS',owned=sorted(owned),affected=affected,baselineGuidCount=258,testRegion=region)
        def verify_after(reply,_):
            after_ids,after_model,after_signatures=capture();added=set(after_ids)-set(before_ids);removed=set(before_ids)-set(after_ids)
            # Save raw delta before any semantic assertion for reconciliation.
            record=dict(step=sid,command=ticket['command'],parameters=ticket['parameters'],before=before_ids,added=sorted(added),removed=sorted(removed),response=reply)
            records.append(record);A.write_json(out/'mutation-readback.json',records)
            if sid in {'wall','window'}:
                new=reply['elements'][0]['elementId']['guid'].lower();assert added=={new} and not removed;owned.add(new)
                if sid=='wall':check_wall(new,2.8,material_id=material['attributeId'])
                else:check_window(new,wall)
            elif sid=='copy':
                assert len(added)==2 and not removed;rows={g:detail(g) for g in added};new_wall=next(g for g,row in rows.items() if row['type']=='Wall');new_window=next(g for g,row in rows.items() if row['type']=='Window')
                check_wall(new_wall,3.1,x=110.5,material_id=other['attributeId'],face=surface);assert A.RUN.close(rows[new_wall]['details']['begCoordinate']['y'],33);check_window(new_window,new_wall);owned.update(added);record.update(newWall=new_wall,newWindow=new_window)
            elif sid=='cleanup':assert not added and removed==set(affected);owned.difference_update(removed)
            else:
                assert not added and not removed
                if sid=='edit':check_wall(wall,3.1,material_id=other['attributeId'],face=surface)
                elif sid=='move':check_wall(wall,3.1,x=110.5,material_id=other['attributeId'],face=surface);check_window(window,wall)
                elif sid=='classify':
                    got=router.read(api,router.prepare('API.GetClassificationsOfElements',dict(elements=[dict(elementId=dict(guid=wall))],classificationSystemIds=[dict(classificationSystemId=system['classificationSystemId'])])),True);assert cls['classificationItemId']['guid'].lower() in A.RUN.canonical(got).lower();record['classificationReadback']=got
                elif sid=='property':
                    got=router.read(api,router.prepare('API.GetPropertyValuesOfElements',dict(elements=[dict(elementId=dict(guid=wall))],properties=[dict(propertyId=prop)])),True);assert 'APA-EXECUTABLE-WALL-01' in A.RUN.canonical(got);record['propertyReadback']=got
            physical=by_id(after_model)
            if sid in {'window','move','copy','open'}:
                for g in owned:
                    if physical[g]['type']=='Wall':
                        quantity=native_body_quantities(physical[g]);record.setdefault('wallBodies',{})[g]=quantity
                        from shapely.geometry import Polygon
                        hole_areas=[]
                        for body in physical[g]['bodies']:
                            vertices=body['vertices']
                            for face in body['faces']:
                                for ring in face['contours'][1:]:
                                    points=[vertices[i] for i in ring]
                                    if max(p[1] for p in points)-min(p[1] for p in points)<1e-6:hole_areas.append(Polygon([(p[0],p[2]) for p in points]).area)
                        assert quantity['status']=='NATIVE_PLANAR_BREP_QUANTITIES' and len(hole_areas)==2 and abs(hole_areas[0]-hole_areas[1])<1e-5 and abs(quantity['volumeCubicMeters']-(6*3.1-hole_areas[0])*.25)<1e-5,quantity
                        record.setdefault('actualOpeningAreas',{})[g]=hole_areas[0]
                        record['windowOverallDimensionsAreNotRoughOpeningDimensions']=True
            if sid=='open':assert after_signatures==current['beforeOpenSignatures'],'SAVE_OPEN_CHANGED_MODEL'
            if sid=='save':current['beforeOpenSignatures']=after_signatures
            record['status']='LIVE_EFFECT_PASS';A.write_json(out/'mutation-readback.json',records)
            return dict(status='NATIVE_TEMPORARY_BIM_EFFECT_PASS',added=sorted(added),removed=sorted(removed),retained258=True)
        steps+=1
        return dict(scene_id='executable-bim-'+out.name+'-'+str(steps)+'-'+sid,affected=affected,retained_signatures=retained,saved_sha256=saved(),authorization=authorization,impact=router.policies[ticket['command']]['impact'],verify_before=verify_before,verify_after=verify_after)
    graph=dict(operations=[dict(id='wall',command='CreateWalls',params=dict(wallsData=[wall_data])),dict(id='wall-read',command='GetDetailsOfElements',params=dict(elements=ref('wall','/elements'))),dict(id='edit',command='ModifyWalls',params=dict(wallsWithDetails=[dict(elementId=element('wall'),height=3.1,buildingMaterialId=other['attributeId'],referenceMaterial=dict(overridden=True,attributeId=surface))]),after=['wall-read']),dict(id='window',command='CreateWindows',params=dict(windowsData=[dict(ownerWallId=element('wall'),centerOffset=3,sillHeight=1,width=1.2,height=1.2,libraryPartName=lib)]),after=['edit']),dict(id='classify',command='SetClassificationsOfElements',params=dict(elementClassifications=[dict(elementId=element('wall'),classificationId=dict(classificationSystemId=system['classificationSystemId'],classificationItemId=cls['classificationItemId']))]),after=['window']),dict(id='property',command='SetPropertyValuesOfElements',params=dict(elementPropertyValues=[dict(elementId=element('wall'),propertyId=prop,propertyValue=dict(value='APA-EXECUTABLE-WALL-01'))]),after=['classify']),dict(id='move',command='MoveElements',params=dict(elementsWithMoveVectors=[dict(elementId=element('wall'),moveVector=dict(x=.5,y=0,z=0),copy=False)]),after=['property']),dict(id='window-read',command='GetDetailsOfElements',params=dict(elements=ref('window','/elements')),after=['move']),dict(id='ifc',command='GetIFCIdsOfElements',params=dict(elements=ref('wall','/elements')),after=['move']),dict(id='mep',command='GetMEPElements',params=dict(domains=['Ventilation']),after=['move']),dict(id='collisions',command='GetCollisions',params=dict(elementsGroup1=ref('wall','/elements'),elementsGroup2=[dict(elementId=dict(guid=g)) for g in b['inventory']],settings=dict(volumeTolerance=.001,performSurfaceCheck=False,surfaceTolerance=.001)),after=['move']),dict(id='copy',command='MoveElements',params=dict(elementsWithMoveVectors=[dict(elementId=element('wall'),moveVector=dict(x=0,y=3,z=0),copy=True)]),after=['window-read','ifc','mep','collisions']),dict(id='save',command='SaveProject',params={},after=['copy']),dict(id='open',command='OpenProject',params=dict(projectFilePath=b['project']['projectPath']),after=['save'])])
    def execute(graph,label):
        start=time.perf_counter();intent=dict(schemaVersion='apa-native-task/1',request=request,graph=graph);preview=A.compile_intent(intent,b['schemaFile'],router=router);preparation.append(time.perf_counter()-start);A.write_json(out/(label+'-plan.json'),preview)
        start=time.perf_counter();result=A.run_native_task(router,api,preview,writer,scoped,lambda state:A.write_json(out/(label+'-checkpoint.json'),state));execution.append(time.perf_counter()-start);A.write_json(out/(label+'-result.json'),result)
        assert result['status']=='WORKFLOW_CALLABLE_VERIFIED',result
        return result
    if existing_wall:
        check_wall(existing_wall,3.1 if existing_window else 2.8,material_id=other['attributeId'] if existing_window else material['attributeId']);quantity=native_body_quantities(by_id(initial[1])[existing_wall]);assert quantity['status']=='NATIVE_PLANAR_BREP_QUANTITIES'
        if existing_window:check_window(existing_window,existing_wall)
        completed={'wall','edit','window'} if existing_window else {'wall'}
        if reconciled_classification:
            if reconciled_classification.get('status')!='LIVE_RECONCILED_NO_REPLAY_PASS' or not reconciled_classification.get('originalSceneId'):raise ValueError('MANUAL_CLASSIFICATION_RECONCILIATION_REQUIRED')
            got=router.read(api,router.prepare('API.GetClassificationsOfElements',dict(elements=[dict(elementId=dict(guid=existing_wall))],classificationSystemIds=[dict(classificationSystemId=system['classificationSystemId'])])),True);assert cls['classificationItemId']['guid'].lower() in A.RUN.canonical(got).lower();completed.add('classify')
        graph['operations']=[step for step in graph['operations'] if step['id'] not in completed]
        for step in graph['operations']:step['after']=[sid for sid in step.get('after',[]) if sid not in completed]
        def replace_wall_reference(value):
            if isinstance(value,dict) and '$result' in value and value['$result']['step'] in completed:
                guid=existing_wall if value['$result']['step']=='wall' else existing_window
                return [dict(elementId=dict(guid=guid))] if value['$result']['pointer']=='/elements' else dict(guid=guid)
            if isinstance(value,dict):return {k:replace_wall_reference(v) for k,v in value.items()}
            if isinstance(value,list):return [replace_wall_reference(v) for v in value]
            return value
        graph=replace_wall_reference(graph)
    if prepare_only:
        preview=A.compile_intent(dict(schemaVersion='apa-native-task/1',request=request,graph=graph),b['schemaFile'],router=router);A.write_json(out/'create-edit-plan.json',preview)
        proof=dict(status='REAL_INPUTS_AND_TYPED_WORKFLOW_PREPARED',stepCount=len(graph['operations']),original258Preserved=True,nativeWrites=api.write_attempts,modelChanges=0)
        assert api.write_attempts==0;A.write_json(out/'PREPARED.json',proof);return proof
    start=time.perf_counter();result=execute(graph,'create-edit');assert len(owned)==4
    assert not result['results']['collisions']['collisions'],'UNPLANNED_COLLISION'
    # New graph explicitly consumes proven temporary ownership after native copy.
    cleanup=dict(operations=[dict(id='cleanup',command='DeleteElements',params=dict(elements=[dict(elementId=dict(guid=g)) for g in sorted(owned)])),dict(id='save',command='SaveProject',params={},after=['cleanup']),dict(id='open',command='OpenProject',params=dict(projectFilePath=b['project']['projectPath']),after=['save'])]);execute(cleanup,'cleanup')
    final=capture();assert final[0]==b['inventory'] and final[2]==protected and not owned
    raw=[json.loads(l) for l in (out/'raw.jsonl').read_text(encoding='utf8').splitlines()]
    proof=dict(status='LIVE_EXECUTABLE_NATIVE_BIM_WORKFLOWS_PASS',folder=str(out),retained258=True,finalGuidCount=len(final[0]),temporaryCreated=4,temporaryDeleted=4,writeEffects=len(records),nativeCalls=dict(api.calls),callableVerified=sorted(router.callable),liveVerified=sorted(router.live),modelGUIDsPreserved=True,saveOpen='PASS_WITH_TEMPORARY_AND_CLEANED_MODEL',temporaryDuplicates=0,operations=records,performance=dict(totalScenarioSeconds=time.perf_counter()-start,planPreparationSeconds=preparation,workflowExecutionSeconds=execution,apiCalls=sum(api.calls.values()),transportSeconds=sum(r['elapsedSeconds'] for r in raw),transportReadAndVerifySeconds=sum(r['elapsedSeconds'] for r in raw if r['command'] not in selected+['SaveProject','OpenProject']),manualSpeedup='NOT_MEASURED'),engineering='NOT_VERIFIED',APXchanged=False)
    A.write_json(out/'FINAL.json',proof);return proof

if __name__=='__main__':
    read=lambda p:json.loads(Path(p).read_text(encoding='utf8'))
    cfg=read(sys.argv[1]);proof=run(read(cfg['baseline']),read(cfg['inputs']),cfg['output'],cfg['journal'],read(cfg['effects']),cfg['authorization'],prepare_only=cfg.get('prepareOnly',False),reconciled_wall=cfg.get('reconciledWall'),reconciled_window=cfg.get('reconciledWindow'),reconciled_classification=cfg.get('reconciledClassification'));print(json.dumps({k:proof[k] for k in ['status','temporaryCreated','temporaryDeleted','finalGuidCount','saveOpen','performance','nativeWrites'] if k in proof}))
