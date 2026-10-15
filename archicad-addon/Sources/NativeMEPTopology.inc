// Adds only relationships absent from existing GetMEPRoutingElements/Ports.
// Existing port dimensions, systems and physical-connection reader is reused.
#include "ACAPI/MEPAdapter.hpp"
#include "ACAPI/MEPRoutingElement.hpp"
#include "ACAPI/MEPRoutingSegment.hpp"
#include "ACAPI/MEPRoutingNode.hpp"
#include "ACAPI/MEPRigidSegment.hpp"
#include "ACAPI/MEPTransition.hpp"
#include "ACAPI/MEPElbow.hpp"
#include "ACAPI/MEPBranch.hpp"
static GS::ObjectState MEPIdentity(const ACAPI::MEP::UniqueID& id){return CreateGuidObjectState(GSGuid2APIGuid(id.GetGuid()));}
static void MEPIds(GS::ObjectState& row,const char* key,const std::vector<ACAPI::MEP::UniqueID>& ids){const auto& list=row.AddList<GS::ObjectState>(key);for(const auto& id:ids)list(MEPIdentity(id));}
GS::ObjectState GetNativeMEPTopologyV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const{
 GS::Array<GS::ObjectState> inputs;p.Get("elements",inputs);GS::ObjectState out("nativeModelWrites",0,"authority","NATIVE_MEP_OWNERSHIP_AND_ROUTE_LOGICAL_ENDPOINTS_NOT_PHYSICAL_CONNECTION_PROOF");const auto& rows=out.AddList<GS::ObjectState>("elements");
 for(const auto& item:inputs){const auto* eid=item.Get("elementId");GS::UniString kind;item.Get("kind",kind);if(!eid){rows(CreateErrorResponse(APIERR_BADPARS,"MEP identity required"));continue;}auto guid=GetGuidFromObjectState(*eid);const auto id=ACAPI::MEP::Adapter::UniqueID(guid);GS::ObjectState row("elementId",CreateGuidObjectState(guid),"kind",kind);
  API_Elem_Head header={};header.guid=guid;const auto he=ACAPI_Element_GetHeader(&header);row.Add("headerQueryError",static_cast<Int32>(he));if(he==NoError){row.Add("homeStory",static_cast<Int32>(header.floorInd));row.Add("nativeTypeId",static_cast<Int32>(header.type.typeID));}
  if(kind=="RoutingElement"){
   auto value=ACAPI::MEP::RoutingElement::Get(id);if(value.IsErr()){rows(CreateErrorResponse(value.UnwrapErr().kind,"RoutingElement unavailable"));continue;}
   row.Add("relativeLevelMetres",value->GetOffsetFromHomeStory());row.Add("domainId",static_cast<Int32>(value->GetDomain()));row.Add("mepSystemId",CreateGuidObjectState(GetAttributeGuidFromIndex(API_MEPSystemID,value->GetMEPSystem())));
   MEPIds(row,"routingSegments",value->GetRoutingSegmentIds());MEPIds(row,"routingNodes",value->GetRoutingNodeIds());
   if(auto v=value->GetLogicallyConnectedPortIdAtRouteBegin())row.Add("logicalBeginPortId",MEPIdentity(*v));if(auto v=value->GetLogicallyConnectedPortIdAtRouteEnd())row.Add("logicalEndPortId",MEPIdentity(*v));
  }else if(kind=="RoutingSegment"){
   auto value=ACAPI::MEP::RoutingSegment::Get(id);if(value.IsErr()){rows(CreateErrorResponse(value.UnwrapErr().kind,"RoutingSegment unavailable"));continue;}
   row.Add("routingElementId",MEPIdentity(value->GetRoutingElementId()));row.Add("beginNodeId",MEPIdentity(value->GetBeginNodeId()));row.Add("endNodeId",MEPIdentity(value->GetEndNodeId()));MEPIds(row,"rigidSegments",value->GetRigidSegmentIds());
   row.Add("crossSectionWidthMetres",value->GetCrossSectionWidth());row.Add("crossSectionHeightMetres",value->GetCrossSectionHeight());row.Add("shapeId",static_cast<Int32>(value->GetCrossSectionShape()));row.Add("wallThicknessMetres",value->GetWallThickness());row.Add("referenceOffsetXMetres",value->GetReferenceLineOffsetX());row.Add("referenceOffsetYMetres",value->GetReferenceLineOffsetY());row.Add("anchorId",static_cast<Int32>(value->GetAnchor()));row.Add("preferenceTableId",MEPIdentity(value->GetPreferenceTableId()));auto ref=value->GetCrossSectionReferenceId();row.Add("referenceIdApplicable",ref.IsOk());if(ref.IsOk())row.Add("crossSectionReferenceId",ref.Unwrap());
  }else if(kind=="RoutingNode"){
   auto value=ACAPI::MEP::RoutingNode::Get(id);if(value.IsErr()){rows(CreateErrorResponse(value.UnwrapErr().kind,"RoutingNode unavailable"));continue;}
   row.Add("routingElementId",MEPIdentity(value->GetRoutingElementId()));row.Add("position",NativeXYZ(value->GetPosition()));MEPIds(row,"elbows",value->GetElbowIds());MEPIds(row,"transitions",value->GetTransitionIds());
   if(auto v=value->GetIncomingSegmentId())row.Add("incomingSegmentId",MEPIdentity(*v));if(auto v=value->GetOutgoingSegmentId())row.Add("outgoingSegmentId",MEPIdentity(*v));
  }else if(kind=="RigidSegment"){
   auto value=ACAPI::MEP::RigidSegment::Get(id);if(value.IsErr()){rows(CreateErrorResponse(value.UnwrapErr().kind,"RigidSegment unavailable"));continue;}
   row.Add("routingSegmentId",MEPIdentity(value->GetRoutingSegmentId()));row.Add("lengthMetres",value->GetLength());row.Add("widthMetres",value->GetWidth());row.Add("heightMetres",value->GetHeight());
   if(auto v=value->GetInsulationThickness())row.Add("insulationThicknessMetres",*v);
  }else if(kind=="Transition"){
   auto value=ACAPI::MEP::Transition::Get(id);if(value.IsErr()){rows(CreateErrorResponse(value.UnwrapErr().kind,"Transition unavailable"));continue;}
   row.Add("routingNodeId",MEPIdentity(value->GetRoutingNodeId()));row.Add("narrowerPortId",MEPIdentity(value->GetNarrowerPortID()));row.Add("widerPortId",MEPIdentity(value->GetWiderPortID()));row.Add("lengthMetres",value->GetLength());row.Add("angleDegrees",value->GetAngle());row.Add("offsetYMetres",value->GetOffsetY());row.Add("offsetZMetres",value->GetOffsetZ());
  }else if(kind=="Elbow"){
   auto value=ACAPI::MEP::Elbow::Get(id);if(value.IsErr()){rows(CreateErrorResponse(value.UnwrapErr().kind,"Elbow unavailable"));continue;}
   row.Add("routingNodeId",MEPIdentity(value->GetRoutingNodeId()));row.Add("domainId",static_cast<Int32>(value->GetDomain()));row.Add("widthMetres",value->GetWidth());row.Add("heightMetres",value->GetHeight());row.Add("shapeId",static_cast<Int32>(value->GetShape()));row.Add("radiusMetres",value->GetRadius());auto factor=value->GetFactorRadius();row.Add("factorRadiusApplicable",factor.IsOk());if(factor.IsOk())row.Add("factorRadius",factor.Unwrap());auto table=value->GetPreferenceTable();row.Add("preferenceTableApplicable",table.IsOk());if(table.IsOk())row.Add("preferenceTableId",MEPIdentity(table.Unwrap()));if(auto v=value->GetInsulationThickness())row.Add("insulationThicknessMetres",*v);
  }else if(kind=="Branch"){
   auto value=ACAPI::MEP::Branch::Get(id);if(value.IsErr()){rows(CreateErrorResponse(value.UnwrapErr().kind,"Branch unavailable"));continue;}
   row.Add("domainId",static_cast<Int32>(value->GetDomain()));row.Add("lengthMetres",value->GetLength());row.Add("branchLengthMetres",value->GetBranchLength());row.Add("branchAngleDegrees",value->GetBranchAngle());row.Add("branchOffsetMetres",value->GetBranchOffset());if(auto v=value->GetInsulationThickness())row.Add("insulationThicknessMetres",*v);
  }else{rows(CreateErrorResponse(APIERR_BADPARS,"Unsupported MEP topology role"));continue;}rows(row);
 }return out;
}
