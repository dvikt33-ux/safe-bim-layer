"""Read-only batch adapter over existing native geometry and Details coverage."""
import argparse
import json
from pathlib import Path
import networkx as nx
import archicad_native_operations as N


def assess_batch(native,targets,details,links,coverage=None):
    if native.get('units')!='m' or native.get('coordinateSystem')!='ABSOLUTE_PROJECT_XYZ':
        raise ValueError('JUNCTIONS_REQUIRE_ACTUAL_NATIVE_WORLD_METRES')
    bodies={e['guid'].lower():e for e in native['elements']}
    graph=nx.DiGraph();rows=[];seen=set()
    source_family=next((f for f in (coverage or {}).get('families',[]) if f['family']=='wall_roof'),{})
    for target in targets:
        wall=target['wallGuid'].lower();roof=target['roofGuid'].lower()
        if wall in seen:raise ValueError('DUPLICATE_JUNCTION_WALL_TARGET')
        seen.add(wall)
        if wall not in bodies or roof not in bodies:raise ValueError('JUNCTION_NATIVE_TARGET_MISSING')
        row=N.assess_wall_roof_junction(bodies[wall],bodies[roof],details[wall],details[roof],links[wall])
        row['junctionId']=target['id']
        row['existingDetailsSourceCandidates']=source_family.get('sourceCandidates',[])
        row['sourceScope']='Existing Details/CSE coverage only; geometry does not verify source assembly or load transfer'
        # Keep the assessment hash bound to the final source-linked payload.
        row['assessmentHash']=N.C.RUN.digest({k:v for k,v in row.items() if k!='assessmentHash'})
        rows.append(row)
        graph.add_edge(roof,wall,dependency='ACTUAL_SHARED_ROOF_LOWER_FACE')
    return {'schema':'APA_WALL_ROOF_BATCH_V1','nativeWrites':0,'repairExecuted':False,
        'junctions':rows,'statuses':{status:sum(r['status']==status for r in rows)
            for status in ('VERIFIED','APPLICABLE_NOT_EXECUTED','NOT_APPLICABLE','NOT_VERIFIED')},
        'sharedDependencyGraph':{'nodes':sorted(graph.nodes),'edges':[list(e) for e in sorted(graph.edges)],
            'acyclic':nx.is_directed_acyclic_graph(graph)},
        'engineeringAcceptance':'ENGINEERING_NOT_VERIFIED'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path,help='Local captured native/target/details/link data')
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();data=json.loads(args.input.read_text(encoding='utf8'))
    result=assess_batch(data['native'],data['targets'],data['details'],data['links'],data.get('coverage'))
    args.output.write_bytes((json.dumps(result,ensure_ascii=False,indent=2)+'\n').encode())
    print(json.dumps({'junctions':len(result['junctions']),'statuses':result['statuses'],'nativeWrites':0}))


if __name__=='__main__':main()
