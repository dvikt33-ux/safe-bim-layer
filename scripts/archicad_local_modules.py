"""Local read/analysis adapters over installed libraries, not native writes."""
from pathlib import Path

def normalize_native(dump):
    import archicad_authored_geometry as G
    return G.normalize_dump(dump,allow_empty=True)

def native_quantities(elements):
    from archicad_connected_ifc import native_body_quantities
    return dict(elements=[dict(guid=e['guid'],quantities=native_body_quantities(e)) for e in elements],authority='EXISTING_NATIVE_BREP_ADAPTER',engineering='NOT_VERIFIED')

def dependency_impact(nodes,edges,changed):
    import networkx as nx
    if len(nodes)!=len(set(nodes)) or set(changed)-set(nodes) or any(len(e)!=2 or set(e)-set(nodes) for e in edges):raise ValueError('GRAPH_IDENTITY_OR_EDGE_INVALID')
    g=nx.DiGraph();g.add_nodes_from(nodes);g.add_edges_from(edges)
    if not nx.is_directed_acyclic_graph(g):return dict(status='CYCLIC',cycleWitness=[list(e) for e in nx.find_cycle(g)],executionAllowed=False)
    affected=set(changed)
    for node in changed:affected.update(nx.descendants(g,node))
    return dict(status='DAG',affected=sorted(affected),updateOrder=[n for n in nx.lexicographical_topological_sort(g) if n in affected],executionAllowed=False)

def polygon_relations(polygons,tolerance=0):
    from shapely.geometry import Polygon
    from shapely.strtree import STRtree
    ids=[row['id'] for row in polygons]
    if len(ids)!=len(set(ids)):raise ValueError('DUPLICATE_POLYGON_ID')
    shapes=[Polygon(p['outline'],p.get('holes',[])) for p in polygons]
    if any(not p.is_valid or p.is_empty for p in shapes):raise ValueError('INVALID_SOURCE_POLYGON')
    tree=STRtree(shapes);relations=[]
    for i,a in enumerate(shapes):
        for j in tree.query(a.buffer(tolerance) if tolerance else a):
            j=int(j)
            if j<=i:continue
            b=shapes[j]
            if a.distance(b)>tolerance:continue
            relations.append(dict(first=ids[i],second=ids[j],intersects=bool(a.intersects(b)),touches=bool(a.touches(b)),intersectionArea=float(a.intersection(b).area),distance=float(a.distance(b))))
    return dict(units='CALLER_COORDINATE_UNITS',polygons=[dict(id=k,area=float(p.area),perimeter=float(p.length)) for k,p in zip(ids,shapes)],relations=relations,scope='2D_SOURCE_POLYGONS_NOT_3D_NATIVE_COLLISION',engineering='NOT_VERIFIED')

def constrained_assignment(tasks,capacities,time_limit=2):
    from ortools.sat.python import cp_model
    if len({t['id'] for t in tasks})!=len(tasks) or any(set(t['costs'])-set(capacities) for t in tasks):raise ValueError('ASSIGNMENT_IDS_OR_SLOTS_INVALID')
    model=cp_model.CpModel();variables={}
    for task in tasks:
        choices=[]
        for slot in task['costs']:
            v=model.NewBoolVar(task['id']+'_'+slot);variables[task['id'],slot]=v;choices.append(v)
        model.AddExactlyOne(choices)
    for slot,capacity in capacities.items():model.Add(sum(v for (task,s),v in variables.items() if s==slot)<=capacity)
    model.Minimize(sum(t['costs'][s]*variables[t['id'],s] for t in tasks for s in t['costs']))
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=time_limit;solver.parameters.num_search_workers=1;solver.parameters.random_seed=0;status=solver.Solve(model)
    result=dict(status=solver.StatusName(status),assignment={},scope='EXPLICIT_INTEGER_COSTS_CAPACITIES_NO_DESIGN_INFERENCE',engineering='NOT_VERIFIED')
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):result.update(assignment={t['id']:next(s for s in t['costs'] if solver.Value(variables[t['id'],s])) for t in tasks},objective=solver.ObjectiveValue())
    return result

def _ifc(path):
    import ifcopenshell
    p=Path(path)
    if p.suffix.casefold() not in {'.ifc','.ifczip','.ifcxml'} or not p.is_file():raise ValueError('EXPLICIT_EXISTING_IFC_FILE_REQUIRED')
    return ifcopenshell.open(str(p))

def ifc_select(path,query):
    import ifcopenshell.util.selector
    import ifcopenshell.util.element
    model=_ifc(path);selected=ifcopenshell.util.selector.filter_elements(model,query)
    return dict(schema=model.schema,elements=[dict(ifcId=getattr(e,'GlobalId',None),stepId=e.id(),type=e.is_a(),name=getattr(e,'Name',None),properties=ifcopenshell.util.element.get_psets(e)) for e in sorted(selected,key=lambda e:e.id())],semanticCompatibility='NOT_VERIFIED')

def ifc_validate(path,express_rules=False):
    import ifcopenshell.validate
    model=_ifc(path);logger=ifcopenshell.validate.json_logger();ifcopenshell.validate.validate(model,logger,express_rules=express_rules)
    return dict(schema=model.schema,status='IFC_SCHEMA_VALID' if not logger.statements else 'IFC_SCHEMA_ISSUES',issues=[{k:str(v) for k,v in row.items()} for row in logger.statements],scope='IFC_SCHEMA_ATTRIBUTES_EXPRESS_NOT_ENGINEERING_ACCEPTANCE')

def ifc_geometry(path,guids):
    import ifcopenshell.geom
    import ifcopenshell.util.shape
    model=_ifc(path);settings=ifcopenshell.geom.settings();settings.set(settings.USE_WORLD_COORDS,True);rows=[]
    for guid in guids:
        row=dict(ifcId=guid)
        try:
            e=model.by_guid(guid);shape=ifcopenshell.geom.create_shape(settings,e);v=shape.geometry.verts;row.update(status='IFC_GEOMETRY_COMPUTED',bounds=[[min(v[i::3]),max(v[i::3])] for i in range(3)],area=ifcopenshell.util.shape.get_area(shape.geometry),volume=ifcopenshell.util.shape.get_volume(shape.geometry),source='IfcOpenShell geometry kernel')
        except (RuntimeError,ValueError) as exc:row.update(status='IFC_GEOMETRY_NOT_AVAILABLE',reason=str(exc))
        rows.append(row)
    return dict(elements=rows,scope='IFC_KERNEL_GEOMETRY_NOT_NATIVE_ARCHICAD_ACCEPTANCE',engineering='NOT_VERIFIED')

def ifc_exchange(path):
    from archicad_connected_ifc import inspect_exchange_semantics
    return inspect_exchange_semantics(path)

def attach(router,manifest):
    """Only code-owned entry points; catalog input cannot import arbitrary code."""
    import hashlib,importlib.metadata
    expected=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if manifest['implementationSHA256']!=expected:raise ValueError('LOCAL_MODULE_SOURCE_DRIFT')
    names={'NormalizeNativeDump':normalize_native,'NativeBodyQuantities':native_quantities,'DependencyImpact':dependency_impact,'PolygonRelations':polygon_relations,'ConstrainedAssignment':constrained_assignment,'IFCSelect':ifc_select,'IFCValidate':ifc_validate,'IFCGeometry':ifc_geometry,'IFCExchangeFacts':ifc_exchange}
    present={'AddOn.APAAnalysis.'+n for n in names}&set(router.catalog['commands'])
    if present:
        if len(present)!=len(names):raise ValueError('PARTIAL_LOCAL_MODULE_ATTACHMENT')
        for name,row in manifest['commands'].items():
            current=router.catalog['commands']['AddOn.APAAnalysis.'+name]
            if current.get('implementationSHA256')!=expected or any(current.get(k)!=row[k] for k in ['parameters','returns','version']):raise ValueError('LOCAL_MODULE_CONTRACT_DRIFT')
    else:
        router.add_local_provider('APAAnalysis',manifest['commands'],names,'archicad_local_modules.py',manifest['dependencies'])
    for name in names:router.catalog['commands']['AddOn.APAAnalysis.'+name]['implementationSHA256']=expected
    for name,row in manifest['commands'].items():router.review_policy('AddOn.APAAnalysis.'+name,'READ_ONLY','READ_ONLY',dict(source='Installed library public API + existing APA adapter; local only, no native write',sha256=expected))
    return dict(status='LOCAL_MODULES_CONNECTED',functions=len(names),newNativeCommands=0)
