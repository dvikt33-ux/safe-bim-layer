"""Compose retained components. CLI is offline/read-only; no live write mode."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import statistics
import time
import urllib.request

import archicad_project_accelerator as A

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / 'schemas/accelerator/capability-registry.json'
READS = A.READS | {'API.IsAddOnCommandAvailable'}


def require_capabilities(registry, required):
    capabilities = {c['id']: c for c in registry['capabilities']}
    providers = {p['id']: p for p in registry['providers']}
    if len(capabilities) != len(registry['capabilities']) or len(providers) != len(registry['providers']):
        raise ValueError('DUPLICATE_REGISTRY_ID')
    routes = {}
    for name in required:
        cap = capabilities.get(name)
        if not cap or cap.get('available') is not True:
            raise ValueError('UNSUPPORTED_MANDATORY_CAPABILITY: ' + name)
        if cap['provider'] not in providers or any(d not in providers for d in cap['requires']):
            raise ValueError('MISSING_PROVIDER_DEPENDENCY: ' + name)
        routes[name] = cap
    return routes


class ReadAdapter:
    """Exact localhost port; no discovery, fallback, mutation, property reads or retry."""
    def __init__(self, provider='direct', core=None):
        if provider not in {'direct', 'alesdev88'}:
            raise ValueError('PROVIDER_NOT_CONFIGURED: ' + provider)
        self.provider = provider
        self.core = core
        self.calls = []
        if provider == 'alesdev88' and core is None:
            from archicad_mcp.connection import ArchicadConnection
            self.core = ArchicadConnection(A.RUN.PORT, timeout=15)

    def __call__(self, command, params):
        if command not in READS:
            raise ValueError('READ_ADAPTER_REFUSED: ' + command)
        self.calls.append(command)
        if self.provider == 'direct' and command != 'API.IsAddOnCommandAvailable':
            return A.native_transport(command, params)
        # Use installed connection's official gateway directly: .tapir() would
        # perform availability discovery before the exact identity check.
        payload_command = command if command.startswith('API.') else 'API.ExecuteAddOnCommand'
        payload_params = params if command.startswith('API.') else {
            'addOnCommandId': {'commandNamespace':'TapirCommand','commandName':command},
            'addOnCommandParameters':params}
        if self.provider == 'alesdev88':
            result = self.core.official(payload_command, payload_params)
        else:
            req = urllib.request.Request(f'http://127.0.0.1:{A.RUN.PORT}',
                json.dumps({'command':payload_command,'parameters':payload_params}).encode('utf-8'),
                {'Content-Type':'application/json'})
            with urllib.request.urlopen(req, timeout=15) as response:
                envelope = json.loads(response.read())
            if envelope.get('succeeded') is not True:
                raise ValueError('OFFICIAL_READ_FAILED: ' + str(envelope.get('error')))
            result = envelope['result']
        if not command.startswith('API.'):
            result = result.get('addOnCommandResponse')
        if not isinstance(result, dict) or 'error' in result:
            raise ValueError('INVALID_OR_FAILED_READ_RESPONSE: ' + command)
        return result


def artifact_index():
    """Reuse existing sources as references, never as unconditional applicable rules."""
    manifest = json.loads((ROOT/'schemas/accelerator/research-manifest.json').read_text(encoding='utf-8'))
    for row in manifest:
        path = (ROOT / row['path']).resolve()
        if not path.is_relative_to(ROOT.resolve()):
            raise ValueError('SOURCE_PATH_OUTSIDE_REPO')
        if hashlib.sha256(path.read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('RESEARCH_SOURCE_CHANGED: ' + row['path'])
    active = ROOT/'details/ACTIVE_RELEASE'
    detail_files = [active, ROOT/'details/README.md']
    if active.exists():
        version=active.read_text(encoding='utf-8').strip()
        if not re.fullmatch(r'v[0-9]+(?:\.[0-9]+)+',version):
            raise ValueError('INVALID_DETAIL_RELEASE_ID')
        release=ROOT/'details/releases'/version
        detail_files += [release/n for n in ('manifest.json','summary.json','audit.json','source_verify.json','SHA256SUMS.txt')]
    # Release identity is retained; avoid treating a catalog as a ready native recipe.
    return {'researchFiles':manifest, 'details':[
        {'path':p.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
         'value':p.read_text(encoding='utf-8') if p == active else None}
        for p in detail_files if p.exists()],
        'normativeApplicability':'NOT_EVALUATED', 'constructionDetailsAcceptance':'NOT_VERIFIED'}


def verify_saved_dump(path):
    """Validate native dump topology, using existing normalizer for raw evidence.

    This is file evidence. It cannot prove a current PLN or the new scene.
    """
    import importlib.util
    path = Path(path)
    source = json.loads(path.read_text(encoding='utf-8'))
    if 'succeeded' in source:
        if source.get('succeeded') is not True:
            raise ValueError('FAILED_NATIVE_DUMP_ENVELOPE')
        source = source['result']['addOnCommandResponse']
    if 'bodies' in source:
        spec=importlib.util.spec_from_file_location('retained_model_dump',ROOT/'archicad-addon/Examples/model_dump_v1.py')
        module=importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        source=module.normalize(source)
    if (source.get('schemaVersion') != 1 or source.get('units') != 'm'
            or source.get('coordinateSystem') != 'ABSOLUTE_PROJECT_XYZ'
            or source.get('vertexIndexBase') != 0):
        raise ValueError('UNSUPPORTED_DUMP_COORDINATES')
    materials = source['materials']
    material_ids = {m['id'] for m in materials}
    if len(material_ids) != len(materials):
        raise ValueError('DUPLICATE_MATERIAL_ID')
    elements = source['elements'] + source.get('unresolvedBodyOwners',[])
    guids=[e['guid'].lower() for e in elements]
    if len(set(guids)) != len(guids) or any(not A.RUN._GUID.fullmatch(g) for g in guids):
        raise ValueError('INVALID_DUMP_IDENTITY')
    counts=dict(elements=len(elements),bodies=0,vertices=0,faces=0,holeContours=0)
    bounds={}
    for element in elements:
        points=[]
        for body in element['bodies']:
            if body['parentGuid'].lower() != element['guid'].lower():
                raise ValueError('BODY_OWNER_MISMATCH')
            vertices=body['vertices']
            if any(not isinstance(v,list) or len(v)!=3 or any(type(x) not in (int,float) or not math.isfinite(x) for x in v) for v in vertices):
                raise ValueError('INVALID_NATIVE_VERTEX')
            points.extend(vertices)
            counts['bodies']+=1
            counts['vertices']+=len(vertices)
            for face in body['faces']:
                if face['materialId'] not in material_ids:
                    raise ValueError('UNRESOLVED_MATERIAL_POOL_ID')
                contours=face['contours']
                if not contours or any(len(c)<3 or any(type(i) is not int or i<0 or i>=len(vertices) for i in c) for c in contours):
                    raise ValueError('INVALID_NATIVE_FACE_CONTOUR')
                counts['faces']+=1
                counts['holeContours']+=len(contours)-1
        if points:
            bounds[element['guid'].lower()]={'min':[min(p[i] for p in points) for i in range(3)],
                                            'max':[max(p[i] for p in points) for i in range(3)]}
    if not counts['bodies'] or not counts['faces']:
        raise ValueError('NATIVE_GEOMETRY_UNAVAILABLE')
    return {'status':'SAVED_DUMP_STRUCTURE_VERIFIED','evidenceKind':'SAVED_FILE',
            'sampleOnly':source.get('sampleOnly',False),'geometryScope':source.get('geometryScope'),
            'sha256':hashlib.sha256(path.read_bytes()).hexdigest(), 'counts':counts,
            'bounds':bounds,'currentProjectVerified':False,'pavilionGeometryVerified':False,
            'materialSemantics':'materialId references material pool; not attributeIndex',
            'solidIntersectionVerified':False}


def run_integration(intent, output, schema=A.RUN.DEFAULT_SCENE_SCHEMA,
                    mode='offline', transport=None, provider='direct', required=None,
                    saved_dump=None, synthetic_execute=False):
    """Sequential integration. Write exercise accepts injected synthetic callable only."""
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    started=time.perf_counter()
    result={'status':'BLOCKED','mode':mode,'provider':provider,'stages':[],
            'modelWriteAttempts':0,'liveWritesAuthorized':False,'plnSaved':False}
    def stage(name, dependencies, action):
        completed={s['id'] for s in result['stages'] if s['status']=='DONE'}
        if not set(dependencies)<=completed:
            raise ValueError('UNSATISFIED_STAGE_DEPENDENCY: '+name)
        begin=time.perf_counter()
        try:
            value=action()
        except Exception:
            result['stages'].append({'id':name,'dependsOn':dependencies,'status':'BLOCKED',
                                    'elapsedSeconds':time.perf_counter()-begin})
            raise
        result['stages'].append({'id':name,'dependsOn':dependencies,'status':'DONE',
                                'elapsedSeconds':time.perf_counter()-begin})
        return value
    try:
        if mode not in {'offline','preflight'}:
            raise ValueError('INTEGRATION_CLI_IS_READ_ONLY')
        registry=json.loads(REGISTRY.read_text(encoding='utf-8'))
        required=list(dict.fromkeys(['pavilion-frame-v1','normative-sources','detail-library']+(required or [])))
        routes=stage('coverage',[],lambda:require_capabilities(registry,required))
        result['routes']=routes
        result['registryDigest']=A.RUN.digest(registry)
        sources=stage('references',['coverage'],artifact_index)
        A.write_json(output/'source-index.json',sources)
        if saved_dump:
            geometry=stage('saved-geometry',['references'],lambda:verify_saved_dump(saved_dump))
            A.write_json(output/'saved-geometry.json',geometry)
        adapter = transport or (ReadAdapter(provider) if mode=='preflight' else None)
        if synthetic_execute and (mode!='offline' or adapter is None or isinstance(adapter,ReadAdapter)
                or getattr(adapter,'evidence_kind',None)!='SYNTHETIC'):
            raise ValueError('SYNTHETIC_EXECUTION_REQUIRES_INJECTED_OFFLINE_TRANSPORT')
        scenario=stage('scene',['references'],lambda:A.run_project(intent,schema,output/'scene',None,
            'preflight' if mode=='preflight' or synthetic_execute else 'offline',adapter))
        result['scene']=scenario
        if isinstance(adapter,ReadAdapter):
            result['scene']['transportEvidenceKind']='LIVE_READ_ONLY'
        if scenario['status'] not in {'READY_FOR_EXPLICIT_TEST_RUN','ACCELERATOR_COMPILED_OFFLINE'}:
            result['stages'][-1]['status']='BLOCKED'
            raise ValueError('SCENE_BLOCKED: '+scenario.get('reason','unknown'))
        if synthetic_execute:
            state=output/'synthetic-ledger'
            state.mkdir()
            completed=stage('synthetic-assembly',['scene'],lambda:A.run_project(intent,schema,
                output/'assembly',state,'execute',adapter,'integration-pavilion-001',scenario['confirmPlanHash']))
            result['assembly']=completed
            if completed['status']!='COMPLETE_UNSAVED' or not completed.get('wholeAssemblyReadback'):
                result['stages'][-1]['status']='BLOCKED'
                raise ValueError('SYNTHETIC_ASSEMBLY_NOT_VERIFIED')
            result['syntheticWriteAttempts']=completed['modelWriteAttempts']
        if mode=='preflight':
            evidence=A.EvidenceAPI(adapter,output)
            evidence.allowed=evidence.allowed | {'API.IsAddOnCommandAvailable'}
            def registration():
                if A.RUN.guarded_project(evidence)!=scenario['binding']:
                    raise ValueError('PROJECT_CHANGED_BEFORE_REGISTRATION_PROBE')
                available=evidence('API.IsAddOnCommandAvailable',{
                    'addOnCommandId':{'commandNamespace':'TapirCommand','commandName':'GetModelDumpV1'}})
                A.write_json(output/'dump-registration.json',available)
                if type(available.get('available')) is not bool:
                    raise ValueError('INVALID_AVAILABILITY_RESPONSE')
                if A.RUN.guarded_project(evidence)!=scenario['binding']:
                    raise ValueError('PROJECT_CHANGED_AFTER_REGISTRATION_PROBE')
                before=json.loads((output/'scene/inventory-before.json').read_text())
                if A.inventory_guids(evidence)!=before:
                    raise ValueError('INVENTORY_CHANGED_DURING_REGISTRATION_PROBE')
                return available['available']
            result['nativeDumpRegistered']=stage('dump-registration',['scene'],registration)
            result['deepGeometryCoverage']='REGISTERED_NOT_EXECUTED' if result['nativeDumpRegistered'] else 'UNAVAILABLE_IN_CURRENT_ADDON'
            result['commandCounts']=dict(A.Counter(scenario['commandCounts'])+evidence.calls)
        result['status']='SYNTHETIC_WHOLE_SCENE_VERIFIED' if synthetic_execute else 'READ_ONLY_PREFLIGHT_READY' if mode=='preflight' else 'INTEGRATION_COMPILED_OFFLINE'
        result['evidenceKind']='LIVE_READ_ONLY' if mode=='preflight' and isinstance(adapter,ReadAdapter) else 'SYNTHETIC' if synthetic_execute or transport is not None else 'OFFLINE'
    except Exception as exc:
        result['reason']=type(exc).__name__+': '+str(exc)
    finally:
        result['elapsedSeconds']=time.perf_counter()-started
        A.write_json(output/'integration-result.json',result)
        A.write_json(output/'SHA256.json',{p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
            for p in output.rglob('*') if p.is_file() and p.name!='SHA256.json'})
    return result


def compare_preflights(intent, output, schema=A.RUN.DEFAULT_SCENE_SCHEMA, repeats=3):
    """No parallel host calls. Compare identical whole read workloads, not creation speed."""
    output=Path(output)
    output.mkdir(parents=True,exist_ok=False)
    rows=[]
    baseline=None
    for index in range(repeats):
        for provider in ('direct','alesdev88'):
            try:
                adapter=ReadAdapter(provider)
                result=run_integration(intent,output/f'{provider}-{index}',schema,'preflight',adapter,provider)
                # Injected ReadAdapter is real read-only; normalize evidence label here.
                result['evidenceKind']='LIVE_READ_ONLY'
                A.write_json(output/f'{provider}-{index}'/'measurement.json',result)
                if result['status']!='READ_ONLY_PREFLIGHT_READY':
                    rows.append({'provider':provider,'status':'BLOCKED','reason':result.get('reason')})
                    # Identity failure/timeouts are terminal; never continue on another route.
                    raise ValueError('READ_ONLY_COMPARISON_STOPPED')
                scene=result['scene']
                signature=A.RUN.digest({'binding':scene['binding'],
                    'inventory':json.loads((output/f'{provider}-{index}'/'scene/inventory-before.json').read_text()),
                    'plan':scene['confirmPlanHash']})
                if baseline is not None and signature!=baseline:
                    raise ValueError('COMPARISON_PROJECT_OR_INVENTORY_CHANGED')
                baseline=signature
                rows.append({'provider':provider,'status':'READY','elapsedSeconds':result['elapsedSeconds'],
                    'sceneSeconds':scene['elapsedSeconds'],'commandCounts':scene['commandCounts'],
                    'nativeDumpRegistered':result['nativeDumpRegistered'],'inventoryUnchanged':scene['inventoryUnchanged'],
                    'modelWriteAttempts':scene['modelWriteAttempts']})
            except Exception as exc:
                summary={'status':'BLOCKED','measurements':rows,'reason':str(exc),'liveWrites':0}
                A.write_json(output/'comparison.json',summary)
                return summary
    summaries={}
    for provider in ('direct','alesdev88'):
        times=[r['elapsedSeconds'] for r in rows if r['provider']==provider]
        summaries[provider]={'n':len(times),'medianSeconds':statistics.median(times),'minSeconds':min(times),'maxSeconds':max(times)}
    summary={'status':'READ_ONLY_COMPARISON_COMPLETE','measurements':rows,'summary':summaries,
        'scope':'read-only whole-scene preflight; alesdev88 connection API, not MCP session',
        'liveWrites':0,'creationSpeed':'NOT_MEASURED','longRunReliability':'NOT_MEASURED',
        'unmeasuredProviders':['lgradisar','huskybim','ifcopenshell'], 'automaticProviderReplacement':False}
    A.write_json(output/'comparison.json',summary)
    return summary


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--intent',type=Path,default=ROOT/'examples/accelerator/pavilion.intent.json')
    p.add_argument('--schema',type=Path,default=A.RUN.DEFAULT_SCENE_SCHEMA)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--provider',choices=['direct','alesdev88'],default='direct')
    g=p.add_mutually_exclusive_group()
    g.add_argument('--preflight',action='store_true')
    g.add_argument('--compare-readonly',action='store_true')
    p.add_argument('--saved-dump',type=Path)
    p.add_argument('--require',action='append')
    args=p.parse_args()
    intent=json.loads(args.intent.read_text(encoding='utf-8-sig'))
    result=compare_preflights(intent,args.output,args.schema) if args.compare_readonly else run_integration(
        intent,args.output,args.schema,'preflight' if args.preflight else 'offline',provider=args.provider,
        required=args.require,saved_dump=args.saved_dump)
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 2 if result['status']=='BLOCKED' else 0


if __name__=='__main__':
    raise SystemExit(main())
