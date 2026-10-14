"""Fresh independent property/edge-matrix tests for PR88 local modules.
Each generated test has a distinct fixture with an independently computed oracle.
No Archicad processes, PLN writes, binary loading or network calls.
Original 735-test suite is intentionally NOT included in this QA run.
"""
from __future__ import annotations
import copy
import itertools
import json
import math
import random
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import archicad_local_modules as L
import archicad_project_accelerator as A
from archicad_dynamic_commands import DynamicCommands

def bind(cls, prefix, index, fn):
    setattr(cls, f"test_{prefix}_{index:03d}", fn)

def rectangle(x0, y0, x1, y1, name):
    return {"id":name,"outline":[[x0,y0],[x1,y0],[x1,y1],[x0,y1]]}

class NovelPropertyMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        catalog = json.loads((ROOT/"schemas/accelerator/mass-capabilities/commands.json").read_text(encoding="utf8"))
        cls.router=DynamicCommands(catalog)
        A.connect_functional_modules(cls.router)

def dag_case(seed):
    def test(self):
        rng=random.Random(10000+seed)
        n=5+seed%6
        nodes=[f"n{i}" for i in range(n)]
        edges=[[nodes[i],nodes[j]] for i in range(n) for j in range(i+1,n) if rng.randrange(10)<4]
        changed=[nodes[(seed*7+3)%n]]
        actual=L.dependency_impact(nodes,edges,changed)
        reach=set(changed)
        while True:
            nxt=reach|{b for a,b in edges if a in reach}
            if nxt==reach:break
            reach=nxt
        self.assertEqual(actual["status"],"DAG")
        self.assertEqual(actual["affected"],sorted(reach))
        self.assertEqual(set(actual["updateOrder"]),reach)
        self.assertEqual(len(actual["updateOrder"]),len(reach))
        pos={v:i for i,v in enumerate(actual["updateOrder"])}
        self.assertTrue(all(pos[a]<pos[b] for a,b in edges if a in reach and b in reach))
        self.assertIs(actual["executionAllowed"],False)
    return test

for seed in range(80):bind(NovelPropertyMatrix,"dag_reachability",seed,dag_case(seed))

def cycle_case(seed):
    def test(self):
        n=2+seed%7
        nodes=[f"cycle{i}" for i in range(n)]
        edges=[[nodes[i],nodes[(i+1)%n]] for i in range(n)]
        edges.extend([[f"cycle{i}",f"cycle{j}"] for i in range(n) for j in range(i+2,n) if (i+j+seed)%5==0])
        actual=L.dependency_impact(nodes,edges,[nodes[seed%n]])
        self.assertEqual(actual["status"],"CYCLIC")
        self.assertTrue(actual["cycleWitness"])
        self.assertTrue(all(pair in edges for pair in actual["cycleWitness"]))
        self.assertIs(actual["executionAllowed"],False)
    return test
for seed in range(32):bind(NovelPropertyMatrix,"cycle_witness",seed,cycle_case(seed))

def rect_case(seed):
    def test(self):
        w=3+seed%6;h=3+(seed//3)%6
        w2=2+(seed//5)%5;h2=2+(seed//7)%5
        dx=(seed*13)%19-8;dy=(seed*7)%19-8
        lhs=rectangle(0,0,w,h,"A")
        rhs=rectangle(dx,dy,dx+w2,dy+h2,"B")
        out=L.polygon_relations([lhs,rhs])
        self.assertAlmostEqual(out["polygons"][0]["area"],w*h)
        self.assertAlmostEqual(out["polygons"][1]["area"],w2*h2)
        self.assertAlmostEqual(out["polygons"][0]["perimeter"],2*(w+h))
        ox=max(0,min(w,dx+w2)-max(0,dx))
        oy=max(0,min(h,dy+h2)-max(0,dy))
        intersects=max(0,dx)<=min(w,dx+w2) and max(0,dy)<=min(h,dy+h2)
        self.assertEqual(len(out["relations"]),int(intersects))
        if intersects:
            relation=out["relations"][0]
            self.assertAlmostEqual(relation["intersectionArea"],ox*oy,places=7)
            self.assertEqual(relation["touches"],ox*oy==0)
            self.assertIs(relation["intersects"],True)
        self.assertEqual(out["scope"],"2D_SOURCE_POLYGONS_NOT_3D_NATIVE_COLLISION")
    return test
for seed in range(60):bind(NovelPropertyMatrix,"rectangle_intersection_oracle",seed,rect_case(seed))

def donut_case(seed):
    def test(self):
        width=6+seed%10
        size=1+(seed//2)%3
        hole=[[1,1],[1+size,1],[1+size,1+size],[1,1+size]]
        a=rectangle(0,0,width,width,"main")
        a["holes"]=[hole]
        b=rectangle(1.1,1.1,1+size-0.1,1+size-0.1,"in-hole")
        out=L.polygon_relations([a,b])
        self.assertAlmostEqual(out["polygons"][0]["area"],width**2-size**2)
        self.assertAlmostEqual(out["polygons"][0]["perimeter"],4*(width+size))
        self.assertEqual(out["relations"],[])
    return test
for seed in range(24):bind(NovelPropertyMatrix,"polygon_hole_oracle",seed,donut_case(seed))

def assignment_case(seed):
    def test(self):
        rng=random.Random(200000+seed)
        count=3+seed%2
        slots=["a","b","c"]
        tasks=[{"id":f"task{i}","costs":{s:rng.randint(-3,17) for s in slots}} for i in range(count)]
        capacities={"a":2,"b":2,"c":2}
        feasible=[]
        for choice in itertools.product(slots,repeat=count):
            if all(choice.count(s)<=capacities[s] for s in slots):
                feasible.append(sum(tasks[i]["costs"][choice[i]] for i in range(count)))
        oracle=min(feasible)
        result=L.constrained_assignment(tasks,capacities,time_limit=3)
        self.assertEqual(result["status"],"OPTIMAL")
        self.assertEqual(set(result["assignment"]),{t["id"] for t in tasks})
        assignment=result["assignment"]
        self.assertTrue(all(sum(s==slot for s in assignment.values())<=capacities[slot] for slot in slots))
        cost=sum(t["costs"][assignment[t["id"]]] for t in tasks)
        self.assertEqual(cost,oracle)
        self.assertEqual(result["objective"],oracle)
        self.assertEqual(result["engineering"],"NOT_VERIFIED")
    return test
for seed in range(48):bind(NovelPropertyMatrix,"cpsat_bruteforce_optimum",seed,assignment_case(seed))

def infeasible_case(seed):
    def test(self):
        count=3+seed%3
        tasks=[{"id":f"t{i}","costs":{"a":1+seed%7+i,"b":2+i+seed%5}} for i in range(count)]
        result=L.constrained_assignment(tasks,{"a":1,"b":1},time_limit=2)
        self.assertEqual(result["status"],"INFEASIBLE")
        self.assertEqual(result["assignment"],{})
        self.assertNotIn("objective",result)
        self.assertEqual(result["engineering"],"NOT_VERIFIED")
    return test
for seed in range(24):bind(NovelPropertyMatrix,"cpsat_infeasible_capacity",seed,infeasible_case(seed))

VALID_LOCAL={
 "NormalizeNativeDump":{"dump":{}},
 "NativeBodyQuantities":{"elements":[]},
 "DependencyImpact":{"nodes":["a"],"edges":[],"changed":["a"]},
 "PolygonRelations":{"polygons":[rectangle(0,0,2,2,"poly")]},
 "ConstrainedAssignment":{"tasks":[{"id":"t","costs":{"s":2}}],"capacities":{"s":1}},
 "IFCSelect":{"path":"synthetic.ifc","query":"IfcWall"},
 "IFCValidate":{"path":"synthetic.ifc"},
 "IFCGeometry":{"path":"synthetic.ifc","guids":[]},
 "IFCExchangeFacts":{"path":"synthetic.ifc"}
}
def input_schema_case(name,mutation):
    def test(self):
        key="AddOn.APAAnalysis."+name
        base=copy.deepcopy(VALID_LOCAL[name])
        required=next(iter(base))
        if mutation==0:del base[required]
        elif mutation==1:base[required]=None
        elif mutation==2:base[required]=42
        elif mutation==3:base["unexpectedInjectedProperty"]={"nested":True}
        elif mutation==4:base[required]=True
        elif mutation==5:base=[]
        with self.assertRaises((ValueError,Exception)):
            self.router.prepare(key,base)
    return test
for idx,name in enumerate(VALID_LOCAL):
    for mutation in range(6):
        bind(NovelPropertyMatrix,"local_schema_rejection",idx*6+mutation,input_schema_case(name,mutation))

def positive_input_case(name):
    def test(self):
        key="AddOn.APAAnalysis."+name
        ticket=self.router.prepare(key,copy.deepcopy(VALID_LOCAL[name]))
        self.assertFalse(ticket["nativeWritePermission"])
        self.router.validate(ticket)
        row=self.router.select(key)
        self.assertEqual(row["executionDomain"],"LOCAL_PYTHON_ANALYTICS_NOT_ARCHICAD")
        self.assertIsNone(row["runtimeRegistered"])
        self.assertEqual(row["effect"],"READ_ONLY")
    return test
for idx,name in enumerate(VALID_LOCAL):
    bind(NovelPropertyMatrix,"local_input_positive_domain",idx,positive_input_case(name))

def contract_immutability_case(name,variant):
    def test(self):
        key="AddOn.APAAnalysis."+name
        t=self.router.prepare(key,copy.deepcopy(VALID_LOCAL[name]))
        mutated=copy.deepcopy(t)
        if variant==0:mutated["nativeWritePermission"]=True
        elif variant==1:mutated["parameters"]["untrusted"]=123
        elif variant==2:mutated["catalogHash"]="0"*64
        with self.assertRaises((ValueError,KeyError)):
            self.router.validate(mutated)
        self.router.validate(t)
    return test
for idx,name in enumerate(VALID_LOCAL):
    for variant in range(3):
        bind(NovelPropertyMatrix,"local_ticket_mutation_rejected",idx*3+variant,contract_immutability_case(name,variant))

def sdk_case(name,variant):
    def test(self):
        key="AddOn.TapirCommand."+name
        row=self.router.select(key)
        self.assertIsNone(row["runtimeRegistered"])
        self.assertFalse(row.get("api")=="local-python")
        self.assertNotEqual(row["status"],"LIVE_VERIFIED")
        self.assertNotEqual(row["status"],"CALLABLE_VERIFIED")
        if variant==0:self.assertEqual(row["commandName"],name)
        elif variant==1:self.assertEqual(row["version"],"29")
        elif variant==2:self.assertEqual(row["api"],"addon-json")
        elif variant==3:self.assertEqual(row["availability"],"SOURCE_CONTRACT_NOT_RUNTIME_PROBED")
    return test
SDK_NAMES=["GetNativeElementDefaultsV1","GetNativePolygonMemoV1","GetNativeWorkingUnitsV1","GetNativeGroupRootsV1","GetNativeLibraryPartOriginV1"]
for idx,name in enumerate(SDK_NAMES):
    for variant in range(4):
        bind(NovelPropertyMatrix,"sdk_source_only_no_live_promotion",idx*4+variant,sdk_case(name,variant))
