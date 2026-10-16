#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read-only, full native geometry audit of BDD working PLN, Archicad 29.

No OpenProject, SaveProject, Create*, Delete*, selection changes or model writes.
Uses the already saved 261-GUID build manifest as a strict identity gate.
--publish writes only one JSON report to private GitHub mailbox.
"""
from __future__ import annotations
import argparse,base64,collections,datetime,hashlib,json,math,pathlib,subprocess,sys,tempfile,urllib.request,uuid

PORT=19727
ORIGINAL=pathlib.Path('C:/LocalAI/SafeBIM_Global_Library_Test_Projects/BDD \u0434\u043e\u043c .pln')
WORKING=ORIGINAL.with_name('BDD \u0434\u043e\u043c - \u043f\u043e \u0447\u0435\u0440\u0442\u0435\u0436\u0430\u043c 2022.pln')
MANIFEST=pathlib.Path(tempfile.gettempdir())/'APA_BDD_House_Construction'/'house_native_manifest.json'
READ=frozenset({'GetProjectInfo','GetAllElements','GetDetailsOfElements','Get3DBoundingBoxes','GetStories'})
PHYSICAL={'Column':49,'Beam':66,'Wall':6,'Slab':3,'Roof':1}
PILES=[(0,9.38),(0,0),(5.34,0),(5.34,1.54),(6.959,1.315),
(14.255,1.09),(14.28,9.38),(1.587,9.38),(3.174,9.38),(4.761,9.38),
(6.348,9.38),(7.935,9.38),(9.522,9.38),(11.109,9.38),(12.696,9.38),
(14.28,7.722),(14.28,6.064),(14.28,4.406),(14.28,2.748),
(12.791,1.09),(11.327,1.09),(9.863,1.09),(8.399,1.09),
(4.005,0),(2.67,0),(1.335,0),(0,1.563),(0,3.126),(0,4.689),
(0,6.252),(0,7.815),(2.38,5.235),(4.76,5.235),(7.14,5.235),
(9.52,5.235),(11.9,5.235),(0,10.58),(3.08,10.58),(0,-3),
(6.58,-3),(6.58,-0.91),(8.7,-0.91),(8.7,-2),(14.28,-2),
(2.193,-3),(4.386,-3),(14.28,-0.455),(11.49,-2),(0,-1.5)]
MAIN=[(0,0),(5.34,0),(5.34,1.09),(14.28,1.09),(14.28,9.38),(0,9.38)]

def get(command,p=None):
    if command not in READ:raise RuntimeError('READ_ONLY_FENCE: '+command)
    req={'command':'API.ExecuteAddOnCommand','parameters':{
        'addOnCommandId':{'commandNamespace':'TapirCommand','commandName':command},
        'addOnCommandParameters':p or {}}}
    data=json.dumps(req,ensure_ascii=False).encode('utf-8')
    with urllib.request.urlopen(urllib.request.Request(
        'http://127.0.0.1:%d'%PORT,data,
        headers={'Content-Type':'application/json'},method='POST'),timeout=90) as resp:
        result=json.load(resp)
    if result.get('succeeded') is not True:
        raise RuntimeError(command+' transport failure')
    payload=result.get('result',{}).get('addOnCommandResponse')
    if not isinstance(payload,dict) or 'error' in payload:
        raise RuntimeError(command+' invalid reply')
    return payload

def target():
    from archicad import ACConnection
    c=ACConnection.connect(PORT)
    if c is None:raise RuntimeError('No Archicad at required port')
    v=c.commands.GetProductInfo()
    if int(v[0])!=29 or int(v[1])!=5101:
        raise RuntimeError('Wrong Archicad build %r'%(v,))
    info=get('GetProjectInfo')
    path=info.get('projectPath') or info.get('projectLocation') or ''
    if path.casefold()!=str(WORKING).casefold() or info.get('isUntitled'):
        raise RuntimeError('Wrong active PLN: %r'%path)
    return info

def guids():
    rows=get('GetAllElements').get('elements')
    if not isinstance(rows,list):raise RuntimeError('Missing element list')
    ids={}
    for x in rows:
        g=(x.get('elementId') or {}).get('guid') or x.get('guid')
        if not isinstance(g,str) or not g or g.lower() in ids:
            raise RuntimeError('Missing/duplicate GUID')
        ids[g.lower()]=g
    return ids

def bbox_valid(x):
    if not isinstance(x,dict):return False
    keys=('xMin','xMax','yMin','yMax','zMin','zMax')
    if not all(isinstance(x.get(k),(int,float)) and math.isfinite(x[k]) and abs(x[k])<1e6 for k in keys):
        return False
    return x['xMin']<=x['xMax'] and x['yMin']<=x['yMax'] and x['zMin']<=x['zMax']

def readback(ids):
    out=[];failures=[]
    for i in range(0,len(ids),20):
        chunk=ids[i:i+20]
        p={'elements':[{'elementId':{'guid':g}} for g in chunk]}
        try:
            d=get('GetDetailsOfElements',p).get('detailsOfElements',[])
            b=get('Get3DBoundingBoxes',p).get('boundingBoxes3D',[])
            if len(d)!=len(chunk) or len(b)!=len(chunk):raise ValueError('Batch array size')
        except Exception as exc:
            failures.append({'offset':i,'error':str(exc)[:180]})
            d=[];b=[]
            for guid in chunk:
                one={'elements':[{'elementId':{'guid':guid}}]}
                try:d.append(get('GetDetailsOfElements',one)['detailsOfElements'][0])
                except Exception:d.append(None)
                try:b.append(get('Get3DBoundingBoxes',one)['boundingBoxes3D'][0])
                except Exception:b.append(None)
        for guid,detail,box in zip(chunk,d,b):
            bb=box.get('boundingBox3D') if isinstance(box,dict) else None
            out.append({'guid':guid,
                        'type':detail.get('type') if isinstance(detail,dict) else None,
                        'id':detail.get('id') if isinstance(detail,dict) else None,
                        'story':detail.get('floorIndex') if isinstance(detail,dict) else None,
                        'details':detail.get('details') if isinstance(detail,dict) else None,
                        'boundingBox3D':bb if bbox_valid(bb) else None,
                        'bboxStatus':'VALID' if bbox_valid(bb) else 'UNAVAILABLE_OR_SENTINEL'})
    return out,failures

def close(a,b,eps=.012):
    return isinstance(a,(int,float)) and abs(a-b)<=eps

def evaluate(rows):
    issues=[];warnings=[]
    counts=dict(collections.Counter(r['type'] for r in rows))
    if counts!=PHYSICAL:issues.append('Native type inventory differs: '+str(counts))
    columns=[r for r in rows if r['type']=='Column']
    unmatched=columns[:]
    for i,(x,y) in enumerate(PILES):
        hits=[r for r in unmatched if isinstance(r['details'],dict)
              and isinstance(r['details'].get('origin'),dict)
              and close(r['details']['origin'].get('x'),x)
              and close(r['details']['origin'].get('y'),y)]
        if len(hits)!=1:issues.append('Pile %d at (%.3f,%.3f): found %d'%(i+1,x,y,len(hits)))
        else:unmatched.remove(hits[0])
    if unmatched:issues.append('Unmatched pile columns: '+str(len(unmatched)))
    for r in columns:
        d=r['details'] if isinstance(r['details'],dict) else {}
        for k,v in [('height',2.4),('width',.3),('depth',.3),('zCoordinate',-3.0)]:
            if not close(d.get(k),v):issues.append('Pile '+r['guid']+' invalid '+k)
        if d.get('circleBased') is not True:issues.append('Pile '+r['guid']+' noncircular')
        b=r['boundingBox3D']
        if b and (not close(b['zMin'],-3.0) or not close(b['zMax'],-.6)):
            issues.append('Pile '+r['guid']+' inconsistent 3D vertical limits')
    walls=[r for r in rows if r['type']=='Wall']
    for a,b in zip(MAIN,MAIN[1:]+MAIN[:1]):
        def pt(q,t):return isinstance(q,dict) and close(q.get('x'),t[0]) and close(q.get('y'),t[1])
        hits=[]
        for r in walls:
            d=r['details'] if isinstance(r['details'],dict) else {}
            s=d.get('begCoordinate');e=d.get('endCoordinate')
            if (pt(s,a) and pt(e,b)) or (pt(s,b) and pt(e,a)):hits.append(r)
        if len(hits)!=1:issues.append('Missing or duplicated original first-pass exterior wall run '+repr((a,b)))
    for r in rows:
        if not r['boundingBox3D']:warnings.append('No valid 3D bbox '+r['type']+' '+r['guid'])
    roof=[r for r in rows if r['type']=='Roof']
    if roof and roof[0]['boundingBox3D']:
        z=roof[0]['boundingBox3D']
        if not 5.7<=z['zMax']<=8.0:
            issues.append('Provisional roof unexpected upper Z '+str(z['zMax']))
    warnings.extend([
        'The native roof is provisional: roof valleys and gables not yet reconstructed.',
        'The 200-mm timber frame + external insulation is not modeled as a native multilayer assembly.',
        'No internal partition wall layout, native doors, or windows yet.',
        'Foundation vertical placement and individual joist end joints remain preliminary.',
        'KR-9 source axes are 14.28x9.38 m; inner chain is 14.18 m; outer envelope is 14.58x9.68 m.',
    ])
    return issues,warnings,counts

def report_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding='utf-8')

def publish(path):
    name='apa-bdd-geometry-audit-%s-%s.json'%(
        datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'),uuid.uuid4().hex[:8])
    dest='safe-bim-mailbox/gpt-live/results/'+name
    p={'branch':'main','message':'BDD house 125 element independent read-only geometry audit',
       'content':base64.b64encode(path.read_bytes()).decode('ascii')}
    tmp=path.with_suffix('.github-tmp.json')
    try:
        report_json(tmp,p)
        r=subprocess.run(['gh','api','--method','PUT',
                          'repos/dvikt33-ux/safe-bim-bridge/contents/'+dest,
                          '--input',str(tmp)],capture_output=True,text=True,timeout=150)
        if r.returncode:raise RuntimeError('GitHub publish: '+r.stderr[-500:])
    finally:tmp.unlink(missing_ok=True)
    return 'https://github.com/dvikt33-ux/safe-bim-bridge/blob/main/'+dest

def main():
    args=argparse.ArgumentParser(description=__doc__)
    args.add_argument('--publish',action='store_true')
    cfg=args.parse_args()
    project=target()
    if not MANIFEST.exists():raise RuntimeError('Expected build manifest not found')
    m=json.loads(MANIFEST.read_text(encoding='utf-8-sig'))
    if m.get('status')!='NATIVE_STRUCTURAL_CORE_SAVED__ROOF_AND_OPENINGS_PROVISIONAL' or m.get('inFlight'):
        raise RuntimeError('Build journal not complete or has in-flight writes')
    old={g.lower() for g in m.get('initialGUIDs',[])}
    primary={g.lower() for s in m.get('stages',[]) for g in s.get('primaryGuids',[])}
    child={g.lower() for s in m.get('stages',[]) for g in s.get('autoChildGuids',[])}
    if (len(old),len(primary),len(child))!=(21,125,115):
        raise RuntimeError('Build manifest counts changed')
    before=guids()
    if set(before)!=old|primary|child or len(before)!=261:
        raise RuntimeError('Actual model GUIDs diverge from saved journal')
    rows,read_errors=readback([before[g] for g in sorted(primary)])
    if before!=guids() or project.get('projectPath')!=target().get('projectPath'):
        raise RuntimeError('Project/geometry changed while capturing; discard')
    problems,warnings,types=evaluate(rows)
    source_unchanged=(ORIGINAL.exists() and hashlib.sha256(ORIGINAL.read_bytes()).hexdigest()==m.get('sourcePLNSHA256'))
    body={'schema':'apa.bdd.native-geometry-readback.v1',
          'timestampUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'targetPLN':str(WORKING),'sourcePLN':str(ORIGINAL),'sourcePLNUnchanged':source_unchanged,
          'source':'LIVE_ARCHICAD_29_TAPIR','writeToPLN':False,
          'initialGUIDs':21,'primaryGUIDs':len(primary),'automaticChildGUIDs':len(child),
          'totalGUIDs':len(before),'actualTypes':types,
          'nativeGeometryChecks':problems,'readErrors':read_errors,
          'warnings':warnings,'elements':rows,
          'status':'MISMATCH' if problems or read_errors else 'CORE_GEOMETRY_PASS__OVERALL_HOUSE_PARTIAL'}
    out=pathlib.Path(tempfile.gettempdir())/'APA_BDD_House_Construction'/'geometry_audit'/(
         'geometry-%s.json'%datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    report_json(out,body)
    print('NATIVE GEOMETRY AUDIT:',body['status'])
    print('PHYSICAL:',json.dumps(types,ensure_ascii=True))
    print('CHECK PROBLEMS:',len(problems),'WARNINGS:',len(warnings))
    print('FULL LOCAL:',out)
    if cfg.publish:print('PRIVATE GITHUB GEOMETRY AUDIT:',publish(out))
    return 0 if not problems and not read_errors else 3

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('AUDIT BLOCKED:',type(exc).__name__,str(exc),file=sys.stderr)
        sys.exit(2)
