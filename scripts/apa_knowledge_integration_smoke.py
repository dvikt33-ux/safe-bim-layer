"""Actual APA entry points + real MCP stdio client, on operator-selected corpus."""
import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import tempfile
import time
import archicad_project_accelerator as APA
import archicad_knowledge_access as K

def run(corpus, output, github_current=False):
    corpus=Path(corpus).resolve();output=Path(output).resolve();output.mkdir(exist_ok=False)
    raw=(corpus/K.PLAN).read_bytes();plan=json.loads(raw);before=hashlib.sha256(raw).hexdigest()
    remote=K.GitHubSource(os.environ.get('APA_GITHUB_READ_TOKEN')) if github_current else None
    cfg=dict(schema='APA_KNOWLEDGE_ACCESS_V1',enabled=True,repo_root=str(corpus),cache_dir=str(output/'cache'),source_mode='GITHUB_CURRENT' if remote else 'LOCAL_CHECKOUT',allowed_classes=['PROJECT_CONTROL','RESEARCH_RUN'],max_return_chars=2500,source_files=['scripts/archicad_bim_documentation.py'],code_root=str(Path(__file__).resolve().parents[1]),code_commit='f5aa4754a0ace251e8541001f17f6fa8eddfe8e5')
    service=K.KnowledgeAccess(cfg,remote);setup=service.rebuild();graph=K.components()['graph']
    sid='APA-P70.A11.S03';aid='ART-P70-A11-S03-DOCUMENTATION-PR70-20261013';second='ART-P70-A11-S03-DOCUMENTATION-FACTS-20261013'
    results={};metrics=[]
    cases=[('project','project state','plan'),('task',sid,'research'),('artifact',aid,'research'),('multidoc',aid+' '+second,'research'),('section','documentation','research')]
    for name,q,mode in cases:
        calls=remote.calls if remote else 0;start=time.perf_counter();r=APA.retrieve_project_knowledge(cfg,q,mode,remote);elapsed=(time.perf_counter()-start)*1000
        assert r['status']=='OK',(name,r)
        text=graph.canonical(r);assert len(text)<=2500
        results[name]=r;metrics.append(dict(case=name,elapsedMs=elapsed,githubCalls=remote.calls-calls if remote else 0,responseChars=len(text),responseBytes=len(text.encode())))
    assert results['task']['items'][0]['status']==plan['tasks'][sid]['status']
    assert results['artifact']['items'][0]['id']==aid
    assert any(x.get('task_id')==sid for x in results['multidoc']['items'])
    eligible=results['project']['items'];assert all(plan['tasks'][x['task_id']]['owner'] is None and all(plan['tasks'][d]['status']=='DONE_PUBLISHED' for d in plan['tasks'][x['task_id']]['depends_on']) for x in eligible)
    for name,operation,args in [('dependencies','dependencies',{'task_id':'APA-P70.A11.S02'}),('impact','impact',{'artifact_id':aid}),('tdk','tdk-trace',{'project_class':'residential.izhs'}),('source','source',{'path':'scripts/archicad_bim_documentation.py','line':1,'count':8})]:
        r=APA.inspect_project_knowledge(cfg,operation,args,remote);assert r['status'] not in ('SOURCE_OR_RELATION_NOT_VERIFIED','BUDGET_TOO_SMALL'),(name,r);results[name]=r
    assert results['tdk']['items'][0]['trace']['normative_authority'] is False
    assert APA.retrieve_project_knowledge(cfg,'documentation',remote=remote,source_class='ARCHIVED_SOURCE')['status']=='ACCESS_DENIED_SOURCE_CLASS'
    config=output/'config-private.json';config.write_text(json.dumps(cfg),encoding='utf8')
    # SDK client launches a separate process and negotiates the protocol over
    # pipes. Calling MCPServer.call_tool in-process is not a stdio acceptance test.
    async def mcp():
        from mcp.client import Client
        from mcp.client.stdio import StdioServerParameters
        params=StdioServerParameters(command=sys.executable,args=[str(Path(K.__file__).resolve()),'mcp','--config',str(config)],env={k:v for k,v in os.environ.items() if k in ('PYTHONPATH','APA_GITHUB_READ_TOKEN','PATH','TIKTOKEN_CACHE_DIR')})
        async with Client(params) as client:
            tools=await client.list_tools();assert [x.name for x in tools.tools]==['apa_retrieve']
            out=[]
            for q in (sid,aid):
                r=await client.call_tool('apa_retrieve',{'query':q});assert not r.is_error
                v=r.structured_content
                if v is None:v=json.loads(next(x.text for x in r.content if hasattr(x,'text')))
                assert v['status']=='OK',(q,v);out.append(v)
            denied=await client.call_tool('apa_retrieve',{'query':'documentation','source_class':'ARCHIVED_SOURCE'})
            denial=denied.structured_content or json.loads(next(x.text for x in denied.content if hasattr(x,'text')))
            assert denial['status']=='ACCESS_DENIED_SOURCE_CLASS'
            return dict(status='STDIO_CLIENT_PASS',sdk=importlib.metadata.version('mcp'),tools=[x.name for x in tools.tools],responses=out,acl='PASS',targetChatGPT='NOT_CONNECTED_OR_VERIFIED')
    mcp_result=asyncio.run(mcp())
    start=time.perf_counter();count=remote.calls if remote else 0
    baseline=remote.read(K.PLAN,results['task']['provenance']['github_commit']) if remote else (corpus/K.PLAN).read_bytes()
    baseline_time=(time.perf_counter()-start)*1000
    assert baseline==raw
    assert hashlib.sha256((corpus/K.PLAN).read_bytes()).hexdigest()==before
    import tiktoken
    enc=tiktoken.get_encoding('o200k_base')
    for row in metrics:row['o200kBaseProxyTokens']=len(enc.encode(graph.canonical(results[row['case']])))
    result={'status':'APA_CORE_AND_STDIO_INTEGRATION_PASS','stageI':'DONE','stageII_localMCP':'DONE','chatGPTConnection':'NOT_VERIFIED','source_mode':cfg['source_mode'],'planRevision':plan['revision'],'planUnchanged':True,'setup':setup,'calls':results,'mcp':mcp_result,'measurements':{'cases':metrics,'rawPlanBytes':len(raw),'rawPlanProxyTokens':len(enc.encode(raw.decode('utf8'))),'baselinePlanFileReadMs':baseline_time,'baselineGitHubCalls':remote.calls-count if remote else 0,'tokenizer':'tiktoken:o200k_base','actualModelBilledTokens':'NOT_MEASURED','quality':'Exact task/artifact/status/shared-reference oracle; not a broad semantic benchmark','warning':'Fresh GitHub verification adds calls; no universal token/call/latency saving claim. Cache build/source retrieval cost and actual MCP tool schema are separate.'}}
    (output/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    print(json.dumps({'status':result['status'],'planRevision':plan['revision'],'mcp':mcp_result['status'],'cases':len(results),'githubCalls':remote.calls if remote else 0}))
    return result

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--corpus',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--github-current',action='store_true');a=p.parse_args();run(a.corpus,a.output,a.github_current)
