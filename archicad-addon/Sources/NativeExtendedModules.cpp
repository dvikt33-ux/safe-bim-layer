#include "NativeExtendedModules.hpp"
#include "MigrationHelper.hpp"
#include <algorithm>

#define DEF(name) name##Command::name##Command():CommandBase(CommonSchema::NotUsed){} GS::String name##Command::GetName() const {return #name;}
DEF(GetNativeEnvelopeMemoV1)
DEF(GetNativeDrawingAssociationsV1)
DEF(GetNativeElementHotspotsV1)
DEF(GetNativeElementQuantitiesV1)
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
GS::ObjectState GetNativeEnvelopeMemoV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0,"authority","NATIVE_ENVELOPE_PARAMETER_MEMO_NOT_RESULTANT_BREP");const auto& rows=out.AddList<GS::ObjectState>("elements");
 for(const auto& item:inputs){API_Element e={};auto err=ReadElement(item,e);if(err!=NoError){rows(CreateErrorResponse(err,"Get envelope element"));continue;}
 if(e.header.type.typeID!=API_RoofID&&e.header.type.typeID!=API_SlabID&&e.header.type.typeID!=API_ShellID){rows(CreateErrorResponse(APIERR_BADID,"Roof Slab Shell required"));continue;}
 API_ElementMemo memo={};const GS::OnExit cleanup([&](){ACAPI_DisposeElemMemoHdls(&memo);});err=ACAPI_Element_GetMemo(e.header.guid,&memo,APIMemoMask_All);if(err!=NoError){rows(CreateErrorResponse(err,"Get envelope memo"));continue;}
 GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"homeStory",static_cast<Int32>(e.header.floorInd),"polygon",PolygonMemo(memo.coords,memo.pends,memo.parcs,memo.vertexIDs,memo.edgeIDs));
 const auto& roofEdges=row.AddList<Int32>("roofEdgeTypes");auto count=memo.roofEdgeTypes?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.roofEdgeTypes))/sizeof(API_RoofEdgeTypeID):0;for(GSIndex i=1;i<count;++i)roofEdges(static_cast<Int32>(memo.roofEdgeTypes[i]));
 if(e.header.type.typeID==API_RoofID){row.Add("roofClass",static_cast<Int32>(e.roof.roofClass));row.Add("pivotPolygon",PolygonMemo(memo.additionalPolyCoords,memo.additionalPolyPends,memo.additionalPolyParcs,memo.additionalPolyVertexIDs,memo.additionalPolyEdgeIDs));row.Add("roofLevel",e.roof.shellBase.level);}
 if(e.header.type.typeID==API_ShellID){row.Add("shellClass",static_cast<Int32>(e.shell.shellClass));const auto& shapes=row.AddList<GS::ObjectState>("shellShapes");for(Int32 i=0;i<2;++i)if(memo.shellShapes[i].coords)shapes(GS::ObjectState("slot",i,"polygon",PolygonMemo(memo.shellShapes[i].coords,memo.shellShapes[i].pends,memo.shellShapes[i].parcs,memo.shellShapes[i].vertexIDs,memo.shellShapes[i].edgeIDs)));
 const auto& contours=row.AddList<GS::ObjectState>("shellContours");const auto n=std::max<Int32>(0,e.shell.numHoles)+(e.shell.hasContour?1:0);
 const auto allocated=memo.shellContours?BMGetPtrSize(reinterpret_cast<GSPtr>(memo.shellContours))/sizeof(API_ShellContourData):0;
 row.Add("shellContourCountExpected",n);row.Add("shellContourCountAllocated",static_cast<Int32>(allocated));
 if(static_cast<GSSize>(n)>allocated){rows(CreateErrorResponse(APIERR_BADPARS,"Shell contour allocation shorter than element metadata"));continue;}
 if(memo.shellContours)for(Int32 i=0;i<n;++i){const auto& c=memo.shellContours[i];GS::ObjectState contour("slot",i,"hole",!e.shell.hasContour||i>0,"depth",c.height,"polygon",PolygonMemo(c.coords,c.pends,c.parcs,c.vertexIDs,c.edgeIDs));const auto& transform=contour.AddList<double>("planeTransform");for(double value:c.plane.tmx)transform(value);contours(contour);}}
 row.Add("serializationBoundary","PARAMETER_TOPOLOGY_ONLY_SIDE_MATERIALS_EDGE_TRIMS_PIVOT_LEVEL_OVERRIDES_SHELL_BODY_FLAGS_AND_AXIS_FRAMES_NOT_SERIALIZED");rows(row);}return out;
}
GS::ObjectState GetNativeDrawingAssociationsV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0);const auto& rows=out.AddList<GS::ObjectState>("drawings");
 for(const auto& item:inputs){API_Element e={};auto err=ReadElement(item,e);if(err!=NoError||e.header.type.typeID!=API_DrawingID){rows(CreateErrorResponse(err==NoError?APIERR_BADID:err,"Drawing required"));continue;}API_DrawingLinkInfo link={};const GS::OnExit cleanup([&](){delete link.linkPath;if(link.viewPath)BMKillPtr(&link.viewPath);});err=ACAPI_Drawing_GetDrawingLink(&e.header.guid,&link);if(err!=NoError){rows(CreateErrorResponse(err,"Get drawing link"));continue;}
 GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"linkGuid",CreateGuidObjectState(link.linkGuid),"linkTypeId",static_cast<Int32>(link.linkTypeID),"viewTypeId",static_cast<Int32>(link.viewType),"contentTypeId",static_cast<Int32>(link.idfTypeID),"viewDeleted",link.viewDeleted,"externalPathPresent",link.linkPath!=nullptr);Int32 status=-1;auto statusErr=ACAPI_Drawing_CheckDrawingStatus(&e.header.guid,&status);row.Add("updateStatus",status);row.Add("statusQueryError",static_cast<Int32>(statusErr));API_Box box={};auto boxErr=ACAPI_Drawing_GetFullDrawingContentBox(&box,&e.header.guid);row.Add("contentBoxQueryError",static_cast<Int32>(boxErr));if(boxErr==NoError)row.Add("fullContentBox",GS::ObjectState("xMin",box.xMin,"yMin",box.yMin,"xMax",box.xMax,"yMax",box.yMax));rows(row);}return out;
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
 for(GSIndex i=0;i<inputs.GetSize();++i)rows(CreateErrorResponse(APIERR_REFUSEDCMD,"QUARANTINED_AC29_QUANTITY_CRASH_NO_ENGINE_CALL"));
 return out;
}
