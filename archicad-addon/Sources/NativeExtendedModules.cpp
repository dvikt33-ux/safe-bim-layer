#include "NativeExtendedModules.hpp"
#include "MigrationHelper.hpp"
#include <algorithm>
#include "Polygon2D.hpp"
#include "ACAPI/Element/Opening/Opening.hpp"
#include "ACAPI/Element/Opening/OpeningGeometry.hpp"
#include "ACAPI/Element/Opening/OpeningExtrusionParameters.hpp"

#define DEF(name) name##Command::name##Command():CommandBase(CommonSchema::NotUsed){} GS::String name##Command::GetName() const {return #name;}
DEF(GetNativeEnvelopeMemoV1)
DEF(GetNativeDrawingAssociationsV1)
DEF(GetNativeElementHotspotsV1)
DEF(GetNativeElementQuantitiesV1)
DEF(GetNativeComponentBindingsV1)
DEF(GetNativeOpeningConnectionsV1)
DEF(GetNativeQuantityPreflightV1)
DEF(GetNativeLibraryPartDefaultsV1)
DEF(GetNativeNavigatorBindingsV1)
DEF(CreateNativeAssemblyV1)
DEF(GetNativeAssemblyEditStateV1)
DEF(ModifyNativeAssemblyV1)
DEF(GetNativeMEPTopologyV1)
#undef DEF
#include "NativeExtendedSchemas.inc"

static GS::ObjectState PolygonMemo(API_Coord** coords,Int32** ends,API_PolyArc** arcs,UInt32** vertices=nullptr,UInt32** edges=nullptr) {
 GS::ObjectState out("indexBase",1,"coordinateFrame","NATIVE_PARAMETER_POLYGON_NOT_RESULTANT_BREP");
 const auto& c=out.AddList<GS::ObjectState>("coordinates");auto n=coords?BMGetHandleSize(reinterpret_cast<GSHandle>(coords))/sizeof(API_Coord):0;
 for(GSIndex i=1;i<n;++i)c(GS::ObjectState("index",static_cast<Int32>(i),"x",(*coords)[i].x,"y",(*coords)[i].y));
 const auto& p=out.AddList<Int32>("contourEnds");n=ends?BMGetHandleSize(reinterpret_cast<GSHandle>(ends))/sizeof(Int32):0;for(GSIndex i=1;i<n;++i)p((*ends)[i]);
 const auto& a=out.AddList<GS::ObjectState>("arcs");n=arcs?BMGetHandleSize(reinterpret_cast<GSHandle>(arcs))/sizeof(API_PolyArc):0;for(GSIndex i=0;i<n;++i)a(GS::ObjectState("beginIndex",(*arcs)[i].begIndex,"endIndex",(*arcs)[i].endIndex,"angle",(*arcs)[i].arcAngle));
 const auto& v=out.AddList<UInt32>("vertexIds");n=vertices?BMGetHandleSize(reinterpret_cast<GSHandle>(vertices))/sizeof(UInt32):0;for(GSIndex i=1;i<n;++i)v((*vertices)[i]);
 const auto& e=out.AddList<UInt32>("edgeIds");n=edges?BMGetHandleSize(reinterpret_cast<GSHandle>(edges))/sizeof(UInt32):0;for(GSIndex i=1;i<n;++i)e((*edges)[i]);return out;
}
static GSErrCode ReadElement(const GS::ObjectState& item,API_Element& e) {
 const auto* id=item.Get("elementId");if(id==nullptr)return APIERR_BADPARS;e.header.guid=GetGuidFromObjectState(*id);return ACAPI_Element_Get(&e);
}

static GS::ObjectState NativeXYZ(const API_Coord3D& c){return GS::ObjectState("x",c.x,"y",c.y,"z",c.z);}
static GS::ObjectState ShellBaseParameters(const API_ShellBaseType& base){
 GS::ObjectState out("structureTypeId",static_cast<Int32>(base.modelElemStructureType),"relativeLevelMetres",base.level,"thicknessMetres",base.thickness,
  "buildingMaterialApplicable",base.modelElemStructureType==API_BasicStructure,"compositeApplicable",base.modelElemStructureType==API_CompositeStructure,
  "buildingMaterialIndex",GetAttributeIndex(base.buildingMaterial),"compositeIndex",GetAttributeIndex(base.composite));
 const auto& surfaces=out.AddList<GS::ObjectState>("surfaceOverrides");
 surfaces(GS::ObjectState("role","top","overridden",base.topMat.hasValue,"surfaceIndex",GetAttributeIndex(base.topMat.value)));
 surfaces(GS::ObjectState("role","side","overridden",base.sidMat.hasValue,"surfaceIndex",GetAttributeIndex(base.sidMat.value)));
 surfaces(GS::ObjectState("role","bottom","overridden",base.botMat.hasValue,"surfaceIndex",GetAttributeIndex(base.botMat.value)));
 return out;
}
// Modern polygon accessors avoid legacy Opening memo layout assumptions. The
// iterators keep contour membership, directed edges and arc angles together.
static GS::ObjectState OpeningPolygon(const Geometry::Polygon2D& polygon){
 GS::ObjectState out("coordinateFrame","OPENING_NATIVE_POLYGON_2D_WITH_RAW_FRAME_SEPARATE","contourCount",static_cast<Int32>(polygon.GetContourNum()));
 const auto& contours=out.AddList<GS::ObjectState>("contours");
 for(auto c=polygon.BeginContour();c!=polygon.EndContour();++c){
  GS::ObjectState contour;const auto& edges=contour.AddList<GS::ObjectState>("edges");
  for(auto e=c->BeginEdge();e!=c->EndEdge();++e){
   const auto& begin=polygon.GetCoord(polygon.GetBeginVertex(e));const auto& end=polygon.GetCoord(polygon.GetEndVertex(e));
   edges(GS::ObjectState("begin",GS::ObjectState("x",begin.x,"y",begin.y),"end",GS::ObjectState("x",end.x,"y",end.y),"arcAngleRadians",polygon.GetEdge(e).GetArcAngle()));
  }contours(contour);
 }return out;
}
static GS::ObjectState Transform(const API_Tranmat& t){GS::ObjectState out;const auto& values=out.AddList<double>("matrix3x4");for(double v:t.tmx)values(v);return out;}
static GS::ObjectState ShellClassParameters(const API_ShellType& shell){
 GS::ObjectState out("coordinateFrame","NATIVE_PARAMETER_GEOMETRY_SHELL_LOCAL_FRAME_NOT_RESULTANT_BREP");
 switch(shell.shellClass){
 case API_ExtrudedShellID:{const auto& c=shell.u.extrudedShell;out.Add("class","Extruded");out.Add("begin",NativeXYZ(c.begC));out.Add("extrusionVector",NativeXYZ(c.extrusionVector));out.Add("shapeDirection",GS::ObjectState("x",c.shapeDirection.x,"y",c.shapeDirection.y));out.Add("slantAngleRadians",c.slantAngle);out.Add("shapePlaneTiltRadians",c.shapePlaneTilt);out.Add("beginPlaneTiltRadians",c.begPlaneTilt);out.Add("endPlaneTiltRadians",c.endPlaneTilt);break;}
 case API_RevolvedShellID:{const auto& c=shell.u.revolvedShell;out.Add("class","Revolved");out.Add("axisBase",Transform(c.axisBase));out.Add("slantAngleRadians",c.slantAngle);out.Add("revolutionAngleRadians",c.revolutionAngle);out.Add("distortionAngleRadians",c.distortionAngle);out.Add("beginAngleRadians",c.begAngle);out.Add("distortionVector",GS::ObjectState("x",c.distortionVector.x,"y",c.distortionVector.y));out.Add("segmentTypeId",static_cast<Int32>(c.segmentType));out.Add("segmentsByArc",c.segmentsByArc);out.Add("segmentsByCircle",c.segmentsByCircle);out.Add("segmentedSurfaces",c.segmentedSurfaces);break;}
 case API_RuledShellID:{const auto& c=shell.u.ruledShell;out.Add("class","Ruled");out.Add("plane1",Transform(c.plane1));out.Add("plane2",Transform(c.plane2));out.Add("morphingRuleId",static_cast<Int32>(c.morphingRule));break;}
 default:out.Add("class","UNSUPPORTED_SDK_CLASS");break;
 }return out;
}
static GS::ObjectState ContourEdge(const API_ContourEdgeData& edge){return GS::ObjectState("edgeTypeId",static_cast<Int32>(edge.edgeType),"sideTypeId",static_cast<Int32>(edge.edgeTrim.sideType),"sideAngleRadians",edge.edgeTrim.sideAngle,"surfaceOverridden",edge.sideMaterial.hasValue,"surfaceIndex",GetAttributeIndex(edge.sideMaterial.value));}
GS::ObjectState GetNativeEnvelopeMemoV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0,"authority","NATIVE_ENVELOPE_PARAMETER_MEMO_NOT_RESULTANT_BREP");const auto& rows=out.AddList<GS::ObjectState>("elements");
 for(const auto& item:inputs){API_Element e={};auto err=ReadElement(item,e);if(err!=NoError){rows(CreateErrorResponse(err,"Get envelope element"));continue;}
 if(e.header.type.typeID!=API_RoofID&&e.header.type.typeID!=API_SlabID&&e.header.type.typeID!=API_ShellID){rows(CreateErrorResponse(APIERR_BADID,"Roof Slab Shell required"));continue;}
 API_ElementMemo memo={};const GS::OnExit cleanup([&](){ACAPI_DisposeElemMemoHdls(&memo);});err=ACAPI_Element_GetMemo(e.header.guid,&memo,APIMemoMask_All);if(err!=NoError){rows(CreateErrorResponse(err,"Get envelope memo"));continue;}
 GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"homeStory",static_cast<Int32>(e.header.floorInd),"polygon",PolygonMemo(memo.coords,memo.pends,memo.parcs,memo.vertexIDs,memo.edgeIDs));
 if(e.header.type.typeID==API_RoofID)row.Add("shellBaseParameters",ShellBaseParameters(e.roof.shellBase));
 if(e.header.type.typeID==API_ShellID)row.Add("shellBaseParameters",ShellBaseParameters(e.shell.shellBase));
 const auto& roofEdges=row.AddList<Int32>("roofEdgeTypes");auto count=memo.roofEdgeTypes?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.roofEdgeTypes))/sizeof(API_RoofEdgeTypeID):0;for(GSIndex i=1;i<count;++i)roofEdges(static_cast<Int32>(memo.roofEdgeTypes[i]));
 if(e.header.type.typeID==API_RoofID){row.Add("roofClass",static_cast<Int32>(e.roof.roofClass));row.Add("pivotPolygon",PolygonMemo(memo.additionalPolyCoords,memo.additionalPolyPends,memo.additionalPolyParcs,memo.additionalPolyVertexIDs,memo.additionalPolyEdgeIDs));row.Add("roofLevel",e.roof.shellBase.level);}
 if(e.header.type.typeID==API_ShellID){row.Add("shellClass",static_cast<Int32>(e.shell.shellClass));const auto& shapes=row.AddList<GS::ObjectState>("shellShapes");for(Int32 i=0;i<2;++i)if(memo.shellShapes[i].coords){const auto& shape=memo.shellShapes[i];GS::ObjectState entry("slot",i,"polygon",PolygonMemo(shape.coords,shape.pends,shape.parcs,shape.vertexIDs,shape.edgeIDs));const auto& flags=entry.AddList<GS::ObjectState>("bodyFlags");const auto nf=shape.bodyFlags?BMGetHandleSize(reinterpret_cast<GSHandle>(shape.bodyFlags))/sizeof(bool):0;for(GSIndex j=0;j<nf;++j)flags(GS::ObjectState("allocationIndex",static_cast<Int32>(j),"generatesBody",(*shape.bodyFlags)[j]));entry.Add("bodyFlagIndexAuthority","RAW_NATIVE_ALLOCATION_INDEX_NO_REINDEXING");shapes(entry);}row.Add("shellClassParameters",ShellClassParameters(e.shell));
 const auto& contours=row.AddList<GS::ObjectState>("shellContours");if(e.shell.numHoles>4096){rows(CreateErrorResponse(APIERR_BADPARS,"Shell contour count exceeds bounded serialization"));continue;}const auto n=static_cast<Int32>(e.shell.numHoles)+(e.shell.hasContour?1:0);
 const auto allocated=memo.shellContours?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.shellContours))/sizeof(API_ShellContourData):0;
 row.Add("shellContourCountExpected",n);row.Add("shellContourCountAllocated",static_cast<Int32>(allocated));
 if(static_cast<GSSize>(n)>allocated){rows(CreateErrorResponse(APIERR_BADPARS,"Shell contour allocation shorter than element metadata"));continue;}
 if(memo.shellContours)for(Int32 i=0;i<n;++i){const auto& c=memo.shellContours[i];GS::ObjectState contour("slot",i,"hole",!e.shell.hasContour||i>0,"depth",c.height,"polygon",PolygonMemo(c.coords,c.pends,c.parcs,c.vertexIDs,c.edgeIDs));const auto& transform=contour.AddList<double>("planeTransform");for(double value:c.plane.tmx)transform(value);const auto ne=c.edgeData?BMGetPtrSize(reinterpret_cast<GSPtr>(c.edgeData))/sizeof(API_ContourEdgeData):0;const auto& edgeData=contour.AddList<GS::ObjectState>("edgeData");for(GSIndex j=0;j<ne;++j){GS::ObjectState edge=ContourEdge(c.edgeData[j]);edge.Add("allocationIndex",static_cast<Int32>(j));edgeData(edge);}contours(contour);}}

 const auto& trims=row.AddList<GS::ObjectState>("edgeTrims");auto nt=memo.edgeTrims?BMGetHandleSize(reinterpret_cast<GSHandle>(memo.edgeTrims))/sizeof(API_EdgeTrim):0;for(GSIndex i=1;i<nt;++i)trims(GS::ObjectState("memoIndex",static_cast<Int32>(i),"sideTypeId",static_cast<Int32>((*memo.edgeTrims)[i].sideType),"sideAngleRadians",(*memo.edgeTrims)[i].sideAngle));
 const auto& materials=row.AddList<GS::ObjectState>("sideMaterials");auto nm=memo.sideMaterials?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.sideMaterials))/sizeof(API_OverriddenAttribute):0;
 // SDK: first and final sideMaterials slots unused; preserve memo indices.
 for(GSIndex i=1;i+1<nm;++i){GS::ObjectState material("memoIndex",static_cast<Int32>(i),"overridden",memo.sideMaterials[i].hasValue);material.Add("surfaceIndex",GetAttributeIndex(memo.sideMaterials[i].value));materials(material);}
 const auto& pivots=row.AddList<GS::ObjectState>("pivotEdgeOverrides");auto np=memo.pivotPolyEdges?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.pivotPolyEdges))/sizeof(API_PivotPolyEdgeData):0;
 for(GSIndex i=1;i<np;++i){const auto& edge=memo.pivotPolyEdges[i];if(edge.nLevelEdgeData<0){rows(CreateErrorResponse(APIERR_BADPARS,"Negative pivot level count"));return out;}auto allocated=edge.levelEdgeData?BMGetPtrSize(reinterpret_cast<GSPtr>(edge.levelEdgeData))/sizeof(API_RoofSegmentData):0;if(static_cast<GSSize>(edge.nLevelEdgeData)>allocated){rows(CreateErrorResponse(APIERR_BADPARS,"Pivot level allocation shorter than count"));return out;}
 GS::ObjectState pivot("memoIndex",static_cast<Int32>(i),"pivotEdgeUniqueId",edge.pivotEdgeUnId,"segmentTypeId",static_cast<Int32>(edge.segmentType));const auto& levels=pivot.AddList<GS::ObjectState>("levels");for(Int32 j=0;j<edge.nLevelEdgeData;++j){const auto& level=edge.levelEdgeData[j];levels(GS::ObjectState("levelIndex",j,"angleRadians",level.angle,"angleTypeId",static_cast<Int32>(level.angleType),"eavesOverhangMetres",level.eavesOverhang,"topSurfaceIndex",GetAttributeIndex(level.topMaterial),"bottomSurfaceIndex",GetAttributeIndex(level.bottomMaterial)));}pivots(pivot);}
 if(e.header.type.typeID==API_ShellID){const auto& plane=row.AddList<double>("shellBasePlaneTransform");for(double v:e.shell.basePlane.tmx)plane(v);}
 row.Add("serializationBoundary","NATIVE_PARAMETER_GEOMETRY_NOT_RESULTANT_BREP; MEMO_INDICES_PRESERVED; SHELL_BODY_FLAGS_CLASS_FRAMES_AND_CONTOUR_EDGE_DATA_SERIALIZED_RAW_ALLOCATION_INDICES");rows(row);}return out;
}

static GS::ObjectState DrawingInCurrentDatabase(const GS::ObjectState& item,bool qualified) {
 API_Element e={};auto err=ReadElement(item,e);if(err!=NoError||e.header.type.typeID!=API_DrawingID)return CreateErrorResponse(err==NoError?APIERR_BADID:err,"Drawing required in target database");
 API_DatabaseInfo db={};const auto dbErr=ACAPI_Database_GetCurrentDatabase(&db);
 API_DrawingLinkInfo link={};const GS::OnExit cleanup([&](){delete link.linkPath;if(link.viewPath)BMKillPtr(&link.viewPath);});err=ACAPI_Drawing_GetDrawingLink(&e.header.guid,&link);if(err!=NoError)return CreateErrorResponse(err,"Get drawing link");
 GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"navigatorItemId",CreateGuidObjectState(e.drawing.drawingGuid),"linkGuid",CreateGuidObjectState(link.linkGuid),"linkTypeId",static_cast<Int32>(link.linkTypeID),"viewTypeId",static_cast<Int32>(link.viewType),"contentTypeId",static_cast<Int32>(link.idfTypeID),"viewDeleted",link.viewDeleted,"externalPathPresent",link.linkPath!=nullptr,"databaseQualified",qualified,"databaseQueryError",static_cast<Int32>(dbErr));
 if(dbErr==NoError){row.Add("databaseTypeId",static_cast<Int32>(db.typeID));row.Add("databaseId",CreateGuidObjectState(DatabaseIdResolver::Instance().GetIdOfDatabase(db)));}
 Int32 status=-1;const auto statusErr=ACAPI_Drawing_CheckDrawingStatus(&e.header.guid,&status);row.Add("updateStatus",status);row.Add("statusQueryError",static_cast<Int32>(statusErr));API_Box box={};const auto boxErr=ACAPI_Drawing_GetFullDrawingContentBox(&box,&e.header.guid);row.Add("contentBoxQueryError",static_cast<Int32>(boxErr));if(boxErr==NoError)row.Add("fullContentBox",GS::ObjectState("xMin",box.xMin,"yMin",box.yMin,"xMax",box.xMax,"yMax",box.yMax));return row;
}
GS::ObjectState GetNativeDrawingAssociationsV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0);const auto& rows=out.AddList<GS::ObjectState>("drawings");
 for(const auto& item:inputs){const auto* db=item.Get("databaseId");if(db==nullptr){rows(DrawingInCurrentDatabase(item,false));continue;}
 GS::Array<API_Guid> ids;ids.Push(GetGuidFromObjectState(*db));GS::ObjectState row;
 const auto restore=ExecuteActionForEachDatabase(ids,[&](){row=DrawingInCurrentDatabase(item,true);return NoError;},[](){},[&](GSErrCode err,const GS::UniString& message){row=CreateErrorResponse(err,message);});
 if(restore!=NoError){out.Add("databaseRestoreError",static_cast<Int32>(restore));rows(CreateErrorResponse(restore,"DRAWING_CONTEXT_RESTORE_FAILED_STOP_FOLLOW_ON_CALLS"));break;}
 if(!row.Contains("error"))row.Add("databaseRestoreError",0);rows(row);
 }return out;
}
GS::ObjectState GetNativeElementHotspotsV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0,"authority","NATIVE_ELEMENT_HOTSPOTS_NOT_BODY_VERTICES");const auto& rows=out.AddList<GS::ObjectState>("elements");for(const auto& item:inputs){API_Element e={};auto err=ReadElement(item,e);if(err!=NoError){rows(CreateErrorResponse(err,"Element required"));continue;}GS::Array<API_ElementHotspot> points;err=ACAPI_Element_GetHotspots(e.header.guid,&points);if(err!=NoError){rows(CreateErrorResponse(err,"Get element hotspots"));continue;}GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"homeStory",static_cast<Int32>(e.header.floorInd));const auto& list=row.AddList<GS::ObjectState>("hotspots");for(const auto& point:points)list(GS::ObjectState("neigId",static_cast<Int32>(point.first.neigID),"neigIndex",point.first.inIndex,"x",point.second.x,"y",point.second.y,"z",point.second.z));rows(row);}return out;
}
GS::ObjectState GetNativeElementQuantitiesV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 // The first real quantity batch terminated AC29 with ACCESS_VIOLATION.
 // No same-call replay or speculative mask/solver workaround is accepted.
 // Preserve the typed contract, but fail before entering the quantity engine.
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);double minimum=0;p.Get("minOpeningSize",minimum);
 GS::ObjectState out("nativeModelWrites",0,"authority","QUANTITY_ENGINE_QUARANTINED_AFTER_RUNTIME_CRASH","minOpeningSize",minimum);
 const auto& rows=out.AddList<GS::ObjectState>("elements");
 for(const auto& ignored:inputs){(void)ignored;rows(CreateErrorResponse(APIERR_REFUSEDCMD,"QUARANTINED_AC29_QUANTITY_CRASH_NO_ENGINE_CALL"));}
 return out;
}

// Existing GetSubelementsOfHierarchicalElements supplies membership. This reader
// adds missing child parameters and independently resolves parent/root owners.
GS::ObjectState GetNativeComponentBindingsV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0,"authority","NATIVE_COMPONENT_PARAMETERS_NOT_RESULTANT_BREP");const auto& rows=out.AddList<GS::ObjectState>("elements");
 for(const auto& item:inputs){API_Element e={};auto err=ReadElement(item,e);if(err!=NoError){rows(CreateErrorResponse(err,"Read component"));continue;}
 GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"variationId",static_cast<Int32>(e.header.type.variationID),"homeStory",static_cast<Int32>(e.header.floorInd));
 API_Guid parent=APINULLGuid,root=APINULLGuid;API_HierarchicalElemType kind=API_UnknownElemType;API_HierarchicalOwnerType mode=API_ParentHierarchicalOwner;
 const auto pe=ACAPI_HierarchicalEditing_GetHierarchicalElementOwner(&e.header.guid,&mode,&kind,&parent);row.Add("parentQueryError",static_cast<Int32>(pe));row.Add("hierarchyKind",static_cast<Int32>(kind));
 if(pe==NoError)row.Add("parentElementId",CreateGuidObjectState(parent));mode=API_RootHierarchicalOwner;const auto re=ACAPI_HierarchicalEditing_GetHierarchicalElementOwner(&e.header.guid,&mode,&kind,&root);row.Add("rootQueryError",static_cast<Int32>(re));if(re==NoError)row.Add("rootElementId",CreateGuidObjectState(root));
 GS::ObjectState values,flags;API_Guid owner=APINULLGuid;bool supported=true;
 switch(e.header.type.typeID){
 case API_CurtainWallID:{const auto& c=e.curtainWall;values.Add("heightMetres",c.height);values.Add("relativeLevelMetres",c.storyRelLevel);values.Add("angleRadians",c.angle);values.Add("nominalWidthMetres",c.nominalWidth);values.Add("segmentCount",c.nSegments);values.Add("frameCount",c.nFrames);values.Add("panelCount",c.nPanels);values.Add("junctionCount",c.nJunctions);values.Add("accessoryCount",c.nAccessories);flags.Add("flipped",c.flipped);break;}
 case API_RailingID:{const auto& c=e.railing;values.Add("nodeCount",c.nNodes);values.Add("segmentCount",c.nSegments);values.Add("referenceVertexCount",c.nVertices);values.Add("bottomOffsetMetres",c.bottomOffset);break;}
 case API_RiserID:{const auto& c=e.stairRiser;owner=c.owner;values.Add("angleRadians",c.angle);values.Add("offsetMetres",c.offset);values.Add("thicknessMetres",c.thickness);values.Add("sequenceNumber",c.sequenceNumber);values.Add("roleId",static_cast<Int32>(c.role));flags.Add("visible",c.visible);row.Add("libraryPartGuid",CreateGuidObjectState(c.libId));break;}
 case API_TreadID:{const auto& c=e.stairTread;owner=c.owner;values.Add("offsetMetres",c.offset);values.Add("thicknessMetres",c.thickness);values.Add("zOffsetMetres",c.zOffset);values.Add("nosingValueMetres",c.nosingValue);values.Add("nosingSlant",c.nosingSlant);values.Add("nosingTypeId",static_cast<Int32>(c.nosingType));values.Add("sequenceNumber",c.sequenceNumber);values.Add("roleId",static_cast<Int32>(c.role));flags.Add("visible",c.visible);flags.Add("isCustom",c.isCustom);row.Add("libraryPartGuid",CreateGuidObjectState(c.libId));break;}
 case API_StairStructureID:{const auto& c=e.stairStructure;owner=c.owner;values.Add("thicknessMetres",c.thickness);values.Add("horizontalThicknessMetres",c.horizontalThickness);values.Add("sequenceNumber",c.sequenceNumber);values.Add("structureTypeId",static_cast<Int32>(c.structType));values.Add("bottomTypeId",static_cast<Int32>(c.bottomType));flags.Add("visible",c.visible);flags.Add("isLanding",c.isLanding);row.Add("libraryPartGuid",CreateGuidObjectState(c.libId));break;}
 case API_CurtainWallPanelID:{const auto& c=e.cwPanel;owner=c.owner;values.Add("thicknessMetres",c.thickness);values.Add("buildingMaterialIndex",GetAttributeIndex(c.buildingMaterial));values.Add("classId",c.classID);values.Add("segmentId",c.segmentID);values.Add("libraryPartIndex",c.libInd);values.Add("outerSurfaceIndex",GetAttributeIndex(c.outerSurfaceMaterial.value));values.Add("innerSurfaceIndex",GetAttributeIndex(c.innerSurfaceMaterial.value));values.Add("cutSurfaceIndex",GetAttributeIndex(c.cutSurfaceMaterial.value));flags.Add("outerSurfaceOverridden",c.outerSurfaceMaterial.hasValue);flags.Add("innerSurfaceOverridden",c.innerSurfaceMaterial.hasValue);flags.Add("cutSurfaceOverridden",c.cutSurfaceMaterial.hasValue);flags.Add("hidden",c.hidden);flags.Add("hasSymbol",c.hasSymbol);break;}
 case API_CurtainWallFrameID:{const auto& c=e.cwFrame;owner=c.owner;values.Add("buildingMaterialIndex",GetAttributeIndex(c.buildingMaterial));values.Add("surfaceIndex",GetAttributeIndex(c.material));values.Add("classId",c.classID);values.Add("segmentId",c.segmentID);values.Add("libraryPartIndex",c.libInd);flags.Add("useOwnMaterial",c.useOwnMaterial);break;}
 case API_RailingSegmentID:{const auto& c=e.railingSegment;owner=c.owner;values.Add("heightMetres",c.height);values.Add("yOffsetMetres",c.yOffset);values.Add("zOffsetMetres",c.zOffset);values.Add("slantAngleRadians",c.slantAngle);values.Add("skewAngleRadians",c.skewAngle);flags.Add("visible",c.visible);break;}
 case API_RailingPostID:{const auto& c=e.railingPost;owner=c.owner;values.Add("bottomRailIndex",c.verticalPosition.bottomRailIndex);values.Add("topRailIndex",c.verticalPosition.topRailIndex);row.Add("libraryPartGuid",CreateGuidObjectState(c.symbID));break;}
 case API_RailingRailID:{const auto& c=e.railingRail;owner=c.owner;values.Add("heightMetres",c.height);values.Add("horizontalOffsetMetres",c.horizontalOffset);flags.Add("visible",c.visible);flags.Add("relative",c.relative);row.Add("libraryPartGuid",CreateGuidObjectState(c.symbID));break;}
 case API_RailingHandrailID:{const auto& c=e.railingHandrail;owner=c.owner;values.Add("heightMetres",c.height);values.Add("horizontalOffsetMetres",c.horizontalOffset);flags.Add("visible",c.visible);flags.Add("doubleHandrail",c.doubleHandrail);row.Add("libraryPartGuid",CreateGuidObjectState(c.symbID));break;}

 case API_RailingNodeID:{const auto& c=e.railingNode;owner=c.owner;values.Add("elevationMetres",c.elevation);values.Add("postOffsetMetres",c.postOffset);flags.Add("visible",c.visible);flags.Add("isStatic",c.isStatic);flags.Add("unifyPatterns",c.unifyPatterns);break;}
 case API_RailingInnerPostID:{const auto& c=e.railingInnerPost;owner=c.owner;values.Add("doublePostOffsetMetres",c.doublePostOffset);values.Add("postCount",c.postNum);values.Add("bottomRailIndex",c.verticalPosition.bottomRailIndex);values.Add("topRailIndex",c.verticalPosition.topRailIndex);row.Add("libraryPartGuid",CreateGuidObjectState(c.symbID));break;}
 case API_RailingBalusterID:{const auto& c=e.railingBaluster;owner=c.owner;row.Add("libraryPartGuid",CreateGuidObjectState(c.symbID));break;}
 case API_RailingPanelID:{const auto& c=e.railingPanel;owner=c.owner;flags.Add("visible",c.visible);row.Add("libraryPartGuid",CreateGuidObjectState(c.symbID));break;}
 case API_RailingToprailID:{const auto& c=e.railingToprail;owner=c.owner;flags.Add("visible",c.visible);row.Add("libraryPartGuid",CreateGuidObjectState(c.symbID));break;}
 default:supported=false;break;
 }
 if(owner!=APINULLGuid)row.Add("declaredOwnerId",CreateGuidObjectState(owner));row.Add("specificParametersSupported",supported);row.Add("parameters",values);row.Add("flags",flags);rows(row);
 }return out;
}

GS::ObjectState GetNativeOpeningConnectionsV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0,"authority","NATIVE_OPENING_HOST_AND_CUT_RELATIONSHIPS");const auto& rows=out.AddList<GS::ObjectState>("elements");
 for(const auto& item:inputs){API_Element e={};const auto err=ReadElement(item,e);if(err!=NoError){rows(CreateErrorResponse(err,"Read opening or host"));continue;}
 GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"homeStory",static_cast<Int32>(e.header.floorInd));const auto id=ACAPI::UniqueID(e.header.guid,ACAPI_GetToken());
 if(e.header.type.typeID==API_OpeningID){auto opening=ACAPI::Element::Opening::Get(id);if(!opening.IsOk()){rows(CreateErrorResponse(APIERR_BADID,"Modern Opening lookup failed"));continue;}
 auto parent=opening->GetParentElement();row.Add("parentResolved",parent.IsOk());if(parent.IsOk()){const auto host=GSGuid2APIGuid(parent->GetGuid());row.Add("hostElementId",CreateGuidObjectState(host));API_Elem_Head header={};header.guid=host;const auto he=ACAPI_Element_GetHeader(&header);row.Add("hostHeaderQueryError",static_cast<Int32>(he));if(he==NoError){row.Add("hostNativeTypeId",static_cast<Int32>(header.type.typeID));row.Add("hostHomeStory",static_cast<Int32>(header.floorInd));}}
 const auto& cuts=row.AddList<GS::ObjectState>("cutElements");for(const auto& cut:opening->GetCutElements())cuts(CreateGuidObjectState(GSGuid2APIGuid(cut.GetGuid())));
 const auto geometry=opening->GetOpeningGeometry();const auto xyz=[](const API_Coord3D& c){return GS::ObjectState("x",c.x,"y",c.y,"z",c.z);};
 row.Add("anchor",xyz(geometry.GetAnchorPoint()));row.Add("vectorX",xyz(geometry.GetVectorX()));row.Add("vectorY",xyz(geometry.GetVectorY()));row.Add("extrusionDirection",xyz(geometry.GetExtrusionDirection()));
 const auto extrusion=opening->GetExtrusionParameters();row.Add("shapeTypeId",static_cast<Int32>(extrusion.GetShapeType()));row.Add("limitTypeId",static_cast<Int32>(extrusion.GetLimitType()));row.Add("constraintId",static_cast<Int32>(extrusion.GetConstraint()));
 if(auto v=extrusion.GetWidth())row.Add("widthMetres",*v);if(auto v=extrusion.GetHeight())row.Add("heightMetres",*v);if(auto v=extrusion.GetFiniteBodyLength())row.Add("finiteBodyLengthMetres",*v);if(auto v=extrusion.GetExtrusionStartOffset())row.Add("startOffsetMetres",*v);
 if(auto v=extrusion.GetLinkedStatus())row.Add("linkedStatusId",static_cast<Int32>(*v));row.Add("anchorTypeId",static_cast<Int32>(extrusion.GetAnchor()));if(auto v=extrusion.GetAnchorAltitude())row.Add("anchorAltitudeMetres",*v);
 row.Add("endSurfaceOverridden",extrusion.IsEndSurfaceAttributeOverridden());row.Add("endSurfaceIndex",GetAttributeIndex(extrusion.GetOverriddenEndSurfaceAttributeIndex()));
 row.Add("extrusionSurfaceOverridden",extrusion.IsExtrusionSurfaceAttributeOverridden());row.Add("extrusionSurfaceIndex",GetAttributeIndex(extrusion.GetOverriddenExtrusionSurfaceAttributeIndex()));row.Add("surfaceOverridesLinked",extrusion.AreOverriddenSurfaceAttributesLinked());
 const auto polygon=geometry.GetPolygon();row.Add("polygonPresent",polygon.has_value());
 if(polygon){if(polygon->GetVertexNum()>65536||polygon->GetEdgeNum()>65536||polygon->GetContourNum()>4096){rows(CreateErrorResponse(APIERR_BADPARS,"Opening polygon exceeds bounded serialization"));continue;}row.Add("openingPolygon",OpeningPolygon(*polygon));}
 row.Add("geometryBoundary","NATIVE_PARAMETER_POLYGON_AND_RAW_FRAME_SEPARATE_NO_FRAME_NORMALIZATION_OR_RESULTANT_BREP");
 }else{auto connected=ACAPI::Element::Opening::GetConnectedOpenings(id,ACAPI_GetToken());if(!connected.IsOk()){rows(CreateErrorResponse(APIERR_BADID,"Connected Opening lookup failed for host"));continue;}const auto& openings=row.AddList<GS::ObjectState>("connectedOpenings");for(const auto& opening:*connected)openings(CreateGuidObjectState(GSGuid2APIGuid(opening.GetGuid())));}
 rows(row);
 }return out;
}

// Stage/type telemetry only. No quantity structures, masks or engine calls.
GS::ObjectState GetNativeQuantityPreflightV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0,"quantityEngineCalled",false,"quarantineRetained",true);const auto& rows=out.AddList<GS::ObjectState>("elements");
 for(const auto& item:inputs){API_Element e={};const auto err=ReadElement(item,e);if(err!=NoError){rows(CreateErrorResponse(err,"PRE_ENGINE_ELEMENT_READ_FAILED"));continue;}
 rows(GS::ObjectState("elementId",CreateGuidObjectState(e.header.guid),"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"homeStory",static_cast<Int32>(e.header.floorInd),"stage","PRE_ENGINE_ELEMENT_IDENTIFIED_NO_QUANTITY_CALL","engineCallAllowed",false));}return out;
}

// Direct SDK identity resolution complements existing complete Navigator trees.
// Each map is explicit. A GUID in another map is never silently substituted.
GS::ObjectState GetNativeNavigatorBindingsV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("items",inputs);GS::ObjectState out("nativeModelWrites",0);const auto& rows=out.AddList<GS::ObjectState>("items");
 for(const auto& input:inputs){const auto* id=input.Get("navigatorItemId");if(id==nullptr){rows(CreateErrorResponse(APIERR_BADPARS,"Navigator ID required"));continue;}const auto guid=GetGuidFromObjectState(*id);GS::UniString map;input.Get("navigatorMapId",map);API_NavigatorItem item={};item.mapId=map=="ProjectMap"?API_ProjectMap:(map=="LayoutBook"?API_LayoutMap:API_PublicViewMap);
 const auto requestedMap=item.mapId;const auto err=ACAPI_Navigator_GetNavigatorItem(&guid,&item);if(err!=NoError){rows(CreateErrorResponse(err,"Navigator identity not resolved in requested map"));continue;}
 GS::ObjectState row("navigatorItemId",CreateGuidObjectState(item.guid),"requestedMap",map,"actualMapId",static_cast<Int32>(item.mapId),"itemTypeId",static_cast<Int32>(item.itemType),"sourceGuid",CreateGuidObjectState(item.sourceGuid),"databaseTypeId",static_cast<Int32>(item.db.typeID),"databaseId",CreateGuidObjectState(DatabaseIdResolver::Instance().GetIdOfDatabase(item.db)),"homeStory",static_cast<Int32>(item.floorNum),"isIndependent",item.isIndependent,"identityMatchesRequest",item.guid==guid,"mapMatchesRequest",item.mapId==requestedMap);
 API_NavigatorItem parent={};parent.mapId=item.mapId;const auto pe=ACAPI_Navigator_GetNavigatorParentItem(&guid,&parent);row.Add("parentQueryError",static_cast<Int32>(pe));if(pe==NoError)row.Add("parentItemId",CreateGuidObjectState(parent.guid));rows(row);
 }return out;
}

#include "NativeAssemblyCommands.inc"
#include "NativeAssemblyModify.inc"
#include "NativeMEPTopology.inc"
