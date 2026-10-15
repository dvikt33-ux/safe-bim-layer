// Extend the existing edit state/masked Element_Change. Public SDK memo only;
// native IDs, counts, allocation ownership and pattern topology are retained.
static GSSize MemoCoordCount(API_Coord** p){return p?BMGetHandleSize(reinterpret_cast<GSHandle>(p))/sizeof(API_Coord)-1:0;}
static bool MemoPointerBounded(const void* p,USize count,USize size){return count<=4096&&(count==0||(p&&BMGetPtrSize(reinterpret_cast<GSPtr>(const_cast<void*>(p)))>=static_cast<GSSize>(count*size)));}
static GS::ObjectState NativePattern(const API_CWSegmentPatternData& p){
 GS::ObjectState out("logicId",static_cast<Int32>(p.logic),"originTypeId",static_cast<Int32>(p.gridOriginType),"divisions",p.nDivisions,"infillPanelClassId",p.infillPanelID,"endWithId",p.endWithID);
 const auto& distances=out.AddList<double>("distances");for(UIndex i=0;i<p.nPattern;++i)distances(p.pattern[i]);const auto& flexible=out.AddList<UInt32>("flexibleIds");for(UIndex i=0;i<p.nFlexibleIDs;++i)flexible(p.flexibleIDs[i]);return out;
}
static void AddAssemblyMemo(const API_Element& e,GS::ObjectState& row){
 GS::Array<GS::UniString> edits;
 if(e.header.type.typeID==API_ShellID){if(e.shell.shellClass==API_ExtrudedShellID&&e.shell.u.extrudedShell.shellShape.nArcs==0&&e.shell.u.extrudedShell.shellShape.nSubPolys==1)edits.Push("profileCoordinates");row.Add("memoEdits",edits);return;}
 if(e.header.type.typeID!=API_CurtainWallID&&e.header.type.typeID!=API_RailingID)return;
 API_ElementMemo memo={};const GS::OnExit cleanup([&](){ACAPI_DisposeElemMemoHdls(&memo);});const auto error=ACAPI_Element_GetMemo(e.header.guid,&memo,APIMemoMask_All);row.Add("memoReadError",static_cast<Int32>(error));if(error!=NoError){row.Add("memoEdits",edits);return;}
 const auto n=MemoCoordCount(memo.coords);if(n<0||n>4096){row.Add("memoBoundsStatus","REFERENCE_ALLOCATION_OUTSIDE_BOUNDED_CONTRACT");row.Add("memoEdits",edits);return;}
 GS::ObjectState data("authority","NATIVE_PARAMETER_MEMO_NOT_RESULTANT_BREP","referencePath",PolygonMemo(memo.coords,memo.pends,memo.parcs,memo.vertexIDs,memo.edgeIDs));
 if(e.header.type.typeID==API_RailingID){const auto nz=memo.polyZCoords?BMGetHandleSize(reinterpret_cast<GSHandle>(memo.polyZCoords))/sizeof(double)-1:0;const auto& z=data.AddList<double>("referenceElevationsMetres");if(nz>=0&&nz<=4096)for(GSIndex i=1;i<=nz;++i)z((*memo.polyZCoords)[i]);data.Add("associationAuthority","NOT_EXPOSED_NO_STAIR_INFERENCE");row.Add("memoPathWriteBlockedReason","NATIVE_ASSOCIATION_EDIT_CONTRACT_NOT_QUALIFIED");}
 else{
  if(n>=2&&(!memo.parcs||BMGetHandleSize(reinterpret_cast<GSHandle>(memo.parcs))==0))edits.Push("referenceCoordinates");
  const auto& p=memo.cWSegPrimaryPattern;const auto& s=memo.cWSegSecondaryPattern;
  if(!MemoPointerBounded(p.pattern,p.nPattern,sizeof(double))||!MemoPointerBounded(p.flexibleIDs,p.nFlexibleIDs,sizeof(UInt32))||!MemoPointerBounded(s.pattern,s.nPattern,sizeof(double))||!MemoPointerBounded(s.flexibleIDs,s.nFlexibleIDs,sizeof(UInt32))){row.Add("memoBoundsStatus","PATTERN_ALLOCATION_SHORT_OR_UNBOUNDED");row.Add("memoEdits",GS::Array<GS::UniString>{});return;}
  data.Add("primaryPattern",NativePattern(p));data.Add("secondaryPattern",NativePattern(s));if(p.nPattern)edits.Push("primaryPatternDistances");if(s.nPattern)edits.Push("secondaryPatternDistances");
  const auto nc=memo.cWSegContour?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.cWSegContour))/sizeof(API_CWContourData):0;
  const auto ns=memo.cWallSegments?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.cWallSegments))/sizeof(API_CWSegmentType):0;if(nc>4096||ns>4096){row.Add("memoBoundsStatus","SEGMENT_OR_CONTOUR_ALLOCATION_UNBOUNDED");row.Add("memoEdits",GS::Array<GS::UniString>{});return;}
  const auto& contours=data.AddList<GS::ObjectState>("curtainWallContours");for(GSIndex i=0;i<nc;++i){const auto& c=memo.cWSegContour[i];const auto count=MemoCoordCount(c.coords);if(count<0||count>4096||c.polygon.nCoords>count)continue;contours(GS::ObjectState("slot",static_cast<Int32>(i),"polygon",PolygonMemo(c.coords,c.pends,c.parcs,c.vertexIDs),"nativeCoordinateCount",c.polygon.nCoords));}
  if(nc==1&&e.curtainWall.nSegments==1&&memo.cWSegContour[0].polygon.nArcs==0&&memo.cWSegContour[0].polygon.nSubPolys==1)edits.Push("curtainWallContourCoordinates");
  const auto& segments=data.AddList<GS::ObjectState>("curtainWallSegments");for(GSIndex i=0;i<ns;++i){const auto& c=memo.cWallSegments[i];segments(GS::ObjectState("elementId",CreateGuidObjectState(c.head.guid),"ownerId",CreateGuidObjectState(c.owner),"begin",NativeXYZ(c.begC),"end",NativeXYZ(c.endC),"extrusion",NativeXYZ(c.extrusion),"gridOrigin",NativeXYZ(c.gridOrigin),"gridAngleNative",c.gridAngle,"segmentTypeId",static_cast<Int32>(c.segmentType),"patternCellCount",c.patternCellNum));}
  data.Add("planeMatrix",Transform(e.curtainWall.planeMatrix));data.Add("planeOffsetMetres",e.curtainWall.planeOffset);
 }
 row.Add("memo",data);row.Add("memoEdits",edits);
}
static GSErrCode ReplaceStraightMemoCoords(API_Coord** coords,const GS::ObjectState& changes,const char* key,GS::Array<GS::UniString>& applied){
 GS::Array<GS::ObjectState> input;const auto n=MemoCoordCount(coords);if(n<2||n>4096||!changes.Get(key,input)||input.GetSize()!=static_cast<USize>(n))return APIERR_BADPARS;
 const bool closed=(*coords)[1].x==(*coords)[n].x&&(*coords)[1].y==(*coords)[n].y;
 for(UIndex i=0;i<input.GetSize();++i){double x=0,y=0;if(!input[i].Get("x",x)||!input[i].Get("y",y)||!std::isfinite(x)||!std::isfinite(y)||std::abs(x)>1000000||std::abs(y)>1000000)return APIERR_BADPARS;(*coords)[i+1]={x,y};}
 if(closed&&((*coords)[1].x!=(*coords)[n].x||(*coords)[1].y!=(*coords)[n].y))return APIERR_BADPARS;applied.Push(key);return NoError;
}
static GSErrCode PrepareAssemblyMemoEdits(const API_Element& e,const GS::ObjectState& changes,API_ElementMemo& memo,UInt64& mask,GS::Array<GS::UniString>& applied){
 const bool ref=changes.Contains("referenceCoordinates"),contour=changes.Contains("curtainWallContourCoordinates"),primary=changes.Contains("primaryPatternDistances"),secondary=changes.Contains("secondaryPatternDistances");if(!ref&&!contour&&!primary&&!secondary)return NoError;
 if(e.header.type.typeID!=API_CurtainWallID)return APIERR_BADPARS;auto err=ACAPI_Element_GetMemo(e.header.guid,&memo,APIMemoMask_All);if(err!=NoError)return err;
 if(ref){if(memo.parcs&&BMGetHandleSize(reinterpret_cast<GSHandle>(memo.parcs))!=0)return APIERR_BADPARS;err=ReplaceStraightMemoCoords(memo.coords,changes,"referenceCoordinates",applied);if(err!=NoError)return err;mask|=APIMemoMask_Polygon;}
 if(contour){if(e.curtainWall.nSegments!=1||!MemoPointerBounded(memo.cWSegContour,1,sizeof(API_CWContourData))||BMGetPtrSize(reinterpret_cast<GSPtr>(memo.cWSegContour))!=sizeof(API_CWContourData))return APIERR_BADPARS;const auto& c=memo.cWSegContour[0];if(c.polygon.nArcs||c.polygon.nSubPolys!=1||c.polygon.nCoords!=MemoCoordCount(c.coords))return APIERR_BADPARS;err=ReplaceStraightMemoCoords(c.coords,changes,"curtainWallContourCoordinates",applied);if(err!=NoError)return err;mask|=APIMemoMask_CWSegContour;}
 const auto pattern=[&](const char* key,API_CWSegmentPatternData& p,UInt64 bit){GS::Array<double> values;if(!changes.Get(key,values)||p.nPattern==0||values.GetSize()!=p.nPattern||!MemoPointerBounded(p.pattern,p.nPattern,sizeof(double)))return static_cast<GSErrCode>(APIERR_BADPARS);for(UIndex i=0;i<values.GetSize();++i){if(!std::isfinite(values[i])||values[i]<=0||values[i]>1000000)return static_cast<GSErrCode>(APIERR_BADPARS);p.pattern[i]=values[i];}mask|=bit;applied.Push(key);return static_cast<GSErrCode>(NoError);};
 if(primary){err=pattern("primaryPatternDistances",memo.cWSegPrimaryPattern,APIMemoMask_CWSegPrimaryPattern);if(err!=NoError)return err;}if(secondary){err=pattern("secondaryPatternDistances",memo.cWSegSecondaryPattern,APIMemoMask_CWSegSecPattern);if(err!=NoError)return err;}return NoError;
}
