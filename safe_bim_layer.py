"""Safe BIM Layer v0.1: deterministic high-level BIM operations over Tapir.

This module deliberately keeps Qwen out of low-level Tapir details.  Callers
provide semantic arguments; the module constructs and validates Tapir payloads,
executes one write at a time, reads elements back, and stops on any mismatch.
"""
from __future__ import annotations
import copy, json, math, urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import jsonschema
except Exception:
    jsonschema = None


class SafeBIMError(RuntimeError):
    pass


class ModalStateError(SafeBIMError):
    """Tapir reports that Archicad cannot accept commands while modal/busy."""

    retry_allowed = False


@dataclass(frozen=True)
class StoryRecord:
    story_index: int
    display_name: str | None
    elevation: float
    next_story_elevation: float | None
    height_to_next: float | None
    previous_index: int | None
    next_index: int | None
    project_zero_relative_z: float


@dataclass(frozen=True)
class VerticalContext:
    project_zero_z: float
    grade_z: float | None = None
    plinth_bottom_z: float | None = None
    plinth_top_z: float | None = None
    source: str | None = None
    justification: str | None = None

    def fingerprint(self) -> dict[str, Any]:
        return asdict(self)


def preflight_plinth_geometry(context: VerticalContext) -> dict[str, Any]:
    """Resolve plinth Z values and fail closed when the Tapir shape is ambiguous."""
    values = context.fingerprint()
    if context.plinth_bottom_z is None or context.plinth_top_z is None:
        raise SafeBIMError('plinth bottom/top Z are required')
    if context.plinth_bottom_z >= context.plinth_top_z:
        raise SafeBIMError('plinth bottom Z must be below top Z')
    if not math.isclose(context.plinth_top_z, context.project_zero_z, abs_tol=1e-6):
        raise SafeBIMError('plinth top Z must equal project zero for this context')
    return {'status': 'UNSUPPORTED_LIVE_GEOMETRY', 'verticalContext': values,
            'expectedZFingerprint': values, 'geometry': None,
            'reason': ('CreateWalls requires a story-relative floorIndex and the pinned '
                       'schema exposes no verified absolute bottom-Z/offset for a safe plinth write'),
            'writeAllowed': False}


class StoryResolver:
    """Resolve stories from factual Archicad elevations, never their names."""
    def __init__(self, tapir, project_zero_z: float | None = None):
        self.tapir = tapir
        self.project_zero_z = project_zero_z

    @staticmethod
    def _items(response):
        value = response.get('result', {}).get('addOnCommandResponse', {})
        for key in ('stories', 'storyData', 'storyItems'):
            if isinstance(value.get(key), list): return value[key]
        return value if isinstance(value, list) else []

    @staticmethod
    def _field(item, *names):
        for name in names:
            if name in item: return item[name]
        return None

    def resolve(self, project_zero_z: float | None = None) -> list[StoryRecord]:
        raw = self.tapir.call('GetStories', {})
        items = self._items(raw)
        rows = []
        for item in items:
            idx = self._field(item, 'storyIndex', 'index', 'floorIndex')
            elevation = self._field(item, 'elevation', 'level', 'elevationFromProjectZero', 'zCoordinate')
            if not isinstance(idx, int) or not isinstance(elevation, (int, float)):
                continue
            rows.append((int(idx), float(elevation), self._field(item, 'name', 'displayName', 'userName')))
        rows.sort(key=lambda x: x[0])
        if not rows:
            raise SafeBIMError('GetStories returned no stories with storyIndex and elevation')
        zero = self.project_zero_z if project_zero_z is None else float(project_zero_z)
        if zero is None: zero = rows[0][1]
        result = []
        for pos, (idx, z, name) in enumerate(rows):
            nxt = rows[pos + 1] if pos + 1 < len(rows) else None
            result.append(StoryRecord(idx, name, z, nxt[1] if nxt else None,
                                      nxt[1] - z if nxt else None,
                                      rows[pos - 1][0] if pos else None,
                                      nxt[0] if nxt else None, z - zero))
        return result

    def by_index(self, story_index: int, project_zero_z: float | None = None) -> StoryRecord:
        for story in self.resolve(project_zero_z):
            if story.story_index == int(story_index): return story
        raise SafeBIMError(f'Unknown storyIndex={story_index}')


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
            response = json.loads(r.read().decode())
        text = json.dumps(response, ensure_ascii=False).lower()
        if 'invalid program status' in text or 'modal dialog' in text or 'modal state' in text:
            raise ModalStateError(
                f'Archicad is modal/busy during {command}; manual Continue required')
        return response

    def change_floor_plan(self, story_index: int) -> dict[str, Any]:
        """Activate a FloorPlan story using the pinned Tapir schema."""
        payload = {'windowType': 'FloorPlan', 'storyIndex': int(story_index)}
        self.validate_payload('ChangeWindow', payload)
        return self.call('ChangeWindow', payload)

    def change_floor_plan_navigator_item(self, navigator_guid: str) -> dict[str, Any]:
        """Activate a story navigator item using the pinned Tapir schema."""
        payload = {'navigatorItemId': {'guid': str(navigator_guid)}}
        self.validate_payload('ChangeWindow', payload)
        return self.call('ChangeWindow', payload)

    def active_story(self) -> int:
        response = self.call('GetStories', {})
        value = response.get('result', {}).get('addOnCommandResponse', {}).get('actStory')
        if not isinstance(value, int):
            raise SafeBIMError(f'GetStories did not return integer actStory: {value!r}')
        return value

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
    def __init__(self, client: TapirClient, vertical_context: VerticalContext | None = None):
        self.tapir=client
        self.vertical_context = vertical_context
        self.story_resolver = StoryResolver(client, vertical_context.project_zero_z
                                            if vertical_context else None)

    def resolve_vertical_context(self, context: VerticalContext | None = None):
        if context is not None:
            self.vertical_context = context
            self.story_resolver.project_zero_z = context.project_zero_z
        stories = self.story_resolver.resolve()
        return {'stories': [asdict(s) for s in stories],
                'verticalContext': self.vertical_context.fingerprint() if self.vertical_context else None}

    def preflight_plinth(self, context: VerticalContext | None = None):
        context = context or self.vertical_context
        if context is None:
            raise SafeBIMError('VerticalContext is required for plinth preflight')
        self.vertical_context = context
        return preflight_plinth_geometry(context)

    @staticmethod
    def _response_items(response):
        return response.get('result', {}).get('addOnCommandResponse', {})

    def _story_navigator_guid(self, tree, story_index):
        if isinstance(tree, dict):
            item = tree.get('navigatorItem', tree)
            if item.get('type') == 'StoryItem' and item.get('prefix') == str(story_index):
                return item.get('navigatorItemId', {}).get('guid')
            for value in tree.values():
                found = self._story_navigator_guid(value, story_index)
                if found:
                    return found
        elif isinstance(tree, list):
            for value in tree:
                found = self._story_navigator_guid(value, story_index)
                if found:
                    return found
        return None

    def ensure_active_story(self, floor_index: int) -> dict[str, Any]:
        """Switch through schema-supported ChangeWindow and prove actStory."""
        target = int(floor_index)
        before = self.tapir.active_story()
        if before == target:
            return {'before': before, 'after': before, 'switched': False}
        tree = self.tapir.call('GetNavigatorItemTree', {'navigatorMapId': 'ProjectMap'})
        guid = self._story_navigator_guid(self._response_items(tree).get('navigatorItemTree'), target)
        if not guid:
            raise SafeBIMError(f'No Project Map StoryItem found for floorIndex={target}')
        change = self.tapir.change_floor_plan_navigator_item(guid)
        if not self._response_items(change).get('success', True):
            raise SafeBIMError(f'ChangeWindow failed for story {target}: {change!r}')
        after = self.tapir.active_story()
        if after != target:
            raise SafeBIMError(f'ChangeWindow read-back mismatch: requested {target}, actStory={after}')
        return {'before': before, 'after': after, 'switched': True, 'navigatorGuid': guid}

    def _read_details(self, guids):
        r=self.tapir.call('GetDetailsOfElements', {'elements':[{'elementId':{'guid':g}} for g in guids]})
        ds=r.get('result',{}).get('addOnCommandResponse',{}).get('detailsOfElements',[])
        return r, ds

    def _reconcile_type(self, expected_type):
        """Read-only post-timeout evidence; never dispatches a second write."""
        listed = self.tapir.call('GetElementsByType', {'elementType': expected_type})
        ids = [x['elementId']['guid'] for x in self._response_items(listed).get('elements', [])
               if 'elementId' in x]
        rr, details = self._read_details(ids) if ids else ({}, [])
        return {'listedResponse': listed, 'readbackResponse': rr,
                'readback': details, 'candidateGuids': ids}

    def _write_and_read(self, command, payload, expected_type, requested_fields, floor_index=None,
                        expected_vertical=None):
        story = self.ensure_active_story(floor_index) if floor_index is not None else None
        if expected_vertical is None and floor_index is not None:
            try: expected_vertical = asdict(self.story_resolver.by_index(floor_index))
            except SafeBIMError: expected_vertical = None
        self.tapir.validate_payload(command,payload)
        try:
            result=self.tapir.call(command,payload)
        except TimeoutError as exc:
            # A Tapir timeout is not a negative result: Archicad may still have
            # completed the modal-blocked write. Never retry before reconciliation.
            reconciliation = self._reconcile_type(expected_type)
            return {'status':'UNKNOWN_OUTCOME', 'error':repr(exc), 'command':command,
                    'story':story, 'requestedPayload':payload, 'expectedVertical': expected_vertical,
                    'reconciliationRequired':True, 'retryAllowed':False,
                    'reconciliation':reconciliation}
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
        return {'status':'PASS' if not diffs and len(ids)==len(requested_fields) else 'FAIL','guids':ids,'tapirResponse':result,'readbackResponse':read_response,'readback':details,'diff':diffs,'expectedVertical':expected_vertical}

    def create_wall_loop(self, contour, floor_index, height, thickness):
        pts=[{'x':float(p['x']),'y':float(p['y'])} for p in contour]
        if len(pts)<4: raise SafeBIMError('contour needs at least 3 vertices plus closure')
        if pts[0] != pts[-1]: pts.append(copy.deepcopy(pts[0]))
        if len(pts)<5 or pts[0] != pts[-1]: raise SafeBIMError('contour must be closed')
        walls=[]; requested=[]
        for a,b in zip(pts,pts[1:]):
            w={'begCoordinate':a,'endCoordinate':b,'floorIndex':int(floor_index),'height':float(height),'thickness':float(thickness),'referenceLineLocation':'Center','structureType':'Basic'}
            walls.append(w); requested.append({'begCoordinate':a,'endCoordinate':b,'height':float(height),'bottomOffset':0,'offset':0,'begThickness':float(thickness),'endThickness':float(thickness),'referenceLineLocation':'Center','structureType':'Basic'})
        story_record = self.story_resolver.by_index(floor_index) if self._can_resolve_story() else None
        expected_top = (story_record.elevation + float(height)) if story_record else None
        out=self._write_and_read('CreateWalls',{'wallsData':walls},'Wall',requested, floor_index,
                                 {'bottom_z': story_record.elevation if story_record else None,
                                  'top_z': expected_top, 'height': float(height),
                                  'story_index': int(floor_index)})
        out['requestedPayload']={'wallsData':walls}; return out

    def create_plinth_segment(self, start, end, grade_z, project_zero_z,
                              floor_index, thickness=0.25):
        """Create one verified wall segment spanning grade to project zero."""
        grade_z, project_zero_z = float(grade_z), float(project_zero_z)
        if grade_z >= project_zero_z:
            raise SafeBIMError('grade_z must be below project_zero_z')
        story = self.story_resolver.by_index(int(floor_index), project_zero_z)
        relative_z = grade_z - float(story.elevation)
        height = project_zero_z - grade_z
        fingerprint = {
            'story_elevation': float(story.elevation),
            'relative_offset': relative_z,
            'expected_bottom': grade_z,
            'expected_top': project_zero_z,
        }
        wall = {
            'begCoordinate': {'x': float(start['x']), 'y': float(start['y'])},
            'endCoordinate': {'x': float(end['x']), 'y': float(end['y'])},
            'floorIndex': int(floor_index), 'zCoordinate': relative_z,
            'height': height, 'thickness': float(thickness),
            'referenceLineLocation': 'Center', 'structureType': 'Basic',
        }
        self.tapir.validate_payload('CreateWalls', {'wallsData': [wall]})
        response = self.tapir.call('CreateWalls', {'wallsData': [wall]})
        ids = [x['elementId']['guid'] for x in self._response_items(response).get('elements', [])]
        if len(ids) != 1:
            raise SafeBIMError('create_plinth_segment returned an unexpected element count')
        read_response, details = self._read_details(ids)
        if len(details) != 1:
            raise SafeBIMError('create_plinth_segment read-back is incomplete')
        detail, actual = details[0], details[0].get('details', {})
        actual_z = float(actual.get('zCoordinate'))
        actual_height = float(actual.get('height'))
        actual_bottom, actual_top = actual_z, actual_z + actual_height
        checks = (detail.get('floorIndex') == int(floor_index) and
                  math.isclose(actual_z, relative_z, abs_tol=1e-6) and
                  math.isclose(actual_height, height, abs_tol=1e-6) and
                  actual.get('structureType') == 'Basic' and
                  math.isclose(actual_bottom, grade_z, abs_tol=1e-6) and
                  math.isclose(actual_top, project_zero_z, abs_tol=1e-6))
        if not checks:
            raise SafeBIMError('create_plinth_segment read-back fingerprint mismatch')
        return {'status': 'PASS', 'guids': ids, 'readback': details,
                'expectedZFingerprint': fingerprint,
                'actual_bottom': actual_bottom, 'actual_top': actual_top}

    def _can_resolve_story(self):
        return hasattr(self.tapir, 'call') and not (getattr(self.tapir, 'schema', None) == {'commands': {}})

    def create_basic_slab(self, contour, level, floor_index, thickness, reference_plane='TOP'):
        pts=[{'x':float(p['x']),'y':float(p['y'])} for p in contour]
        if pts[0] == pts[-1]: pts=pts[:-1]
        story_record = self.story_resolver.by_index(floor_index) if self._can_resolve_story() else None
        top_z = (story_record.elevation + float(level)) if story_record else None
        payload={'slabsData':[{'level':float(level),'floorIndex':int(floor_index),'thickness':float(thickness),'polygonCoordinates':pts}]}
        story = self.ensure_active_story(floor_index)
        self.tapir.validate_payload('CreateSlabs',payload)
        try:
            result=self.tapir.call('CreateSlabs',payload)
        except TimeoutError as exc:
            reconciliation = self._reconcile_type('Slab')
            return {'status':'UNKNOWN_OUTCOME','error':repr(exc),'command':'CreateSlabs',
                    'story':story,'requestedPayload':payload,
                    'expectedVertical': {'top_z': top_z, 'bottom_z': top_z-float(thickness) if top_z is not None else None,
                                         'reference_plane': reference_plane, 'level': float(level)},
                    'reconciliationRequired':True,'retryAllowed':False,
                    'reconciliation':reconciliation}
        ids=[x['elementId']['guid'] for x in result.get('result',{}).get('addOnCommandResponse',{}).get('elements',[]) if 'elementId' in x]
        diffs=[]
        if len(ids)!=1: diffs.append({'path':'count','requested':1,'actual':len(ids)})

        modify_payload = {
            'slabsWithDetails': [{
                'elementId': {'guid': ids[0]},
                'thickness': float(thickness),
                'structureType': 'Basic'
            }]
        } if len(ids) == 1 else {'slabsWithDetails': []}

        # This is intentionally schema-gated: do not claim support for a
        # stale local schema or invent a ModifySlabs contract.
        if not self.tapir.schema or 'ModifySlabs' not in self.tapir.schema.get('commands', {}):
            raise SafeBIMError(
                'Local Tapir schema does not contain ModifySlabs; refusing to '
                'send an unverified slab mutation.'
            )
        self.tapir.validate_payload('ModifySlabs', modify_payload)
        try:
            modify_result = self.tapir.call('ModifySlabs', modify_payload)
        except TimeoutError as exc:
            reconciliation = self._reconcile_type('Slab')
            return {'status':'UNKNOWN_OUTCOME','error':repr(exc),'command':'ModifySlabs',
                    'story':story,'requestedPayload':payload,'guids':ids,
                    'reconciliationRequired':True,'retryAllowed':False,
                    'reconciliation':reconciliation}

        rr,ds=self._read_details(ids)
        if ds:
            actual=ds[0].get('details',{}); st=actual.get('structureType'); th=actual.get('thickness')
            if st!='Basic': diffs.append({'path':'details.structureType','requested':'Basic','actual':st})
            if not _num_equal(float(thickness),th): diffs.append({'path':'details.thickness','requested':float(thickness),'actual':th})
        elif len(ids)==1:
            diffs.append({'path':'readback','requested':'one slab detail','actual':'<missing>'})
        out={'status':'PASS' if not diffs and len(ids)==1 else 'FAIL','guids':ids,'requestedPayload':payload,'tapirResponse':result,'modifyPayload':modify_payload,'modifyResponse':modify_result,'readbackResponse':rr,'readback':ds,'diff':diffs,
             'expectedVertical': {'top_z': top_z, 'bottom_z': top_z-float(thickness) if top_z is not None else None,
                                  'reference_plane': reference_plane, 'level': float(level)}}
        return out

    def _insert_opening(self, command, collection, expected_type, host_wall_guid, params):
        _, host_details = self._read_details([host_wall_guid])
        if len(host_details) != 1 or not isinstance(host_details[0].get('floorIndex'), int):
            raise SafeBIMError(f'Cannot resolve host wall floorIndex for {host_wall_guid}')
        story = self.ensure_active_story(host_details[0]['floorIndex'])
        item={'ownerWallId':{'guid':host_wall_guid},'centerOffset':float(params['centerOffset']),'sillHeight':float(params.get('sillHeight',0.0)),'width':float(params['width']),'height':float(params['height'])}
        payload={collection:[item]}; self.tapir.validate_payload(command,payload)
        try:
            result=self.tapir.call(command,payload)
        except TimeoutError as exc:
            reconciliation = self._reconcile_type(expected_type)
            return {'status':'UNKNOWN_OUTCOME','error':repr(exc),'command':command,
                    'story':story,'requestedPayload':payload,'reconciliationRequired':True,
                    'retryAllowed':False,'reconciliation':reconciliation}
        ids=[x['elementId']['guid'] for x in result.get('result',{}).get('addOnCommandResponse',{}).get('elements',[]) if 'elementId' in x]
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
