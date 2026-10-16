"""Execute one source-qualified timber-stud batch through installed APA.

Requires a local reviewed manifest, existing SceneWriter ledger and backups.
No network downloads, private project paths, retries or alternative writer.
The single CreateColumns call is followed by a batched native Details check,
hierarchy ownership reconciliation and the router's retained BREP checks.
SaveProject is journaled separately only after the create scene reaches PASS.
"""
from __future__ import annotations
import argparse,hashlib,json,math,shutil,sqlite3,sys,time
from datetime import datetime,timezone
from pathlib import Path
import archicad_project_accelerator as APA
import archicad_scene_run as RUN
import archicad_connected_components as C
import archicad_bim_documentation as D

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def utc():return datetime.now(timezone.utc).isoformat()
def write(p,v):
    temp=p.with_suffix('.writing.tmp')
    temp.write_text(json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf8')
    temp.replace(p)
def require(test,message):
    if not test:raise ValueError(message)
def same(x,y):return type(x) in (int,float) and math.isfinite(x) and abs(x-y)<1e-5
def details(api,guids):
    reply=api('GetDetailsOfElements',dict(elements=[dict(elementId=dict(guid=g)) for g in guids]))
    rows=reply.get('detailsOfElements')
    require(isinstance(rows,list) and len(rows)==len(guids),'NATIVE_DETAILS_CARDINALITY')
    require(all(isinstance(r,dict) and 'error' not in r for r in rows),'NATIVE_DETAILS_ERROR')
    return dict(zip(guids,rows))
def verify_stud_bodies(native,created,items,ownership):
    """Column physical bodies belong to its owned ColumnSegment, not root."""
    require(len(created)==len(items) and bool(created) and set(ownership)==set(created),'SOURCE_STUD_OWNERSHIP_CARDINALITY')
    bodies={e['guid'].lower():e for e in native['elements']}
    proof=[]
    for guid,item in zip(created,items):
        require(bodies[guid]['type']=='Column','NATIVE_COLUMN_ROOT_TYPE_REQUIRED')
        segment_ids=ownership[guid]
        require(len(segment_ids)==1,'SOURCE_SINGLE_STUD_SEGMENT_REQUIRED')
        segment=bodies[segment_ids[0]]
        require(segment['type']=='ColumnSegment' and segment['relationships'].get('hostGuid','').lower()==guid,'NATIVE_COLUMN_SEGMENT_OWNER_MISMATCH')
        material=segment['materialBindings'].get('buildingMaterial',{})
        require(material.get('guid','').lower()==item['buildingMaterialId']['guid'].lower(),'STUD_BREP_MATERIAL_MISMATCH')
        vertices=[v for body in segment.get('bodies',[]) for v in body['vertices']]
        require(bool(vertices),'STUD_NATIVE_SEGMENT_BREP_MISSING')
        bounds={axis:(min(v[i] for v in vertices),max(v[i] for v in vertices)) for i,axis in enumerate('xyz')}
        xyz=item['coordinates']
        for axis,span in [('x',.1),('y',.05),('z',2.9)]:
            lo,hi=bounds[axis]
            require(same(hi-lo,span),'STUD_BREP_SECTION_OR_HEIGHT_MISMATCH:'+axis)
            require(same(lo,0 if axis=='z' else xyz[axis]-span/2),'STUD_BREP_POSITION_MISMATCH:'+axis)
        proof.append(dict(rootGuid=guid,segmentGuid=segment_ids[0],bounds=bounds,materialGuid=material['guid'],status='NATIVE_STUD_BODY_PASS'))
    return dict(status='NATIVE_COLUMN_SEGMENT_BODIES_MATCH_SOURCE_PASS',physicalCount=len(proof),elements=proof)
def main(args):
    manifest_path=Path(args.manifest).resolve()
    m=json.loads(manifest_path.read_text(encoding='utf8'))
    require(m['schema']=='apa.source-qualified-native-batch/1','MANIFEST_SCHEMA')
    require(m['command']=='CreateColumns' and len(m['items'])==13,'EXACT_SOURCE_STUD_BATCH_REQUIRED')
    out=Path(args.output).resolve();out.mkdir(parents=True,exist_ok=False)
    (out/'raw').mkdir()
    report=dict(schema='apa.source-qualified-live-native-batch/1',status='PREFLIGHT_STARTED',startedAtUTC=utc(),automaticRetry=False,nativeCreateCalls=0,saveCalls=0,manifestSha256=sha(manifest_path),installedAPA=str(Path(APA.__file__).resolve().parents[1]),ledgerPath=str(Path(args.ledger).resolve()))
    report_path=out/'report.json';write(report_path,report)
    shutil.copy2(manifest_path,out/'source-manifest.json')
    api=None
    try:
        target=m['target'];working=Path(target['path']);protected=m['protectedSource']
        baseline=json.loads(Path(m['baselineBackup']).read_text(encoding='utf8'))
        require(baseline['status']=='BASELINE_264_GUID_AND_CODE_LEDGER_PLN_BACKUP_PASS','BACKUP_PROOF_REQUIRED')
        for name,h in baseline['backups'].items():
            require(sha(Path(m['baselineBackup']).parent/name)==h,'BACKUP_HASH_CHANGED:'+name)
        require(sha(working)==target['savedSha256'],'SAVED_WORKING_PLN_DRIFT')
        require(sha(protected['path'])==protected['sha256'],'PROTECTED_SOURCE_DRIFT')
        require(sha(m['sourcePDF']['path'])==m['sourcePDF']['sha256'],'SOURCE_PDF_DRIFT')
        RUN.bind_authorized_saved_copy(target['port'],target['path'],target['name'],target['savedSha256'],m['authorization'])
        save_grant=[False]
        last_native_dump=[None]
        def measured_transport(command,params):
            reply=APA.native_transport(command,params)
            if command=='GetModelDumpV1':
                last_native_dump[0]=reply
            if command=='SaveProject':
                require(save_grant[0] and params=={} and reply=={'success':True},'SAVE_NOT_GRANTED_OR_NATIVE_FAILURE')
                after_sha=sha(working)
                require(after_sha!=target['savedSha256'],'SAVE_DID_NOT_CHANGE_WORKING_BYTES')
                require(sha(protected['path'])==protected['sha256'],'PROTECTED_SOURCE_CHANGED_DURING_SAVE')
                # Rebind the same authorized path to the actual saved bytes so
                # the existing writer's post-save identity guard can run.
                RUN.bind_authorized_saved_copy(target['port'],target['path'],target['name'],after_sha,m['authorization']+':SAVE_PASS_HASH_TRANSITION')
                report['saveHashTransition']=dict(before=target['savedSha256'],after=after_sha)
            return reply
        api=APA.EvidenceAPI(measured_transport,out/'raw',execute=args.apply)
        identity=RUN.guarded_project_for_read(api)
        product=api('API.GetProductInfo',{})
        require(product['version']==target['major'] and product['buildNumber']==target['build'],'WRONG_NATIVE_PRODUCT')
        known=set(g.lower() for g in m['knownGuids'])
        require(len(known)==264 and set(APA.inventory_guids(api))==known,'EXACT_264_KNOWN_GUIDS_REQUIRED')
        material=next((r for r in api('GetAttributesByType',{'attributeType':'BuildingMaterial'})['attributes'] if r['attributeId']['guid'].lower()==m['material']['guid']),None)
        require(material is not None and material['name']==m['material']['name'],'SOURCE_TIMBER_MATERIAL_NOT_FOUND')
        schema=Path(APA.__file__).resolve().parents[1]/'schemas/tapir-live-1.5.10/tapir-scene-live.json'
        router=APA.native_command_router(schema,include_functional_modules=False)
        for cmd,kind,impact in [('CreateColumns','CREATE','MODEL'),('SaveProject','TRANSACTION','PROJECT')]:
            router.review_policy(cmd,kind,impact,dict(source='Reviewed source-qualified timber member batch and save after native PASS',sha256=router.contract_hash(cmd)))
        ledger=Path(args.ledger).resolve()
        require(ledger.is_file(),'EXISTING_SCENEWRITER_LEDGER_REQUIRED')
        with sqlite3.connect('file:'+ledger.as_posix()+'?mode=ro',uri=True) as db:
            for sid in [m['sceneId'],m['saveSceneId']]:
                require(db.execute('SELECT 1 FROM scenes WHERE scene_id=?',(sid,)).fetchone() is None,'SCENE_RESERVED_NEVER_REPLAY:'+sid)
            require(all(r[0]=='PASS' for r in db.execute('SELECT state FROM scenes')),'EXISTING_LEDGER_HAS_UNRECONCILED_SCENE')
        before_rows=details(api,sorted(known))
        for item in m['items']:
            require(item['buildingMaterialId']['guid']==m['material']['guid'],'STUD_MATERIAL_DRIFT')
            require(item['width']==.1 and item['depth']==.05 and item['height']==2.9 and item['coordinates']['z']==0 and item['floorIndex']==0 and item['circleBased'] is False and item['isWidthAndHeightLinked'] is False,'STUD_SOURCE_DIMENSION_DRIFT')
            for row in before_rows.values():
                v=row.get('details',{});o=v.get('origin',{})
                if row.get('type')=='Column' and same(o.get('x'),item['coordinates']['x']) and same(o.get('y'),item['coordinates']['y']):
                    require(not (v.get('zCoordinate',-100)<2.9-1e-5 and v.get('zCoordinate',-100)+v.get('height',0)>1e-5),'DUPLICATE_OR_OVERLAPPING_NATIVE_STUD')
        affected=set(m['affectedGuids']);retained=sorted(known-affected)
        native_before=D.capture_full_model(api,sorted(known))
        signatures=C.retained_geometry_signatures(native_before,retained)
        require(set(signatures)==set(retained),'RETAINED_NATIVE_SIGNATURES_INCOMPLETE')
        write(out/'native-before.json',native_before)
        write(out/'retained-signatures-before.json',signatures)
        preview=APA.prepare_native_task(router,dict(schemaVersion='apa-native-task/1',request='Create thirteen PDF-qualified 100x50x2900 timber studs of partition frames 1.12 and 1.13',graph=dict(operations=[dict(id='create-source-stud-batch',command=m['command'],params=dict(columnsData=m['items']))])))
        write(out/'apa-plan.json',preview)
        report.update(status='SOURCE_BASELINE_AND_EXISTING_PIPELINE_PREFLIGHT_PASS',identity=identity,product=product,knownGUIDCount=264,sourceInterpretation=m['interpretation'],plannedPhysicalElements=13,material=material,prewriteSavedSha256=sha(working))
        write(report_path,report)
        if not args.apply:
            print(report['status'],flush=True);return 0
        require(not (out/'ATTEMPTED.lock').exists(),'RUN_ALREADY_ATTEMPTED')
        (out/'ATTEMPTED.lock').write_text(utc(),encoding='ascii')
        writer=RUN.SceneWriter(api,ledger,schema_path=schema,allow_3d_view_for_write=True)
        created=[];expected_after=set();post_signatures={}
        def before(_):
            require(set(APA.inventory_guids(api))==known,'INVENTORY_DRIFT_BEFORE_NATIVE_CREATE')
            require(sha(protected['path'])==protected['sha256'],'PROTECTED_SOURCE_DRIFT')
            require(sha(m['sourcePDF']['path'])==m['sourcePDF']['sha256'],'SOURCE_PDF_DRIFT')
            return dict(status='SOURCE_AND_264_NATIVE_GUIDS_PASS',sourceManifestSha256=sha(manifest_path))
        def after(reply,prior):
            created.extend(r['elementId']['guid'].lower() for r in reply['elements'])
            require(not known.intersection(created),'NATIVE_GUID_ALREADY_EXISTED')
            # One Details call covers every created physical object, its
            # affected wall and all three previously accepted windows.
            checked=details(api,created+sorted(affected)+m['existingWindows'])
            for guid,item in zip(created,m['items']):
                row=checked[guid];v=row.get('details',{});o=v.get('origin',{})
                require(row.get('type')=='Column' and row.get('floorIndex')==0,'STUD_NATIVE_TYPE_OR_STORY_MISMATCH')
                for key,val in [('width',.1),('depth',.05),('height',2.9),('zCoordinate',0),('axisRotationAngle',0)]:
                    require(same(v.get(key),val),'STUD_NATIVE_FIELD_MISMATCH:'+key)
                require(all(same(o.get(k),item['coordinates'][k]) for k in ('x','y')),'STUD_NATIVE_POSITION_MISMATCH')
                require(v.get('coreAnchor')=='Center' and v.get('circleBased') is False and v.get('isSlanted') is False and v.get('isWidthAndHeightLinked') is False,'STUD_NATIVE_SECTION_OR_ORIENTATION_MISMATCH')
                require(v.get('buildingMaterialId',{}).get('guid','').lower()==m['material']['guid'],'STUD_NATIVE_MATERIAL_MISMATCH')
            for guid in sorted(affected)+m['existingWindows']:
                require(checked[guid]==before_rows[guid],'EXISTING_WALL_OR_WINDOW_SETTINGS_CHANGED:'+guid)
            ownership=APA.assembly_subelements(api,{str(i):dict(guid=g,kind='Column') for i,g in enumerate(created)},'Column')
            children={g for values in ownership.values() for g in values}
            require(len(children)==13 and not children.intersection(known|set(created)),'UNEXPECTED_NATIVE_COLUMN_SEGMENTS')
            expected_after.update(known|set(created)|children)
            actual=set(APA.inventory_guids(api))
            require(actual==expected_after,'NATIVE_INVENTORY_DELTA_NOT_ROOTS_PLUS_SEGMENTS')
            write(out/'affected-native-details.json',checked)
            write(out/'column-segment-ownership.json',ownership)
            return dict(status='THIRTEEN_SOURCE_TIMBER_STUDS_NATIVE_READBACK_PASS',createdGuids=created,automaticSegmentGuids=sorted(children),known264Retained=True,finalGUIDCount=len(actual),singleBatchedDetailsVerification=True)
        outcome=router.execute_batch(writer,m['sceneId'],m['command'],m['items'],sorted(affected),signatures,target['savedSha256'],m['authorization'],'MODEL',after,verify_before=before)
        report.update(batchOutcome=outcome,nativeCreateCalls=api.calls[m['command']],createdPhysicalGuids=created,status='NATIVE_BATCH_PASS_UNSAVED' if outcome['status']=='PASS' else 'PARTIAL_OR_UNKNOWN_OUTCOME_NEVER_REPLAY')
        write(report_path,report)
        require(outcome['status']=='PASS','BATCH_NOT_PASS_NO_SAVE_NO_RETRY')
        require(api.calls[m['command']]==1 and len(created)==13,'ONE_NATIVE_CALL_NOT_CONFIRMED')
        # The router just performed the post-batch native BREP read once.
        # Reuse that same raw response for new bodies instead of re-reading.
        require(last_native_dump[0] is not None,'POST_BATCH_NATIVE_MODEL_MISSING')
        native_after=C.G.normalize_dump(last_native_dump[0])
        require(expected_after<={e['guid'].lower() for e in native_after['elements']},'POST_BATCH_NATIVE_MODEL_INCOMPLETE')
        post_signatures.update(C.retained_geometry_signatures(native_after,sorted(expected_after)))
        write(out/'native-after.json',native_after)
        # Verify actual resultant bodies independently of the scalar details.
        ownership=json.loads((out/'column-segment-ownership.json').read_text(encoding='utf8'))
        body_proof=verify_stud_bodies(native_after,created,m['items'],ownership)
        write(out/'resultant-native-body-proof.json',body_proof)
        report['resultantBodyVerification']=body_proof['status']
        write(report_path,report)
        save_grant[0]=True
        def before_save(_):
            require(report['batchOutcome']['status']=='PASS' and report['resultantBodyVerification'].endswith('PASS'),'CREATE_PASS_REQUIRED_BEFORE_SAVE')
            return dict(status='CREATE_AND_NATIVE_BODY_PASS_SAVE_ALLOWED')
        def after_save(reply,prior):
            require(reply=={'success':True} and set(APA.inventory_guids(api))==expected_after,'SAVE_RESPONSE_OR_INVENTORY_MISMATCH')
            require(sha(protected['path'])==protected['sha256'],'PROTECTED_SOURCE_CHANGED')
            return dict(status='WORKING_PLN_SAVE_NATIVE_INVENTORY_PASS',savedSha256=sha(working),finalGUIDCount=len(expected_after))
        saved=router.execute(writer,m['saveSceneId'],router.prepare('SaveProject',{}),[],post_signatures,target['savedSha256'],m['authorization'],'PROJECT',after_save,verify_before=before_save)
        report.update(saveOutcome=saved,saveCalls=api.calls['SaveProject'])
        require(saved['status']=='PASS','SAVE_OUTCOME_NOT_PASS_NEVER_REPEAT')
        require(sha(protected['path'])==protected['sha256'],'FINAL_PROTECTED_SOURCE_CHANGED')
        report.update(status='LIVE_BATCH_13_PHYSICAL_ONE_NATIVE_CREATE_AND_WORKING_PLN_SAVE_PASS',finishedAtUTC=utc(),finalGUIDCount=len(expected_after),physicalCreatedCount=len(created),originalSourceUnchanged=True,savedWorkingSha256=sha(working),savedReopened='NOT_RUN',engineering='NOT_VERIFIED',calls=dict(api.calls))
        print(report['status'],flush=True)
    except BaseException as exc:
        report.update(status='PARTIAL_OR_UNKNOWN_OUTCOME_NEVER_REPLAY' if api and api.write_attempts else 'PREFLIGHT_BLOCKED_ZERO_WRITES',error=type(exc).__name__+': '+str(exc),failedAtUTC=utc(),manualReconciliationRequired=bool(api and api.write_attempts))
        print(report['status'],report['error'],flush=True)
        raise
    finally:
        if api:
            report.update(nativeCreateCalls=api.calls[m['command']],saveCalls=api.calls['SaveProject'],writeAttempts=api.write_attempts,calls=dict(api.calls))
            records=[json.loads(line) for line in (out/'raw/raw.jsonl').read_text(encoding='utf8').splitlines()]
            report['nativeCreateTransportSeconds']=[r['elapsedSeconds'] for r in records if r['command']==m['command']]
        write(report_path,report)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',required=True)
    parser.add_argument('--ledger',required=True)
    parser.add_argument('--output',required=True)
    parser.add_argument('--apply',action='store_true')
    main(parser.parse_args())
