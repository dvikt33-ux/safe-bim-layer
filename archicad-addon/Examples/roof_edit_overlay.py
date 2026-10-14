"""Extend the existing Tapir Roof commands in an isolated SDK source overlay."""
from pathlib import Path


def apply(addon_source):
    path=Path(addon_source)/'Sources/ExtendedElementCommands.cpp'
    text=path.read_text(encoding='utf8')
    if '// APA_NATIVE_ROOF_EDIT_V1' in text:return
    def replace_once(old,new):
        nonlocal text
        if text.count(old)!=1:raise ValueError('ROOF_OVERLAY_SOURCE_ANCHOR_CHANGED')
        text=text.replace(old,new,1)
    start=text.index('GS::Optional<GS::UniString> CreateRoofsCommand::GetInputParametersSchema')
    end=text.index('GS::Optional<GS::UniString> CreateRoofsCommand::GetRawResponseSchema',start)
    block=text[start:end];anchor='"level": { "type": "number" },'
    if block.count(anchor)!=1:raise ValueError('ROOF_CREATE_SCHEMA_ANCHOR_CHANGED')
    text=text[:start]+block.replace(anchor,anchor+'\n                        "sourceRoofId": { "$ref": "#/ElementId" },',1)+text[end:]
    replace_once('''            bool changed = false;
            {
                auto error = ApplyRoofStructure (element, nullptr, data, changed);''','''            // APA_NATIVE_ROOF_EDIT_V1: copy native common attributes, not SEO or geometry.
            GS::ObjectState sourceRoofId;
            if (data.Get ("sourceRoofId", sourceRoofId)) {
                API_Element source = {};
                source.header.guid = GetGuidFromObjectState (sourceRoofId);
                err = ACAPI_Element_Get (&source);
                if (err != NoError || source.header.type != API_RoofID) {
                    elements.Push (CreateErrorResponse (APIERR_BADPARS, "Readable native source Roof required."));
                    continue;
                }
                element.roof.shellBase = source.roof.shellBase;
                element.header.layer = source.header.layer;
                element.header.floorInd = source.header.floorInd;
            }
            bool changed = false;
            {
                auto error = ApplyRoofStructure (element, nullptr, data, changed);''')
    start=text.index('GS::Optional<GS::UniString> ModifyRoofsCommand::GetInputParametersSchema')
    end=text.index('GS::Optional<GS::UniString> ModifyRoofsCommand::GetRawResponseSchema',start)
    block=text[start:end];anchor='"elementId": { "$ref": "#/ElementId" },'
    if block.count(anchor)!=1:raise ValueError('ROOF_MODIFY_SCHEMA_ANCHOR_CHANGED')
    extra='''
                        "floorIndex": { "type": "integer" },
                        "angle": { "type": "number", "exclusiveMinimum": 0, "exclusiveMaximum": 1.5707963267948966 },
                        "pivotLine": {
                            "type": "object", "properties": {
                                "begCoordinate": { "$ref": "#/Coordinate2D" },
                                "endCoordinate": { "$ref": "#/Coordinate2D" }
                            }, "additionalProperties": false, "required": ["begCoordinate", "endCoordinate"]
                        },'''
    text=text[:start]+block.replace(anchor,anchor+extra,1)+text[end:]
    replace_once('''            if (element.roof.roofClass != API_PolyRoofID) {
                results.Push (CreateFailedExecutionResult (APIERR_NOTSUPPORTED, "Only multi-plane roofs are supported.")); 
                continue;
            }

            API_Element mask = {};''','''            if (element.header.type != API_RoofID) {
                results.Push (CreateFailedExecutionResult (APIERR_BADPARS, "Native Roof required."));
                continue;
            }
            const bool isSinglePlane = element.roof.roofClass == API_PlaneRoofID;
            if ((isSinglePlane && (item.Get ("levels") != nullptr || item.Get ("eavesOverhang") != nullptr)) ||
                (!isSinglePlane && (item.Get ("angle") != nullptr || item.Get ("pivotLine") != nullptr))) {
                results.Push (CreateFailedExecutionResult (APIERR_BADPARS, "Roof class and requested slope contract disagree."));
                continue;
            }

            API_Element mask = {};''')
    start=text.index('GS::ObjectState ModifyRoofsCommand::Execute')
    end=text.index('\n}\n',start)+3
    block=text[start:end]
    anchor='''            auto error = ApplyRoofDetails (element, &mask, item, stories, changed);'''
    replacement='''            if (isSinglePlane) {
                auto angle = GetOptionalDouble (item, "angle");
                if (angle.HasValue ()) {
                    element.roof.u.planeRoof.angle = angle.Get ();
                    ACAPI_ELEMENT_MASK_SET (mask, API_RoofType, u.planeRoof.angle);
                    changed = true;
                }
                GS::ObjectState pivot;
                if (item.Get ("pivotLine", pivot)) {
                    GS::ObjectState beg, end;
                    pivot.Get ("begCoordinate", beg); pivot.Get ("endCoordinate", end);
                    if (IsSame2DCoordinate (beg, end)) {
                        results.Push (CreateFailedExecutionResult (APIERR_BADPARS, "Zero length roof pivot."));
                        continue;
                    }
                    element.roof.u.planeRoof.baseLine.c1 = Get2DCoordinateFromObjectState (beg);
                    element.roof.u.planeRoof.baseLine.c2 = Get2DCoordinateFromObjectState (end);
                    element.roof.u.planeRoof.posSign = true;
                    ACAPI_ELEMENT_MASK_SET (mask, API_RoofType, u.planeRoof.baseLine);
                    ACAPI_ELEMENT_MASK_SET (mask, API_RoofType, u.planeRoof.posSign);
                    changed = true;
                }
            }
            auto error = ApplyRoofDetails (element, &mask, item, stories, changed);'''
    if block.count(anchor)!=1:raise ValueError('ROOF_MODIFY_IMPLEMENTATION_CHANGED')
    block=block.replace(anchor,replacement,1)
    block=block.replace('''                ACAPI_Element_GetMemo (element.header.guid, &memo);''','''                // Build new contour handles; never reuse mismatched edge arrays.
                if (!isSinglePlane) ACAPI_Element_GetMemo (element.header.guid, &memo);''',1)
    block=block.replace('''auto error = BuildRoofMemoFromGeometry (element, memo, polygonOutline, polygonArcs, holes);''','''auto error = isSinglePlane
                    ? BuildPlaneRoofMemoFromGeometry (element, memo, polygonOutline, polygonArcs, holes)
                    : BuildRoofMemoFromGeometry (element, memo, polygonOutline, polygonArcs, holes);''',1)
    block=block.replace('''                err = ACAPI_Element_Change (&element, &mask, &memo, APIMemoMask_AdditionalPolygon, true);''','''                if (isSinglePlane) ACAPI_ELEMENT_MASK_SET (mask, API_RoofType, u.planeRoof.poly);
                err = ACAPI_Element_Change (&element, &mask, &memo,
                    isSinglePlane ? (APIMemoMask_Polygon | APIMemoMask_EdgeTrims | APIMemoMask_SideMaterials) : APIMemoMask_AdditionalPolygon, true);''',1)
    text=text[:start]+block+text[end:]
    # Vertical cuts give genuine matching faces at assembled SinglePlane ridges.
    start=text.index('GS::Optional<GS::UniString> BuildPlaneRoofMemoFromGeometry')
    end=text.index('\n}\n',start)
    block=text[start:end]
    index=block.rfind('    return {};')
    if index<0:raise ValueError('ROOF_MEMO_RETURN_CHANGED')
    edge='''    memo.edgeTrims = reinterpret_cast<API_EdgeTrim**> (BMAllocateHandle ((nCoords + 1) * sizeof (API_EdgeTrim), ALLOCATE_CLEAR, 0));
    memo.sideMaterials = reinterpret_cast<API_OverriddenAttribute*> (BMAllocatePtr ((nCoords + 1) * sizeof (API_OverriddenAttribute), ALLOCATE_CLEAR, 0));
    if (memo.edgeTrims == nullptr || memo.sideMaterials == nullptr) return "Roof edge allocation failed.";
    for (Int32 i = 1; i <= nCoords; ++i) {
        (*memo.edgeTrims)[i].sideType = APIEdgeTrim_Vertical;
        memo.sideMaterials[i] = element.roof.shellBase.sidMat;
    }

'''
    block=block[:index]+edge+block[index:];text=text[:start]+block+text[end:]
    path.write_text(text,encoding='utf8')
