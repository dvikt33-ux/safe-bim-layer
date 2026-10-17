// Native groups through existing AC29 add-on and the documented Graphisoft SDK.
// One API command per composite operation, one Archicad Undo scope.
// Never select the user's GUI selection or silently include unrequested members.
#include <cmath>
#include <vector>

static bool APAGroupContainsExactly(const GS::Array<API_Guid>& actual, const GS::Array<API_Guid>& expected) {
 if (actual.GetSize()!=expected.GetSize())return false;
 for (const auto& a:actual){bool found=false;for(const auto& b:expected)if(a==b){found=true;break;}if(!found)return false;}
 return true;
}
static GSErrCode APAGroupMembers(const API_Guid& group,GS::Array<API_Guid>& out){
 if(group==APINULLGuid)return APIERR_BADID;
 return ACAPI_Grouping_GetAllGroupedElems(group,&out);
}
static GSErrCode APAGroupReadHeaders(const GS::Array<API_Guid>& guids,short& floor){
 bool first=true;
 for(const auto& id:guids){
  API_Elem_Head head={};head.guid=id;auto err=ACAPI_Element_GetHeader(&head);if(err!=NoError)return err;
  if(first){floor=head.floorInd;first=false;}else if(head.floorInd!=floor)return APIERR_BADPARS;
 }
 return first?APIERR_BADPARS:NoError;
}
GS::Optional<GS::UniString> CreateNativeGroupV1Command::GetInputParametersSchema() const {
 return R"APA({"type":"object","additionalProperties":false,"required":["memberIds","sourceRef"],"properties":{"memberIds":{"type":"array","minItems":2,"maxItems":128,"uniqueItems":true,"items":{"type":"object","additionalProperties":false,"required":["guid"],"properties":{"guid":{"type":"string","minLength":10}}}},"sourceRef":{"type":"string","minLength":8}}})APA";
}
GS::Optional<GS::UniString> CreateNativeGroupV1Command::GetRawResponseSchema() const {
 return R"APA({"type":"object","properties":{"nativeModelWrites":{"type":"integer"},"groupId":{"type":"object"},"memberCount":{"type":"integer"},"error":{"type":"object"}},"additionalProperties":false})APA";
}
GS::ObjectState CreateNativeGroupV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 GS::Array<GS::ObjectState> input;
 GS::UniString source;
 if(!p.Get("memberIds",input)||!p.Get("sourceRef",source)||source.GetLength()<8||input.GetSize()<2||input.GetSize()>128)return CreateErrorResponse(APIERR_BADPARS,"Source-qualified 2..128 members required");
 GS::Array<API_Guid> ids;
 for(const auto& item:input){
  API_Guid guid=GetGuidFromObjectState(item);
  if(guid==APINULLGuid)return CreateErrorResponse(APIERR_BADID,"Invalid member GUID");
  for(const auto& old:ids)if(old==guid)return CreateErrorResponse(APIERR_BADPARS,"Duplicate member GUID");
  API_Guid current=APINULLGuid;auto err=ACAPI_Grouping_GetGroup(guid,&current);
  if(err!=NoError)return CreateErrorResponse(err,"Group membership read failed");
  if(current!=APINULLGuid)return CreateErrorResponse(APIERR_BADPARS,"Existing group requires explicit higher-level nesting; implicit re-group denied");
  ids.Push(guid);
 }
 short floor=0;auto err=APAGroupReadHeaders(ids,floor);
 if(err!=NoError)return CreateErrorResponse(err,"Members must exist on one story");
 API_Guid created=APINULLGuid;
 err=ACAPI_CallUndoableCommand("APA create native group",[&]()->GSErrCode {
  auto status=ACAPI_Grouping_Create(ids,&created);
  if(status!=NoError)return status;
  GS::Array<API_Guid> actual;status=APAGroupMembers(created,actual);
  if(status!=NoError)return status;
  return APAGroupContainsExactly(actual,ids)?NoError:APIERR_BADPARS;
 });
 if(err!=NoError)return CreateErrorResponse(err,"Native group creation/readback failed; undo scope rejected");
 return GS::ObjectState("nativeModelWrites",1,"groupId",CreateGuidObjectState(created),"memberCount",static_cast<Int32>(ids.GetSize()));
}
GS::Optional<GS::UniString> CloneNativeGroupV1Command::GetInputParametersSchema() const {
 return R"APA({"type":"object","additionalProperties":false,"required":["groupId","sourceRef","translations"],"properties":{"groupId":{"type":"object","additionalProperties":false,"required":["guid"],"properties":{"guid":{"type":"string","minLength":10}}},"sourceRef":{"type":"string","minLength":8},"translations":{"type":"array","minItems":1,"maxItems":32,"items":{"type":"object","additionalProperties":false,"required":["dx","dy","dz"],"properties":{"dx":{"type":"number"},"dy":{"type":"number"},"dz":{"type":"number"}}}}}})APA";
}
GS::Optional<GS::UniString> CloneNativeGroupV1Command::GetRawResponseSchema() const {
 return R"APA({"type":"object","properties":{"nativeModelWrites":{"type":"integer"},"sourceGroupId":{"type":"object"},"newGroupIds":{"type":"array","items":{"type":"object"}},"createdElements":{"type":"array","items":{"type":"object"}},"error":{"type":"object"}},"additionalProperties":false})APA";
}
GS::ObjectState CloneNativeGroupV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 const auto* groupNode=p.Get("groupId");GS::UniString source;
 GS::Array<GS::ObjectState> translations;
 if(groupNode==nullptr||!p.Get("sourceRef",source)||source.GetLength()<8||
    !p.Get("translations",translations)||translations.IsEmpty()||translations.GetSize()>32)
  return CreateErrorResponse(APIERR_BADPARS,"Qualified group and translations required");
 API_Guid sourceGroup=GetGuidFromObjectState(*groupNode);
 GS::Array<API_Guid> originals;
 auto err=APAGroupMembers(sourceGroup,originals);
 if(err!=NoError)return CreateErrorResponse(err,"Group read failed");
 if(originals.GetSize()<2||originals.GetSize()>128||
    originals.GetSize()*translations.GetSize()>200)
  return CreateErrorResponse(APIERR_BADPARS,"Group copy count outside safe bounds");
 short floor=0;err=APAGroupReadHeaders(originals,floor);
 if(err!=NoError)return CreateErrorResponse(err,"Group members on incompatible stories");
 GS::Array<API_Neig> templateNeigs;
 for(const auto& id:originals){
  API_Elem_Head head={};head.guid=id;
  err=ACAPI_Element_GetHeader(&head);if(err!=NoError)return CreateErrorResponse(err,"Group member header unavailable");
  API_Neig neig={};neig.guid=id;
  err=ACAPI_Element_ElemTypeToNeigID(head.type,neig.neigID);
  if(err!=NoError)return CreateErrorResponse(err,"Group member cannot be transformed using native neig");
  templateNeigs.Push(neig);
 }
 struct Shift{double x,y,z;};std::vector<Shift> shifts;
 for(const auto& item:translations){
  double dx=0,dy=0,dz=0;
  if(!item.Get("dx",dx)||!item.Get("dy",dy)||!item.Get("dz",dz)||
     !std::isfinite(dx)||!std::isfinite(dy)||!std::isfinite(dz)||
     std::abs(dx)>100000||std::abs(dy)>100000||std::abs(dz)>100000||
     (dx==0&&dy==0&&dz==0))return CreateErrorResponse(APIERR_BADPARS,"Finite nonzero translation required");
  for(const auto& s:shifts)if(s.x==dx&&s.y==dy&&s.z==dz)return CreateErrorResponse(APIERR_BADPARS,"Duplicate group offset");
  shifts.push_back({dx,dy,dz});
 }
 GS::Array<API_Guid> newGroups,created;
 err=ACAPI_CallUndoableCommand("APA clone native group",[&]()->GSErrCode {
  for(const auto& v:shifts){
   GS::Array<API_Neig> neigs=templateNeigs;
   API_EditPars edit={};edit.typeID=APIEdit_Drag;edit.withDelete=false; // Drag a Copy
   edit.begC={0.0,0.0,0.0};edit.endC={v.x,v.y,v.z};
   auto step=ACAPI_Element_Edit(&neigs,edit);
   if(step!=NoError)return step;
   if(neigs.GetSize()!=originals.GetSize())return APIERR_BADPARS;
   GS::Array<API_Guid> added;
   for(const auto& n:neigs){
    if(n.guid==APINULLGuid)return APIERR_BADID;
    for(const auto& src:originals)if(src==n.guid)return APIERR_BADPARS;
    for(const auto& previous:created)if(previous==n.guid)return APIERR_BADPARS;
    for(const auto& previous:added)if(previous==n.guid)return APIERR_BADPARS;
    API_Elem_Head check={};check.guid=n.guid;step=ACAPI_Element_GetHeader(&check);
    if(step!=NoError)return step;
    added.Push(n.guid);
   }
   API_Guid copiedGroup=APINULLGuid;
   step=ACAPI_Grouping_GetGroup(added[0],&copiedGroup);
   if(step!=NoError)return step;
   if(copiedGroup==APINULLGuid)step=ACAPI_Grouping_Create(added,&copiedGroup);
   if(step!=NoError)return step;
   GS::Array<API_Guid> actual;step=APAGroupMembers(copiedGroup,actual);
   if(step!=NoError||!APAGroupContainsExactly(actual,added))return APIERR_BADPARS;
   newGroups.Push(copiedGroup);
   for(const auto& id:added)created.Push(id);
  }
  return NoError;
 });
 if(err!=NoError)return CreateErrorResponse(err,"Group clone failed native readback; undo scope rejected");
 GS::ObjectState out("nativeModelWrites",static_cast<Int32>(created.GetSize()),"sourceGroupId",CreateGuidObjectState(sourceGroup));
 const auto& groups=out.AddList<GS::ObjectState>("newGroupIds");for(const auto& g:newGroups)groups(CreateGuidObjectState(g));
 const auto& elems=out.AddList<GS::ObjectState>("createdElements");for(const auto& g:created)elems(GS::ObjectState("elementId",CreateGuidObjectState(g)));
 return out;
}


GS::Optional<GS::UniString> GetNativeGroupMembersV1Command::GetInputParametersSchema() const {
 return R"APA({"type":"object","additionalProperties":false,"required":["groupId"],"properties":{"groupId":{"type":"object","additionalProperties":false,"required":["guid"],"properties":{"guid":{"type":"string","minLength":10}}}}})APA";
}
GS::Optional<GS::UniString> GetNativeGroupMembersV1Command::GetRawResponseSchema() const {
 return R"APA({"type":"object","properties":{"nativeModelWrites":{"const":0},"groupId":{"type":"object"},"memberIds":{"type":"array","items":{"type":"object"}},"error":{"type":"object"}},"additionalProperties":false})APA";
}
GS::ObjectState GetNativeGroupMembersV1Command::Execute(const GS::ObjectState& p,GS::ProcessControl&) const {
 const auto* id=p.Get("groupId");
 if(!id)return CreateErrorResponse(APIERR_BADPARS,"groupId required");
 const API_Guid guid=GetGuidFromObjectState(*id);
 GS::Array<API_Guid> members;const auto err=APAGroupMembers(guid,members);
 if(err!=NoError)return CreateErrorResponse(err,"Native group members unavailable");
 GS::ObjectState out("nativeModelWrites",0,"groupId",CreateGuidObjectState(guid));
 const auto& list=out.AddList<GS::ObjectState>("memberIds");
 for(const auto& member:members)list(CreateGuidObjectState(member));
 return out;
}
