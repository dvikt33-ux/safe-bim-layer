#include "NativeGridCommands.hpp"
#include "MigrationHelper.hpp"

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
            "isArray", p.typeMod != API_ParSimple);
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
