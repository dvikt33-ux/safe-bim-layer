// Thin public SDK Element_Test defaults+Create paths for previously unexposed
// native tools. Called only by the existing SceneWriter with scoped CREATE.
GS::ObjectState CreateNativeAssemblyV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::UniString kind;p.Get("kind",kind);double length=0,height=0,depth=0,level=0;Int32 story=0;p.Get("length",length);p.Get("height",height);p.Get("extrusionDepth",depth);p.Get("relativeLevel",level);p.Get("homeStory",story);const auto* origin=p.Get("origin");double x=0,y=0;if(origin){origin->Get("x",x);origin->Get("y",y);}
 if(origin==nullptr||length<=0||height<=0||story< -100||story>100)return CreateErrorResponse(APIERR_BADPARS,"Explicit bounded geometry required");
 API_Element e={};API_ElementMemo memo={};const GS::OnExit cleanup([&](){ACAPI_DisposeElemMemoHdls(&memo);});
 if(kind=="CurtainWall")e.header.type=API_CurtainWallID;else if(kind=="Railing")e.header.type=API_RailingID;else if(kind=="ExtrudedShell"){e.header.type=API_ShellID;e.shell.shellClass=API_ExtrudedShellID;}else return CreateErrorResponse(APIERR_BADID,"Unsupported native assembly type");
 auto err=ACAPI_Element_GetDefaults(&e,&memo);if(err!=NoError)return CreateErrorResponse(err,"Native assembly defaults unavailable");e.header.floorInd=static_cast<short>(story);
 if(kind=="ExtrudedShell"){
 if(depth<=0)return CreateErrorResponse(APIERR_BADPARS,"Shell extrusion depth required");e.shell.shellClass=API_ExtrudedShellID;e.shell.shellBase.level=level;auto& shape=e.shell.u.extrudedShell.shellShape;shape.nCoords=4;shape.nSubPolys=1;shape.nArcs=0;auto& m=memo.shellShapes[0];
 if(m.coords)BMKillHandle(reinterpret_cast<GSHandle*>(&m.coords));if(m.pends)BMKillHandle(reinterpret_cast<GSHandle*>(&m.pends));if(m.parcs)BMKillHandle(reinterpret_cast<GSHandle*>(&m.parcs));if(m.bodyFlags)BMKillHandle(reinterpret_cast<GSHandle*>(&m.bodyFlags));
 m.coords=reinterpret_cast<API_Coord**>(BMAllocateHandle(5*sizeof(API_Coord),ALLOCATE_CLEAR,0));m.pends=reinterpret_cast<Int32**>(BMAllocateHandle(2*sizeof(Int32),ALLOCATE_CLEAR,0));m.bodyFlags=reinterpret_cast<bool**>(BMAllocateHandle(5*sizeof(bool),ALLOCATE_CLEAR,0));if(!m.coords||!m.pends||!m.bodyFlags)return CreateErrorResponse(APIERR_MEMFULL,"Shell profile allocation failed");
 (*m.coords)[1]={-length/2,0};(*m.coords)[2]={0,height};(*m.coords)[3]={length/2,0};(*m.coords)[4]=(*m.coords)[1];(*m.pends)[1]=4;(*m.bodyFlags)[1]=true;(*m.bodyFlags)[2]=true;(*m.bodyFlags)[3]=false;(*m.bodyFlags)[4]=true;e.shell.u.extrudedShell.begC={x,y,0};e.shell.u.extrudedShell.extrusionVector={0,depth,0};
 }else{
 if(memo.coords)BMKillHandle(reinterpret_cast<GSHandle*>(&memo.coords));if(memo.parcs)BMKillHandle(reinterpret_cast<GSHandle*>(&memo.parcs));memo.coords=reinterpret_cast<API_Coord**>(BMAllocateHandle(3*sizeof(API_Coord),ALLOCATE_CLEAR,0));if(!memo.coords)return CreateErrorResponse(APIERR_MEMFULL,"Reference line allocation failed");(*memo.coords)[1]={x,y};(*memo.coords)[2]={x+length,y};
 if(kind=="CurtainWall"){e.curtainWall.nSegments=1;e.curtainWall.height=height;e.curtainWall.storyRelLevel=level;}
 else{e.railing.nVertices=2;e.railing.bottomOffset=level;e.railing.defSegment.height=height;if(memo.polyZCoords)BMKillHandle(reinterpret_cast<GSHandle*>(&memo.polyZCoords));memo.polyZCoords=reinterpret_cast<double**>(BMAllocateHandle(3*sizeof(double),ALLOCATE_CLEAR,0));if(!memo.polyZCoords)return CreateErrorResponse(APIERR_MEMFULL,"Railing reference elevations allocation failed");}
 }
 err=ACAPI_CallUndoableCommand("APA native assembly",[&](){return ACAPI_Element_Create(&e,&memo);});if(err!=NoError)return CreateErrorResponse(err,"Native assembly creation failed");
 GS::ObjectState out("nativeModelWrites",1,"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"homeStory",static_cast<Int32>(e.header.floorInd),"placementFrame","HOME_STORY_RELATIVE_LEVEL","engineering","NOT_VERIFIED");const auto& list=out.AddList<GS::ObjectState>("createdElements");list(GS::ObjectState("elementId",CreateGuidObjectState(e.header.guid)));return out;
}
