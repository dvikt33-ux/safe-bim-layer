import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path('apa-geometry-deps').resolve()));sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
import archicad_authored_geometry as G
A.RUN.bind_isolated_writer_pln(19724)
folder=Path('apa-live-evidence/geometry-integrated-contact-20261011');folder.mkdir(parents=True,exist_ok=False)
source=json.loads(Path('apa-live-evidence/core-final-readonly-20261011/result.json').read_text(encoding='utf8'))
api=A.EvidenceAPI(A.native_transport,folder)
result={'status':'BLOCKED','modelWriteAttempts':0,'automaticRetry':False}
try:result=G.run(api,source['preflight'],source['created'],source['inventory'],folder)
except Exception as exc:result['reason']=type(exc).__name__+': '+str(exc)
result['commandCounts']=dict(api.calls)
A.write_json(folder/'result.json',result)
A.write_json(folder/'SHA256.json',{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.iterdir() if f.is_file()})
print(json.dumps({k:v for k,v in result.items() if k not in ('bounds','aabbCandidates','graphEdges','nativeVolumeIntersectionPairs','nativeSurfaceCheckPairs','xyOverlapWithoutNativeVolumeCollision','sharedNativeSurfaces')},ensure_ascii=True,indent=2))
print('PairCounts',json.dumps({k:len(result.get(k,[])) for k in ['nativeVolumeIntersectionPairs','nativeSurfaceCheckPairs','xyOverlapWithoutNativeVolumeCollision','graphEdges','sharedNativeSurfaces']}))
sys.exit(0 if result['status']=='NATIVE_AUTHORED_GEOMETRY_READBACK_PASS' else 2)
