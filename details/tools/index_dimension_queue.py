#!/usr/bin/env python3
from __future__ import annotations
import base64,collections,json,pathlib,tarfile,tempfile
D=pathlib.Path(__file__).resolve().parents[1]

def rows(p):
 return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]

def main():
 rel=(D/'ACTIVE_RELEASE').read_text(encoding='utf-8').strip()
 src=D/'releases'/rel/f'machine-state-{rel}.tar.gz.b64'
 with tempfile.TemporaryDirectory(prefix='queue-index-') as td0:
  td=pathlib.Path(td0);tgz=td/'m.tgz';out=td/'x';out.mkdir();tgz.write_bytes(base64.b64decode(src.read_text(encoding='ascii')))
  with tarfile.open(tgz,'r:gz') as t:t.extractall(out)
  qfiles=list(out.rglob(f'dimension_binding_queue_{rel}.jsonl'))
  if len(qfiles)!=1:raise RuntimeError(f'queue files {len(qfiles)}')
  q=rows(qfiles[0])
  by=collections.defaultdict(list)
  for r in q:by[r.get('source_id') or 'UNKNOWN'].append(r)
  result={'release':rel,'total':len(q),'sources':[]}
  for sid,rs in sorted(by.items(),key=lambda kv:(-len(kv[1]),kv[0])):
   pr=collections.Counter(x.get('priority') or 'unknown' for x in rs);kinds=collections.Counter(x.get('queue_kind') or 'unknown' for x in rs)
   result['sources'].append({'source_id':sid,'total':len(rs),'priority':dict(sorted(pr.items())),'queue_kinds':dict(kinds.most_common()),'sample_record_ids':[x.get('record_id') for x in rs[:20]]})
  p=D/'index'/'dimension_queue_by_source.json';p.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
  print(json.dumps(result,ensure_ascii=False,indent=2))
 return 0
if __name__=='__main__':raise SystemExit(main())