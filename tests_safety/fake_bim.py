"""In-memory, schema-valid fake BIM. Never performs a network request."""
import copy
import threading
from pathlib import Path
from safe_bim_layer import TapirClient

PROJECT = '/fake/project-A.pln'
CONTOUR = [{'x':0,'y':0}, {'x':2,'y':0}, {'x':2,'y':2}, {'x':0,'y':2}]
WALL = dict(contour=CONTOUR, floor_index=0, height=3.7, thickness=.25)
PLINTH = dict(start={'x':0,'y':0}, end={'x':2,'y':0}, grade_z=3.9,
              project_zero_z=4.5, floor_index=1, thickness=.25)
SLAB = dict(contour=CONTOUR, floor_index=1, level=.2, thickness=.25, reference_plane='TOP')


def envelope(**kw):
    return {'result': {'addOnCommandResponse': kw}}


class FakeBIM(TapirClient):
    def __init__(self):
        super().__init__(schema_path=str(Path(__file__).resolve().parents[1]/'tapir-1.5.8.json'))
        self.project = PROJECT
        self.active = 0
        self.elevations = {0:0., 1:4.5, 2:8.2, 3:11.2}
        self.elements = {}
        self.calls = []
        self.dispatches = []
        self.on_call = lambda *_: None
        self.on_created = lambda *_: None
        self.on_dispatch = lambda *_: None
        self.on_details = lambda ds: ds
        self.lock = threading.RLock()
        self.entered = threading.Event()
        self.release = threading.Event()
        self.block = False

    def call(self, command, payload):
        with self.lock:
            self.calls.append((command, copy.deepcopy(payload), self.project))
        replacement = self.on_call(command, payload)
        if replacement is not None:
            return replacement
        if command == 'GetAddOnVersion':
            version = getattr(self, 'addon_version', '1.5.9')
            if not isinstance(version, str):
                raise RuntimeError('GetAddOnVersion unavailable')
            return envelope(version=version)
        if command == 'GetProjectInfo':
            return envelope(projectPath=self.project)
        if command == 'GetStories':
            return envelope(actStory=self.active, stories=[{'index':i, 'name':f'arbitrary-{i}', 'level':z} for i,z in self.elevations.items()])
        if command == 'GetNavigatorItemTree':
            return envelope(navigatorItemTree=[{'type':'StoryItem','prefix':str(i),'navigatorItemId':{'guid':f'story-{i}'}} for i in self.elevations])
        if command == 'ChangeWindow':
            self.active = int(payload['navigatorItemId']['guid'].split('-')[-1])
            return envelope(success=True)
        if command == 'GetElementsByType':
            return envelope(elements=[{'elementId':{'guid':g}} for g,d in self.elements.items() if d['type']==payload['elementType']])
        if command == 'GetDetailsOfElements':
            rows = [copy.deepcopy(self.elements[e['elementId']['guid']]) for e in payload['elements'] if e['elementId']['guid'] in self.elements]
            return envelope(detailsOfElements=self.on_details(rows))
        if command not in {'CreateWalls','CreateSlabs','CreateWindows','CreateDoors'}:
            raise AssertionError(f'unexpected fake command {command}')
        with self.lock:
            self.dispatches.append((command, copy.deepcopy(payload), self.project))
        self.on_dispatch(command, payload)
        if self.block:
            self.entered.set()
            if not self.release.wait(10):
                raise RuntimeError('fake write barrier timeout')
        guids = []
        with self.lock:
            if command == 'CreateWalls':
                for w in payload['wallsData']:
                    write_relative = w['zCoordinate']
                    # Live Tapir: CreateWalls zCoordinate is story-relative when floorIndex
                    # is set; GetDetails wall zCoordinate is the absolute bottom.
                    detail = dict(begCoordinate=w['begCoordinate'], endCoordinate=w['endCoordinate'],
                                  zCoordinate=self.elevations[w['floorIndex']] + write_relative,
                                  bottomOffset=write_relative, height=w['height'],
                                  relativeTopStory=0, offset=0, begThickness=w['thickness'], endThickness=w['thickness'],
                                  structureType=w['structureType'], referenceLineLocation=w['referenceLineLocation'])
                    guids.append(self.add('Wall', w['floorIndex'], detail))
            elif command == 'CreateSlabs':
                for w in payload['slabsData']:
                    plane = w['referencePlaneLocation']
                    detail = dict(level=w['level'], zCoordinate=self.elevations[w['floorIndex']]+w['level'],
                                  referencePlaneLocation=plane, thickness=w['thickness'], structureType='Basic',
                                  offsetFromTop=0 if plane=='Top' else w['thickness'], polygonOutline=w['polygonCoordinates'])
                    guids.append(self.add('Slab', w['floorIndex'], detail))
            else:
                kind, collection = ('Window','windowsData') if command=='CreateWindows' else ('Door','doorsData')
                for w in payload[collection]:
                    host = w['ownerWallId']['guid']
                    detail = {k:v for k,v in w.items() if k!='ownerWallId'}
                    detail['ownerElementId'] = {'guid':host}
                    guids.append(self.add(kind, self.elements[host]['floorIndex'], detail))
        self.on_created(command, guids)
        return envelope(elements=[{'elementId':{'guid':g}} for g in guids])

    def add(self, kind, floor, detail):
        guid = f'{kind}-{len(self.elements)+1}'
        self.elements[guid] = {'type':kind, 'floorIndex':floor, 'id':'human-label-not-GUID', 'details':copy.deepcopy(detail)}
        return guid
