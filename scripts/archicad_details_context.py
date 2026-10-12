"""Details v2.12 source joins and applicability over the shared native context.

All73context records are evaluated independently. Source compile gates are
retained; a geometric candidate does not certify a manufacturer assembly.
"""
import base64,copy,hashlib,io,json,tarfile
from pathlib import Path
import networkx as nx
from shapely.geometry import box
import archicad_connected_components as C


class DetailsContext:
    def __init__(self,root):
        blob=base64.b64decode((Path(root)/'details/releases/v2.12/machine-state-v2.12.tar.gz.b64').read_bytes())
        if hashlib.sha256(blob).hexdigest()!=C.DETAILS_SHA:raise ValueError('DETAILS_SOURCE_HASH_MISMATCH')
        with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as t:
            def read(name,lines=False):
                member=t.getmember(name)
                if not member.isfile() or member.size>20000000:raise ValueError('DETAILS_MEMBER_INVALID')
                f=t.extractfile(member);return [json.loads(l) for l in f if l.strip()] if lines else json.load(f)
            active=read('details_active_v2.12.jsonl',True)
            self.records={r['context_detail_id']:r for r in active if 'context_detail_id' in r}
            if len(self.records)!=73:raise ValueError('CONTEXT_ID_COVERAGE_OR_DUPLICATE')
            self.facts={r['fact_id']:r for r in read('parameter_facts_v2.12.jsonl',True)}
            self.sources={r['source_id']:r for r in read('sources_v2.12.json')}
            self.checks=read('SOURCE_VERIFY_FULL_v2.12.json')['representation_checks']
        for identifier,r in self.records.items():
            source_id=identifier.split('__')[0]
            source=self.sources[source_id];representation=r['source_locator']['representation']
            declared=[p for p in json.loads(source['representations_json']) if p['name']==representation]
            checked=[p for p in self.checks if p['source_id']==source_id and p['name']==representation]
            if len(declared)!=1 or len(checked)!=1 or not checked[0]['match'] or declared[0]['sha256']!=checked[0]['actual_sha256']:
                raise ValueError('CONTEXT_SOURCE_REPRESENTATION_MISMATCH')
            if r['source_locator']['page']!=r['pdf_page']:raise ValueError('CONTEXT_PAGE_MISMATCH')
            refs=set(r['inherited_fact_ids'])
            for entity in r['components']+r['context_entities']:refs.update(entity.get('source_parameter_fact_refs',[]))
            for op in r['operation_graph']:refs.update(op.get('fact_refs',[]))
            if any(ref not in self.facts or self.facts[ref]['source_id']!=source_id for ref in refs):raise ValueError('CONTEXT_DANGLING_OR_CROSS_SOURCE_FACT')

    def evaluate(self,context,product_bindings=None):
        if context['units']!='m' or context['coordinateSystem']!='ABSOLUTE_PROJECT_XYZ':raise ValueError('DETAILS_REQUIRES_NATIVE_WORLD_METRES')
        product_bindings=product_bindings or {};elements=context['elements'];graph=nx.Graph()
        for sid,e in elements.items():
            if not C.RUN._GUID.fullmatch(e['guid']):raise ValueError('DETAILS_NATIVE_GUID_INVALID')
            graph.add_node(sid,**{k:e.get(k) for k in ['guid','kind','floorIndex','hostGuid','materialBindings']})
        # Native body bounds provide a conservative candidate screen; no invented
        # exact joint or bearing-capacity inference from a bounding box.
        for sid,a in elements.items():
            for tid,b in elements.items():
                if sid>=tid:continue
                linked=a.get('hostGuid','')==b['guid'] or b.get('hostGuid','')==a['guid']
                near=any(box(x[0][0],x[1][0],x[0][1],x[1][1]).distance(box(y[0][0],y[1][0],y[0][1],y[1][1]))<.01
                    and min(x[2][1],y[2][1])-max(x[2][0],y[2][0])>=-.01 for x in a.get('bounds',[]) for y in b.get('bounds',[]))
                if linked or near:graph.add_edge(sid,tid,evidence='NATIVE_HOST' if linked else 'NATIVE_AABB_CANDIDATE')
        rows=[]
        for identifier,r in self.records.items():
            matches=[]
            for sid,wall in elements.items():
                if wall['kind']!='Wall':continue
                product=product_bindings.get(wall['guid'],{})
                material_verified=(product.get('nativeMaterialBindings')==wall.get('materialBindings') and bool(product.get('nativeMaterialBindings')))
                source_product=product.get('sourceProduct')
                reasons=[]
                if source_product not in r['source_products_in_title'] or not material_verified:reasons.append('SOURCE_PRODUCT_OR_NATIVE_MATERIAL_UNRESOLVED')
                neighbors=list(graph.neighbors(sid))
                wanted={e['preferred_archicad_tool'] for e in r['context_entities'] if e.get('required')}
                bound=[t for t in neighbors if elements[t]['kind'] in wanted]
                if wanted and not all(any(elements[t]['kind']==kind for t in bound) for kind in wanted):reasons.append('REQUIRED_GEOMETRIC_CONTEXT_MISSING')
                matches.append({'hostGuid':wall['guid'],'hostStepId':sid,'floorIndex':wall['floorIndex'],
                    'nativeBoundsMeters':wall['bounds'],'nativeMaterialBindings':wall.get('materialBindings',{}),
                    'contextGuids':[elements[t]['guid'] for t in bound],'sourceProduct':source_product,
                    'applicability':'CANDIDATE_CONTEXT_MATCH' if not reasons else 'NOT_APPLICABLE_OR_UNRESOLVED','reasons':reasons})
            refs=set(r['inherited_fact_ids'])
            for e in r['components']+r['context_entities']:refs.update(e.get('source_parameter_fact_refs',[]))
            for op in r['operation_graph']:refs.update(op.get('fact_refs',[]))
            rows.append({'detailId':identifier,'sourceId':identifier.split('__')[0],'sourceLocator':r['source_locator'],
                'junctionType':r['junction_type'],'wallTypeId':r['wall_type_id'],'bindings':matches,
                'resolvedFacts':[{'factId':ref,'unit':self.facts[ref]['normalized_unit'],'values':json.loads(self.facts[ref]['value_json'])} for ref in sorted(refs)],
                'relations':r['relations'],'operationGraph':r['operation_graph'],'compileBlockers':list(r['compile_blockers']),
                'assemblyWriteAllowed':False,'sourceCommitAllowed':r['commit_allowed'],'engineeringAcceptance':'NOT_VERIFIED'})
        return {'schema':'APA_DETAILS_NATIVE_CONTEXT_V1','archiveSha256':C.DETAILS_SHA,'contextDetailCount':len(rows),
            'nativeContextHash':C.RUN.digest(context),'nativeGraphNodes':graph.number_of_nodes(),'nativeGraphEdges':graph.number_of_edges(),
            'details':rows,'scope':'Source-verified applicability/host/material/geometry/fact exchange; exact assembly source gates preserved',
            'engineeringAcceptance':'NOT_VERIFIED'}

    def exchange(self,result,detail_id,host_guid):
        rows=[r for r in result['details'] if r['detailId']==detail_id]
        if len(rows)!=1:raise ValueError('DETAIL_ID_NOT_UNIQUE')
        row=copy.deepcopy(rows[0]);bindings=[b for b in row['bindings'] if b['hostGuid']==host_guid]
        if len(bindings)!=1:raise ValueError('DETAIL_HOST_NOT_VERIFIED')
        row['bindings']=bindings;return row
