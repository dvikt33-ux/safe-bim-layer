#!/usr/bin/env python3
import base64,json,pathlib,tarfile,tempfile
D=pathlib.Path(__file__).resolve().parents[1]
def rows(p): return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def has(x):
    def s(v):
        if isinstance(v,str): return ['POR'] if 'BRAAS_ROOF_DETAILS' in v else []
        if isinstance(v,dict): return sum((s(k)+s(w) for k,w in v.items()),[])
        if isinstance(v,list): return sum((s(w) for w in v),[])
        return []
    return bool(s(x))
with tempfile.TemporaryDirectory() as td:
    t=pathlib.Path(td); tg=t/'a.tgz'
    tg.write_bytes(base64.b64decode((D/'releases'/'v2.4'/'machine-state-v2.4.tar.gz.b64').read_text()))
    with tarfile.open(tg,'r:gz') as f: f.extractall(t)
    root=list(t.rglob('details_active_v2.4.jsonl'))[0].parent
    for name in ['details_active_v2.4.jsonl','parameter_facts_v2.4.jsonl','component_variants_v2.4.jsonl','dimension_binding_queue_v2.4.jsonl']:
        a=[r for r in rows(root/name) if has(r)]
        print('FILE',name,'COUNT',len(a))
        for r in a[:3]: print(json.dumps(r,ensure_ascii=False,indent=2))
