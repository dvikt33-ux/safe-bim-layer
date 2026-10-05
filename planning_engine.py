"""Offline deterministic rectangular planning. No normative lookup or BIM execution."""
from copy import deepcopy
from itertools import product
import math

from constraint_compilation import ConstraintCompilation
from functional_program import FunctionalProgram
from design_stage0 import fingerprint

FLOW = ["REQUIRE VERIFIED CONSTRAINT COMPILATION", "READ FUNCTIONAL SPACES",
        "READ MANDATORY CONSTRAINTS", "READ PREFERENCES", "READ SITE FACTS",
        "DETERMINE FLOOR SET", "ASSIGN SPACES TO FLOORS", "BUILD RELATIONSHIP GRAPH",
        "GENERATE INITIAL RECTANGULAR LAYOUT", "RESOLVE OVERLAPS", "CREATE CIRCULATION",
        "CHECK HARD CONSTRAINTS SUPPORTED BY V0", "SCORE PREFERENCES", "AUDIT CANDIDATE",
        "RETURN BEST VALID CANDIDATE"]
RELATIONS = {"REQUIRED_ADJACENCY", "PREFERRED_ADJACENCY", "AVOID_ADJACENCY",
             "REQUIRED_ACCESS", "EXTERNAL_ACCESS", "VERTICAL_CONNECTION", "SEPARATION_REQUIRED"}
NUMERIC_OPS = {"eq", "neq", "gt", "gte", "lt", "lte"}
POLICY = dict(policyId="rectangular-planner-v0", revision="1", basisType="PLANNER_HEURISTIC",
              defaultAspectRatios=[1.0, 1.25, 1.5, 2.0], defaultRoomArea=12.0,
              circulationWidth=1.2, adjacencyEpsilon=0.01, numericTolerance=1e-7,
              maxCandidates=24, maxGenerationAttempts=72, maxImprovementPasses=4, maxPlacementAttempts=64,
              maxSpaces=128, maxFloors=16,
              floorAliases={"ground":"floor-1", "upper":"floor-2"},
              scoringRegistry=dict(revision="1", weights={"COMPACTNESS":1.0,
                  "SPACIOUSNESS":1.0, "STRUCTURAL_REGULARITY":1.0, "REQUESTED_AREA":1.0,
                  "PREFERRED_ADJACENCY":2.0, "AVOID_ADJACENCY":2.0, "SPACE_LOCATION":1.0}))
CAPABILITY_REGISTRY = dict(revision="1", supported={
    "SPACE_AREA":"m2 numeric per instance", "BUILDING_WIDTH":"m numeric global envelope",
    "BUILDING_DEPTH":"m numeric global envelope", "FLOOR_COUNT":"count",
    "SPACE_QUANTITY":"count", "SPACE_EXISTS":"boolean", "SPACE_FUNCTION":"program function",
    "SPACE_LOCATION":"explicit FLOOR reference", "RELATIONSHIP":"declared rectangle/access semantics",
    "OBJECT":"explicit preserved point/rectangle", "ZONE":"explicit prohibited rectangle",
    "SITE_PLACEMENT":"axis-aligned rectangular boundary"},
    deferredDomains={"MATERIAL":"BIM material assignment", "STRUCTURE":"structural design",
                     "EQUIPMENT":"equipment / MEP", "PARKING":"parking design"},
    deferredSubjects={"CLIENT_BUDGET":"cost model", "PHASING":"construction phasing",
                      "USER_COUNT":"occupancy analysis", "USER_LABEL":"occupancy metadata",
                      "ACCESSLEVEL":"access policy", "PRIVACYLEVEL":"privacy assessment",
                      "NOISESENSITIVITY":"acoustics", "NOISEGENERATION":"acoustics",
                      "DAYLIGHTPREFERENCE":"daylight simulation", "FUNCTIONALZONE":"zone metadata"},
    deferredDownstreamScopes=["BIM_TRANSLATOR","ARCHICAD_EXECUTION","STRUCTURAL_DESIGN",
                              "MEP_DESIGN","COST_ESTIMATION","MATERIAL_ASSIGNMENT"],
    unknown="UNSUPPORTED")


def number(v):
    return type(v) in (float, int) and math.isfinite(v)


def policy_checked(p):
    p = deepcopy(p)
    if not isinstance(p, dict) or set(p) != set(POLICY):
        raise ValueError("strict declarative planner policy; expressions forbidden")
    if p["basisType"] != "PLANNER_HEURISTIC" or not all(isinstance(p[k], str) and p[k] for k in ("policyId", "revision")):
        raise ValueError("versioned heuristic policy required")
    for k in ("defaultRoomArea", "circulationWidth", "adjacencyEpsilon", "numericTolerance"):
        if not number(p[k]) or p[k] <= 0: raise ValueError("positive finite policy values required")
    if p["numericTolerance"] >= p["adjacencyEpsilon"]: raise ValueError("numeric tolerance below adjacency epsilon required")
    for k, limit in (("maxCandidates",256), ("maxGenerationAttempts",4096), ("maxImprovementPasses",32), ("maxPlacementAttempts",4096), ("maxSpaces",1024), ("maxFloors",128)):
        if type(p[k]) is not int or not 1 <= p[k] <= limit: raise ValueError("bounded integer search limits required")
    ratios = p["defaultAspectRatios"]
    if not isinstance(ratios,list) or not 1 <= len(ratios) <= 16 or any(not number(x) or x <= 0 for x in ratios):
        raise ValueError("bounded positive aspect ratios required")
    if not isinstance(p["floorAliases"],dict) or any(not isinstance(k,str) or not isinstance(v,str) for k,v in p["floorAliases"].items()):
        raise ValueError("explicit floor aliases required")
    reg = p["scoringRegistry"]
    if not isinstance(reg,dict) or set(reg) != {"revision","weights"} or not isinstance(reg["revision"],str) or set(reg["weights"]) != set(POLICY["scoringRegistry"]["weights"]) or any(not number(x) or x < 0 for x in reg["weights"].values()):
        raise ValueError("versioned declarative scoring weights required")
    return p


def accept(c, actual, tolerance):
    op,v = c["operator"],c["value"]
    if op in NUMERIC_OPS and number(v) and number(actual):
        return {"eq":lambda:abs(actual-v)<=tolerance, "neq":lambda:abs(actual-v)>tolerance,
                "gt":lambda:actual>v+tolerance, "gte":lambda:actual>=v-tolerance,
                "lt":lambda:actual<v-tolerance, "lte":lambda:actual<=v+tolerance}[op]()
    if op in {"eq","require","preserve"}: return actual == v
    if op in {"neq","prohibit"}: return actual != v
    if op in {"in","not_in"}: return (actual in v) == (op == "in")
    return False


def shared_boundary(a,b,tol=1e-7):
    if a["floorId"] != b["floorId"]: return 0.0
    if abs(a["x"]+a["width"]-b["x"])<=tol or abs(b["x"]+b["width"]-a["x"])<=tol:
        return max(0.0,min(a["y"]+a["depth"],b["y"]+b["depth"])-max(a["y"],b["y"]))
    if abs(a["y"]+a["depth"]-b["y"])<=tol or abs(b["y"]+b["depth"]-a["y"])<=tol:
        return max(0.0,min(a["x"]+a["width"],b["x"]+b["width"])-max(a["x"],b["x"]))
    return 0.0


def overlap(a,b,tol=1e-7):
    return a["floorId"] == b["floorId"] and min(a["x"]+a["width"],b["x"]+b["width"])-max(a["x"],b["x"])>tol and min(a["y"]+a["depth"],b["y"]+b["depth"])-max(a["y"],b["y"])>tol


def exterior_edges(room,env,tol):
    return [name for name,yes in (("WEST",abs(room["x"])<=tol), ("SOUTH",abs(room["y"])<=tol),
        ("EAST",abs(room["x"]+room["width"]-env["width"])<=tol),
        ("NORTH",abs(room["y"]+room["depth"]-env["depth"])<=tol)) if yes]


def rectangle(geom):
    """Only a confirmed metre rectangle (or point obstacle), never a polygon bbox substitute."""
    if geom.get("unit") != "m": raise ValueError("unsupported site units")
    coords = geom["coordinates"]
    if geom["type"] == "Point":
        if len(coords)!=2 or not all(number(x) for x in coords): raise ValueError("invalid point")
        return (coords[0],coords[1],coords[0],coords[1])
    if geom["type"] != "Polygon" or len(coords)!=1 or len(coords[0])!=5 or coords[0][0]!=coords[0][-1]:
        raise ValueError("rectangular site polygons only")
    pts = coords[0][:-1]
    if any(len(p)!=2 or not all(number(v) for v in p) for p in pts): raise ValueError("invalid polygon")
    xs,ys = sorted({p[0] for p in pts}),sorted({p[1] for p in pts})
    if len(xs)!=2 or len(ys)!=2 or set(map(tuple,pts))!=set(product(xs,ys)) or any(a[0]!=b[0] and a[1]!=b[1] for a,b in zip(coords[0],coords[0][1:])):
        raise ValueError("axis-aligned rectangular site polygons only")
    return xs[0],ys[0],xs[1],ys[1]


def intersects_closed(a,b):
    return min(a[2],b[2]) >= max(a[0],b[0]) and min(a[3],b[3]) >= max(a[1],b[1])


def capability(c):
    s,d,op,u = c["subject"],c["domain"],c["operator"],c["unit"]
    prefix = s.split(":")[0]
    if prefix in {"SPACE_AREA","SPACE_QUANTITY","SPACE_EXISTS","SPACE_FUNCTION","SPACE_LOCATION"}:
        if ":" not in s or not s.split(":",1)[1]: return "UNSUPPORTED","explicit measured program space ID required"
        target="SPACE:"+s.split(":",1)[1]
        if any(x not in {"PROJECT","BUILDING",target} for x in c["scope"]):
            return "UNSUPPORTED","scope does not identify the measured program space"
    if d in CAPABILITY_REGISTRY["deferredDomains"]:
        return "NOT_PLANNING_DOMAIN",CAPABILITY_REGISTRY["deferredDomains"][d]
    if prefix in CAPABILITY_REGISTRY["deferredSubjects"]:
        return "NOT_PLANNING_DOMAIN",CAPABILITY_REGISTRY["deferredSubjects"][prefix]
    # Explicit downstream exclusion is retained; unrecognized planning domains fail closed.
    reqs = [r.get("originalRequirement",{}) for r in c.get("sourceRefs",[]) if r.get("originalRequirement")]
    if reqs and all(r.get("downstreamDomains") and set(r["downstreamDomains"])<=set(CAPABILITY_REGISTRY["deferredDownstreamScopes"]) for r in reqs):
        return "NOT_PLANNING_DOMAIN","explicit normative downstream domains exclude planning"
    units = {"SPACE_AREA":"m2","BUILDING_WIDTH":"m","BUILDING_DEPTH":"m","FLOOR_COUNT":"count","SPACE_QUANTITY":"count"}
    if prefix in units and u == units[prefix] and op in NUMERIC_OPS and number(c["value"]):
        if prefix in {"BUILDING_WIDTH","BUILDING_DEPTH","FLOOR_COUNT"} and any(x not in {"PROJECT","BUILDING"} for x in c["scope"]):
            return "UNSUPPORTED","only global envelope/floor count supported"
        return "SUPPORTED",CAPABILITY_REGISTRY["supported"][prefix]
    if prefix in {"SPACE_EXISTS","SPACE_FUNCTION","SPACE_LOCATION"} and u=="none" and op in {"require","eq","neq","prohibit","in","not_in"}:
        return "SUPPORTED",CAPABILITY_REGISTRY["supported"][prefix]
    if prefix=="RELATIONSHIP" and isinstance(c["value"],str) and c["value"] in RELATIONS and op in {"require","eq"}: return "SUPPORTED","rectangle/access relationship"
    if d=="SITE" and ((prefix=="OBJECT" and op=="preserve" and c["value"]=="EXISTING_OBJECT") or (prefix=="ZONE" and op=="prohibit" and c["value"]=="SITE_ZONE")):
        return "SUPPORTED","verified site obstacle"
    if s=="SITE_PLACEMENT" and u=="none" and op=="require" and c["value"] in (True,"REQUIRED"):
        return "SUPPORTED","rectangular site placement"
    return "UNSUPPORTED","no v0 evaluator for this subject/unit/operator"


def candidate_fingerprint(candidate,input_fp,policy_fp):
    v=deepcopy(candidate); v.pop("candidateFingerprint",None)
    return fingerprint(dict(candidate=v,constraintCompilationFingerprint=input_fp,plannerPolicyFingerprint=policy_fp))


class PlanningEngine:
    def __init__(self,compilation,functional_program,policy=None):
        if not isinstance(compilation,ConstraintCompilation) or not isinstance(functional_program,FunctionalProgram):
            raise TypeError("live ConstraintCompilation and referenced FunctionalProgram required")
        self._compilation,self._program=compilation,functional_program
        self._policy=policy_checked(POLICY if policy is None else policy)
        self._result=None

    def update_policy(self,policy):
        checked=policy_checked(policy)
        if checked!=self._policy:
            self._policy=checked
            if self._result: self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="PLANNER_POLICY_CHANGED")

    def _inputs(self):
        self._compilation.require_verified(); inp=self._compilation.planning_input(); cc=self._compilation.result()
        self._program.require_verified(); fp=self._program.result()
        if fingerprint({k:v for k,v in fp.items() if k!="programFingerprint"})!=fp["programFingerprint"]:
            raise ValueError("referenced Functional Program artifact integrity mismatch")
        if inp!=cc["planningInput"] or inp["sourceCompilationFingerprint"]!=cc["constraintCompilationFingerprint"] or inp["functionalProgramRef"]!=fp["programFingerprint"]:
            raise ValueError("planningInput fingerprint/reference mismatch")
        return inp,fp

    def _refresh(self):
        if self._result and self._result["status"]=="VERIFIED":
            try:
                inp,_=self._inputs()
                same=inp["sourceCompilationFingerprint"]==self._result["constraintCompilationFingerprint"] and fingerprint(self._policy)==self._result["plannerPolicyFingerprint"]
            except (ValueError,RuntimeError,KeyError): same=False
            if not same: self._result.update(status="INVALIDATED",canProgress=False,invalidationReason="COMPILATION_OR_PROGRAM_CHANGED")

    def result(self):
        self._refresh(); return deepcopy(self._result)

    def require_verified(self):
        self._refresh()
        if not self._result or self._result["status"]!="VERIFIED" or not self._result["canProgress"]:
            raise RuntimeError("Planning Engine progression blocked")
        # Rerun generation and independent audit against live exact inputs. Stored/copied claims are not evidence.
        fresh=self._compute()
        if fresh["status"]!="VERIFIED" or fresh!=self._result:
            raise RuntimeError("Planning Engine result integrity/re-audit failed")
        return deepcopy(fresh["gateProof"])

    def selected_candidate(self):
        self.require_verified(); return deepcopy(self._result["selectedCandidate"])

    def _prepare(self,inp,fp):
        p=self._policy; mandatory=inp["mandatoryConstraints"]
        n=fp["stage0Context"].get("floor_count",{}).get("value")
        if type(n) is not int or not 1<=n<=p["maxFloors"]: raise ValueError("verified bounded floor count required")
        floors=["floor-"+str(i) for i in range(1,n+1)]
        rooms=[]; ids=set()
        for s in fp["spaces"]:
            if s["spaceId"] in ids or type(s["quantity"]) is not int or s["quantity"]<1: raise ValueError("duplicate/invalid program spaces")
            ids.add(s["spaceId"])
            for i in range(s["quantity"]):
                sid=s["spaceId"] if s["quantity"]==1 else s["spaceId"]+"#"+str(i+1)
                rooms.append(dict(spaceId=sid,programSpaceId=s["spaceId"],function=s["function"],area=p["defaultRoomArea"],floorId=floors[0],fixedFloor=False))
        if len(rooms)>p["maxSpaces"] or not rooms: raise ValueError("bounded nonempty room program required")
        constraints={r["spaceId"]:[c for c in mandatory if c["subject"].endswith(":"+r["programSpaceId"])] for r in rooms}
        for r in rooms:
            cs=constraints[r["spaceId"]]; areas=[c for c in cs if c["subject"].startswith("SPACE_AREA:")]
            # Nonbinding requested area supplies a search target, never a hard bound.
            preferred=[c for c in inp["preferences"] if c["subject"]=="SPACE_AREA:"+r["programSpaceId"] and number(c["value"])]
            targets=[c["value"] for c in preferred+areas if c["operator"] in {"eq","gte","gt"}]
            target=max(targets) if targets else r["area"]
            lower=max([p["numericTolerance"]*10]+[c["value"]+(p["numericTolerance"]*2 if c["operator"]=="gt" else 0) for c in areas if c["operator"] in {"gte","gt","eq"}])
            upper=min([math.inf]+[c["value"]-(p["numericTolerance"]*2 if c["operator"]=="lt" else 0) for c in areas if c["operator"] in {"lte","lt","eq"}])
            r["area"]=min(max(target,lower),upper)
            if not number(r["area"]) or r["area"]<=0 or not all(accept(c,r["area"],p["numericTolerance"]) for c in areas): raise ValueError("NO_VALID_PLAN_FOUND: impossible area")
            locations=[c for c in cs if c["subject"].startswith("SPACE_LOCATION:")]
            allowed=[f for f in floors if all(accept(c,"FLOOR:"+f,p["numericTolerance"]) for c in locations)]
            if not allowed: raise ValueError("NO_VALID_PLAN_FOUND: incompatible floor requirements")
            preferred_floor=next((self._policy["floorAliases"].get(c["value"],str(c["value"]).removeprefix("FLOOR:")) for c in inp["preferences"] if c["subject"]=="SPACE_LOCATION:"+r["programSpaceId"] and isinstance(c["value"],str)),None)
            r["floorId"]=preferred_floor if preferred_floor in allowed else allowed[0]
            r["fixedFloor"]=bool(locations)
        # Required adjacency is assigned to one floor unless an explicit floor prevents it.
        relations=[c for c in mandatory+inp["preferences"] if c["subject"].startswith("RELATIONSHIP:")]
        for _ in range(p["maxImprovementPasses"]):
            changed=False
            for c in relations:
                if c["strength"]!="MANDATORY" or c["value"]!="REQUIRED_ADJACENCY": continue
                a,b=self._endpoints(c,rooms)
                for x,y in product(a,b):
                    if x["floorId"]!=y["floorId"]:
                        if x["fixedFloor"] and y["fixedFloor"]: continue
                        mover,target=(y,x) if x["fixedFloor"] or not y["fixedFloor"] else (x,y)
                        loc=[z for z in constraints[mover["spaceId"]] if z["subject"].startswith("SPACE_LOCATION:")]
                        if all(accept(z,"FLOOR:"+target["floorId"],p["numericTolerance"]) for z in loc):
                            mover["floorId"]=target["floorId"]; changed=True
            if not changed: break
        return floors,rooms,relations

    @staticmethod
    def _endpoints(c,rooms):
        parts=c["subject"].split(":",3)
        if len(parts)!=4: raise ValueError("malformed relationship")
        _,typ,a,b=parts
        if typ!=c["value"]: raise ValueError("relationship type mismatch")
        groups=[[r for r in rooms if r["programSpaceId"]==s] for s in (a,b)]
        if not groups[0] or (not groups[1] and not (typ=="EXTERNAL_ACCESS" and b=="EXTERIOR")):
            raise ValueError("dangling relationship")
        return groups

    def _basis(self,cs,policy="rectangular-planner-v0"):
        return [dict(compiledConstraintId=c["compiledConstraintId"]) for c in cs]+[dict(basisType="PLANNER_HEURISTIC",policyId=policy,plannerPolicyFingerprint=fingerprint(self._policy))]

    def _generate(self,inp,fp,floors,templates,relations,strategy,ratio_index,columns):
        p=self._policy; degree={r["spaceId"]:0 for r in templates}
        for c in relations:
            a,b=self._endpoints(c,templates)
            for r in a+b: degree[r["spaceId"]]+=1
        placed=[]; circulation=[]; decisions=[]; links=[]
        for floor in floors:
            rooms=[deepcopy(r) for r in templates if r["floorId"]==floor]
            key=lambda r:(not r["fixedFloor"],-degree[r["spaceId"]],-r["area"],r["spaceId"])
            rooms.sort(key=key if strategy=="relationship-first" else lambda r:(not r["fixedFloor"],-r["area"],-degree[r["spaceId"]],r["spaceId"]))
            # Bounded adjacent swaps minimize hard relationship violations in strip order.
            def order_cost(seq):
                pos={r["programSpaceId"]:[i for i,x in enumerate(seq) if x["programSpaceId"]==r["programSpaceId"]] for r in seq}
                cost=0
                for c in relations:
                    if c["strength"]!="MANDATORY": continue
                    _,typ,a,b=c["subject"].split(":",3)
                    if a not in pos or b not in pos: continue
                    adj=all(abs(i-j)==1 and i//columns==j//columns for i,j in product(pos[a],pos[b]))
                    if typ=="REQUIRED_ADJACENCY": cost+=int(not adj)
                    if typ in {"SEPARATION_REQUIRED","AVOID_ADJACENCY"}: cost+=int(adj)
                return cost
            for _ in range(p["maxImprovementPasses"]):
                base=order_cost(rooms); best=rooms; swap_attempts=0
                for i in range(len(rooms)):
                    for j in range(i+1,len(rooms)):
                        if swap_attempts>=p["maxPlacementAttempts"]: break
                        swap_attempts+=1
                        alt=rooms[:]; alt[i],alt[j]=alt[j],alt[i]
                        score=order_cost(alt)
                        if score<base: base,best=score,alt
                if best==rooms: break
                rooms=best
            y=0.0
            for rowindex,start in enumerate(range(0,len(rooms),columns)):
                row=rooms[start:start+columns]; x=0.0; dims=[]
                for r in row:
                    ratio=p["defaultAspectRatios"][ratio_index]
                    width=math.sqrt(r["area"]*ratio); depth=r["area"]/width
                    dims.append((r,width,depth))
                rowwidth=sum(w for _,w,_ in dims); corridor=dict(circulationId="circulation-"+floor+"-"+str(rowindex+1),type="CIRCULATION",floorId=floor,x=0.0,y=y,width=rowwidth,depth=p["circulationWidth"],area=rowwidth*p["circulationWidth"])
                circulation.append(corridor); y+=p["circulationWidth"]
                for r,width,depth in dims:
                    r.update(x=x,y=y,width=width,depth=depth,geometryType="RECTANGLE",unit="m")
                    r.pop("fixedFloor"); placed.append(r); x+=width
                    links.append(dict(fromId=r["spaceId"],toId=corridor["circulationId"],type="SPACE_TO_CIRCULATION"))
                    cs=[c for c in inp["mandatoryConstraints"] if c["subject"].endswith(":"+r["programSpaceId"]) or "SPACE:"+r["programSpaceId"] in c["scope"]]
                    for typ,val in (("FLOOR_ASSIGNMENT",floor),("ROOM_SIZE",dict(width=width,depth=depth,area=r["area"])),("ROOM_PLACEMENT",dict(x=r["x"],y=r["y"]))):
                        decisions.append(dict(decisionId=typ+":"+r["spaceId"],type=typ,spaceId=r["spaceId"],value=val,basis=self._basis(cs,strategy)))
                decisions.append(dict(decisionId=corridor["circulationId"],type="CIRCULATION_PLACEMENT",value=deepcopy(corridor),basis=self._basis([],"circulation-width-and-row-packing-v0")))
                y+=max((d for _,_,d in dims),default=0)
            # Row corridors on one floor are connected along x=0 through an explicit strip.
            if len([c for c in circulation if c.get("floorId")==floor])>1:
                # Shift every room/row corridor to leave a collision-free longitudinal circulation spine.
                for item in placed+circulation:
                    if item.get("floorId")==floor: item["x"]+=p["circulationWidth"]
                spine=dict(circulationId="spine-"+floor,type="CIRCULATION",floorId=floor,x=0.0,y=0.0,width=p["circulationWidth"],depth=y,area=p["circulationWidth"]*y)
                circulation.append(spine)
                for c in circulation:
                    if c.get("floorId")==floor and c is not spine: links.append(dict(fromId=c["circulationId"],toId=spine["circulationId"],type="CIRCULATION_CONNECTION"))
                decisions.append(dict(decisionId=spine["circulationId"],type="CIRCULATION_PLACEMENT",value=deepcopy(spine),basis=self._basis([],"connected-row-spine-v0")))
        width=max(r["x"]+r["width"] for r in placed+circulation); depth=max(r["y"]+r["depth"] for r in placed+circulation)
        env=dict(x=0.0,y=0.0,width=width,depth=depth,area=width*depth,unit="m",basis="GEOMETRY_BOUNDING_BOX")
        if len(floors)>1:
            connector=dict(connectorId="stair-1",type="VERTICAL_CONNECTION",floors=deepcopy(floors),representation="ABSTRACT_CONNECTOR",dimensionalCompliance="NOT_EVALUATED")
            circulation.append(connector)
            decisions.append(dict(decisionId="stair-1",type="VERTICAL_CONNECTOR",value=deepcopy(connector),basis=self._basis([c for c in inp["mandatoryConstraints"] if c["subject"]=="FLOOR_COUNT"],"abstract-multifloor-connection-v0")))
        for r in placed:
            edges=exterior_edges(r,env,p["numericTolerance"])
            r["externalAccess"]=bool(edges); r["buildingEdge"]=edges[0] if edges else None
        # Decisions record final shifted positions, not intermediate placements.
        for dec in decisions:
            if dec["type"]=="ROOM_PLACEMENT":
                r=next(r for r in placed if r["spaceId"]==dec["spaceId"]); dec["value"]=dict(x=r["x"],y=r["y"])
            if dec["type"]=="CIRCULATION_PLACEMENT":
                dec["value"]=deepcopy(next(c for c in circulation if c.get("circulationId")==dec["decisionId"]))
        decisions.append(dict(decisionId="floor-set",type="FLOOR_SET",value=floors,basis=[dict(upstreamArtifact="functionalProgramRef",artifactFingerprint=inp["functionalProgramRef"],path="stage0Context.floor_count")]+self._basis([c for c in inp["mandatoryConstraints"] if c["subject"]=="FLOOR_COUNT"])))
        decisions.append(dict(decisionId="envelope",type="BUILDING_ENVELOPE",value=deepcopy(env),basis=self._basis([c for c in inp["mandatoryConstraints"] if c["subject"] in {"BUILDING_WIDTH","BUILDING_DEPTH"}],"geometry-bounding-box-v0")))
        candidate=dict(candidateId="candidate-"+fingerprint([strategy,ratio_index,columns])[:16],strategy=strategy,floors=[dict(floorId=f) for f in floors],spaces=placed,circulation=circulation,relationships=deepcopy(relations),circulationLinks=links,buildingEnvelope=env,sitePlacement=None,sitePlacementStatus="NOT_REQUIRED_BY_COMPILED_CONSTRAINTS",siteFacts=deepcopy(inp["siteFacts"]),decisions=decisions,deferredConstraints=[dict(constraint=deepcopy(c),capability="NOT_PLANNING_DOMAIN",downstreamScope=capability(c)[1]) for c in inp["mandatoryConstraints"] if capability(c)[0]=="NOT_PLANNING_DOMAIN"])
        candidate["sitePlacement"],candidate["sitePlacementStatus"]=self._place_site(candidate,inp)
        if candidate["sitePlacement"]:
            candidate["decisions"].append(dict(decisionId="site-placement",type="SITE_PLACEMENT",value=deepcopy(candidate["sitePlacement"]),basis=self._basis([c for c in inp["mandatoryConstraints"] if c["domain"]=="SITE" or c["subject"]=="SITE_PLACEMENT"],"boundary-and-obstacle-event-search-v0")))
        return candidate

    def _site_spec(self,inp):
        cs=[c for c in inp["mandatoryConstraints"] if capability(c)[0]=="SUPPORTED" and (c["subject"]=="SITE_PLACEMENT" or c["domain"]=="SITE")]
        if not cs: return None,[],[]
        facts={f["subject"]:f for f in inp["siteFacts"]}
        boundary=facts.get("BOUNDARY")
        if not boundary: raise ValueError("unsupported site placement: no verified boundary")
        box=rectangle(boundary["value"]["geometry"])
        if box[0]==box[2] or box[1]==box[3]: raise ValueError("site boundary must be a rectangle")
        obstacles=[]; crs=boundary["value"]["geometry"]["coordinateSystemId"]
        for c in cs:
            if c["subject"]=="SITE_PLACEMENT": continue
            fact=facts.get(c["subject"]) or facts.get("CONTEXT:"+c["subject"].split(":",1)[1])
            if not fact or not fact["value"].get("geometry"): raise ValueError("unsupported site obstacle geometry")
            geom=fact["value"]["geometry"]
            if geom["coordinateSystemId"]!=crs: raise ValueError("site CRS mismatch")
            obstacles.append(dict(compiledConstraintId=c["compiledConstraintId"],factId=fact["factId"],rectangle=rectangle(geom)))
        return box,obstacles,[boundary["factId"]]+[o["factId"] for o in obstacles]

    def _place_site(self,candidate,inp):
        box,obstacles,facts=self._site_spec(inp)
        if box is None: return None,"NOT_REQUIRED_BY_COMPILED_CONSTRAINTS"
        w,d=candidate["buildingEnvelope"]["width"],candidate["buildingEnvelope"]["depth"]
        # Numerical contact avoidance is an explicit algorithm epsilon, never a setback/clearance norm.
        eps=self._policy["adjacencyEpsilon"]
        xs=sorted({box[0],box[2]-w,*[o["rectangle"][2]+eps for o in obstacles],*[o["rectangle"][0]-w-eps for o in obstacles]})
        ys=sorted({box[1],box[3]-d,*[o["rectangle"][3]+eps for o in obstacles],*[o["rectangle"][1]-d-eps for o in obstacles]})
        for attempt,(x,y) in enumerate(product(xs,ys)):
            if attempt>=self._policy["maxPlacementAttempts"]: break
            rect=(x,y,x+w,y+d)
            if x>=box[0] and y>=box[1] and x+w<=box[2] and y+d<=box[3] and not any(intersects_closed(rect,o["rectangle"]) for o in obstacles):
                return dict(x=x,y=y,width=w,depth=d,unit="m",coordinateSystemId=next(f for f in inp["siteFacts"] if f["subject"]=="BOUNDARY")["value"]["geometry"]["coordinateSystemId"],factRefs=facts,orientationFacts=[f["factId"] for f in inp["siteFacts"] if f["subject"]=="ORIENTATION"],rotationDegrees=0,rotationBasis="PLANNER_HEURISTIC_AXIS_ALIGNED",setbacks=[],clearanceConstraints=[],placementAttempts=attempt+1),"PLACED"
        return None,"NO_VALID_SITE_PLACEMENT_FOUND"

    def _relation_actual(self,c,rooms,candidate):
        a,b=self._endpoints(c,rooms); typ=c["value"]; p=self._policy
        if typ=="EXTERNAL_ACCESS":
            return all(exterior_edges(r,candidate["buildingEnvelope"],p["numericTolerance"]) and r.get("externalAccess") is True and r.get("buildingEdge") in exterior_edges(r,candidate["buildingEnvelope"],p["numericTolerance"]) for r in a)
        if typ=="REQUIRED_ACCESS":
            # Independent circulation path, without traversing another program room.
            corridors={x["circulationId"]:x for x in candidate["circulation"] if x.get("type")=="CIRCULATION"}
            graph={k:set() for k in corridors}
            for link in candidate["circulationLinks"]:
                x,y=link["fromId"],link["toId"]
                if x in corridors and y in corridors and shared_boundary(corridors[x],corridors[y],p["numericTolerance"])>p["adjacencyEpsilon"]:
                    graph[x].add(y);graph[y].add(x)
            def ports(r): return {l["toId"] for l in candidate["circulationLinks"] if l["fromId"]==r["spaceId"] and l["toId"] in corridors and shared_boundary(r,corridors[l["toId"]],p["numericTolerance"])>p["adjacencyEpsilon"]}
            def connected(x,y):
                visited=set(); todo=list(ports(x)); targets=ports(y)
                while todo:
                    z=todo.pop()
                    if z in visited: continue
                    if z in targets: return True
                    visited.add(z); todo.extend(graph[z]-visited)
                return False
            return all(connected(x,y) for x,y in product(a,b))
        if typ=="VERTICAL_CONNECTION":
            return all(x["floorId"]!=y["floorId"] and any(z.get("type")=="VERTICAL_CONNECTION" and {x["floorId"],y["floorId"]}<=set(z.get("floors",[])) for z in candidate["circulation"]) for x,y in product(a,b))
        values=[shared_boundary(x,y,p["numericTolerance"])>p["adjacencyEpsilon"] for x,y in product(a,b)]
        return all(not x for x in values) if typ in {"AVOID_ADJACENCY","SEPARATION_REQUIRED"} else all(values)

    def audit_candidate(self,candidate):
        """Independent validation against live input; ignores claimed status/checks/score."""
        inp,fp=self._inputs()
        return self._validate(deepcopy(candidate),inp,fp)

    def _validate(self,candidate,inp,fp):
        p=self._policy; tol=p["numericTolerance"]; issues=[]; checks=[]
        try:
            floors,templates,_=self._prepare(inp,fp); rooms=candidate["spaces"]
            expected={r["spaceId"]:r for r in templates}
            if len(rooms)!=len(expected) or len({r["spaceId"] for r in rooms})!=len(rooms) or {r["spaceId"] for r in rooms}!=set(expected): issues.append("exact program instance set required")
            if [x["floorId"] for x in candidate["floors"]]!=floors: issues.append("exact verified floor set required")
            circulation=[c for c in candidate["circulation"] if c.get("type")=="CIRCULATION"]
            for r in rooms+circulation:
                if r["floorId"] not in floors or any(not number(r[k]) for k in ("x","y","width","depth","area")) or r["width"]<=0 or r["depth"]<=0 or r["x"]<0 or r["y"]<0 or abs(r["area"]-r["width"]*r["depth"])>tol:
                    raise ValueError("positive finite metre rectangle with exact area required")
                if r in rooms and (r.get("geometryType")!="RECTANGLE" or r.get("unit")!="m" or r["programSpaceId"]!=expected[r["spaceId"]]["programSpaceId"]): issues.append("rectangle/program identity invalid")
            allrect=rooms+circulation
            for i,a in enumerate(allrect):
                for b in allrect[i+1:]:
                    if overlap(a,b,tol): issues.append("interior overlap: "+str(a.get("spaceId",a.get("circulationId")))+" / "+str(b.get("spaceId",b.get("circulationId"))))
            env=candidate["buildingEnvelope"]
            if any(not number(env[k]) or env[k]<=0 for k in ("width","depth","area")) or env.get("x")!=0 or env.get("y")!=0 or env.get("unit")!="m" or abs(env["area"]-env["width"]*env["depth"])>tol: issues.append("invalid building envelope")
            if abs(env["width"]-max(r["x"]+r["width"] for r in allrect))>tol or abs(env["depth"]-max(r["y"]+r["depth"] for r in allrect))>tol: issues.append("envelope differs from actual geometry")
            cids=[c["circulationId"] for c in circulation]
            if len(set(cids))!=len(cids) or set(cids)&set(expected): issues.append("duplicate circulation IDs")
            if any(c.get("type") not in {"CIRCULATION","VERTICAL_CONNECTION"} for c in candidate["circulation"]): issues.append("unknown circulation representation")
            if not circulation or any(not any(c["floorId"]==f for c in circulation) for f in {r["floorId"] for r in rooms}): issues.append("missing circulation")
            rectangles={r["spaceId"]:r for r in rooms}|{c["circulationId"]:c for c in circulation}
            for link in candidate["circulationLinks"]:
                x,y=link["fromId"],link["toId"]
                if x not in rectangles or y not in cids: issues.append("dangling circulation link")
                elif shared_boundary(rectangles[x],rectangles[y],tol)<=p["adjacencyEpsilon"] or link["type"]!=("SPACE_TO_CIRCULATION" if x in expected else "CIRCULATION_CONNECTION"):
                    issues.append("circulation link lacks a physical shared boundary")
            for r in rooms:
                if not any(l["fromId"]==r["spaceId"] and l["toId"] in cids and shared_boundary(r,rectangles[l["toId"]],tol)>p["adjacencyEpsilon"] for l in candidate["circulationLinks"]): issues.append("room has no direct circulation access")
            connectors=[c for c in candidate["circulation"] if c.get("type")=="VERTICAL_CONNECTION"]
            if len(connectors)!=(1 if len(floors)>1 else 0) or any(c.get("connectorId")!="stair-1" for c in connectors): issues.append("unexpected vertical connectors")
            if len(floors)>1 and not any(c.get("floors")==floors and c.get("representation")=="ABSTRACT_CONNECTOR" and c.get("dimensionalCompliance")=="NOT_EVALUATED" for c in connectors): issues.append("abstract vertical connector missing or false compliance claim")
            if candidate["relationships"]!=[c for c in inp["mandatoryConstraints"]+inp["preferences"] if c["subject"].startswith("RELATIONSHIP:")]: issues.append("relationship graph differs from compiled input")
            for c in candidate["relationships"]: self._endpoints(c,rooms)
            box,obstacles,facts=self._site_spec(inp); siteok=box is None and candidate["sitePlacement"] is None and candidate["sitePlacementStatus"]=="NOT_REQUIRED_BY_COMPILED_CONSTRAINTS"
            if box is not None and candidate["sitePlacement"]:
                v=candidate["sitePlacement"]
                if any(not number(v[k]) for k in ("x","y","width","depth")): raise ValueError("invalid site placement geometry")
                rect=(v["x"],v["y"],v["x"]+v["width"],v["y"]+v["depth"])
                boundary=next(f for f in inp["siteFacts"] if f["subject"]=="BOUNDARY")
                siteok=abs(v["width"]-env["width"])<=tol and abs(v["depth"]-env["depth"])<=tol and rect[0]>=box[0] and rect[1]>=box[1] and rect[2]<=box[2] and rect[3]<=box[3] and not any(intersects_closed(rect,o["rectangle"]) for o in obstacles) and v["factRefs"]==facts and v["coordinateSystemId"]==boundary["value"]["geometry"]["coordinateSystemId"] and v["unit"]=="m" and v["rotationDegrees"]==0 and v["setbacks"]==[] and v["clearanceConstraints"]==[]
            if not siteok: issues.append("blocking site placement violation")
            if candidate["siteFacts"]!=inp["siteFacts"]: issues.append("site facts differ from verified input")
            for c in inp["mandatoryConstraints"]:
                cap,why=capability(c)
                if cap=="NOT_PLANNING_DOMAIN": continue
                values=[]; s=c["subject"]; prefix=s.split(":")[0]
                if cap!="SUPPORTED": checks.append(dict(compiledConstraintId=c["compiledConstraintId"],status="UNSUPPORTED",reason=why)); continue
                if s=="FLOOR_COUNT": values=[len(floors)]
                elif s in {"BUILDING_WIDTH","BUILDING_DEPTH"}: values=[env["width" if s=="BUILDING_WIDTH" else "depth"]]
                elif prefix in {"SPACE_AREA","SPACE_QUANTITY","SPACE_EXISTS","SPACE_FUNCTION","SPACE_LOCATION"}:
                    group=[r for r in rooms if r["programSpaceId"]==s.split(":",1)[1]]
                    if prefix=="SPACE_QUANTITY": values=[len(group)]
                    elif prefix=="SPACE_EXISTS": values=[bool(group)]
                    else: values=[r["area"] if prefix=="SPACE_AREA" else r["function"] if prefix=="SPACE_FUNCTION" else "FLOOR:"+r["floorId"] for r in group]
                elif prefix=="RELATIONSHIP": values=[self._relation_actual(c,rooms,candidate)]
                else: values=[siteok]
                passed=bool(values) and (all(values) if prefix in {"RELATIONSHIP","OBJECT","ZONE","SITE_PLACEMENT"} else all(accept(c,v,tol) for v in values))
                checks.append(dict(compiledConstraintId=c["compiledConstraintId"],subject=s,status="PASS" if passed else "FAIL",actual=values,expected=dict(operator=c["operator"],value=c["value"],unit=c["unit"]),evidenceKind="INDEPENDENT_GEOMETRY_AUDIT"))
            decisions=candidate["decisions"]; known={c["compiledConstraintId"] for c in inp["mandatoryConstraints"]+inp["preferences"]}
            required={"floor-set","envelope"}|{typ+":"+r["spaceId"] for r in rooms for typ in ("ROOM_SIZE","ROOM_PLACEMENT","FLOOR_ASSIGNMENT")}|set(cids)
            if len(floors)>1: required.add("stair-1")
            if candidate["sitePlacement"]: required.add("site-placement")
            dids=[d["decisionId"] for d in decisions]
            if len(set(dids))!=len(dids) or set(dids)!=required: issues.append("incomplete/duplicate decision provenance")
            for d in decisions:
                if not d.get("basis") or any(not ((b.get("compiledConstraintId") in known) or (b.get("basisType")=="PLANNER_HEURISTIC" and isinstance(b.get("policyId"),str) and b.get("plannerPolicyFingerprint")==fingerprint(p)) or (b.get("upstreamArtifact")=="functionalProgramRef" and b.get("artifactFingerprint")==inp["functionalProgramRef"] and b.get("path")=="stage0Context.floor_count")) for b in d["basis"]): issues.append("invalid provenance origin")
                if d["type"] in {"ROOM_SIZE","ROOM_PLACEMENT","FLOOR_ASSIGNMENT"}:
                    r=next(r for r in rooms if r["spaceId"]==d["spaceId"])
                    val=r["floorId"] if d["type"]=="FLOOR_ASSIGNMENT" else {k:r[k] for k in (("x","y") if d["type"]=="ROOM_PLACEMENT" else ("width","depth","area"))}
                    if d["value"]!=val: issues.append("decision differs from audited geometry")
                elif d["decisionId"]=="floor-set" and d["value"]!=floors: issues.append("floor provenance differs from floor set")
                elif d["decisionId"]=="envelope" and d["value"]!=env: issues.append("envelope provenance differs from geometry")
                elif d["decisionId"] in cids and d["value"]!=rectangles[d["decisionId"]]: issues.append("circulation provenance differs from geometry")
                elif d["decisionId"]=="stair-1" and d["value"]!=connectors[0]: issues.append("connector provenance differs")
                elif d["decisionId"]=="site-placement" and d["value"]!=candidate["sitePlacement"]: issues.append("site provenance differs from placement")
            deferred=[dict(constraint=deepcopy(c),capability="NOT_PLANNING_DOMAIN",downstreamScope=capability(c)[1]) for c in inp["mandatoryConstraints"] if capability(c)[0]=="NOT_PLANNING_DOMAIN"]
            if candidate["deferredConstraints"]!=deferred: issues.append("deferred constraints must be retained exactly")
        except (KeyError,TypeError,ValueError,OverflowError,StopIteration) as exc:
            issues.append("malformed candidate: "+str(exc))
        status="INVALID_GEOMETRY" if issues else "UNSUPPORTED" if any(c["status"]=="UNSUPPORTED" for c in checks) else "INVALID_CONSTRAINT" if any(c["status"]!="PASS" for c in checks) else "VALID"
        return dict(status=status,geometryIssues=issues,constraintChecks=checks,constraintCoverage=1.0 if status=="VALID" else 0.0,provenanceCoverage=1.0 if status=="VALID" else 0.0)

    def _score(self,candidate,inp):
        p=self._policy; scores=[]; unsupported=[]; rooms=candidate["spaces"]; env=candidate["buildingEnvelope"]
        for c in inp["preferences"]:
            s=c["subject"]; prefix=s.split(":")[0]; kind=None; raw=None
            if prefix=="GOAL":
                kind=c["value"]
                if kind=="COMPACTNESS": raw=-env["area"]
                elif kind=="SPACIOUSNESS":
                    targets={r["programSpaceId"]:next((x["value"] for x in inp["mandatoryConstraints"]+inp["preferences"] if x["subject"]=="SPACE_AREA:"+r["programSpaceId"] and number(x["value"])),p["defaultRoomArea"]) for r in rooms}
                    raw=sum(r["area"]/max(targets[r["programSpaceId"]],p["numericTolerance"]) for r in rooms)
                elif kind=="STRUCTURAL_REGULARITY":
                    edges=[(r["x"],r["x"]+r["width"],r["y"],r["y"]+r["depth"]) for r in rooms]
                    raw=sum(sum(abs(a[k]-b[k])<=p["numericTolerance"] for k in range(4)) for i,a in enumerate(edges) for b in edges[i+1:])
            elif prefix=="RELATIONSHIP" and c["value"] in RELATIONS:
                kind="AVOID_ADJACENCY" if c["value"]=="AVOID_ADJACENCY" else "PREFERRED_ADJACENCY"
                raw=1.0 if self._relation_actual(c,rooms,candidate) else -1.0
            elif prefix=="SPACE_AREA" and number(c["value"]):
                kind="REQUESTED_AREA"; raw=-sum(abs(r["area"]-c["value"]) for r in rooms if r["programSpaceId"]==s.split(":",1)[1])
            elif prefix=="SPACE_LOCATION":
                kind="SPACE_LOCATION"; desired=p["floorAliases"].get(c["value"],str(c["value"]).removeprefix("FLOOR:"))
                raw=sum(float(r["floorId"]==desired) for r in rooms if r["programSpaceId"]==s.split(":",1)[1])
            if raw is None or kind not in p["scoringRegistry"]["weights"]:
                unsupported.append(dict(compiledConstraintId=c["compiledConstraintId"],subject=s,value=c["value"],status="UNSUPPORTED_PREFERENCE",reason="no v0 scoring evaluator or verified module/cost model",constraint=deepcopy(c))); continue
            goalweight=c.get("goalMetadata",{}).get("weight")
            weight=p["scoringRegistry"]["weights"][kind]*(goalweight if number(goalweight) else 1.0)
            scores.append(dict(compiledConstraintId=c["compiledConstraintId"],kind=kind,raw=raw,weight=weight,score=raw*weight,basisType="PLANNER_HEURISTIC",scoringRegistryRevision=p["scoringRegistry"]["revision"]))
        return scores,unsupported

    def _compute(self):
        out=dict(stage="PLANNING_ENGINE",status="BLOCKED",canProgress=False,flow=[],constraintCompilationFingerprint=None,plannerPolicyFingerprint=fingerprint(self._policy),capabilityRegistry=deepcopy(CAPABILITY_REGISTRY),candidatesGenerated=0,candidatesValid=0,selectedCandidateId=None,selectedCandidate=None,candidateSummaries=[],unsupportedMandatoryConstraints=[],unsupportedPreferences=[],generationIssues=[],constraintCoverage=0.0,provenanceCoverage=0.0,gateProof={})
        try:
            inp,fp=self._inputs(); out["constraintCompilationFingerprint"]=inp["sourceCompilationFingerprint"]
            out["flow"]=deepcopy(FLOW)
            for c in inp["mandatoryConstraints"]:
                cap,why=capability(c)
                if cap=="UNSUPPORTED": out["unsupportedMandatoryConstraints"].append(dict(compiledConstraintId=c["compiledConstraintId"],status="UNSUPPORTED_MANDATORY_CONSTRAINT",reason=why,constraint=deepcopy(c)))
            if out["unsupportedMandatoryConstraints"]: raise ValueError("UNSUPPORTED_MANDATORY_CONSTRAINT")
            try: self._site_spec(inp)
            except ValueError as exc:
                out["unsupportedMandatoryConstraints"]=[dict(compiledConstraintId=c["compiledConstraintId"],status="UNSUPPORTED_MANDATORY_CONSTRAINT",reason=str(exc),constraint=deepcopy(c)) for c in inp["mandatoryConstraints"] if c["domain"]=="SITE" or c["subject"]=="SITE_PLACEMENT"]
                raise
            floors,rooms,relations=self._prepare(inp,fp)
            for c in relations: self._endpoints(c,rooms)
            candidates=[]; seen=set(); maxfloor=max(sum(r["floorId"]==f for r in rooms) for f in floors)
            variants=[("area-descending",0,maxfloor),("relationship-first",0,maxfloor),("compact-strip",0,max(1,math.ceil(math.sqrt(maxfloor))))]
            variants += [(strategy,ratio,cols) for ratio in range(len(self._policy["defaultAspectRatios"])) for cols in range(1,maxfloor+1) for strategy in ("area-descending","relationship-first")]
            attempts=0
            for strategy,ratio,cols in variants:
                if len(candidates)>=self._policy["maxCandidates"] or attempts>=self._policy["maxGenerationAttempts"]: break
                attempts+=1
                c=self._generate(inp,fp,floors,rooms,relations,strategy,ratio,cols)
                geometry=fingerprint([c["spaces"],c["circulation"],c["sitePlacement"]])
                if geometry in seen: continue
                seen.add(geometry)
                validation=self._validate(c,inp,fp); c.update(validation)
                c["preferenceScores"],unsupported=self._score(c,inp)
                c["score"]=sum(s["score"] for s in c["preferenceScores"])
                out["unsupportedPreferences"]=unsupported
                c["candidateFingerprint"]=candidate_fingerprint(c,inp["sourceCompilationFingerprint"],out["plannerPolicyFingerprint"])
                candidates.append(c)
            valid=[c for c in candidates if c["status"]=="VALID"]
            out.update(candidatesGenerated=len(candidates),candidatesValid=len(valid),generationAttempts=attempts,candidateSummaries=[{k:deepcopy(c[k]) for k in ("candidateId","candidateFingerprint","strategy","status","score","constraintChecks","geometryIssues","preferenceScores")} for c in candidates])
            if not valid:
                out["status"]="NO_VALID_PLAN_FOUND";out["generationIssues"].append(dict(reason="bounded search exhausted without a valid candidate"))
            else:
                best=sorted(valid,key=lambda c:(-c["score"],c["candidateId"]))[0]
                proof=self._validate(best,inp,fp)
                if proof["status"]!="VALID": raise ValueError("final independent audit failed")
                out.update(status="VERIFIED",canProgress=True,selectedCandidateId=best["candidateId"],selectedCandidate=best,constraintCoverage=1.0,provenanceCoverage=1.0)
                out["gateProof"]=dict(compilationVerified=True,planningInputFingerprintValid=True,exactProgramInstances=True,geometryValid=True,overlaps=0,mandatoryRelationshipViolations=0,blockingSiteViolations=0,unsupportedMandatoryConstraints=0,allSupportedMandatoryPass=True,constraintCoverage=1.0,provenanceCoverage=1.0,candidateFingerprint=best["candidateFingerprint"],constraintCompilationFingerprint=out["constraintCompilationFingerprint"],plannerPolicyFingerprint=out["plannerPolicyFingerprint"],auditRerunBeforeProgression=True,evidenceBoundary="OFFLINE_ABSTRACT_RECTANGULAR_PLANNING",realStairCompliance="NOT_EVALUATED")
                out["flow"].append("PLANNING_ENGINE VERIFIED")
        except (ValueError,RuntimeError,KeyError,TypeError,OverflowError) as exc:
            if str(exc).startswith("NO_VALID_PLAN_FOUND"): out["status"]="NO_VALID_PLAN_FOUND"
            out["generationIssues"].append(dict(reason=str(exc)))
        out["planningEngineFingerprint"]=fingerprint(out)
        return out

    def audit(self):
        self._result=self._compute(); return deepcopy(self._result)


def text_plan(candidate):
    """Coordinate representation from the generated geometry, without a second layout model."""
    lines=["LOCAL XY: metres; x right / y up; rectangles [x,y,width,depth]"]
    for f in candidate["floors"]:
        lines.extend(["",f["floorId"].upper()])
        for r in sorted([r for r in candidate["spaces"] if r["floorId"]==f["floorId"]],key=lambda r:(-r["y"],r["x"],r["spaceId"])):
            lines.append("  "+r["spaceId"]+": ["+", ".join(format(r[k],".6f") for k in ("x","y","width","depth"))+"] area="+format(r["area"],".6f"))
        for c in candidate["circulation"]:
            if c.get("floorId")==f["floorId"]: lines.append("  "+c["circulationId"]+": ["+", ".join(format(c[k],".6f") for k in ("x","y","width","depth"))+"]")
    return "\n".join(lines)+"\n"
