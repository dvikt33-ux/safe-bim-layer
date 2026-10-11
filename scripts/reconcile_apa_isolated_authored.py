"""One-shot reconciliation of the exact isolated authored S02 live checkpoint.

Reuses SceneWriter for the four missing walls; never replays the six creates.
Default is read-only proof. ModifySlabs and continuation require its exact hash.
"""
from contextlib import closing
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

import archicad_project_accelerator as A
RUN=A.RUN
ORIGIN='isolated-authored-20261011-1928'
SUFFIX='isolated-authored-20261011-reconciled'
FAILED='native-slab-level-2'
FAILED_GUID='B11481A3-AE24-4B64-8C32-9A5BDADF9562'
TABLE='isolated_authored_reconciliations'


def journal_rows(db):
    return db.execute('SELECT step_id,state,guid,output FROM steps WHERE scene_id=? ORDER BY rowid',(ORIGIN,)).fetchall()


def verify_step(api,step,guid,plan):
    floor=next(iter(step['params'].values()))[0]['floorIndex']
    kind=RUN.verify_readback(step['command'],step['params'],RUN.requested_details(api,guid),
        expected_floor=floor,expected_story_level=RUN.story_level_for_floor(plan['storyBindings'],floor),
        expected_slab_material_guid=plan['slabBasicMaterialGuid'] if step['command']=='CreateSlabs' else None,
        slab_level_is_absolute=True)
    return {'guid':guid,'kind':kind,'floorIndex':floor}


def proof(api,evidence,journal):
    hashes=json.loads((evidence/'SHA256.json').read_text(encoding='utf8'))
    for name,expected in hashes.items():
        if Path(name).name!=name or hashlib.sha256((evidence/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('SOURCE_EVIDENCE_BYTES_CHANGED')
    old=json.loads((evidence/'preflight.json').read_text(encoding='utf8'))
    original=json.loads((evidence/'result.json').read_text(encoding='utf8'))
    before=json.loads((evidence/'inventory-before.json').read_text(encoding='utf8'))
    intent=json.loads((evidence/'plan.json').read_text(encoding='utf8'))['intent']
    if original['scene']['sceneId']!=ORIGIN or original['scene']['failedStep']!=FAILED:
        raise ValueError('NOT_THE_EXACT_AUTHORED_CHECKPOINT')
    binding=RUN.guarded_project(api,old['storyBindings'][0])
    if binding!=old['binding'] or binding['path']!=RUN.APPROVED_ISOLATED_WRITER_PATH:
        raise ValueError('CHECKPOINT_TARGET_CHANGED')
    with closing(sqlite3.connect(journal.resolve().as_uri()+'?mode=ro',uri=True)) as db:
        scene=db.execute('SELECT plan_hash,state FROM scenes WHERE scene_id=?',(ORIGIN,)).fetchone()
        rows=journal_rows(db)
        reserved=db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?",(TABLE,)).fetchone()
        if reserved and db.execute(f'SELECT 1 FROM {TABLE} WHERE origin=?',(ORIGIN,)).fetchone():
            raise ValueError('RECONCILIATION_RESERVED_NEVER_RETRY')
    if scene!=(old['sourcePlanHash'],'PARTIAL_OR_UNKNOWN_OUTCOME'):
        raise ValueError('ORIGINAL_SCENE_STATE_DRIFT')
    if (len(rows)!=6 or [r[0] for r in rows]!=old['executionOrder'][:6]
            or [r[1] for r in rows]!=['PASS']*5+['CREATED_UNVERIFIED']
            or rows[-1][0]!=FAILED or rows[-1][2]!=FAILED_GUID):
        raise ValueError('EXACT_SIX_CREATED_GUIDS_NOT_ESTABLISHED')
    native=A.inventory_guids(api)
    if native!=sorted(before+[r[2].lower() for r in rows]) or len(before)!=20:
        raise ValueError('NATIVE_INVENTORY_NOT_EXACT_ORIGINAL20_PLUS6')
    compiled=A.compile_authored_intent(intent,RUN.DEFAULT_SCENE_SCHEMA,api)
    expected=copy.deepcopy(old['graph'])
    next(s for s in expected['operations'] if s['id']==FAILED)['params']['slabsData'][0]['level']=3.
    if compiled['graph']!=expected or compiled['executionOrder']!=old['executionOrder']:
        raise ValueError('CORRECTED_PLAN_DIFF_NOT_ONLY_UPPER_SLAB_Z')
    known={r[2].lower() for r in rows}
    def unowned_scan(cmd,params):
        result=api(cmd,params)
        if cmd=='GetAllElements':
            if sorted(r['elementId']['guid'].lower() for r in result['elements'])!=native:
                raise ValueError('INVENTORY_CHANGED_DURING_RECOVERY_PROOF')
            return {'elements':[r for r in result['elements'] if r['elementId']['guid'].lower() not in known]}
        return result
    writer=RUN.SceneWriter(unowned_scan,journal,preview_factory=A.AUTHORED_NATIVE.make_read_only_scene_writer_preview_factory(compiled['authoredCandidate']))
    plan=writer.preflight(40,40)
    operations={s['id']:s for s in plan['graph']['operations']}
    for sid,state,guid,_ in rows[:5]:verify_step(api,operations[sid],guid,plan)
    target=RUN.requested_details(api,FAILED_GUID)
    details=target.get('details',{})
    if (target.get('type')!='Slab' or target.get('floorIndex')!=1
            or details.get('structureType')!='Composite'
            or not RUN.close(details.get('thickness'),.3)
            or not RUN.close(details.get('level'),-3.)
            or not RUN.close(details.get('zCoordinate'),0.)
            or not RUN.compare_polygon(operations[FAILED]['params']['slabsData'][0]['polygonCoordinates'],details.get('polygonOutline'))):
        raise ValueError('CREATED_UPPER_SLAB_NOT_EXACT_OBSERVED_MISMATCH')
    modify={'slabsWithDetails':[{'elementId':{'guid':FAILED_GUID},'structureType':'Basic',
        'zCoordinate':3.,'thickness':.2,'buildingMaterialId':{'guid':plan['slabBasicMaterialGuid']}}]}
    record={'origin':ORIGIN,'suffix':SUFFIX,'oldPlanHash':old['sourcePlanHash'],
        'newPlanHash':plan['sourcePlanHash'],'binding':binding,'originalRows':rows,
        'inventory':native,'modify':modify,'guid':FAILED_GUID,
        'userAuthorization':'2026-10-11 current chat: запись в pln разрешаю любую, продолжай'}
    if A.inventory_guids(api)!=native or RUN.guarded_project(api,old['storyBindings'][0])!=binding:
        raise ValueError('CHECKPOINT_PREWRITE_DRIFT')
    return {'status':'READY_FOR_EXACT_RECONCILIATION','confirmPlanHash':RUN.digest(record),
        'intent':record,'preflight':plan,'modelWriteAttempts':0}


def execute(api,ticket,journal,token):
    if token!=ticket['confirmPlanHash']:raise ValueError('RECOVERY_TOKEN_MISMATCH')
    record=ticket['intent'];plan=ticket['preflight']
    with closing(sqlite3.connect(journal)) as db:
        db.execute('PRAGMA synchronous=FULL')
        db.execute(f'CREATE TABLE IF NOT EXISTS {TABLE}(origin TEXT PRIMARY KEY,token TEXT,state TEXT,intent TEXT,result TEXT)')
        db.commit();db.execute('BEGIN IMMEDIATE')
        if journal_rows(db)!=[tuple(r) for r in record['originalRows']]:raise ValueError('OLD_LEDGER_CHANGED_BEFORE_RECOVERY')
        if db.execute(f'SELECT 1 FROM {TABLE} WHERE origin=?',(ORIGIN,)).fetchone():raise ValueError('RECOVERY_ALREADY_RESERVED')
        db.execute(f'INSERT INTO {TABLE} VALUES(?,?,?,?,?)',(ORIGIN,token,'ATTEMPTED',RUN.canonical(record),'{}'));db.commit()
        try:
            if RUN.guarded_project(api,plan['storyBindings'][0])!=record['binding'] or A.inventory_guids(api)!=record['inventory']:
                raise ValueError('OPERATION_BOUNDARY_DRIFT')
            raw=api('ModifySlabs',record['modify'])
            if raw.get('executionResults')!=[{'success':True}]:raise ValueError('MODIFY_NOT_CONFIRMED')
            ops={s['id']:s for s in plan['graph']['operations']}
            prefix={sid:verify_step(api,ops[sid],guid,plan) for sid,_,guid,_ in record['originalRows']}
            if A.inventory_guids(api)!=record['inventory']:raise ValueError('GUIDS_CHANGED_DURING_MODIFY')
            db.execute(f'UPDATE {TABLE} SET state=? WHERE origin=?',('READBACK_PASS',ORIGIN));db.commit()
        except Exception as exc:
            result={'status':'PARTIAL_OR_UNKNOWN_OUTCOME','reason':str(exc),'automaticRetry':False,'guid':FAILED_GUID}
            db.execute(f'UPDATE {TABLE} SET state=?,result=? WHERE origin=?',(result['status'],RUN.canonical(result),ORIGIN));db.commit();return result
    def final_check(preflight,created):
        for sid,value in created.items():
            if sid!='__plan__':verify_step(api,ops[sid],value['guid'],preflight)
        baseline=set(record['inventory'])-{r[2].lower() for r in record['originalRows']}
        expected=sorted(baseline|{v['guid'].lower() for k,v in created.items() if k!='__plan__'})
        if A.inventory_guids(api)!=expected:raise ValueError('FINAL_WHOLE_MODEL_GUID_DIFF')
    writer=RUN.SceneWriter(api,journal);writer.required_story=plan['storyBindings'][0]
    result=writer._execute_verified_plan(plan,SUFFIX,plan['sourcePlanHash'],seeded_created=prefix,
        approval_source=record['userAuthorization'],on_before_complete=final_check)
    with closing(sqlite3.connect(journal)) as db:
        if journal_rows(db)!=[tuple(r) for r in record['originalRows']]:raise ValueError('HISTORICAL_LEDGER_CHANGED')
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--journal',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--execute',action='store_true');p.add_argument('--confirm-plan-hash');args=p.parse_args()
    args.output.mkdir(parents=True,exist_ok=False);RUN.bind_isolated_writer_pln(19724)
    api=A.EvidenceAPI(A.native_transport,args.output,execute=args.execute)
    try:
        ticket=proof(api,args.evidence,args.journal);A.write_json(args.output/'preflight.json',ticket)
        result=execute(api,ticket,args.journal,args.confirm_plan_hash) if args.execute else ticket
    except Exception as exc:result={'status':'PARTIAL_OR_UNKNOWN_OUTCOME' if api.write_attempts else 'BLOCKED','reason':str(exc),'automaticRetry':False}
    result['modelWriteAttempts']=api.write_attempts;result['commandCounts']=dict(api.calls)
    A.write_json(args.output/'result.json',result)
    A.write_json(args.output/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in args.output.iterdir() if f.is_file()})
    print(json.dumps({k:v for k,v in result.items() if k not in ('intent','preflight')},ensure_ascii=True,indent=2))
    return 0 if result['status'] in ('READY_FOR_EXACT_RECONCILIATION','COMPLETE_UNSAVED') else 2


if __name__=='__main__':sys.exit(main())
