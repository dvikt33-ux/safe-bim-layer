// Public Element_Get/Change masks, shared by all supported assembly kinds.
// This is a native adapter, never a writer, retry loop or placement engine.
#include <cmath>
#include <string>

static GS::UniString AssemblyStamp(const API_Element& e){return std::to_string(e.header.modiStamp).c_str();}
static API_Guid AssemblyAttributeGuid(API_AttrTypeID type,API_AttributeIndex index){
 API_Attribute value={};value.header.typeID=type;value.header.index=index;const auto err=ACAPI_Attribute_Get(&value);
 const GS::OnExit cleanup([&](){if(type==API_MaterialID)delete value.material.texture.fileLoc;});return err==NoError?value.header.guid:APINULLGuid;
}
static GS::String AssemblyKind(const API_Element& e){switch(e.header.type.typeID){
 case API_CurtainWallID:return "CurtainWall";case API_CurtainWallFrameID:return "CurtainWallFrame";case API_CurtainWallPanelID:return "CurtainWallPanel";
 case API_RailingID:return "Railing";case API_RailingSegmentID:return "RailingSegment";case API_RailingNodeID:return "RailingNode";
 case API_RailingRailID:return "RailingRail";case API_RailingHandrailID:return "RailingHandrail";case API_ShellID:return "Shell";default:return "UNSUPPORTED";}}

static GSErrCode AssemblyFields(API_Element& e,API_Element& mask,const GS::ObjectState& changes,GS::ObjectState& values,GS::ObjectState& attributes,GS::Array<GS::UniString>& applied){
 GSErrCode err=NoError;
 const auto number=[&](const char* name,double& field,double low,double high,auto setMask){values.Add(name,field);if(!changes.Contains(name))return;double v=0;if(!changes.Get(name,v)||!std::isfinite(v)||v<low||v>high){err=APIERR_BADPARS;return;}field=v;setMask();applied.Push(name);};
 const auto flag=[&](const char* name,bool& field,auto setMask){values.Add(name,field);if(!changes.Contains(name))return;bool v=false;if(!changes.Get(name,v)){err=APIERR_BADPARS;return;}field=v;setMask();applied.Push(name);};
 const auto attribute=[&](const char* name,API_AttributeIndex& field,API_AttrTypeID type,auto setMask){
  attributes.Add(name,GS::ObjectState("index",GetAttributeIndex(field),"attributeId",CreateGuidObjectState(AssemblyAttributeGuid(type,field))));
  if(!changes.Contains(name))return;const auto* value=changes.Get(name);if(!value||!value->Contains("guid")){err=APIERR_BADPARS;return;}const auto guid=GetGuidFromObjectState(*value);const auto header=GetAttributeHeadFromGuid(guid);
  if(guid==APINULLGuid||header.typeID!=type||GetAttributeIndex(header.index)<=0||header.guid!=guid){err=APIERR_BADID;return;}field=header.index;setMask();applied.Push(name);
 };
#define NUM(alias,Struct,obj,member,low,high) number(alias,e.obj.member,low,high,[&](){ACAPI_ELEMENT_MASK_SET(mask,Struct,member);})
#define BOOL(alias,Struct,obj,member) flag(alias,e.obj.member,[&](){ACAPI_ELEMENT_MASK_SET(mask,Struct,member);})
#define ATTR(alias,Struct,obj,member,type) attribute(alias,e.obj.member,type,[&](){ACAPI_ELEMENT_MASK_SET(mask,Struct,member);})
 switch(e.header.type.typeID){
 case API_CurtainWallID:
  values.Add("heightMetres",e.curtainWall.height);if(changes.Contains("heightMetres"))return APIERR_BADPARS; // Observed NoError/no effect for input-only height mask; use explicit native contour memo.
  NUM("relativeLevelMetres",API_CurtainWallType,curtainWall,storyRelLevel,-1000000,1000000);NUM("referencePlaneOffsetMetres",API_CurtainWallType,curtainWall,offset,-1000,1000);NUM("nominalWidthMetres",API_CurtainWallType,curtainWall,nominalWidth,0.0001,100);BOOL("flipped",API_CurtainWallType,curtainWall,flipped);break;
 case API_CurtainWallPanelID:
  NUM("thicknessMetres",API_CWPanelType,cwPanel,thickness,0.0001,100);ATTR("buildingMaterialId",API_CWPanelType,cwPanel,buildingMaterial,API_BuildingMaterialID);
  ATTR("outerSurfaceId",API_CWPanelType,cwPanel,outerSurfaceMaterial.value,API_MaterialID);BOOL("outerSurfaceOverridden",API_CWPanelType,cwPanel,outerSurfaceMaterial.hasValue);
  ATTR("innerSurfaceId",API_CWPanelType,cwPanel,innerSurfaceMaterial.value,API_MaterialID);BOOL("innerSurfaceOverridden",API_CWPanelType,cwPanel,innerSurfaceMaterial.hasValue);
  ATTR("cutSurfaceId",API_CWPanelType,cwPanel,cutSurfaceMaterial.value,API_MaterialID);BOOL("cutSurfaceOverridden",API_CWPanelType,cwPanel,cutSurfaceMaterial.hasValue);break;
 case API_CurtainWallFrameID:
  ATTR("buildingMaterialId",API_CWFrameType,cwFrame,buildingMaterial,API_BuildingMaterialID);ATTR("surfaceId",API_CWFrameType,cwFrame,material,API_MaterialID);BOOL("useOwnMaterial",API_CWFrameType,cwFrame,useOwnMaterial);NUM("panelHoleDepthMetres",API_CWFrameType,cwFrame,d,0,100);NUM("panelHoleWidthMetres",API_CWFrameType,cwFrame,w,0,100);break;
 case API_RailingID:
  NUM("defaultSegmentHeightMetres",API_RailingType,railing,defSegment.height,0.001,100);NUM("defaultPostOffsetMetres",API_RailingType,railing,defNode.postOffset,-1000,1000);NUM("relativeLevelMetres",API_RailingType,railing,bottomOffset,-1000000,1000000);break;
 case API_RailingSegmentID:
  NUM("heightMetres",API_RailingSegmentType,railingSegment,height,0.001,100);NUM("yOffsetMetres",API_RailingSegmentType,railingSegment,yOffset,-1000,1000);NUM("zOffsetMetres",API_RailingSegmentType,railingSegment,zOffset,-1000,1000);break;
 case API_RailingNodeID:
  NUM("elevationMetres",API_RailingNodeType,railingNode,elevation,-1000000,1000000);NUM("postOffsetMetres",API_RailingNodeType,railingNode,postOffset,-1000,1000);break;
 case API_RailingRailID:
  NUM("heightMetres",API_RailingRailType,railingRail,height,-1000,1000);NUM("horizontalOffsetMetres",API_RailingRailType,railingRail,horizontalOffset,-1000,1000);BOOL("visible",API_RailingRailType,railingRail,visible);break;
 case API_RailingHandrailID:
  NUM("heightMetres",API_RailingHandrailType,railingHandrail,height,-1000,1000);NUM("horizontalOffsetMetres",API_RailingHandrailType,railingHandrail,horizontalOffset,-1000,1000);BOOL("visible",API_RailingHandrailType,railingHandrail,visible);break;
 case API_ShellID:
  NUM("relativeLevelMetres",API_ShellType,shell,shellBase.level,-1000000,1000000);
  if(e.shell.shellBase.modelElemStructureType==API_BasicStructure){NUM("thicknessMetres",API_ShellType,shell,shellBase.thickness,0.0001,100);ATTR("buildingMaterialId",API_ShellType,shell,shellBase.buildingMaterial,API_BuildingMaterialID);}
  if(e.shell.shellBase.modelElemStructureType==API_CompositeStructure)ATTR("compositeId",API_ShellType,shell,shellBase.composite,API_CompWallID);
  ATTR("topSurfaceId",API_ShellType,shell,shellBase.topMat.value,API_MaterialID);BOOL("topSurfaceOverridden",API_ShellType,shell,shellBase.topMat.hasValue);
  ATTR("sideSurfaceId",API_ShellType,shell,shellBase.sidMat.value,API_MaterialID);BOOL("sideSurfaceOverridden",API_ShellType,shell,shellBase.sidMat.hasValue);
  ATTR("bottomSurfaceId",API_ShellType,shell,shellBase.botMat.value,API_MaterialID);BOOL("bottomSurfaceOverridden",API_ShellType,shell,shellBase.botMat.hasValue);
  if(e.shell.shellClass==API_ExtrudedShellID){
   NUM("extrusionXMetres",API_ShellType,shell,u.extrudedShell.extrusionVector.x,-1000000,1000000);NUM("extrusionYMetres",API_ShellType,shell,u.extrudedShell.extrusionVector.y,-1000000,1000000);NUM("extrusionZMetres",API_ShellType,shell,u.extrudedShell.extrusionVector.z,-1000000,1000000);
   NUM("beginXMetres",API_ShellType,shell,u.extrudedShell.begC.x,-1000000,1000000);NUM("beginYMetres",API_ShellType,shell,u.extrudedShell.begC.y,-1000000,1000000);NUM("beginZMetres",API_ShellType,shell,u.extrudedShell.begC.z,-1000000,1000000);
   NUM("slantAngleRadians",API_ShellType,shell,u.extrudedShell.slantAngle,-6.283185307179586,6.283185307179586);NUM("shapePlaneTiltRadians",API_ShellType,shell,u.extrudedShell.shapePlaneTilt,-6.283185307179586,6.283185307179586);NUM("beginPlaneTiltRadians",API_ShellType,shell,u.extrudedShell.begPlaneTilt,-6.283185307179586,6.283185307179586);NUM("endPlaneTiltRadians",API_ShellType,shell,u.extrudedShell.endPlaneTilt,-6.283185307179586,6.283185307179586);
  }else if(e.shell.shellClass==API_RevolvedShellID){
   NUM("slantAngleRadians",API_ShellType,shell,u.revolvedShell.slantAngle,-6.283185307179586,6.283185307179586);NUM("revolutionAngleRadians",API_ShellType,shell,u.revolvedShell.revolutionAngle,0.000001,6.283185307179586);NUM("distortionAngleRadians",API_ShellType,shell,u.revolvedShell.distortionAngle,-3.141592653589793,3.141592653589793);NUM("beginAngleRadians",API_ShellType,shell,u.revolvedShell.begAngle,-6.283185307179586,6.283185307179586);
  }break;
 default:return APIERR_BADID;
 }
#undef NUM
#undef BOOL
#undef ATTR
 return err;
}

static GS::ObjectState AssemblyEditState(API_Element e){
 API_Element mask={};GS::ObjectState values,attributes;GS::Array<GS::UniString> ignored;const auto err=AssemblyFields(e,mask,{},values,attributes,ignored);if(err!=NoError)return CreateErrorResponse(err,"Unsupported assembly edit state");
 GS::ObjectState row("elementId",CreateGuidObjectState(e.header.guid),"kind",AssemblyKind(e),"nativeTypeId",static_cast<Int32>(e.header.type.typeID),"homeStory",static_cast<Int32>(e.header.floorInd),"modificationStamp",AssemblyStamp(e),"values",values,"attributes",attributes,"associationAuthority","NOT_VERIFIED_NO_SPATIAL_INFERENCE");
 if(e.header.type.typeID==API_ShellID)row.Add("shellClass",static_cast<Int32>(e.shell.shellClass));
 AddAssemblyMemo(e,row);
 API_Guid root=APINULLGuid;API_HierarchicalOwnerType mode=API_RootHierarchicalOwner;API_HierarchicalElemType type=API_UnknownElemType;const auto re=ACAPI_HierarchicalEditing_GetHierarchicalElementOwner(&e.header.guid,&mode,&type,&root);row.Add("rootQueryError",static_cast<Int32>(re));if(re==NoError&&root!=APINULLGuid)row.Add("rootElementId",CreateGuidObjectState(root));return row;
}
GS::ObjectState GetNativeAssemblyEditStateV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const{
 GS::Array<GS::ObjectState> items;p.Get("elements",items);GS::ObjectState out("nativeModelWrites",0);const auto& rows=out.AddList<GS::ObjectState>("elements");for(const auto& item:items){API_Element e={};auto err=ReadElement(item,e);rows(err==NoError?AssemblyEditState(e):CreateErrorResponse(err,"Read assembly edit state"));}return out;
}
GS::ObjectState ModifyNativeAssemblyV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const{
 API_Element e={};auto err=ReadElement(p,e);if(err!=NoError)return CreateErrorResponse(err,"Assembly not found");
 GS::UniString expectedKind,stamp;p.Get("expectedKind",expectedKind);p.Get("expectedModificationStamp",stamp);const auto* changes=p.Get("changes");
 if(expectedKind!=AssemblyKind(e)||stamp!=AssemblyStamp(e)||changes==nullptr)return CreateErrorResponse(APIERR_BADPARS,"Assembly type or modification stamp changed; no write");
 API_Element mask={};GS::ObjectState values,attributes;GS::Array<GS::UniString> applied;err=AssemblyFields(e,mask,*changes,values,attributes,applied);if(err!=NoError)return CreateErrorResponse(err,"Invalid field value or attribute identity; no write");
 API_ElementMemo memo={};const GS::OnExit cleanup([&](){ACAPI_DisposeElemMemoHdls(&memo);});UInt64 memoMask=0;
 err=PrepareAssemblyMemoEdits(e,*changes,memo,memoMask,applied);if(err!=NoError)return CreateErrorResponse(err,"Invalid/unsupported native memo edit; no write");
 if(changes->Contains("profileCoordinates")){
  if(e.header.type.typeID!=API_ShellID||e.shell.shellClass!=API_ExtrudedShellID)return CreateErrorResponse(APIERR_BADPARS,"Profile editing requires ExtrudedShell; no write");
  const auto& shape=e.shell.u.extrudedShell.shellShape;GS::Array<GS::ObjectState> coords;
  if(!changes->Get("profileCoordinates",coords)||shape.nArcs!=0||shape.nSubPolys!=1||shape.nCoords<3||shape.nCoords>4096||coords.GetSize()!=static_cast<USize>(shape.nCoords))return CreateErrorResponse(APIERR_BADPARS,"Profile requires same bounded straight single-contour topology; no write");
  err=ACAPI_Element_GetMemo(e.header.guid,&memo,APIMemoMask_All);if(err!=NoError)return CreateErrorResponse(err,"Read profile memo; no write");auto& m=memo.shellShapes[0];const auto allocated=m.coords?BMGetHandleSize(reinterpret_cast<GSHandle>(m.coords))/sizeof(API_Coord):0;
  if(allocated<=static_cast<GSSize>(shape.nCoords))return CreateErrorResponse(APIERR_BADPARS,"Profile coordinate allocation too short; no write");
  const bool closed=(*m.coords)[1].x==(*m.coords)[shape.nCoords].x&&(*m.coords)[1].y==(*m.coords)[shape.nCoords].y;
  for(UIndex i=0;i<coords.GetSize();++i){double x=0,y=0;if(!coords[i].Get("x",x)||!coords[i].Get("y",y)||!std::isfinite(x)||!std::isfinite(y)||std::abs(x)>1000000||std::abs(y)>1000000)return CreateErrorResponse(APIERR_BADPARS,"Invalid profile coordinate; no write");(*m.coords)[i+1]={x,y};}
  if(closed&&((*m.coords)[1].x!=(*m.coords)[shape.nCoords].x||(*m.coords)[1].y!=(*m.coords)[shape.nCoords].y))return CreateErrorResponse(APIERR_BADPARS,"Profile closure changed; no write");
  memoMask=APIMemoMask_Polygon;applied.Push("profileCoordinates");
 }
 if(changes->GetFieldCount()==0||changes->GetFieldCount()!=applied.GetSize())return CreateErrorResponse(APIERR_BADPARS,"Field not applicable to this native kind/structure; no write");
 if(e.header.type.typeID==API_ShellID&&e.shell.shellClass==API_ExtrudedShellID){const auto& v=e.shell.u.extrudedShell.extrusionVector;if(v.x*v.x+v.y*v.y+v.z*v.z<1e-12)return CreateErrorResponse(APIERR_BADPARS,"Zero extrusion vector; no write");}
 err=ACAPI_CallUndoableCommand("APA parameter edit",[&](){API_Element current={};current.header.guid=e.header.guid;const auto ge=ACAPI_Element_Get(&current);if(ge!=NoError)return ge;if(AssemblyStamp(current)!=stamp)return static_cast<GSErrCode>(APIERR_BADPARS);return ACAPI_Element_Change(&e,&mask,memoMask?&memo:nullptr,memoMask,true);});
 if(err!=NoError)return CreateErrorResponse(err,"Native assembly change failed; reconcile before retry");
 GS::ObjectState out("nativeModelWrites",1,"rootGUIDPreservation","TARGET_GUID_RETAINED_CHILDREN_REQUIRE_INDEPENDENT_READBACK","engineering","NOT_VERIFIED");const auto& modified=out.AddList<GS::ObjectState>("modifiedElements");modified(GS::ObjectState("elementId",CreateGuidObjectState(e.header.guid)));out.Add("appliedFields",applied);return out;
}
