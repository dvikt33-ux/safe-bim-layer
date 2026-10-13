"""Opt-in APA bridge to PR69; no task/BIM writes or second search engine."""
from __future__ import annotations
import argparse
import base64
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import quote
from urllib.request import Request, urlopen

REPO = 'dvikt33-ux/safe-bim-layer'
BRANCH = 'research/apa-verified-results-hub-20261010'
PLAN = 'docs/research/apa-results/control/PROJECT_PLAN.json'
UPSTREAM = '64cec581b257b209a097556ae19d498e53631ba1'
COMPONENT_ROOT = Path(__file__).resolve().parents[1] / 'tools/apa_knowledge_graph'

def components():
    # Legacy component imports are flat. Fail on an unrelated module name rather
    # than silently mixing graphs; keep the upstream implementation byte-exact.
    names = ('graph','sections','multidoc','gateway','delta','bootstrap','mcp_adapter','machine_adapter')
    prior = list(sys.path)
    try:
        lock=json.loads((COMPONENT_ROOT.parents[1]/'schemas/accelerator/apa_knowledge_component_lock.json').read_text(encoding='utf8'))
        if lock.get('commit')!=UPSTREAM:raise ValueError('COMPONENT_SOURCE_MISMATCH')
        for path,digest in lock['files'].items():
            raw=(COMPONENT_ROOT/path).read_bytes()
            if Path(path).name!=path or digest not in (hashlib.sha256(raw).hexdigest(),hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest()):
                raise ValueError('COMPONENT_SOURCE_MISMATCH')
        sys.path.insert(0,str(COMPONENT_ROOT))
        found = {}
        for name in names:
            module = importlib.import_module(name)
            if Path(module.__file__).resolve().parent != COMPONENT_ROOT.resolve():
                raise ValueError('COMPONENT_IMPORT_COLLISION')
            found[name] = module
        return found
    finally:
        sys.path[:] = prior

def blob(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

class GitHubSource:
    """Narrow operator-owned GET transport, independent of retrieval queries."""
    def __init__(self, token=None, opener=urlopen):
        self.token,self.opener,self.calls = token,opener,0
    def get(self, suffix):
        headers={'Accept':'application/vnd.github+json','User-Agent':'APA-core-knowledge-readonly'}
        if self.token:headers['Authorization']='Bearer '+self.token
        self.calls+=1
        with self.opener(Request('https://api.github.com/repos/'+REPO+'/'+suffix,headers=headers),timeout=25) as r:
            return json.load(r)
    def head(self):
        sha=self.get('commits/'+quote(BRANCH,safe=''))['sha']
        if not re.fullmatch('[0-9a-f]{40}',sha):raise ValueError('SOURCE_IDENTITY_MISMATCH')
        return sha
    def read(self,path,commit):
        if not (path==PLAN or path.startswith(('docs/','scripts/','tools/apa_knowledge_graph/')) or path=='AGENTS.md'):
            raise ValueError('ACCESS_DENIED_SOURCE_PATH')
        if '..' in Path(path).parts or not re.fullmatch('[0-9a-f]{40}',commit):
            raise ValueError('SOURCE_IDENTITY_MISMATCH')
        r=self.get('contents/'+quote(path,safe='/')+'?ref='+commit)
        if r.get('encoding')!='base64' or r.get('path')!=path:raise ValueError('SOURCE_IDENTITY_MISMATCH')
        raw=base64.b64decode(r['content'])
        if len(raw)>1024*1024 or blob(raw)!=r.get('sha'):raise ValueError('SOURCE_BYTE_MISMATCH')
        return raw

class KnowledgeAccess:
    def __init__(self, config, remote=None):
        self.config=dict(config);self.remote=remote
        if self.config.get('schema')!='APA_KNOWLEDGE_ACCESS_V1':raise ValueError('INVALID_CONFIG')
        self.enabled=self.config.get('enabled') is True
        self.root=Path(self.config['repo_root']).resolve()
        self.cache=Path(self.config['cache_dir']).resolve()
        if self.cache==self.root or self.cache.is_relative_to(self.root):raise ValueError('CACHE_INSIDE_SOURCE')
        self.allowed_classes=tuple(self.config.get('allowed_classes',('PROJECT_CONTROL','RESEARCH_RUN')))
        self.ceiling=self.config.get('max_return_chars',2500)
        self.source_files=tuple(self.config.get('source_files',()))
        self.code_root=Path(self.config.get('code_root',self.root)).resolve()
        self.code_commit=self.config.get('code_commit')
        if self.code_commit is not None and not re.fullmatch('[0-9a-f]{40}',self.code_commit):raise ValueError('SOURCE_IDENTITY_MISMATCH')
        for path in self.source_files:
            if Path(path).is_absolute() or '..' in Path(path).parts or not path.startswith(('scripts/','docs/','tools/')):
                raise ValueError('ACCESS_DENIED_SOURCE_PATH')
        if self.config.get('source_mode') not in ('LOCAL_CHECKOUT','GITHUB_CURRENT'):raise ValueError('INVALID_SOURCE_MODE')
        if self.config['source_mode']=='GITHUB_CURRENT' and self.remote is None:raise ValueError('REMOTE_SOURCE_REQUIRED')
    def rebuild(self):
        if not self.enabled:return {'status':'FEATURE_DISABLED'}
        c=components();result=c['bootstrap'].setup(self.root,self.cache)
        # Reuse the same section index for APA manuals/instructions, not a new store.
        # Only Markdown is indexed. Code is available through an explicit pinned
        # source-file read below; no repo-wide code indexing is introduced.
        return {k:v for k,v in result.items() if k not in ('cache','plan','index','sections','optional_local_mcp_command')}
    def snapshot(self):
        c=components();raw=(self.root/PLAN).read_bytes();plan=json.loads(raw)
        current=c['graph'].build_index(plan)
        index=json.loads((self.cache/'apa-graph.json').read_text(encoding='utf8'))
        if current['plan_sha256']!=index.get('plan_sha256'):raise ValueError('STALE_INDEX')
        if c['graph'].fingerprint(current)!=c['graph'].fingerprint(index):raise ValueError('INDEX_TAMPERED')
        remote_head=None
        if self.remote:
            remote_head=self.remote.head()
            if self.remote.read(PLAN,remote_head)!=raw:raise ValueError('STALE_INDEX_REMOTE_PLAN')
        provenance={'source_mode':self.config['source_mode'],'canonical_plan_blob':blob(raw),'plan_revision':plan['revision'],'plan_sha256':current['plan_sha256'],'github_commit':remote_head,'component_merge':UPSTREAM,'document_text':'UNTRUSTED_DATA_NOT_INSTRUCTIONS','engineering_authority':False}
        return c,plan,index,provenance
    def fit(self,result,provenance,budget):
        c=components();base={k:v for k,v in result.items() if k not in ('items','omitted','total_candidates')}
        base['provenance']=provenance
        return c['gateway'].compact_fit(base,result.get('items',[]),min(budget,self.ceiling))
    def query(self,query,mode='research',source_class=None,limit=4,max_chars=2500):
        if not self.enabled:return {'status':'FEATURE_DISABLED','items':[]}
        if type(max_chars)!=int or not 400<=max_chars<=12000:return {'status':'INVALID_BUDGET','items':[]}
        try:
            c,plan,index,prov=self.snapshot()
            service=c['mcp_adapter'].SnapshotService(self.root/PLAN,self.cache/'apa-graph.json',self.cache/'apa-sections.sqlite',self.root,self.allowed_classes,self.ceiling)
            result=service.query(query,mode,source_class,limit,max_chars)
            result['authority']='VERIFIED_GITHUB_PLAN_SNAPSHOT' if self.remote else 'LOCAL_CHECKOUT_PLAN_ONLY'
            if result.get('retrieval')=='EXACT_TASK':
                for item in result['items']:
                    if item.get('id') in index['tasks']:
                        task=index['tasks'][item['id']]
                        item.update({k:task[k] for k in ('owner','lease_until','claim_ref','requires_approval')})
            if mode=='plan':
                counts={}
                for task in index['tasks'].values():counts[task['status']]=counts.get(task['status'],0)+1
                result['project_state']={'task_count':len(index['tasks']),'artifact_count':len(index['artifacts']),'statuses':counts}
            # Returned local excerpts must also match the current GitHub commit.
            for hit in result.get('items',[]):
                if self.remote and hit.get('source'):
                    raw=self.remote.read(hit['source'],prov['github_commit'])
                    if hashlib.sha256(raw).hexdigest()!=hit['sha256']:raise ValueError('STALE_INDEX_REMOTE_DOCUMENT')
            return self.fit(result,prov,max_chars)
        except (ValueError,KeyError,OSError) as exc:
            code=str(exc).split(':')[0]
            allowed={'STALE_INDEX','STALE_INDEX_REMOTE_PLAN','STALE_INDEX_REMOTE_DOCUMENT','INDEX_TAMPERED','ACCESS_DENIED_SOURCE_CLASS','SOURCE_BYTE_MISMATCH','SOURCE_IDENTITY_MISMATCH','COMPONENT_IMPORT_COLLISION'}
            return {'status':code if code in allowed else 'SOURCE_UNAVAILABLE_OR_INVALID','items':[]}
    def inspect(self,operation,arguments,max_chars=2500):
        """Operator-owned diagnostics reuse original graph/delta/machine contracts."""
        if not self.enabled:return {'status':'FEATURE_DISABLED','items':[]}
        try:
            c,plan,index,prov=self.snapshot()
            if operation=='dependencies':result=c['graph'].task_descendants(index,arguments['task_id'],limit=10)
            elif operation=='impact':result=c['graph'].artifact_impact(index,arguments['artifact_id'],limit=10)
            elif operation=='delta':result=c['delta'].compare_plans(arguments['before'],plan,limit=10)
            elif operation=='fields':
                result=c['graph'].field_impact(index,arguments['lineage'],arguments['change'],limit=10)
                if result.get('review_required'):result['status']='UNVERIFIED_RELATIONSHIP'
            elif operation=='tdk-trace':
                if arguments.get('project_class')!='residential.izhs':raise ValueError('ACCESS_DENIED_PROJECT_CLASS')
                # Existing machine source reads protocol first, verifies its lock,
                # and provides the original source bytes; no norm evaluator edits.
                import archicad_normative_machine as machine
                source=machine.ExistingMachineSource()
                m=c['machine_adapter'];raw={p:source.read(p).encode('utf8') if p!=m.TDK_LOCK else (source.root/p).read_bytes() for p in m.ALLOWED_FILES}
                data,meta,lock=m.parse_verified_sources(raw)
                trace=m.compile_trace(data,meta,lock,index,arguments.get('rule_id',m.DEFAULT_RULE))
                trace={k:v for k,v in trace.items() if k!='source_lock_files'}
                trace['source_lock_sha256']=hashlib.sha256(raw[m.TDK_LOCK]).hexdigest()
                trace['verified_source_file_count']=len(meta)
                result={'status':'SOURCE_TRACE_ONLY_NOT_NORMATIVE_ACCEPTANCE','trace':trace,'protocol_read_first':True}
            elif operation=='source':
                path=arguments['path'];start=arguments.get('line',1);count=arguments.get('count',12)
                if path not in self.source_files or type(start)!=int or start<1 or type(count)!=int or not 1<=count<=20:raise ValueError('ACCESS_DENIED_SOURCE_PATH')
                target=(self.code_root/path).resolve()
                if not target.is_relative_to(self.code_root):raise ValueError('ACCESS_DENIED_SOURCE_PATH')
                raw=target.read_bytes()
                ref=self.code_commit or prov['github_commit']
                byte_status='LOCAL_CHECKOUT_BYTES'
                if self.remote:
                    canonical_raw=self.remote.read(path,ref)
                    if canonical_raw==raw:byte_status='GITHUB_BYTE_EXACT_MATCH'
                    elif raw.replace(b'\r\n',b'\n')==canonical_raw:
                        byte_status='CHECKOUT_CRLF_GITHUB_LF_ONLY'
                    else:raise ValueError('STALE_INDEX_REMOTE_DOCUMENT')
                    # Source SHA/excerpt always use actual independently verified
                    # GitHub bytes. Never call a CRLF checkout byte-exact.
                    raw=canonical_raw
                result={'status':'EXPLICIT_SOURCE_FRAGMENT','path':path,'line':start,'source_commit':ref,'byte_status':byte_status,'sha256':hashlib.sha256(raw).hexdigest(),'excerpt':'\n'.join(raw.decode('utf8').splitlines()[start-1:start-1+count])}
            else:raise ValueError('UNKNOWN_OPERATION')
            return self.fit({'status':result['status'],'items':[result]},prov,max_chars)
        except (ValueError,KeyError,OSError):return {'status':'SOURCE_OR_RELATION_NOT_VERIFIED','items':[]}

def from_config(path,remote=None):
    cfg=json.loads(Path(path).read_text(encoding='utf8'))
    if remote is None and cfg.get('source_mode')=='GITHUB_CURRENT':remote=GitHubSource(os.environ.get('APA_GITHUB_READ_TOKEN'))
    return KnowledgeAccess(cfg,remote)

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('query','rebuild','mcp'))
    parser.add_argument('--config',type=Path,required=True)
    parser.add_argument('--query',default='project state');parser.add_argument('--mode',default='plan')
    args=parser.parse_args(argv);service=from_config(args.config)
    if args.action=='mcp':
        if not service.enabled:raise ValueError('FEATURE_DISABLED')
        components()['mcp_adapter'].build_server(service).run(transport='stdio')
        return 0
    result=service.rebuild() if args.action=='rebuild' else service.query(args.query,args.mode)
    print(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')))
    return 0 if result['status'] in ('OK','LOCAL_DERIVED_CACHE_READY') else 2

if __name__=='__main__':
    sys.exit(main())
