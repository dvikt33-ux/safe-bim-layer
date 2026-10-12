"""Small optional CP-SAT provider over already measured native body bounds.

Chooses among explicit straight-route candidates. This is neither a custom
pathfinder nor engineering clearance approval. Native collision readback is
required independently of the solver's conservative AABB feasibility screen.
"""
import math


def choose_straight_route(context,start_x,end_x,ys,z,half_width,half_height,
                          desired_y,clearance=0.05,time_limit=2.0):
    from ortools.sat.python import cp_model
    values=[start_x,end_x,z,half_width,half_height,desired_y,clearance,time_limit,*ys]
    if (not ys or len(set(ys))!=len(ys) or any(type(v) not in (int,float) or not math.isfinite(v) for v in values)
            or start_x>=end_x or half_width<=0 or half_height<=0 or clearance<0 or not 0<time_limit<=30):
        raise ValueError('STRAIGHT_ROUTE_CANDIDATES_INVALID')
    if context.get('coordinateSystem')!='ABSOLUTE_PROJECT_XYZ' or context.get('units')!='m':
        raise ValueError('SOLVER_REQUIRES_NATIVE_METRE_WORLD_CONTEXT')
    candidates=[]
    for y in ys:
        envelope=[(start_x-clearance,end_x+clearance),
            (y-half_width-clearance,y+half_width+clearance),
            (z-half_height-clearance,z+half_height+clearance)]
        blockers=[]
        for sid,element in context['elements'].items():
            if element['kind']=='MEPRouting':continue  # Existing route is the subject.
            for bounds in element.get('bounds',[]):
                if all(min(a[1],b[1])-max(a[0],b[0])>1e-7 for a,b in zip(envelope,bounds)):
                    blockers.append(sid);break
        candidates.append({'y':y,'blockedBy':blockers,'envelopeMeters':envelope})
    model=cp_model.CpModel();selected=[model.NewBoolVar('route_'+str(i)) for i in range(len(ys))]
    model.AddExactlyOne(selected)
    for i,candidate in enumerate(candidates):
        if candidate['blockedBy']:model.Add(selected[i]==0)
    # Explicit millimetre displacement preference, deterministic index tie-break.
    model.Minimize(sum((round(abs(y-desired_y)*1000)*(len(ys)+1)+i)*selected[i] for i,y in enumerate(ys)))
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=time_limit
    solver.parameters.num_search_workers=1;solver.parameters.random_seed=0
    status=solver.Solve(model)
    result={'status':solver.StatusName(status),'provider':'OR-Tools CP-SAT','candidates':candidates,
        'scope':'ONE_EXPLICIT_STRAIGHT_ROUTE_CANDIDATE_SET','nativeCollisionAcceptance':'NOT_VERIFIED',
        'engineeringAcceptance':'NOT_VERIFIED','elapsedSeconds':solver.WallTime()}
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        index=next(i for i,v in enumerate(selected) if solver.Value(v))
        result.update(selectedIndex=index,nodeCoordinates=[{'x':x,'y':ys[index],'z':z} for x in (start_x,end_x)])
    return result
