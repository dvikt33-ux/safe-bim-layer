"""Safe BIM Layer v0.1: deterministic high-level BIM operations over Tapir.

This module deliberately keeps Qwen out of low-level Tapir details.  Callers
provide semantic arguments; the module constructs and validates Tapir payloads,
executes one write at a time, reads elements back, and stops on any mismatch.
"""
from __future__ import annotations
import copy, json, math, urllib.request
from pathlib import Path
from typing import Any

try:
    import jsonschema
except Exception:
    jsonschema = None


class SafeBIMError(RuntimeError):
    pass


class TapirClient:
    def __init__(self, base_url='http://127.0.0.1:19723', schema_path=None):
        self.base_url = base_url
        self.schema = json.load(open(schema_path, encoding='utf-8')) if schema_path else None

    def call(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
        body = {'command':'API.ExecuteAddOnCommand','parameters':{
            'addOnCommandId': {'commandNamespace':'TapirCommand','commandName':command},
            'addOnCommandParameters': params}}
        req = urllib.request.Request(self.base_url, data=json.dumps(body).encode(), headers={'Content-Type':'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())

    def validate_payload(self, command: str, params: dict[str, Any]) -> None:
        if not self.schema:
            raise SafeBIMError('Tapir schema is not loaded')
        spec = self.schema.get('commands', {}).get(command)
        if not spec:
            raise SafeBIMError(f'No schema for {command}')
        self._validate_node(spec.get('parameters') or {'type':'object'}, params, f'{command}.parameters')

    def schema_ref(self, value):
        # Tapir schema stores command parameters inline; refs are resolved from
        # the root document by RefResolver.  Returning an inline dict is enough.
        return value or {'type':'object'}

    def _minimal_validate(self, command, params):
        required={'CreateWalls':['wallsData'],'CreateSlabs':['slabsData'],'CreateWindows':['windowsData'],'CreateDoors':['doorsData']}.get(command,[])
        missing=[x for x in required if x not in params]
        if missing: raise SafeBIMError(f'{command} missing required fields: {missing}')

    def _resolve_ref(self, ref):
        if not ref or not ref.startswith('#/'):
            return None
        key=ref[2:]
        return self.schema.get(key) or self.schema.get('common_schemas',{}).get(key)

    def _validate_node(self, node, value, path):
        if '$ref' in node:
            target=self._resolve_ref(node['$ref'])
            if target is None: raise SafeBIMError(f'Unresolved Tapir schema ref {node["$ref"]} at {path}')
            return self._validate_node(target,value,path)
        typ=node.get('type')
        if typ=='object':
            if not isinstance(value,dict): raise SafeBIMError(f'{path} must be object')
            allowed=set(node.get('properties',{})); missing=[k for k in node.get('required',[]) if k not in value]
            if missing: raise SafeBIMError(f'{path} missing required fields {missing}')
            if node.get('additionalProperties') is False:
                extra=[k for k in value if k not in allowed]
                if extra: raise SafeBIMError(f'{path} has unsupported fields {extra}')
            for k,v in value.items():
                if k in node.get('properties',{}): self._validate_node(node['properties'][k],v,f'{path}.{k}')
        elif typ=='array':
            if not isinstance(value,list): raise SafeBIMError(f'{path} must be array')
            if 'minItems' in node and len(value)<node['minItems']: raise SafeBIMError(f'{path} has too few items')
            if 'maxItems' in node and len(value)>node['maxItems']: raise SafeBIMError(f'{path} has too many items')
            if 'items' in node:
                for i,x in enumerate(value): self._validate_node(node['items'],x,f'{path}[{i}]')
        elif typ=='string':
            if not isinstance(value,str): raise SafeBIMError(f'{path} must be string')
            if 'enum' in node and value not in node['enum']: raise SafeBIMError(f'{path} unsupported enum {value!r}; allowed={node["enum"]}')
        elif typ=='integer':
            if not isinstance(value,int) or isinstance(value,bool): raise SafeBIMError(f'{path} must be integer')
        elif typ=='number':
            if not isinstance(value,(int,float)) or isinstance(value,bool): raise SafeBIMError(f'{path} must be number')
            if node.get('exclusiveMinimum') is not None and value<=node['exclusiveMinimum']: raise SafeBIMError(f'{path} must be > {node["exclusiveMinimum"]}')


def _num_equal(a, b, tol=1e-9):
    return isinstance(a,(int,float)) and isinstance(b,(int,float)) and abs(float(a)-float(b)) <= tol


def _diff(requested, actual, path=''):
    out=[]
    if isinstance(requested, dict) and isinstance(actual, dict):
        for k in sorted(set(requested)|set(actual)):
            p=f'{path}.{k}' if path else k
            if k not in requested: out.append({'path':p,'requested':'<missing>','actual':actual[k]})
            elif k not in actual: out.append({'path':p,'requested':requested[k],'actual':'<missing>'})
            else: out.extend(_diff(requested[k],actual[k],p))
    elif isinstance(requested, list) and isinstance(actual, list):
        for i in range(max(len(requested),len(actual))):
            p=f'{path}[{i}]'
            if i>=len(requested): out.append({'path':p,'requested':'<missing>','actual':actual[i]})
            elif i>=len(actual): out.append({'path':p,'requested':requested[i],'actual':'<missing>'})
            else: out.extend(_diff(requested[i],actual[i],p))
    elif isinstance(requested,(int,float)) and isinstance(actual,(int,float)):
        if not _num_equal(requested,actual): out.append({'path':path,'requested':requested,'actual':actual})
    elif requested != actual: out.append({'path':path,'requested':requested,'actual':actual})
    return out


class SafeBIMLayer:
    def __init__(self, client: TapirClient): self.tapir=client

    def _read_details(self, guids):
        r=self.tapir.call('GetDetailsOfElements', {'elements':[{'elementId':{'guid':g}} for g in guids]})
        ds=r.get('result',{}).get('addOnCommandResponse',{}).get('detailsOfElements',[])
        return r, ds

    def _write_and_read(self, command, payload, expected_type, requested_fields):
        self.tapir.validate_payload(command,payload)
        result=self.tapir.call(command,payload)
        ids=[x['elementId']['guid'] for x in result.get('result',{}).get('addOnCommandResponse',{}).get('elements',[]) if 'elementId' in x]
        read_response, details=self._read_details(ids)
        diffs=[]
        if len(ids) != len(requested_fields): diffs.append({'path':'count','requested':len(requested_fields),'actual':len(ids)})
        for i, req in enumerate(requested_fields):
            if i>=len(details): break
            d=details[i]
            if d.get('type') != expected_type: diffs.append({'path':f'[{i}].type','requested':expected_type,'actual':d.get('type')})
            actual=d.get('details',{})
            for k,v in req.items():
                if k not in actual: diffs.append({'path':f'[{i}].details.{k}','requested':v,'actual':'<missing>'})
                elif isinstance(v,dict): diffs.extend(_diff(v,actual[k],f'[{i}].details.{k}'))
                elif isinstance(v,(int,float)):
                    if not _num_equal(v,actual[k]): diffs.append({'path':f'[{i}].details.{k}','requested':v,'actual':actual[k]})
                elif v != actual[k]: diffs.append({'path':f'[{i}].details.{k}','requested':v,'actual':actual[k]})
        return {'status':'PASS' if not diffs and len(ids)==len(requested_fields) else 'FAIL','guids':ids,'tapirResponse':result,'readbackResponse':read_response,'readback':details,'diff':diffs}

    def create_wall_loop(self, contour, floor_index, height, thickness):
        pts=[{'x':float(p['x']),'y':float(p['y'])} for p in contour]
        if len(pts)<4: raise SafeBIMError('contour needs at least 3 vertices plus closure')
        if pts[0] != pts[-1]: pts.append(copy.deepcopy(pts[0]))
        if len(pts)<5 or pts[0] != pts[-1]: raise SafeBIMError('contour must be closed')
        walls=[]; requested=[]
        for a,b in zip(pts,pts[1:]):
            w={'begCoordinate':a,'endCoordinate':b,'floorIndex':int(floor_index),'height':float(height),'thickness':float(thickness),'referenceLineLocation':'Center','structureType':'Basic'}
            walls.append(w); requested.append({'begCoordinate':a,'endCoordinate':b,'height':float(height),'bottomOffset':0,'offset':0,'begThickness':float(thickness),'endThickness':float(thickness),'referenceLineLocation':'Center','structureType':'Basic'})
        out=self._write_and_read('CreateWalls',{'wallsData':walls},'Wall',requested)
        out['requestedPayload']={'wallsData':walls}; return out

    def create_basic_slab(self, contour, level, floor_index, thickness):
        pts=[{'x':float(p['x']),'y':float(p['y'])} for p in contour]
        if pts[0] == pts[-1]: pts=pts[:-1]
        payload={'slabsData':[{'level':float(level),'floorIndex':int(floor_index),'thickness':float(thickness),'polygonCoordinates':pts}]}
        self.tapir.validate_payload('CreateSlabs',payload)
        result=self.tapir.call('CreateSlabs',payload)
        ids=[x['elementId']['guid'] for x in result.get('result',{}).get('addOnCommandResponse',{}).get('elements',[]) if 'elementId' in x]
        rr,ds=self._read_details(ids); diffs=[]
        if len(ids)!=1: diffs.append({'path':'count','requested':1,'actual':len(ids)})
        if ds:
            actual=ds[0].get('details',{}); st=actual.get('structureType'); th=actual.get('thickness')
            if st!='Basic': diffs.append({'path':'details.structureType','requested':'Basic','actual':st})
            if not _num_equal(float(thickness),th): diffs.append({'path':'details.thickness','requested':float(thickness),'actual':th})
        out={'status':'PASS' if not diffs and len(ids)==1 else 'FAIL','guids':ids,'requestedPayload':payload,'tapirResponse':result,'readbackResponse':rr,'readback':ds,'diff':diffs}
        return out

    def _insert_opening(self, command, collection, expected_type, host_wall_guid, params):
        item={'ownerWallId':{'guid':host_wall_guid},'centerOffset':float(params['centerOffset']),'sillHeight':float(params.get('sillHeight',0.0)),'width':float(params['width']),'height':float(params['height'])}
        payload={collection:[item]}; self.tapir.validate_payload(command,payload)
        result=self.tapir.call(command,payload); ids=[x['elementId']['guid'] for x in result.get('result',{}).get('addOnCommandResponse',{}).get('elements',[]) if 'elementId' in x]
        rr,ds=self._read_details(ids); diffs=[]
        if len(ids)!=1: diffs.append({'path':'count','requested':1,'actual':len(ids)})
        if ds:
            actual=ds[0].get('details',{}); owner=actual.get('ownerElementId',{}).get('guid')
            if owner != host_wall_guid: diffs.append({'path':'details.ownerElementId.guid','requested':host_wall_guid,'actual':owner})
            for k in ('centerOffset','width','height','sillHeight'):
                if k in item and not _num_equal(item[k],actual.get(k)): diffs.append({'path':f'details.{k}','requested':item[k],'actual':actual.get(k)})
        return {'status':'PASS' if not diffs and len(ids)==1 else 'FAIL','guids':ids,'requestedPayload':payload,'tapirResponse':result,'readbackResponse':rr,'readback':ds,'diff':diffs}

    def insert_window(self, host_wall_guid, params): return self._insert_opening('CreateWindows','windowsData','Window',host_wall_guid,params)
    def insert_door(self, host_wall_guid, params): return self._insert_opening('CreateDoors','doorsData','Door',host_wall_guid,params)

    def create_room(self, contour, wall_height, wall_thickness, slab, door=None, windows=None):
        """Create a room; openings are optional and are skipped when omitted."""
        windows = windows or []
        out={'status':'PASS','walls':None,'slab':None,'door':None,'windows':[]}
        out['walls']=self.create_wall_loop(contour,0,wall_height,wall_thickness)
        if out['walls']['status']!='PASS': out['status']='FAIL'; return out
        out['slab']=self.create_basic_slab(contour,0,0,slab['thickness'])
        if out['slab']['status']!='PASS': out['status']='FAIL'; return out
        host=out['walls']['guids'][0]
        if door is not None:
            out['door']=self.insert_door(host,door)
            if out['door']['status']!='PASS': out['status']='FAIL'; return out
        for w in windows:
            r=self.insert_window(host,w); out['windows'].append(r)
            if r['status']!='PASS': out['status']='FAIL'; return out
        return out
