#include "NativeStairCommands.hpp"
#include "MigrationHelper.hpp"
#include <cmath>

static void AddPolyline (GS::ObjectState& out, const char* name, const API_StairPolylineData& poly) {
    const auto& list = out.AddList<GS::ObjectState> (name);
    if (poly.coords == nullptr) return;
    for (Int32 i = 1; i <= poly.polygon.nCoords; ++i) list (Create2DCoordinateObjectState ((*poly.coords)[i]));
}
static GS::ObjectState StairState (const API_Element& e, const API_ElementMemo& memo) {
    const auto& s = e.stair; const auto& r = s.rules;
    GS::ObjectState out ("contract", "APA_NATIVE_STAIR_GEOMETRY_V1", "elementId", CreateGuidObjectState (e.header.guid),
        "nativeType", "Stair", "nativeTypeId", static_cast<Int32> (e.header.type.typeID),
        "nativeVariationId", static_cast<Int32> (e.header.type.variationID), "floorIndex", static_cast<Int32> (e.header.floorInd),
        "totalHeight", s.totalHeight, "flightWidth", s.flightWidth, "stepNum", s.stepNum, "treadNum", s.treadNum,
        "riserHeight", s.riserHeight, "treadDepth", s.treadDepth, "treadDepthLocked", s.treadDepthLocked,
        "totalHeightLocked", s.totalHeightLocked, "extraTopTread", s.extraTopTread, "extraBottomTread", s.extraBottomTread,
        "walkingLineOffset", s.walkingLineOffset, "walkingLinePosition", static_cast<Int32> (s.walkingLinePosition),
        "baselinePosition", static_cast<Int32> (s.baselinePosition), "baselineOffset", s.baselineOffset,
        "levelFromHomeStory", s.basePlane.basePoint.z, "nativeModelWrites", 0);
    out.Add ("rules", GS::ObjectState ("ruleMinValue", r.ruleMinValue, "ruleMinApplied", r.ruleMinApplied,
        "ruleMaxValue", r.ruleMaxValue, "ruleMaxApplied", r.ruleMaxApplied,
        "treadDepthMinValue", r.treadDepthMinValue, "treadDepthMinApplied", r.treadDepthMinApplied,
        "treadDepthMaxValue", r.treadDepthMaxValue, "treadDepthMaxApplied", r.treadDepthMaxApplied,
        "riserHeightMinValue", r.riserHeightMinValue, "riserHeightMinApplied", r.riserHeightMinApplied,
        "riserHeightMaxValue", r.riserHeightMaxValue, "riserHeightMaxApplied", r.riserHeightMaxApplied));
    AddPolyline (out, "baseLinePoints", memo.stairBaseLine); AddPolyline (out, "walkingLinePoints", memo.stairWalkingLine);
    out.Add ("engineeringAcceptance", "NOT_VERIFIED"); return out;
}
static GSErrCode ReadStair (const API_Guid& guid, API_Element& e, API_ElementMemo& memo) {
    e.header.guid = guid; GSErrCode err = ACAPI_Element_Get (&e);
    if (err != NoError) return err;
    if (e.header.type.typeID != API_StairID) return APIERR_BADID;
    return ACAPI_Element_GetMemo (guid, &memo, APIMemoMask_All);
}
static GS::Optional<GS::ObjectState> ExactSettings (API_Element& e, API_ElementMemo& memo, const Stories& stories, const GS::ObjectState& params) {
    CreateStairsCommand existing;
    auto failure = existing.SetTypeSpecificParameters (e, memo, stories, params);
    if (failure.HasValue ()) return failure;
    const double h = e.stair.totalHeight, g = e.stair.treadDepth, r = e.stair.riserHeight, w = e.stair.flightWidth;
    const UInt32 n = e.stair.stepNum; bool locked = false;
    if (!params.Get ("treadDepthLocked", locked) || !locked || n < 2 || !std::isfinite (h) || !std::isfinite (g) || !std::isfinite (r) || !std::isfinite (w) ||
        h <= 0 || g <= 0 || r <= 0 || w <= 0 || std::abs (n*r-h) > 1e-8) return CreateErrorResponse (APIERR_BADPARS, "ExactStairRequiresExplicitConsistentLockedDimensions");
    const auto& rules = e.stair.rules;
    const double sum = 2*r+g;
    if ((rules.ruleMinApplied && sum < rules.ruleMinValue-1e-8) || (rules.ruleMaxApplied && sum > rules.ruleMaxValue+1e-8))
        return CreateErrorResponse (APIERR_BADPARS, "SourceFavoriteRule_2R_plus_G_Incompatible_NoRuleOverride_NoCreate");
    if ((rules.treadDepthMinApplied && g < rules.treadDepthMinValue-1e-8) || (rules.treadDepthMaxApplied && g > rules.treadDepthMaxValue+1e-8) ||
        (rules.riserHeightMinApplied && r < rules.riserHeightMinValue-1e-8) || (rules.riserHeightMaxApplied && r > rules.riserHeightMaxValue+1e-8))
        return CreateErrorResponse (APIERR_BADPARS, "SourceFavoriteRiserOrGoingRangeIncompatible_NoRuleOverride_NoCreate");
    e.stair.treadDepthLocked = true; e.stair.totalHeightLocked = true;
    API_StairSolutionID solution = APISS_NotSolved;
    const GSErrCode err = ACAPI_HierarchicalEditing_SolveStair (&e.stair, &memo, &solution);
    if (err != NoError || solution == APISS_NotSolved) return CreateErrorResponse (err != NoError ? err : APIERR_BADPARS, "NativeSolverCannotSatisfyLockedSourceDimensions_NoCreate");
    if (std::abs (e.stair.totalHeight-h) > 1e-8 || std::abs (e.stair.treadDepth-g) > 1e-8 || std::abs (e.stair.riserHeight-r) > 1e-8 ||
        std::abs (e.stair.flightWidth-w) > 1e-8 || e.stair.stepNum != n) return CreateErrorResponse (APIERR_BADPARS, "NativeSolverChangedSourceDimensions_NoCreate");
    GS::Array<GS::ObjectState> points; params.Get ("baseLinePoints", points);
    if (memo.stairBaseLine.coords == nullptr || memo.stairBaseLine.polygon.nCoords != static_cast<Int32> (points.GetSize ())) return CreateErrorResponse (APIERR_BADPARS, "NativeSolverChangedSourceBaseline_NoCreate");
    for (UIndex i = 0; i < points.GetSize (); ++i) {
        const API_Coord p = Get2DCoordinateFromObjectState (points[i]); const auto& q = (*memo.stairBaseLine.coords)[i+1];
        if (std::abs (p.x-q.x) > 1e-8 || std::abs (p.y-q.y) > 1e-8) return CreateErrorResponse (APIERR_BADPARS, "NativeSolverMovedSourceBaseline_NoCreate");
    }
    return {};
}

// One explicit straight-flight test schema; no global rule/preference fields.
static GS::UniString StairDataSchema () {
    return R"({"type":"object","properties":{"favoriteName":{"type":"string","minLength":1},"elementId":{"$ref":"#/ElementId"},"baseLinePoints":{"type":"array","minItems":2,"maxItems":2,"items":{"type":"object","properties":{"x":{"type":"number"},"y":{"type":"number"}},"required":["x","y"],"additionalProperties":false}},"zCoordinate":{"type":"number"},"floorIndex":{"type":"integer"},"totalHeight":{"type":"number","exclusiveMinimum":0},"flightWidth":{"type":"number","exclusiveMinimum":0},"stepNum":{"type":"integer","minimum":2},"riserHeight":{"type":"number","exclusiveMinimum":0},"treadDepth":{"type":"number","exclusiveMinimum":0},"treadDepthLocked":{"type":"boolean","enum":[true]},"finishVisible":{"type":"boolean"},"expectedTotalHeight":{"type":"number"},"expectedGoing":{"type":"number"},"expectedStepNum":{"type":"integer"}},"required":["baseLinePoints","zCoordinate","floorIndex","totalHeight","flightWidth","stepNum","riserHeight","treadDepth","treadDepthLocked","finishVisible"],"additionalProperties":false})";
}
CreateExactStairsV1Command::CreateExactStairsV1Command () { commandName = "CreateExactStairsV1"; }
GS::Optional<GS::UniString> CreateExactStairsV1Command::GetInputParametersSchema () const {
    return GS::UniString (R"({"type":"object","properties":{"stairsData":{"type":"array","minItems":1,"maxItems":1,"items":)") + StairDataSchema () + R"(}},"required":["stairsData"],"additionalProperties":false})";
}
GS::Optional<GS::ObjectState> CreateExactStairsV1Command::SetTypeSpecificParameters (API_Element& e, API_ElementMemo& memo, const Stories& stories, const GS::ObjectState& params) const { return ExactSettings (e, memo, stories, params); }

#define APA_STAIR_READ_IMPL(CLASS,NAME) \
CLASS::CLASS () : CommandBase (CommonSchema::Used) {} \
GS::String CLASS::GetName () const { return NAME; } \
GS::Optional<GS::UniString> CLASS::GetRawResponseSchema () const { return R"({"type":"object","additionalProperties":true})"; }
APA_STAIR_READ_IMPL(GetNativeStairGeometryV1Command,"GetNativeStairGeometryV1")
APA_STAIR_READ_IMPL(EvaluateNativeStairGeometryV1Command,"EvaluateNativeStairGeometryV1")
APA_STAIR_READ_IMPL(ModifyNativeStairGeometryV1Command,"ModifyNativeStairGeometryV1")
#undef APA_STAIR_READ_IMPL
GS::Optional<GS::UniString> GetNativeStairGeometryV1Command::GetInputParametersSchema () const { return R"({"type":"object","properties":{"elementId":{"$ref":"#/ElementId"}},"required":["elementId"],"additionalProperties":false})"; }
GS::ObjectState GetNativeStairGeometryV1Command::Execute (const GS::ObjectState& params, GS::ProcessControl&) const {
    API_Element e = {}; API_ElementMemo memo = {}; const GS::OnExit guard ([&] () { ACAPI_DisposeElemMemoHdls (&memo); });
    const GSErrCode err = ReadStair (GetGuidFromArrayItem ("elementId", params), e, memo);
    if (err != NoError) return CreateErrorResponse (err, "NativeStairRequired"); return StairState (e, memo);
}
GS::Optional<GS::UniString> EvaluateNativeStairGeometryV1Command::GetInputParametersSchema () const { return StairDataSchema (); }
GS::ObjectState EvaluateNativeStairGeometryV1Command::Execute (const GS::ObjectState& params, GS::ProcessControl&) const {
    API_Element e = {}; API_ElementMemo memo = {}; const GS::OnExit guard ([&] () { ACAPI_DisposeElemMemoHdls (&memo); });
    const GSErrCode err = ReadStair (GetGuidFromArrayItem ("elementId", params), e, memo);
    if (err != NoError) return CreateErrorResponse (err, "NativeStairSourceRequired");
    auto failure = ExactSettings (e, memo, GetStories (), params);
    if (failure.HasValue ()) return failure.Get ();
    auto out = StairState (e, memo); out.Add ("status", "DETACHED_NATIVE_SOLVER_PASS_NOT_CREATED"); return out;
}
GS::Optional<GS::UniString> ModifyNativeStairGeometryV1Command::GetInputParametersSchema () const { return StairDataSchema (); }
GS::ObjectState ModifyNativeStairGeometryV1Command::Execute (const GS::ObjectState& params, GS::ProcessControl&) const {
    API_Element e = {}; API_ElementMemo memo = {}; const GS::OnExit guard ([&] () { ACAPI_DisposeElemMemoHdls (&memo); });
    GSErrCode err = ReadStair (GetGuidFromArrayItem ("elementId", params), e, memo);
    if (err != NoError) return CreateErrorResponse (err, "NativeStairRequired");
    double height = 0, going = 0; UInt32 steps = 0; Int32 floor = 0;
    if (!params.Get ("expectedTotalHeight", height) || !params.Get ("expectedGoing", going) || !params.Get ("expectedStepNum", steps) || !params.Get ("floorIndex", floor) ||
        !std::isfinite (height) || !std::isfinite (going) || std::abs (height-e.stair.totalHeight) > 1e-8 || std::abs (going-e.stair.treadDepth) > 1e-8 || steps != e.stair.stepNum || floor != e.header.floorInd) return CreateErrorResponse (APIERR_BADPARS, "NativeStairEditBaselineDrift");
    auto failure = ExactSettings (e, memo, GetStories (), params); if (failure.HasValue ()) return failure.Get ();
    API_Element mask = {}; ACAPI_ELEMENT_MASK_CLEAR (mask);
    ACAPI_ELEMENT_MASK_SET (mask, API_StairType, totalHeight); ACAPI_ELEMENT_MASK_SET (mask, API_StairType, treadDepth);
    ACAPI_ELEMENT_MASK_SET (mask, API_StairType, riserHeight); ACAPI_ELEMENT_MASK_SET (mask, API_StairType, stepNum);
    ACAPI_ELEMENT_MASK_SET (mask, API_StairType, flightWidth); ACAPI_ELEMENT_MASK_SET (mask, API_StairType, basePlane);
    ACAPI_ELEMENT_MASK_SET (mask, API_StairType, treadDepthLocked); ACAPI_ELEMENT_MASK_SET (mask, API_StairType, totalHeightLocked);
    err = ACAPI_CallUndoableCommand ("APA exact native Stair edit", [&] () -> GSErrCode { return ACAPI_Element_Change (&e, &mask, &memo, APIMemoMask_All, true); });
    if (err != NoError) return CreateErrorResponse (err, "NativeStairEdit");
    GS::ObjectState out; out.AddList<GS::ObjectState> ("executionResults") (CreateSuccessfulExecutionResult ()); return out;
}
