import json,hashlib,sys
from pathlib import Path
sys.path.insert(0,str(Path('apa-core/scripts').resolve()))
import archicad_project_accelerator as A
folder=Path('apa-live-evidence/extension-delta-20261011-2002');folder.mkdir(parents=True,exist_ok=False)
A.RUN.bind_isolated_writer_pln(19724);api=A.EvidenceAPI(A.native_transport,folder)
A.RUN.guarded_project(api)
inv=A.inventory_guids(api)
extras=['55d1a829-c83c-4fe1-8073-f8b83d102170','5988ad8c-dcc4-43fe-9bd5-cf3fcc8fc48a']
details={g:A.RUN.requested_details(api,g) for g in extras}
bounds=api('Get3DBoundingBoxes',{'elements':[{'elementId':{'guid':g}} for g in extras]})
A.write_json(folder/'result.json',{'status':'READ_ONLY_DELTA_INSPECTED','inventory':inv,'extras':details,'bounds':bounds,'modelWriteAttempts':0})
A.write_json(folder/'SHA256.json',{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()})
print(json.dumps({'extras':details,'bounds':bounds},ensure_ascii=True,indent=2))
