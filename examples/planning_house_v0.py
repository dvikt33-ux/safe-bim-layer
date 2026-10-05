"""Reproducible offline synthetic house demo using live existing producer APIs."""
import argparse
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from design_stage0 import Stage0
from functional_program import FunctionalProgram
from design_intent import DesignIntent
from site_context import SiteContext
from project_constraints import ProjectConstraintInput
from normative_bundle import ProjectNormativeBundle, GlobalRuleLibrary
from constraint_compilation import ConstraintCompilation
from planning_engine import PlanningEngine, text_plan


def load_case(path=None):
    path=path or ROOT/"docs/examples/planning_engine_v0/house-inputs.json"
    data=json.loads(path.read_text(encoding="utf-8"))
    s0=Stage0(data["stage0Registry"],data["stage0Sources"]);s0.audit()
    fp=FunctionalProgram(s0,data["functionalProgramSources"]);fp.audit()
    di=DesignIntent(s0,fp,data["designIntentSources"]);di.audit()
    site=SiteContext(s0,data["siteSources"],data["siteRequirements"]);site.audit()
    pc=ProjectConstraintInput(s0,fp,di,site,data["projectConstraintSources"]);pc.audit()
    lib=GlobalRuleLibrary(data["syntheticNormativeFixture"])
    bundle=ProjectNormativeBundle(s0,fp,di,site,pc,lib,data["normativeScope"]);bundle.audit()
    cc=ConstraintCompilation(s0,fp,di,site,pc,bundle,data["compilationDomains"],data["compilationReferences"]);cc.audit()
    for obj in (s0,fp,di,site,pc,bundle,cc): obj.require_verified()
    # After producer verification, any global-library read would fail the demonstration.
    lib.data=lambda: (_ for _ in ()).throw(AssertionError("planner accessed global normative library"))
    return PlanningEngine(cc,fp,data["plannerPolicy"]),(s0,fp,di,site,pc,bundle,cc)


def write(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2,allow_nan=False)+"\n",encoding="utf-8")


def run(output,path=None):
    engine,upstream=load_case(path);before=[u.result() for u in upstream]
    result=engine.audit()
    if result["status"]!="VERIFIED": raise RuntimeError(result["generationIssues"] or result["candidateSummaries"])
    gate=engine.require_verified();candidate=engine.selected_candidate()
    if before!=[u.result() for u in upstream]: raise AssertionError("upstream mutated")
    repeated=engine.audit()
    if repeated!=result: raise AssertionError("determinism failure")
    output.mkdir(parents=True,exist_ok=True)
    write(output/"sample-planning-candidate.json",candidate)
    write(output/"planning-engine-result.json",result)
    write(output/"planning-engine-repeat.json",repeated)
    write(output/"VERIFIED-gate-proof.json",gate)
    write(output/"planningInput.json",engine._compilation.planning_input())
    (output/"sample-plan.txt").write_text(text_plan(candidate),encoding="utf-8")
    return result


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args();r=run(args.output)
    print("PLANNING_ENGINE",r["status"],"candidates",r["candidatesGenerated"],"valid",r["candidatesValid"],r["selectedCandidateId"])
