import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import archicad_project_accelerator as APA
import archicad_knowledge_access as K

S1='APA-P70.A11.S02';S2='APA-P70.A11.S03';S3='APA-P70.A07.S01'
def task(sid,status,deps=(),owner=None):
    return dict(id=sid,title='Task '+sid,status=status,priority=1,depends_on=list(deps),related=[],inputs=['ART-DOC'],evidence=[],owner=owner,claim_ref=None,lease_until=None,requires_approval=False)

class Remote:
    def __init__(self,root):self.root=root;self.files={};self.calls=0
    def head(self):self.calls+=1;return 'a'*40
    def read(self,path,commit):self.calls+=1;return self.files.get(path,(self.root/path).read_bytes())

class Integration(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)/'source';self.cache=Path(self.temp.name)/'cache'
        self.control=self.root/Path(K.PLAN).parent;self.control.mkdir(parents=True)
        self.doc=self.control/'manual.md';self.doc.write_text('# Documentation\nNative plan and schedule.\n',encoding='utf8')
        self.plan={'revision':1,'tasks':{S1:task(S1,'DONE_PUBLISHED'),S2:task(S2,'PARTIAL',[S1]),S3:task(S3,'READY',[S2])},'artifacts':{'ART-DOC':{'id':'ART-DOC','kind':'DOCUMENT','verification':'READBACK_VERIFIED','uri':'docs/research/apa-results/control/manual.md'},'ART-OTHER':{'id':'ART-OTHER','kind':'REPORT','verification':'SOURCE_VERIFIED','uri':'docs/research/apa-results/control/manual.md'}}}
        self.plan['tasks'][S2]['evidence'].append('ART-OTHER');self.save()
        self.cfg=dict(schema='APA_KNOWLEDGE_ACCESS_V1',enabled=True,repo_root=str(self.root),cache_dir=str(self.cache),source_mode='GITHUB_CURRENT',max_return_chars=2500,allowed_classes=['PROJECT_CONTROL','RESEARCH_RUN'],source_files=['docs/research/apa-results/control/manual.md'])
        self.remote=Remote(self.root);K.KnowledgeAccess(self.cfg,self.remote).rebuild()
        self.before=(self.root/K.PLAN).read_bytes()
    def save(self):(self.root/K.PLAN).write_text(json.dumps(self.plan),encoding='utf8')
    def query(self,q,mode='research',**kw):return APA.retrieve_project_knowledge(self.cfg,q,mode,self.remote,**kw)
    def test_actual_core_task_and_lease_read(self):
        r=self.query(S2);self.assertEqual(r['items'][0]['status'],'PARTIAL');self.assertIn('lease_until',r['items'][0]);self.assertEqual(r['provenance']['source_mode'],'GITHUB_CURRENT')
    def test_project_state_and_next_without_claim(self):
        r=self.query('project state','plan');self.assertEqual(r['project_state']['task_count'],3);self.assertEqual([x['task_id'] for x in r['items']],[S2]);self.assertEqual((self.root/K.PLAN).read_bytes(),self.before)
    def test_artifact_lookup_and_multi_document_relation(self):
        self.assertEqual(self.query('ART-DOC')['items'][0]['id'],'ART-DOC')
        r=self.query('ART-DOC ART-OTHER');self.assertEqual(r['retrieval'],'MULTI_ARTIFACT_GRAPH');self.assertTrue(any(x.get('task_id')==S2 for x in r['items']))
    def test_dependency_and_impact_calls_from_core(self):
        r=APA.inspect_project_knowledge(self.cfg,'dependencies',{'task_id':S1},self.remote)
        self.assertEqual({x['id'] for x in r['items'][0]['results']},{S2,S3})
        r=APA.inspect_project_knowledge(self.cfg,'impact',{'artifact_id':'ART-DOC'},self.remote);self.assertEqual(r['status'],'OK')
    def test_remote_change_is_stale_even_if_local_index_matches(self):
        changed=copy.deepcopy(self.plan);changed['revision']=2;changed['tasks'][S2]['status']='IN_PROGRESS';self.remote.files[K.PLAN]=json.dumps(changed).encode()
        self.assertEqual(self.query(S2)['status'],'STALE_INDEX_REMOTE_PLAN')
    def test_local_change_requires_safe_rebuild(self):
        self.plan['revision']=2;self.plan['tasks'][S2]['status']='IN_PROGRESS';self.save()
        self.assertEqual(self.query(S2)['status'],'STALE_INDEX')
        K.KnowledgeAccess(self.cfg,self.remote).rebuild();self.assertEqual(self.query(S2)['items'][0]['status'],'IN_PROGRESS')
    def test_forged_graph_status_cannot_reuse_plan_hash(self):
        file=self.cache/'apa-graph.json';v=json.loads(file.read_text());v['tasks'][S2]['status']='DONE_PUBLISHED';file.write_text(json.dumps(v))
        self.assertEqual(self.query(S2)['status'],'INDEX_TAMPERED')
    def test_remote_document_change_rejects_cached_excerpt(self):
        self.remote.files[self.doc.relative_to(self.root).as_posix()]=b'# Other\nChanged'
        self.assertEqual(self.query('Documentation')['status'],'STALE_INDEX_REMOTE_DOCUMENT')
    def test_source_acl_and_small_budget(self):
        self.assertEqual(self.query('Documentation',source_class='ARCHIVED_SOURCE')['status'],'ACCESS_DENIED_SOURCE_CLASS')
        self.assertEqual(self.query(S2,max_chars=1)['status'],'INVALID_BUDGET')
        self.assertLessEqual(len(K.components()['graph'].canonical(self.query(S2,max_chars=900))),900)
    def test_disabled_flag_does_not_read_source(self):
        self.assertEqual(APA.retrieve_project_knowledge({'enabled':False},S2)['status'],'FEATURE_DISABLED')
    def test_explicit_source_fragment_and_no_path_escape(self):
        r=APA.inspect_project_knowledge(self.cfg,'source',{'path':self.doc.relative_to(self.root).as_posix(),'line':1,'count':2},self.remote)
        self.assertEqual(r['status'],'EXPLICIT_SOURCE_FRAGMENT')
        r=APA.inspect_project_knowledge(self.cfg,'source',{'path':'../../secret'},self.remote);self.assertEqual(r['status'],'SOURCE_OR_RELATION_NOT_VERIFIED')
    def test_delta_reports_actual_status_change(self):
        before=copy.deepcopy(self.plan);before['tasks'][S2]['status']='READY'
        r=APA.inspect_project_knowledge(self.cfg,'delta',{'before':before},self.remote);self.assertEqual(r['items'][0]['changes'][0]['id'],S2)
    def test_unverified_relationship_does_not_propagate(self):
        fields={k:{'project_class':'residential.izhs','task_id':S2} for k in ['a','b']}
        lineage={'schema':'APA_FIELD_LINEAGE_V1','fields':fields,'edges':[{'from':'a','to':'b','kind':'REFERENCES','verification':'UNVERIFIED','project_class':'residential.izhs'}]}
        r=APA.inspect_project_knowledge(self.cfg,'fields',{'lineage':lineage,'change':{'field_id':'a','project_class':'residential.izhs','before':1,'after':2}},self.remote)
        self.assertEqual(r['status'],'UNVERIFIED_RELATIONSHIP');self.assertEqual(r['items'][0]['verified_impacts'],[])
    def test_cross_building_trace_default_deny(self):
        r=APA.inspect_project_knowledge(self.cfg,'tdk-trace',{'project_class':'residential.mkd'},self.remote);self.assertEqual(r['status'],'SOURCE_OR_RELATION_NOT_VERIFIED')
    def test_corrupt_remote_contents_digest_is_rejected(self):
        import io
        def opener(*a,**kw):return io.BytesIO(json.dumps({'encoding':'base64','path':K.PLAN,'content':'e30=','sha':'f'*40}).encode())
        with self.assertRaisesRegex(ValueError,'SOURCE_BYTE_MISMATCH'):K.GitHubSource(opener=opener).read(K.PLAN,'a'*40)
    def test_crlf_source_is_not_claimed_byte_exact(self):
        path=self.doc.relative_to(self.root).as_posix();canonical=self.doc.read_bytes()
        self.doc.write_bytes(canonical.replace(b'\n',b'\r\n'));self.remote.files[path]=canonical
        r=APA.inspect_project_knowledge(self.cfg,'source',{'path':path},self.remote)
        self.assertEqual(r['items'][0]['byte_status'],'CHECKOUT_CRLF_GITHUB_LF_ONLY')
        self.assertEqual(r['items'][0]['sha256'],__import__('hashlib').sha256(canonical).hexdigest())
    def test_unavailable_remote_does_not_fall_back_to_local_authority(self):
        def unavailable():raise OSError('unreachable')
        self.remote.head=unavailable;self.assertEqual(self.query(S2)['status'],'SOURCE_UNAVAILABLE_OR_INVALID')
    def test_local_mode_is_explicit_and_no_git_calls(self):
        cfg={**self.cfg,'source_mode':'LOCAL_CHECKOUT'}
        r=APA.retrieve_project_knowledge(cfg,S2);self.assertEqual(r['authority'],'LOCAL_CHECKOUT_PLAN_ONLY')

if __name__=='__main__':unittest.main()
