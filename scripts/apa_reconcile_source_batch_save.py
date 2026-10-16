"""Reconcile an already created batch and journal its first SaveProject.

This command cannot dispatch Create*: the only allowed mutation is one
SaveProject through the existing DynamicCommands/SceneWriter/SQLite path.
"""
from __future__ import annotations
import argparse,json,sqlite3
from pathlib import Path
import apa_source_qualified_native_batch as B
APA,RUN,C,D=B.APA,B.RUN,B.C,B.D

def reconcile(args):
    prior=Path(args.run).resolve()
    r=json.loads((prior/'report.json').read_text(encoding='utf8'))
    m=json.loads((prior/'source-manifest.json').read_text(encoding='utf8'))
    B.require(r['nativeCreateCalls']==1 and r['saveCalls']==0 and r['batchOutcome']['status']=='PASS','ONE_EXISTING_CREATE_PASS_AND_NO_SAVE_REQUIRED')
    B.require(r['error']=='ValueError: STUD_NATIVE_BREP_MISSING','ONLY_EXACT_COLUMN_ROOT_BODY_INSPECTION_FAILURE_CAN_RECONCILE')
    B.require(B.sha(prior/'source-manifest.json')==r['manifestSha256'],'ORIGINAL_SOURCE_MANIFEST_DRIFT')
    out=prior/'reconciliation';out.mkdir(exist_ok=False);(out/'raw').mkdir()
    ledger=Path(r['ledgerPath']);target=m['target'];protected=m['protectedSource']
    result=dict(schema='apa.reconciled-source-batch-save/1',status='READ_ONLY_RECONCILIATION_STARTED',startedAtUTC=B.utc(),createCalls=0,saveCalls=0,originalReportSha256=B.sha(prior/'report.json'),automaticRetry=False)
    api=None
    try:
        B.require(B.sha(target['path'])==target['savedSha256'],'WORKING_SAVED_BYTES_DRIFT')
        B.require(B.sha(protected['path'])==protected['sha256'],'PROTECTED_SOURCE_DRIFT')
        B.require(B.sha(m['sourcePDF']['path'])==m['sourcePDF']['sha256'],'SOURCE_PDF_DRIFT')
        with sqlite3.connect('file:'+ledger.as_posix()+'?mode=ro',uri=True) as db:
            stored=db.execute('SELECT state,result FROM scenes WHERE scene_id=?',(m['sceneId'],)).fetchone()
            B.require(stored is not None and stored[0]=='PASS','EXISTING_CREATE_SCENE_NOT_PASS')
            B.require(json.loads(stored[1])=={k:v for k,v in r['batchOutcome'].items() if k!='bulkMetrics'},'CREATE_LEDGER_AND_RECORDED_RESULT_DIFFER')
            B.require(db.execute('SELECT 1 FROM scenes WHERE scene_id=?',(m['saveSceneId'],)).fetchone() is None,'SAVE_ALREADY_RESERVED_NEVER_REPLAY')
        RUN.bind_authorized_saved_copy(target['port'],target['path'],target['name'],target['savedSha256'],m['authorization'])
        save_allowed=[False]
        def save_transport(command,params):
            B.require(not command.startswith(('Create','Modify','Delete','Set')),'RECONCILIATION_FORBIDS_ALL_MODEL_MUTATIONS')
            reply=APA.native_transport(command,params)
            if command=='SaveProject':
                B.require(save_allowed[0] and params=={} and reply=={'success':True},'SAVE_NOT_QUALIFIED_OR_NATIVE_FAILURE')
                new_hash=B.sha(target['path'])
                B.require(new_hash!=target['savedSha256'],'SAVE_BYTES_NOT_CHANGED')
                B.require(B.sha(protected['path'])==protected['sha256'],'PROTECTED_SOURCE_CHANGED')
                RUN.bind_authorized_saved_copy(target['port'],target['path'],target['name'],new_hash,m['authorization']+':RECONCILED_FIRST_SAVE')
                result['saveHashTransition']=dict(before=target['savedSha256'],after=new_hash)
            return reply
        api=APA.EvidenceAPI(save_transport,out/'raw',execute=False)
        identity=RUN.guarded_project_for_read(api)
        product=api('API.GetProductInfo',{})
        B.require(product['version']==29 and product['buildNumber']==5101,'WRONG_NATIVE_PRODUCT')
        created=r['createdPhysicalGuids']
        ownership=json.loads((prior/'column-segment-ownership.json').read_text(encoding='utf8'))
        expected=set(m['knownGuids'])|set(created)|{g for children in ownership.values() for g in children}
        B.require(len(expected)==290 and set(APA.inventory_guids(api))==expected,'RECONCILIATION_290_GUID_MISMATCH')
        current=D.capture_full_model(api,sorted(expected))
        recorded=json.loads((prior/'native-after.json').read_text(encoding='utf8'))
        signatures=C.retained_geometry_signatures(current,sorted(expected))
        B.require(signatures==C.retained_geometry_signatures(recorded,sorted(expected)),'MODEL_DRIFT_SINCE_SINGLE_CREATE')
        proof=B.verify_stud_bodies(current,created,m['items'],ownership)
        before=json.loads((prior/'native-before.json').read_text(encoding='utf8'))
        old=C.retained_geometry_signatures(before,m['knownGuids'])
        retained_now=C.retained_geometry_signatures(current,m['knownGuids'])
        changed=[g for g in old if old[g]!=retained_now[g]]
        B.require(set(changed)<=set(m['affectedGuids']),'UNAUTHORIZED_RETAINED_GEOMETRY_CHANGE')
        result.update(status='READ_ONLY_RECONCILIATION_PASS',identity=identity,product=product,finalGUIDCount=len(expected),all264KnownGuidsRetained=True,createdPhysicalCount=13,createdAutomaticSegmentCount=13,bodyProof=proof,changedExistingGeometryGuids=changed,retainedUnchangedSignatureCount=264-len(changed),existingNorthWallAndThreeWindowDetails='UNCHANGED_FROM_SINGLE_BATCH_NATIVE_DETAILS',explanation='Native Column roots have no body; owned ColumnSegment bodies match all thirteen exact source rectangles. No Create was repeated.')
        B.write(out/'native-reconciliation.json',current)
        B.write(out/'reconciliation-report.json',result)
        schema=Path(APA.__file__).resolve().parents[1]/'schemas/tapir-live-1.5.10/tapir-scene-live.json'
        router=APA.native_command_router(schema,include_functional_modules=False)
        router.review_policy('SaveProject','TRANSACTION','PROJECT',dict(source='User-authorized working PLN save after existing native create PASS and independent read-only reconciliation',sha256=router.contract_hash('SaveProject')))
        writer=RUN.SceneWriter(api,ledger,schema_path=schema,allow_3d_view_for_write=True)
        save_allowed[0]=True
        def before_save(_):
            B.require(result['status']=='READ_ONLY_RECONCILIATION_PASS','RECONCILIATION_PASS_REQUIRED')
            return dict(status='RECONCILED_THIRTEEN_NATIVE_STUDS_PASS',bodyProofHash=RUN.digest(proof),sourceManifestSha256=r['manifestSha256'])
        def after_save(reply,prior_state):
            B.require(reply=={'success':True} and set(APA.inventory_guids(api))==expected,'SAVE_RESPONSE_OR_INVENTORY_DRIFT')
            B.require(B.sha(protected['path'])==protected['sha256'],'PROTECTED_SOURCE_CHANGED')
            return dict(status='RECONCILED_WORKING_PLN_SAVE_PASS',savedSha256=B.sha(target['path']),finalGUIDCount=290)
        saved=router.execute(writer,m['saveSceneId'],router.prepare('SaveProject',{}),[],signatures,target['savedSha256'],m['authorization'],'PROJECT',after_save,verify_before=before_save)
        result['saveOutcome']=saved
        B.require(saved['status']=='PASS','SAVE_OUTCOME_NOT_PASS_DO_NOT_RETRY')
        result.update(status='LIVE_13_PHYSICAL_ONE_CREATE_RECONCILED_AND_WORKING_PLN_SAVED_PASS',finishedAtUTC=B.utc(),savedWorkingSha256=B.sha(target['path']),protectedOriginalUnchanged=B.sha(protected['path'])==protected['sha256'],savedReopened='NOT_RUN',engineering='NOT_VERIFIED')
        print(result['status'],flush=True)
    except BaseException as exc:
        result.update(status='RECONCILIATION_OR_SAVE_BLOCKED_DO_NOT_REPLAY',error=type(exc).__name__+': '+str(exc))
        raise
    finally:
        if api:result.update(createCalls=sum(v for k,v in api.calls.items() if k.startswith('Create')),saveCalls=api.calls['SaveProject'],calls=dict(api.calls))
        B.write(out/'reconciliation-report.json',result)
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--run',required=True)
    reconcile(p.parse_args())
