"""One authorized seven-stud copy and one working PLN save, via original APA."""
import argparse,hashlib,json,os,sqlite3,sys
from pathlib import Path

BASE="e91d5670f20202c269d442bafc6e66a4cb13d223344122243b7237047a9ff3aa"
SOURCE="33b96850ad07547a9b12524de8bc46479fd98fbbce6772436d388be679836d66"
WORK=Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом - по чертежам 2022.pln")
ORIG=Path(r"C:\LocalAI\SafeBIM_Global_Library_Test_Projects\BDD дом .pln")
ROOT=Path(r"C:\LocalAI\APA_AC29_Stable")
LEDGER=Path(os.environ.get("LOCALAPPDATA",str(Path.home())))/"APA_BDD_Window1p8"/"apa_scene_writer.sqlite"
SRC="b8d528f0-ab6a-4ece-a62d-74e3a0d7c46c"
WOOD="e7ef3819-b3e8-419f-b313-5172e6b0412c"
XY=[(9.37,v) for v in [9.255,8.838,8.420,8.008,7.595,6.995,6.395]]
AUTH="USER_APPROVED_BDD_114_X_9_370_20261017"
COPY="BDD_114_APPROVED_SEVEN_COPY_20261017"
SAVE="BDD_114_APPROVED_SEVEN_SAVE_20261017"

def need(cond,reason):
    if not cond:raise ValueError(reason)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def near(a,b):return type(a) in (int,float) and abs(a-b)<0.00035
def info(api,guids):
    rows=api("GetDetailsOfElements",{"elements":[{"elementId":{"guid":g}} for g in guids]}).get("detailsOfElements")
    need(isinstance(rows,list) and len(rows)==len(guids),"DETAILS_CARDINALITY")
    return dict(zip(guids,rows))
def physical(row):
    v=[p for body in row.get("bodies",[]) for p in body["vertices"]]
    return [(min(p[i] for p in v),max(p[i] for p in v)) for i in range(3)] if v else None
def child(elements,g):
    children=[(k,e) for k,e in elements.items() if e["type"]=="ColumnSegment" and e.get("relationships",{}).get("hostGuid","").lower()==g]
    need(len(children)==1,"COLUMN_CHILD_OWNERSHIP_AMBIGUOUS")
    return children[0]
def verify_stud(detail,segment,point):
    d=detail["details"];o=d["origin"]
    need(detail["type"]=="Column" and detail["floorIndex"]==0,"STUD_TYPE_STORY_DRIFT")
    need(all(near(d.get(k),v) for k,v in [("width",.1),("depth",.05),("height",2.9),("zCoordinate",0),("axisRotationAngle",0)]),"STUD_DIMENSION_DRIFT")
    need(near(o["x"],point[0]) and near(o["y"],point[1]),"STUD_LOCATION_DRIFT")
    need(d["buildingMaterialId"]["guid"].lower()==WOOD,"STUD_MATERIAL_DRIFT")
    b=physical(segment)
    need(segment["materialBindings"]["buildingMaterial"]["guid"].lower()==WOOD and b is not None,"STUD_SEGMENT_BREP_OR_WOOD_DRIFT")
    need(all(near(b[i][0],point[i]-h) and near(b[i][1],point[i]+h) for i,h in enumerate([.05,.025])) and near(b[2][0],0) and near(b[2][1],2.9),"STUD_NATIVE_BREP_DRIFT")

def run(folder,approval):
    need(approval==AUTH,"SOURCE_EXPLICIT_WRITE_AUTHORIZATION_MISSING")
    need(digest(WORK)==BASE and digest(ORIG)==SOURCE,"SAVED_WORK_OR_PROTECTED_SOURCE_CHANGED")
    need((folder/"attempted.json").is_file(),"JOB_ATTEMPT_JOURNAL_MISSING")
    need(LEDGER.is_file(),"ORIGINAL_SCENE_WRITER_LEDGER_MISSING")
    with sqlite3.connect(f"file:{LEDGER.as_posix()}?mode=ro",uri=True) as db:
        need(not any(db.execute("SELECT 1 FROM scenes WHERE scene_id=?",(sid,)).fetchone() for sid in (COPY,SAVE)),"SCENE_ALREADY_USED_NO_RETRY")
        unresolved=db.execute("SELECT scene_id,state,result FROM scenes WHERE state != 'PASS'").fetchall()
        # Historical BDD 150-copy scene did dispatch: its native response
        # preceded a verifier bug (GetAllElements has GUIDs but no type).
        # Preserve this UNKNOWN journal record, never call the 150-copy again.
        # Current 290 GUID + exact file SHA and the native BREP preflight below
        # are mandatory before a separate one-shot BDD 1.14 scene.
        need(len(unresolved)==1 and unresolved[0][0]=="BDD_BULK150_GRID_AND_LINE_20261016" and
             unresolved[0][1]=="PARTIAL_OR_UNKNOWN_OUTCOME",
             "UNRELATED_UNRECONCILED_SCENE")
        previous=json.loads(unresolved[0][2])
        need(previous.get("reason")=="ValueError: MASS_COPY_UNEXPECTED_NATIVE_ELEMENT_TYPES" and
             bool(previous.get("nativeResponse")),
             "HISTORIC_SCENE_FAILURE_REASON_OR_RESPONSE_DRIFT")
    sys.path.insert(0,str(ROOT/"scripts"))
    import archicad_project_accelerator as APA
    import archicad_scene_run as RUN
    import archicad_connected_components as C
    import archicad_bim_documentation as D
    schema=ROOT/"schemas/tapir-live-1.5.10/tapir-scene-live.json"
    need(schema.is_file(),"INSTALLED_APA_SCHEMA_MISSING")
    RUN.bind_authorized_saved_copy(19727,str(WORK),WORK.stem,BASE,AUTH)
    saved_hash=[None];grant=[False]
    def transport(cmd,params):
        if cmd=="SaveProject":need(grant[0] and params=={},"EARLY_SAVE_FORBIDDEN")
        reply=APA.native_transport(cmd,params)
        if cmd=="SaveProject":
            need(reply=={"success":True},"NATIVE_SAVE_NOT_CONFIRMED")
            new=digest(WORK)
            need(new!=BASE and digest(ORIG)==SOURCE,"WORKING_SAVE_HASH_PROOF_FAILED")
            RUN.bind_authorized_saved_copy(19727,str(WORK),WORK.stem,new,AUTH+":SAVED")
            saved_hash[0]=new
        return reply
    raw=folder/"raw";raw.mkdir(exist_ok=False)
    api=APA.EvidenceAPI(transport,raw,execute=True)
    binding=RUN.guarded_project_for_read(api)
    need(binding["activeViewStoryIndex"] in (0,-1),"REQUIRES_STORY_0_OR_3D")
    need(APA.archicad29(api).get("buildNumber")==5101,"ARCHICAD_29_BUILD_MISMATCH")
    before=set(APA.inventory_guids(api))
    need(len(before)==290 and SRC in before,"EXACT_290_NATIVE_MODEL_REQUIRED")
    dump=D.capture_full_model(api,sorted(before))
    old={e["guid"].lower():e for e in C.G.normalize_dump(dump)["elements"]}
    need(set(old)==before,"MODEL_DUMP_INCOMPLETE")
    # Fresh sloped-roof assessment on the live model; old AABB evidence is not enough.
    import importlib.util
    from shapely.geometry import box
    review_path=ROOT/"controllers"/"apa_bdd114_native_roof_face_review.py"
    need(review_path.is_file(),"REVIEWED_NATIVE_ROOF_CHECKER_MISSING")
    review_bytes=review_path.read_bytes()
    review_blob=hashlib.sha1(b"blob "+str(len(review_bytes)).encode()+bytes([0])+review_bytes).hexdigest()
    need(review_blob=="35a7bd794317ba91056334aff6801cd0ec71f220","NATIVE_ROOF_CHECKER_SOURCE_DRIFT")
    spec=importlib.util.spec_from_file_location("bdd114_approved_roof",review_path)
    roofcheck=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(roofcheck)
    roof=old["f0d643a1-b236-4dfc-844a-98424a12b9b7"]
    north=old["7b332594-ab82-43b4-bfc2-ab5ad549c2c9"]
    need(roof["type"]=="Roof" and north["type"]=="Wall","NATIVE_STRUCTURE_DRIFT")
    north_box=physical(north)
    need(north_box is not None,"NORTH_WALL_BREP_MISSING")
    for index,(x,y) in enumerate(XY):
        candidate=box(x-.05,y-.025,x+.05,y+.025)
        lowest,face_count=roofcheck.minimum_native_roof_height_over_footprint(roof,C.G,candidate)
        need(face_count>=1 and lowest>2.902,"NATIVE_ROOF_FACE_CLEARANCE_FAILED:"+str(index+1))
        block=[(x-.05,x+.05),(y-.025,y+.025),(0,2.9)]
        joint=all(block[k][0]<north_box[k][1]-1e-8 and north_box[k][0]<block[k][1]-1e-8 for k in range(3))
        need(joint==(index==0),"NORTH_WALL_STUD_JUNCTION_DRIFT:"+str(index+1))
        for guid,element in old.items():
            if guid in (roof["guid"].lower(),north["guid"].lower()):continue
            if element["type"]=="ColumnSegment":continue
            for body in element.get("bodies",[]):
                vertices=body.get("vertices",[])
                if not vertices:continue
                bounds=[(min(p[k] for p in vertices),max(p[k] for p in vertices)) for k in range(3)]
                need(not all(block[k][0]<bounds[k][1]-1e-8 and bounds[k][0]<block[k][1]-1e-8 for k in range(3)),
                     "OTHER_NATIVE_BREP_ENVELOPE_INTERSECTION:"+guid)
    original=info(api,[SRC])[SRC];sg,seg=child(old,SRC)
    verify_stud(original,seg,(3.53,9.255))
    # Avoid any existing physical column at intended locations.
    for guid,row in old.items():
        if row["type"]!="ColumnSegment":continue
        box=physical(row)
        if box:
            for x,y in XY:
                need(not(box[0][0]<x+.05 and x-.05<box[0][1] and box[1][0]<y+.025 and y-.025<box[1][1]),"EXISTING_STUD_OCCUPIES_DESTINATION")
    original_sig=RUN.digest({"root":C.ROOF.geometry_signature(old[SRC]),"segment":C.ROOF.geometry_signature(seg),"details":original})
    retained=sorted(before-{SRC})
    sig=C.retained_geometry_signatures(dump,retained)
    need(set(sig)==set(retained),"RETAINED_BREP_INCOMPLETE")
    router=APA.native_command_router(schema,include_functional_modules=False)
    for name,kind,impact in [("MoveElements","CREATE","MODEL"),("SaveProject","TRANSACTION","PROJECT")]:
        router.review_policy(name,kind,impact,{"source":AUTH,"sha256":router.contract_hash(name)})
    writer=RUN.SceneWriter(api,LEDGER,schema_path=schema,allow_3d_view_for_write=True)
    vectors=[{"x":round(x-3.53,6),"y":round(y-9.255,6),"z":0.} for x,y in XY]
    report_path=folder/"native-write-result.json"
    result={"schema":"APA_BDD114_NATIVE_SEVEN_COPY_SAVE_V1","status":"INTENT_RECORDED","modelWrites":0,"copyScene":COPY,"saveScene":SAVE}
    report_path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    created=[];full_post=[None];post_guids=[]
    def check_before(native_api):
        need(set(APA.inventory_guids(native_api))==before and digest(WORK)==BASE and digest(ORIG)==SOURCE,"PREWRITE_GUID_OR_FILE_DRIFT")
        return {"status":"SOURCE_AND_290_MODEL_PASS"}
    def check_after(reply,prior):
        post=set(APA.inventory_guids(api));new=post-before
        need(before<=post and len(post)==304 and len(new)==14,"SEVEN_PLUS_SEVEN_GUID_DELTA_REQUIRED")
        native=D.capture_full_model(api,sorted(post))
        elements={e["guid"].lower():e for e in C.G.normalize_dump(native)["elements"]}
        need(set(elements)==post,"NEW_NATIVE_BREP_INCOMPLETE")
        roots=sorted(g for g in new if elements[g]["type"]=="Column")
        kids={g for g in new if elements[g]["type"]=="ColumnSegment"}
        need(len(roots)==len(kids)==7,"EXACT_NEW_ROOT_AND_CHILD_COUNT_REQUIRED")
        typed=info(api,roots)
        matched=set()
        for xy in XY:
            choices=[g for g in roots if near(typed[g]["details"]["origin"]["x"],xy[0]) and near(typed[g]["details"]["origin"]["y"],xy[1])]
            need(len(choices)==1 and choices[0] not in matched,"NEW_ROOT_COORDINATE_NOT_UNIQUE")
            g=choices[0];ch,segment=child(elements,g)
            need(ch in kids,"NEW_SEGMENT_OWNER_OR_GUID_DRIFT")
            verify_stud(typed[g],segment,xy);matched.add(g)
        preserved=info(api,[SRC])[SRC]
        child_id,source_segment=child(elements,SRC)
        need(child_id==sg and RUN.digest({"root":C.ROOF.geometry_signature(elements[SRC]),"segment":C.ROOF.geometry_signature(source_segment),"details":preserved})==original_sig,"SOURCE_PROTOTYPE_CHANGED")
        need(digest(WORK)==BASE and digest(ORIG)==SOURCE,"COPY_SAVED_UNEXPECTEDLY")
        created.extend(roots);post_guids.extend(sorted(post));full_post[0]=native
        return {"status":"BDD114_SEVEN_COLUMN_BREP_PASS","newPhysicalCopyCount":7,"prototypeGuidUnchanged":True,"createdRoots":roots,"createdSegments":sorted(kids)}
    outcome=router.copy_existing_many(writer,COPY,SRC,"Column",vectors,sig,BASE,AUTH,check_before,check_after)
    result.update(status="COPY_PASS_UNSAVED" if outcome["status"]=="PASS" else "UNKNOWN_COPY_NEVER_RETRY",modelWrites=api.write_attempts,copyCalls=api.calls["MoveElements"])
    report_path.write_text(json.dumps(result,indent=2)+"\n",encoding="utf8")
    need(outcome["status"]=="PASS" and api.calls["MoveElements"]==1 and len(created)==7 and full_post[0] is not None,"COPY_PASS_REQUIRED_BEFORE_SAVE")
    signatures=C.retained_geometry_signatures(full_post[0],post_guids)
    need(len(signatures)==304,"SAVE_NEEDS_304_BREP_SIGNATURES")
    grant[0]=True
    def before_save(_):
        need(set(APA.inventory_guids(api))==set(post_guids) and digest(WORK)==BASE and digest(ORIG)==SOURCE,"SAVE_MODEL_DRIFT")
        return {"status":"COPY_READBACK_AND_304_MODEL_PASS"}
    def after_save(reply,prior):
        need(reply=={"success":True} and saved_hash[0] and digest(WORK)==saved_hash[0] and digest(ORIG)==SOURCE and set(APA.inventory_guids(api))==set(post_guids),"SAVE_READBACK_FAILED")
        return {"status":"WORKING_PLN_304_GUID_SAVED_PASS","savedSha256":saved_hash[0]}
    saved=router.execute(writer,SAVE,router.prepare("SaveProject",{}),[],signatures,BASE,AUTH,"PROJECT",after_save,verify_before=before_save)
    result.update(status="BDD114_SEVEN_NATIVE_COPIES_AND_SAVE_PASS" if saved["status"]=="PASS" else "UNKNOWN_SAVE_NEVER_RETRY",modelWrites=api.write_attempts,saveCalls=api.calls["SaveProject"],savedSha256=saved_hash[0],newColumnGuids=created,finalGuidCount=304)
    report_path.write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    need(saved["status"]=="PASS" and api.calls["SaveProject"]==1,"SINGLE_SAVE_NOT_CONFIRMED")
    print("APA_STATUS:",result["status"])
    print("GUIDS: 304 | MOVE_CALLS: 1 | SAVE_CALLS: 1")
    print("REPORT:",report_path)

if __name__=="__main__":
    ap=argparse.ArgumentParser();ap.add_argument("--job-folder",required=True);ap.add_argument("--approval",required=True)
    a=ap.parse_args()
    try:run(Path(a.job_folder),a.approval)
    except Exception as e:
        print("APA_STATUS: BLOCKED_OR_UNKNOWN_DO_NOT_RETRY",flush=True)
        print("ERROR:",type(e).__name__+": "+str(e),flush=True);sys.exit(2)
