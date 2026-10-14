#include "NativeGridCommands.hpp"
#include "MigrationHelper.hpp"
#include <cmath>
#include <cstring>
#include "APABuildIdentity.hpp"

GetAPARuntimeInfoV1Command::GetAPARuntimeInfoV1Command () : CommandBase (CommonSchema::NotUsed) {}
GS::String GetAPARuntimeInfoV1Command::GetName () const { return "GetAPARuntimeInfoV1"; }
GS::Optional<GS::UniString> GetAPARuntimeInfoV1Command::GetInputParametersSchema () const { return R"({"type":"object","properties":{},"additionalProperties":false})"; }
GS::Optional<GS::UniString> GetAPARuntimeInfoV1Command::GetRawResponseSchema () const { return R"({"type":"object","additionalProperties":true})"; }
GS::ObjectState GetAPARuntimeInfoV1Command::Execute (const GS::ObjectState&, GS::ProcessControl&) const {
    return GS::ObjectState ("contract", "APA_NATIVE_RUNTIME_IDENTITY_V1", "buildIdentity", APA_BUILD_IDENTITY,
        "sourceRevision", APA_SOURCE_REVISION, "sdkMajor", 29, "developerId", 826567491, "localId", 368333322,
        "stairSolverPolicy", "REQUIRE_COMPLETE_MEMO_NO_NULL_EDGE_VERTEX_DATA", "nativeModelWrites", 0);
}

static bool IsGrid (const API_Element& e) {
    return e.header.type.typeID == API_ObjectID && e.header.type.variationID == APIVarId_GridElement;
}

static const char* ParamKind (API_AddParID type) {
    switch (type) {
        case APIParT_Length: return "Length";
        case APIParT_Angle: return "Angle";
        case APIParT_Integer: return "Integer";
        case APIParT_RealNum: return "Real";
        case APIParT_Boolean: return "Boolean";
        case APIParT_CString: return "String";
        default: return "Unsupported";
    }
}

static GS::ObjectState GridState (const API_Element& e, const API_ElementMemo& memo) {
    GS::ObjectState out ("contract", "APA_NATIVE_GRID_INSTANCE_V1", "elementId", CreateGuidObjectState (e.header.guid),
        "nativeTypeId", static_cast<Int32> (e.header.type.typeID),
        "nativeVariationId", static_cast<Int32> (e.header.type.variationID),
        "nativeVariationName", "APIVarId_GridElement", "nativeTypeName", "GridElement",
        "libraryPartIndex", e.object.libInd, "floorIndex", static_cast<Int32> (e.header.floorInd),
        "x", e.object.pos.x, "y", e.object.pos.y, "angle", e.object.angle, "xRatio", e.object.xRatio, "yRatio", e.object.yRatio,
        "levelFromHomeStory", e.object.level, "nativeModelWrites", 0);
    const auto& list = out.AddList<GS::ObjectState> ("nativeParameters");
    const GSSize count = memo.params == nullptr ? 0 : BMGetHandleSize (reinterpret_cast<GSHandle> (memo.params)) / sizeof (API_AddParType);
    for (GSIndex i = 0; i < count; ++i) {
        const auto& p = (*memo.params)[i];
        GS::ObjectState value ("name", p.name, "nativeType", static_cast<Int32> (p.typeID), "nativeTypeName", ParamKind (p.typeID), "description", GS::UniString (p.uDescname), "isArray", p.typeMod != API_ParSimple);
        if (p.typeMod == API_ParSimple && p.typeID == APIParT_CString) value.Add ("value", GS::UniString (p.value.uStr));
        else if (p.typeMod == API_ParSimple && (p.typeID == APIParT_Integer || p.typeID == APIParT_Length || p.typeID == APIParT_Angle || p.typeID == APIParT_RealNum || p.typeID == APIParT_Boolean)) value.Add ("value", p.value.real);
        else value.Add ("valueStatus", "UNSUPPORTED_OR_ARRAY_NOT_SERIALIZED");
        list (value);
    }
    return out;
}

// Explicit actual parameter names/types, never guessed Grid label/length aliases.
static GSErrCode SetGridParameters (API_ElementMemo& memo, const GS::Array<GS::ObjectState>& changes) {
    const GSSize count = memo.params == nullptr ? 0 : BMGetHandleSize (reinterpret_cast<GSHandle> (memo.params)) / sizeof (API_AddParType);
    GS::HashSet<GS::String> seen;
    for (const auto& change : changes) {
        GS::String name; Int32 type = -1;
        if (!change.Get ("name", name) || !change.Get ("nativeType", type) || seen.Contains (name)) return APIERR_BADPARS;
        seen.Add (name); API_AddParType* found = nullptr;
        for (GSIndex i = 0; i < count; ++i) if (name == (*memo.params)[i].name) found = &(*memo.params)[i];
        if (found == nullptr || found->typeMod != API_ParSimple || static_cast<Int32> (found->typeID) != type || (found->flags & API_ParFlg_Disabled) != 0) return APIERR_BADPARS;
        if (found->typeID == APIParT_CString) {
            GS::UniString value;
            if (!change.Get ("value", value) || value.GetLength () >= API_UAddParStrLen) return APIERR_BADPARS;
            GS::ucscpy (found->value.uStr, value.ToUStr ().Get ());
        } else if (found->typeID == APIParT_Integer || found->typeID == APIParT_Length || found->typeID == APIParT_Angle || found->typeID == APIParT_RealNum || found->typeID == APIParT_Boolean) {
            double value = 0;
            if (!change.Get ("value", value) || !std::isfinite (value) ||
                (found->typeID == APIParT_Integer && std::floor (value) != value) ||
                (found->typeID == APIParT_Boolean && value != 0 && value != 1)) return APIERR_BADPARS;
            found->value.real = value;
        } else return APIERR_BADPARS;
    }
    return NoError;
}

GetNativeGridDefaultsV1Command::GetNativeGridDefaultsV1Command () : CommandBase (CommonSchema::NotUsed) {}
GS::String GetNativeGridDefaultsV1Command::GetName () const { return "GetNativeGridDefaultsV1"; }
GS::Optional<GS::UniString> GetNativeGridDefaultsV1Command::GetInputParametersSchema () const {
    return R"({"type":"object","properties":{},"additionalProperties":false})";
}
GS::Optional<GS::UniString> GetNativeGridDefaultsV1Command::GetRawResponseSchema () const {
    return R"({"type":"object","additionalProperties":true})";
}
GS::ObjectState GetNativeGridDefaultsV1Command::Execute (const GS::ObjectState&, GS::ProcessControl&) const {
    API_Element element = {};
    API_ElementMemo memo = {};
    const GS::OnExit guard ([&memo] () { ACAPI_DisposeElemMemoHdls (&memo); });
    element.header.type.typeID = API_ObjectID;
    element.header.type.variationID = APIVarId_GridElement;
    const GSErrCode err = ACAPI_Element_GetDefaults (&element, &memo);
    if (err != NoError) return CreateErrorResponse (err, "NativeGridDefaults");
    if (element.header.type.typeID != API_ObjectID || element.header.type.variationID != APIVarId_GridElement)
        return CreateErrorResponse (APIERR_BADID, "GridToolVariationMismatch");
    GS::ObjectState out ("contract", "APA_NATIVE_GRID_DEFAULTS_V1",
        "nativeTypeId", static_cast<Int32> (element.header.type.typeID),
        "nativeVariationId", static_cast<Int32> (element.header.type.variationID),
        "nativeVariationName", "APIVarId_GridElement",
        "libraryPartIndex", element.object.libInd,
        "nativeModelWrites", 0, "nativeToolDefaultWrites", 0);
    out.Add ("defaultPlacement", GS::ObjectState ("x", element.object.pos.x,
        "y", element.object.pos.y, "levelFromHomeStory", element.object.level,
        "angle", element.object.angle, "xRatio", element.object.xRatio, "yRatio", element.object.yRatio));
    const auto& add = out.AddList<GS::ObjectState> ("nativeParameters");
    const GSSize count = memo.params == nullptr ? 0 : BMGetHandleSize (reinterpret_cast<GSHandle> (memo.params)) / sizeof (API_AddParType);
    for (GSIndex i = 0; i < count; ++i) {
        const API_AddParType& p = (*memo.params)[i];
        GS::ObjectState value ("name", p.name, "nativeType", static_cast<Int32> (p.typeID),
            "nativeTypeName", ParamKind (p.typeID), "description", GS::UniString (p.uDescname), "isArray", p.typeMod != API_ParSimple);
        if (p.typeMod == API_ParSimple) {
            if (p.typeID == APIParT_CString && p.value.uStr != nullptr)
                value.Add ("value", GS::UniString (p.value.uStr));
            else if (p.typeID == APIParT_Integer || p.typeID == APIParT_Length ||
                    p.typeID == APIParT_Angle || p.typeID == APIParT_RealNum ||
                    p.typeID == APIParT_Boolean || p.typeID == APIParT_Mater ||
                    p.typeID == APIParT_LineTyp || p.typeID == APIParT_FillPat || p.typeID == APIParT_PenCol)
                value.Add ("value", p.value.real);
            else value.Add ("valueStatus", "NON_SCALAR_OR_UNSUPPORTED_TYPE_NOT_SERIALIZED");
        } else value.Add ("valueStatus", "ARRAY_NOT_SERIALIZED");
        add (value);
    }
    out.Add ("axisGeometryAcceptance", "NOT_VERIFIED_DEFAULTS_ARE_NOT_CREATED_AXES");
    return out;
}

GetNativeGridElementsV1Command::GetNativeGridElementsV1Command () : CommandBase (CommonSchema::Used) {}
GS::String GetNativeGridElementsV1Command::GetName () const { return "GetNativeGridElementsV1"; }
GS::Optional<GS::UniString> GetNativeGridElementsV1Command::GetInputParametersSchema () const {
    return R"({"type":"object","properties":{"elements":{"type":"array","minItems":1,"maxItems":64,"items":{"$ref":"#/ElementIdArrayItem"}}},"required":["elements"],"additionalProperties":false})";
}
GS::Optional<GS::UniString> GetNativeGridElementsV1Command::GetRawResponseSchema () const { return R"({"type":"object","additionalProperties":true})"; }
GS::ObjectState GetNativeGridElementsV1Command::Execute (const GS::ObjectState& params, GS::ProcessControl&) const {
    GS::Array<GS::ObjectState> ids; params.Get ("elements", ids); GS::ObjectState out;
    const auto& list = out.AddList<GS::ObjectState> ("grids");
    for (const auto& id : ids) {
        API_Element e = {}; e.header.guid = GetGuidFromElementsArrayItem (id);
        API_ElementMemo memo = {}; const GS::OnExit guard ([&] () { ACAPI_DisposeElemMemoHdls (&memo); });
        GSErrCode err = ACAPI_Element_Get (&e);
        if (err != NoError) return CreateErrorResponse (err, "NativeGridGet");
        if (!IsGrid (e)) return CreateErrorResponse (APIERR_BADID, "NativeGridVariationRequired_NotGenericObject");
        err = ACAPI_Element_GetMemo (e.header.guid, &memo, APIMemoMask_AddPars);
        if (err != NoError) return CreateErrorResponse (err, "NativeGridParameters");
        list (GridState (e, memo));
    }
    return out;
}

CreateNativeGridElementsV1Command::CreateNativeGridElementsV1Command () : CommandBase (CommonSchema::NotUsed) {}
GS::String CreateNativeGridElementsV1Command::GetName () const { return "CreateNativeGridElementsV1"; }
GS::Optional<GS::UniString> CreateNativeGridElementsV1Command::GetInputParametersSchema () const {
    return R"({"type":"object","properties":{"gridsData":{"type":"array","minItems":1,"maxItems":1,"items":{"type":"object","properties":{"x":{"type":"number"},"y":{"type":"number"},"angle":{"type":"number"},"floorIndex":{"type":"integer"},"expectedLibraryPartIndex":{"type":"integer","minimum":1},"parameters":{"type":"array","minItems":1,"items":{"type":"object","properties":{"name":{"type":"string","minLength":1},"nativeType":{"type":"integer"},"value":{"type":["number","string"]}},"required":["name","nativeType","value"],"additionalProperties":false}}},"required":["x","y","angle","floorIndex","expectedLibraryPartIndex","parameters"],"additionalProperties":false}}},"required":["gridsData"],"additionalProperties":false})";
}
GS::Optional<GS::UniString> CreateNativeGridElementsV1Command::GetRawResponseSchema () const { return R"({"type":"object","additionalProperties":true})"; }
GS::ObjectState CreateNativeGridElementsV1Command::Execute (const GS::ObjectState& params, GS::ProcessControl&) const {
    GS::Array<GS::ObjectState> rows; params.Get ("gridsData", rows);
    if (rows.GetSize () != 1) return CreateErrorResponse (APIERR_BADPARS, "ExactlyOneNativeGrid");
    API_Element e = {}; e.header.type.typeID = API_ObjectID; e.header.type.variationID = APIVarId_GridElement;
    API_ElementMemo memo = {}; const GS::OnExit guard ([&] () { ACAPI_DisposeElemMemoHdls (&memo); });
    GSErrCode err = ACAPI_Element_GetDefaults (&e, &memo);
    if (err != NoError) return CreateErrorResponse (err, "NativeGridDefaults");
    const auto& row = rows[0]; Int32 library = -1, floor = 0;
    if (!row.Get ("expectedLibraryPartIndex", library) || !IsGrid (e) || e.object.libInd != library) return CreateErrorResponse (APIERR_BADPARS, "NativeGridDefaultsDrift");
    double x = 0, y = 0, angle = 0;
    if (!row.Get ("x", x) || !row.Get ("y", y) || !row.Get ("angle", angle) || !row.Get ("floorIndex", floor) || floor < -32768 || floor > 32767 || !std::isfinite (x) || !std::isfinite (y) || !std::isfinite (angle)) return CreateErrorResponse (APIERR_BADPARS, "NativeGridPlacement");
    e.object.pos = { x, y }; e.object.angle = angle; e.header.floorInd = static_cast<short> (floor);
    GS::Array<GS::ObjectState> changes; row.Get ("parameters", changes);
    if (changes.GetSize () == 0) return CreateErrorResponse (APIERR_BADPARS, "ExplicitGridParametersRequired");
    err = SetGridParameters (memo, changes);
    if (err != NoError) return CreateErrorResponse (err, "NativeGridSourceParameterMismatch");
    // Mirror the provider's existing Object/GDL A/B dimension synchronization.
    // This does not select a generic Object tool: GREL defaults remain pinned.
    for (const auto& change : changes) {
        GS::String name; Int32 type = -1; double value = 0;
        change.Get ("name", name); change.Get ("nativeType", type);
        if (type == static_cast<Int32> (APIParT_Length) && (name == "A" || name == "B")) {
            if (!change.Get ("value", value) || value <= 0) return CreateErrorResponse (APIERR_BADPARS, "NativeGridDimensionMustBePositive");
            if (name == "A") e.object.xRatio = value; else e.object.yRatio = value;
        }
    }
    e.header.guid = APINULLGuid;
    err = ACAPI_CallUndoableCommand ("APA native Grid", [&] () -> GSErrCode { return ACAPI_Element_Create (&e, &memo); });
    if (err != NoError) return CreateErrorResponse (err, "NativeGridCreate");
    GS::ObjectState out; out.AddList<GS::ObjectState> ("elements") (GS::ObjectState ("elementId", CreateGuidObjectState (e.header.guid)));
    return out;
}

ModifyNativeGridElementsV1Command::ModifyNativeGridElementsV1Command () : CommandBase (CommonSchema::Used) {}
GS::String ModifyNativeGridElementsV1Command::GetName () const { return "ModifyNativeGridElementsV1"; }
GS::Optional<GS::UniString> ModifyNativeGridElementsV1Command::GetInputParametersSchema () const {
    return R"({"type":"object","properties":{"gridsWithDetails":{"type":"array","minItems":1,"maxItems":1,"items":{"type":"object","properties":{"elementId":{"$ref":"#/ElementId"},"x":{"type":"number"},"y":{"type":"number"},"angle":{"type":"number"},"expectedX":{"type":"number"},"expectedY":{"type":"number"},"expectedAngle":{"type":"number"}},"required":["elementId","x","y","angle","expectedX","expectedY","expectedAngle"],"additionalProperties":false}}},"required":["gridsWithDetails"],"additionalProperties":false})";
}
GS::Optional<GS::UniString> ModifyNativeGridElementsV1Command::GetRawResponseSchema () const { return R"({"type":"object","additionalProperties":true})"; }
GS::ObjectState ModifyNativeGridElementsV1Command::Execute (const GS::ObjectState& params, GS::ProcessControl&) const {
    GS::Array<GS::ObjectState> rows; params.Get ("gridsWithDetails", rows);
    if (rows.GetSize () != 1) return CreateErrorResponse (APIERR_BADPARS, "ExactlyOneNativeGridEdit");
    const auto& row = rows[0]; API_Element e = {}; e.header.guid = GetGuidFromArrayItem ("elementId", row);
    GSErrCode err = ACAPI_Element_Get (&e);
    if (err != NoError) return CreateErrorResponse (err, "NativeGridGet");
    if (!IsGrid (e)) return CreateErrorResponse (APIERR_BADID, "NativeGridVariationRequired_NotGenericObject");
    double oldX = 0, oldY = 0, oldAngle = 0, x = 0, y = 0, angle = 0;
    if (!row.Get ("expectedX", oldX) || !row.Get ("expectedY", oldY) || !row.Get ("expectedAngle", oldAngle) || !row.Get ("x", x) || !row.Get ("y", y) || !row.Get ("angle", angle) ||
        !std::isfinite (x) || !std::isfinite (y) || !std::isfinite (angle) || !std::isfinite (oldX) || !std::isfinite (oldY) || !std::isfinite (oldAngle) ||
        std::abs (e.object.pos.x-oldX) > 1e-8 || std::abs (e.object.pos.y-oldY) > 1e-8 || std::abs (e.object.angle-oldAngle) > 1e-8) return CreateErrorResponse (APIERR_BADPARS, "NativeGridEditBaselineDrift");
    e.object.pos = { x, y }; e.object.angle = angle;
    API_Element mask = {}; ACAPI_ELEMENT_MASK_CLEAR (mask);
    ACAPI_ELEMENT_MASK_SET (mask, API_ObjectType, pos); ACAPI_ELEMENT_MASK_SET (mask, API_ObjectType, angle);
    err = ACAPI_CallUndoableCommand ("APA edit native Grid", [&] () -> GSErrCode { return ACAPI_Element_Change (&e, &mask, nullptr, 0, true); });
    if (err != NoError) return CreateErrorResponse (err, "NativeGridEdit");
    GS::ObjectState out; out.AddList<GS::ObjectState> ("executionResults") (CreateSuccessfulExecutionResult ()); return out;
}
