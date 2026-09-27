"""Safe BIM Layer v0.1: deterministic high-level BIM operations over Tapir.

This module deliberately keeps Qwen out of low-level Tapir details.  Callers
provide semantic arguments; the module constructs and validates Tapir payloads,
executes one write at a time, reads elements back, and stops on any mismatch.
"""
from __future__ import annotations
import copy, json, math, urllib.request
import hashlib
import threading
from contextlib import contextmanager
from safe_bim_verification import (VerificationError, number, equal, response_items,
                                   element_guids, verify_details, guid_key, wall_z_contract)
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
            # Skip records without a usable index/elevation. Duplicate valid indexes
            # are fail-closed below; names are never used as identity.
            if isinstance(idx, bool) or not isinstance(idx, int):
                continue
            if isinstance(elevation, bool) or not isinstance(elevation, (int, float)) or not math.isfinite(float(elevation)):
                continue
            rows.append((int(idx), float(elevation), self._field(item, 'name', 'displayName', 'userName')))
        if len({r[0] for r in rows}) != len(rows):
            raise SafeBIMError("duplicate factual story index")
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
        self.schema = json.loads(Path(schema_path).read_text(encoding='utf-8')) if schema_path else None

    def call(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
        """Public entry. Allowlisted reads only. Mutations never leave this method."""
        from safe_bim_command_policy import CommandClass, classify
        if classify(command) != CommandClass.READ_ONLY:
            raise SafeBIMError(
                f'public TapirClient.call refuses {command!r}; mutations require the gateway')
        return self._post(command, params)

    def transport(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
        """Physical send. The mutation gateway is the only permitted caller."""
        from safe_bim_mutation_gateway import require_transport_permit
        require_transport_permit()
        return self._post(command, params)

    def _post(self, command: str, params: dict[str, Any]) -> dict[str, Any]:
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
        raise SafeBIMError('ChangeWindow is refused on the public client')

    def change_floor_plan_navigator_item(self, navigator_guid: str) -> dict[str, Any]:
        raise SafeBIMError('ChangeWindow is refused on the public client')

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
    def __init__(self, client: TapirClient, vertical_context: VerticalContext | None = None, gateway=None):
        self.tapir=client
        self.gateway = gateway
        self._execution = threading.local()
        self.vertical_context = vertical_context
        self.story_resolver = StoryResolver(client, vertical_context.project_zero_z
                                            if vertical_context else None)

    def _gate(self):
        if self.gateway is None:
            from safe_bim_mutation_gateway import MutationGateway
            self.gateway = MutationGateway(self.tapir)
        return self.gateway

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
        payload = {'navigatorItemId': {'guid': str(guid)}}
        self.tapir.validate_payload('ChangeWindow', payload)
        gate = self._gate()
        with gate.session_if_needed():
            change = gate.dispatch('ChangeWindow', payload)
        if not self._response_items(change).get('success', True):
            raise SafeBIMError(f'ChangeWindow failed for story {target}: {change!r}')
        after = self.tapir.active_story()
        if after != target:
            raise SafeBIMError(f'ChangeWindow read-back mismatch: requested {target}, actStory={after}')
        return {'before': before, 'after': after, 'switched': True, 'navigatorGuid': guid}

    def _read_details(self, guids):
        if not guids or len(set(guids)) != len(guids):
            raise SafeBIMError('nonempty unique GUIDs required')
        responses, details = [], []
        # Pinned Tapir details.id is NOT a GUID. Bind each singleton response
        # to its exact GUID request, not a zip of two potentially truncated lists.
        for guid in guids:
            response = self.tapir.call('GetDetailsOfElements', {'elements': [{'elementId': {'guid': guid}}]})
            rows = response_items(response).get('detailsOfElements')
            if not isinstance(rows, list) or len(rows) != 1 or not isinstance(rows[0], dict) or 'error' in rows[0]:
                raise SafeBIMError('incomplete/malformed singleton read-back')
            detail = copy.deepcopy(rows[0])
            for echoed in (detail.get('guid'), detail.get('elementId', {}).get('guid')):
                if echoed is not None and (not isinstance(echoed, str) or guid_key(echoed) != guid_key(guid)):
                    raise SafeBIMError('echoed GUID mismatch')
            detail['verifiedGuid'] = guid
            responses.append(response)
            details.append(detail)
        return responses, details

    @contextmanager
    def execution_context(self, prepared, before_write, receipt):
        if getattr(self._execution, 'value', None) is not None:
            raise SafeBIMError('nested execution context')
        self._execution.value = (prepared, before_write, receipt)
        try:
            yield
        finally:
            self._execution.value = None

    @staticmethod
    def _point(p):
        if not isinstance(p, dict) or set(p) != {'x', 'y'}:
            raise SafeBIMError('point must contain exactly x/y')
        return {'x': number(p['x']), 'y': number(p['y'])}

    @staticmethod
    def _positive(value):
        value = number(value)
        if value <= 0:
            raise SafeBIMError('positive dimension required')
        return value

    @staticmethod
    def _floor(value):
        if isinstance(value, bool) or not isinstance(value, int):
            raise SafeBIMError('integer floor_index required')
        return value

    def prepare(self, operation, params):
        """Read-only preflight; full expected contract exists BEFORE checkpoint dispatch."""
        params = copy.deepcopy(params)
        metadata = {k: params.pop(k) for k in ('verticalContext', 'expectedZFingerprint') if k in params}
        try:
            prepared = self._prepare(operation, params)
            fp = prepared.get('expectedZFingerprint', {})
            supplied = metadata.get('expectedZFingerprint')
            if supplied is not None:
                if not isinstance(supplied, dict) or not supplied or set(supplied) - set(fp):
                    raise SafeBIMError('unsupported expectedZFingerprint')
                if any(not equal(fp[k], v) for k, v in supplied.items()):
                    raise SafeBIMError('expectedZFingerprint contradicts factual preflight')
            context = metadata.get('verticalContext')
            if context is not None:
                fields = set(VerticalContext.__dataclass_fields__)
                if not isinstance(context, dict) or set(context) - fields:
                    raise SafeBIMError('invalid verticalContext')
                for key, value in context.items():
                    if key not in {'source', 'justification'} and value is not None:
                        number(value)
                if operation == 'create_plinth_segment':
                    mapping = {'project_zero_z': params['project_zero_z'], 'grade_z': params['grade_z'],
                               'plinth_bottom_z': params['grade_z'], 'plinth_top_z': params['project_zero_z']}
                    if any(context.get(k) is not None and not equal(context[k], v) for k, v in mapping.items()):
                        raise SafeBIMError('verticalContext contradicts plinth')
            prepared['verticalContext'] = context
            prepared['params'] = params
            prepared['operation'] = operation
            # Inventory is an execution newness check, NEVER an absence proof
            # after an uncertain dispatch. Foreign matches are never adopted.
            prepared['preexistingGuids'] = element_guids(self.tapir.call('GetElementsByType', {'elementType': prepared['type']}))
            raw = json.dumps(prepared, sort_keys=True, ensure_ascii=False, allow_nan=False)
            prepared['contractHash'] = hashlib.sha256(raw.encode()).hexdigest()
            return prepared
        except VerificationError as exc:
            raise SafeBIMError(str(exc)) from exc

    def _prepare(self, operation, p):
        if operation in {'insert_window', 'insert_door'}:
            host = p['host_wall_guid']
            if not isinstance(host, str) or not host:
                raise SafeBIMError('host GUID required')
            _, host_rows = self._read_details([host])
            if host_rows[0].get('type') != 'Wall':
                raise SafeBIMError('host must be a wall')
            floor = self._floor(host_rows[0].get('floorIndex'))
        else:
            floor = self._floor(p['floor_index'])
        story = self.story_resolver.by_index(floor)
        elevation = number(story.elevation)
        expected, fp = [], {}
        if operation == 'create_wall_segment':
            thickness = self._positive(p.get('thickness', .25))
            a, b = self._point(p['start']), self._point(p['end'])
            if a == b:
                raise SafeBIMError('zero-length wall segment')
            height = self._positive(p['height'])
            bottom = elevation
            vertical = wall_z_contract(floor, elevation, bottom, height)
            walls = [{'begCoordinate': a, 'endCoordinate': b, 'floorIndex': floor,
                      'zCoordinate': vertical['write_relative_z'], 'height': height, 'thickness': thickness,
                      'referenceLineLocation': 'Center', 'structureType': 'Basic'}]
            expected = [{'begCoordinate': a, 'endCoordinate': b,
                         'zCoordinate': vertical['expected_readback_z'],
                         'bottomOffset': vertical['write_relative_z'], 'height': height, 'relativeTopStory': 0,
                         'begThickness': thickness, 'endThickness': thickness,
                         'offset': 0, 'referenceLineLocation': 'Center', 'structureType': 'Basic'}]
            command, payload, kind = 'CreateWalls', {'wallsData': walls}, 'Wall'
            fp = vertical
        elif operation in {'create_wall_loop', 'create_plinth_segment'}:
            thickness = self._positive(p.get('thickness', .25))
            if operation == 'create_plinth_segment':
                a, b = self._point(p['start']), self._point(p['end'])
                if a == b:
                    raise SafeBIMError('zero-length plinth')
                pts = [a, b]
                bottom, top = number(p['grade_z']), number(p['project_zero_z'])
                height = self._positive(top - bottom)
                vertical = wall_z_contract(floor, elevation, bottom, height)
            else:
                pts = [self._point(q) for q in p['contour']]
                if pts and pts[0] == pts[-1]: pts = pts[:-1]
                if len(pts) < 3 or len({(q['x'], q['y']) for q in pts}) != len(pts):
                    raise SafeBIMError('nondegenerate contour required')
                pts.append(copy.deepcopy(pts[0]))
                height = self._positive(p['height'])
                bottom, top = elevation, elevation + height
                vertical = wall_z_contract(floor, elevation, bottom, height)
            walls = []
            for a, b in zip(pts, pts[1:]):
                # floorIndex is present, so this zCoordinate is the write offset
                # (absolute bottom - story elevation), never the read-back value.
                walls.append({'begCoordinate': a, 'endCoordinate': b, 'floorIndex': floor,
                              'zCoordinate': vertical['write_relative_z'], 'height': height, 'thickness': thickness,
                              'referenceLineLocation': 'Center', 'structureType': 'Basic'})
                expected.append({'begCoordinate': a, 'endCoordinate': b,
                                 'zCoordinate': vertical['expected_readback_z'],
                                 'bottomOffset': vertical['write_relative_z'], 'height': height, 'relativeTopStory': 0,
                                 'begThickness': thickness, 'endThickness': thickness,
                                 'offset': 0, 'referenceLineLocation': 'Center', 'structureType': 'Basic'})
            command, payload, kind = 'CreateWalls', {'wallsData': walls}, 'Wall'
            fp = vertical
        elif operation == 'create_basic_slab':
            pts = [self._point(q) for q in p['contour']]
            if pts and pts[0] == pts[-1]: pts = pts[:-1]
            if len(pts) < 3 or len({(q['x'], q['y']) for q in pts}) != len(pts):
                raise SafeBIMError('nondegenerate slab contour required')
            level, thickness = number(p['level']), self._positive(p['thickness'])
            plane = p.get('reference_plane', 'TOP')
            if not isinstance(plane, str) or plane.upper() not in {'TOP', 'BOTTOM'}:
                raise SafeBIMError('basic slab reference plane must be Top or Bottom')
            plane = plane.title()
            offset = 0. if plane == 'Top' else thickness
            reference = elevation + level
            top, bottom = reference + offset, reference + offset - thickness
            payload = {'slabsData': [{'level': level, 'floorIndex': floor, 'thickness': thickness,
                                     'referencePlaneLocation': plane, 'polygonCoordinates': pts}]}
            expected = [{'level': level, 'zCoordinate': reference, 'referencePlaneLocation': plane,
                         'thickness': thickness, 'offsetFromTop': offset, 'structureType': 'Basic',
                         'polygonOutline': pts}]
            command, kind = 'CreateSlabs', 'Slab'
            fp = {'floorIndex': floor, 'story_elevation': elevation, 'level': level,
                  'thickness': thickness, 'reference_plane': plane, 'expected_top': top,
                  'expected_bottom': bottom, 'structureType': 'Basic'}
        elif operation in {'insert_window', 'insert_door'}:
            intended = p['params']
            if not isinstance(intended, dict) or set(intended) - {'centerOffset', 'sillHeight', 'width', 'height'}:
                raise SafeBIMError('invalid opening params')
            item = {'ownerWallId': {'guid': host}, 'centerOffset': number(intended['centerOffset']),
                    'sillHeight': number(intended.get('sillHeight', 0)),
                    'width': self._positive(intended['width']), 'height': self._positive(intended['height'])}
            is_window = operation == 'insert_window'
            command, kind = ('CreateWindows', 'Window') if is_window else ('CreateDoors', 'Door')
            payload = {'windowsData' if is_window else 'doorsData': [item]}
            expected = [{**{k: v for k, v in item.items() if k != 'ownerWallId'}, 'ownerElementId': {'guid': host}}]
        else:
            raise SafeBIMError(f'unsupported operation {operation!r}')
        self.tapir.validate_payload(command, payload)
        return {'type': kind, 'floorIndex': floor, 'storyElevation': elevation,
                'command': command, 'payload': payload, 'expected': expected, 'expectedZFingerprint': fp}

    def verify_saved(self, prepared, guids):
        story = self.story_resolver.by_index(prepared['floorIndex'])
        if not equal(story.elevation, prepared['storyElevation']):
            raise SafeBIMError('story elevation changed since preflight')
        _, details = self._read_details(guids)
        verify_details(prepared, guids, details)
        return details

    def _execute(self, operation, params):
        context = getattr(self._execution, 'value', None)
        prepared = context[0] if context else self.prepare(operation, params)
        clean = {k: v for k, v in params.items() if k not in {'verticalContext', 'expectedZFingerprint'}}
        if operation != prepared['operation'] or clean != prepared['params']:
            raise SafeBIMError('execution does not match pinned prepared contract')
        dispatched = False
        try:
            from safe_bim_command_policy import PolicyError, assert_single_create_item
            try:
                assert_single_create_item(prepared['command'], prepared['payload'])
            except PolicyError as exc:
                raise SafeBIMError(str(exc)) from exc
            gate = self._gate()
            owns_admission = not gate.admitted
            if owns_admission:
                gate.begin_step(prepared['command'])
            try:
                self.ensure_active_story(prepared['floorIndex'])
                if context:
                    context[1](prepared['command'], prepared['payload'])
                dispatched = True
                response = gate.dispatch(prepared['command'], prepared['payload'])
            finally:
                if owns_admission:
                    gate.end_step()
            guids = element_guids(response, len(prepared['expected']))
            old = {guid_key(g) for g in prepared['preexistingGuids']}
            if any(guid_key(g) in old for g in guids):
                raise SafeBIMError('create returned pre-existing/foreign GUID')
            if context:
                context[2]({'status': 'UNKNOWN_OUTCOME', 'readbackVerified': False,
                            'guids': guids, 'operation': operation, 'contractHash': prepared['contractHash'],
                            'executionIdentity': prepared.get('executionIdentity')})
            details = self.verify_saved(prepared, guids)
            result = {'status': 'PASS', 'readbackVerified': True, 'guids': guids, 'readback': details,
                      'operation': operation, 'contractHash': prepared['contractHash'],
                      'executionIdentity': prepared.get('executionIdentity'),
                      'expectedZFingerprint': prepared['expectedZFingerprint'], 'requestedPayload': prepared['payload']}
            if prepared['type'] in {'Wall', 'Slab'}:
                actual = details[0]['details']
                if prepared['type'] == 'Wall':
                    # Read-back z is already absolute bottom. Do not add story elevation again.
                    result['actual_bottom'] = number(actual['zCoordinate'])
                    result['actual_top'] = result['actual_bottom'] + number(actual['height'])
                else:
                    result['actual_top'] = prepared['storyElevation'] + number(actual['level']) + number(actual['offsetFromTop'])
                    result['actual_bottom'] = result['actual_top'] - number(actual['thickness'])
            if context:
                context[2](result)  # durable verified receipt BEFORE step DONE
            return result
        except Exception as exc:
            if getattr(exc, 'execution_control', False):
                raise
            # No repair-write or retry follows a bad readback.
            return {'status': 'UNKNOWN_OUTCOME' if dispatched else 'WAITING_USER', 'error': repr(exc),
                    'retryAllowed': False, 'reconciliationRequired': True, 'readbackVerified': False}

    def create_wall_loop(self, contour, floor_index, height, thickness):
        return self._execute('create_wall_loop', dict(contour=contour, floor_index=floor_index, height=height, thickness=thickness))

    def create_wall_segment(self, start, end, floor_index, height, thickness):
        return self._execute('create_wall_segment', dict(start=start, end=end, floor_index=floor_index, height=height, thickness=thickness))

    def create_plinth_segment(self, start, end, grade_z, project_zero_z, floor_index, thickness=.25):
        return self._execute('create_plinth_segment', dict(start=start, end=end, grade_z=grade_z,
                             project_zero_z=project_zero_z, floor_index=floor_index, thickness=thickness))

    def create_basic_slab(self, contour, level, floor_index, thickness, reference_plane='TOP'):
        # Do not ModifySlabs on an unverified GUID. Create must already satisfy the
        # requested Basic/plane/thickness contract; otherwise stop UNKNOWN for review.
        return self._execute('create_basic_slab', dict(contour=contour, level=level, floor_index=floor_index,
                             thickness=thickness, reference_plane=reference_plane))

    def insert_window(self, host_wall_guid, params):
        return self._execute('insert_window', dict(host_wall_guid=host_wall_guid, params=params))

    def insert_door(self, host_wall_guid, params):
        return self._execute('insert_door', dict(host_wall_guid=host_wall_guid, params=params))

    def create_room(self, contour, wall_height, wall_thickness, slab, door=None, windows=None):
        """Refused. A room is several physical creates and cannot be one resumable step."""
        raise SafeBIMError('create_room is refused; it is not a single resumable step')
