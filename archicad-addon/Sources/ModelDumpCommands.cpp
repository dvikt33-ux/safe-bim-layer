#include "ModelDumpCommands.hpp"
#include "MigrationHelper.hpp"
#include "ACAPI/Element/Opening/Opening.hpp"
#include <set>
#include <map>
#include <string>
#include <vector>
#include <chrono>

namespace {
GS::ObjectState XY (const API_Coord& p) { return GS::ObjectState ("x", p.x, "y", p.y); }
GS::ObjectState XYZ (double x, double y, double z) { return GS::ObjectState ("x", x, "y", y, "z", z); }
std::string Key (const API_Guid& g) { return APIGuidToString (g).ToCStr ().Get (); }
GSErrCode Component (API_3DTypeID type, Int32 i, API_Component3D& c) {
    c = {}; c.header.typeID = type; c.header.index = i;
    return ACAPI_ModelAccess_GetComponent (&c);
}
GS::ObjectState Attribute (API_AttrTypeID type, API_AttributeIndex index, const char* field) {
    GS::ObjectState os ("nativeField", field, "attributeType", static_cast<Int32> (type), "attributeIndex", GetAttributeIndex (index));
    if (GetAttributeIndex (index) == 0) return os;
    API_Attribute a = {}; GS::UniString name;
    a.header.typeID = type; a.header.index = index; a.header.uniStringNamePtr = &name;
    GSErrCode err = ACAPI_Attribute_Get (&a);
    if (err == NoError) {
        os.Add ("guid", APIGuidToString (a.header.guid)); os.Add ("name", name);
        if (type == API_BuildingMaterialID) os.Add ("defaultSurface", Attribute (API_MaterialID, a.buildingMaterial.cutMaterial, "buildingMaterial.cutMaterial"));
        if (type == API_CompWallID) {
            API_AttributeDefExt def = {};
            GSErrCode de = ACAPI_Attribute_GetDefExt (type, index, &def);
            if (de == NoError && def.cwall_compItems != nullptr) {
                const auto& skins = os.AddList<GS::ObjectState> ("skins");
                for (Int32 i = 0; i < a.compWall.nComps; ++i) {
                    const auto& skin = (*def.cwall_compItems)[i];
                    skins (GS::ObjectState ("index", i, "thickness", skin.fillThick,
                        "buildingMaterial", Attribute (API_BuildingMaterialID, skin.buildingMaterial, "composite.skin.buildingMaterial")));
                }
            } else os.Add ("definitionReadError", static_cast<Int32> (de));
            ACAPI_DisposeAttrDefsHdlsExt (&def);
        }
    }
    else os.Add ("readError", static_cast<Int32> (err));
    // Surface attributes alone can return an allocated texture location.
    if (type == API_MaterialID) delete a.material.texture.fileLoc;
    return os;
}
GS::ObjectState Override (const API_OverriddenAttribute& a, const char* field) {
    GS::ObjectState os = Attribute (API_MaterialID, a.value, field);
    os.Add ("overridden", a.hasValue);
    os.Add ("effectiveWhen", "overridden=true; otherwise use structure/GDL source");
    return os;
}
void Structure (GS::ObjectState& os, API_ModelElemStructureType type, API_AttributeIndex bm, API_AttributeIndex composite, API_AttributeIndex profile, const char* field) {
    os.Add ("structureType", static_cast<Int32> (type));
    if (type == API_BasicStructure) os.Add ("buildingMaterial", Attribute (API_BuildingMaterialID, bm, field));
    if (type == API_CompositeStructure) os.Add ("composite", Attribute (API_CompWallID, composite, field));
    if (type == API_ProfileStructure) os.Add ("profile", Attribute (API_ProfileID, profile, field));
}
void MaterialParameters (const API_Element& e, GS::ObjectState& bindings) {
    API_ElementMemo memo = {};
    const GS::OnExit disposeMemo ([&] () { ACAPI_DisposeElemMemoHdls (&memo); });
    GSErrCode err = ACAPI_Element_GetMemo (e.header.guid, &memo, APIMemoMask_AddPars);
    API_GetParamsType active = {};
    bool opened = false;
    const GS::OnExit disposeParameters ([&] () {
        if (opened) ACAPI_LibraryPart_CloseParameters ();
        ACAPI_DisposeAddParHdl (&active.params);
    });
    API_AddParType** parameters = memo.params;
    const char* source = "ACAPI_Element_GetMemo(APIMemoMask_AddPars)";
    if (parameters == nullptr) {
        API_ParamOwnerType owner = {}; owner.libInd = -1; owner.guid = e.header.guid; owner.type = e.header.type;
        err = ACAPI_LibraryPart_OpenParameters (&owner);
        opened = err == NoError;
        if (opened) err = ACAPI_LibraryPart_GetActParameters (&active);
        parameters = active.params; source = "ACAPI_LibraryPart_GetActParameters";
    }
    bindings.Add ("parameterApi", source);
    if (err != NoError || parameters == nullptr) { bindings.Add ("parameterReadError", static_cast<Int32> (err)); return; }
    bindings.Add ("parameterUseInScript", "NOT_TRACED; typed native assignments, not guessed face roles");
    const auto& list = bindings.AddList<GS::ObjectState> ("materialParameters");
    GSSize count = BMGetHandleSize (reinterpret_cast<GSHandle> (parameters)) / sizeof (API_AddParType);
    for (GSSize i = 0; i < count; ++i) {
        const auto& p = (*parameters)[i];
        API_AttrTypeID type;
        if (p.typeID == APIParT_Mater) type = API_MaterialID;
        else if (p.typeID == APIParT_BuildingMaterial) type = API_BuildingMaterialID;
        else if (p.typeID == APIParT_Profile) type = API_ProfileID;
        else continue;
        GS::ObjectState item ("name", p.name, "index", p.index, "nativeParameterType", static_cast<Int32> (p.typeID), "flags", p.flags);
        if (p.typeMod == API_ParSimple) {
            item.Add ("value", p.value.real);
            if (p.value.real > 0) item.Add ("attribute", Attribute (type, ACAPI_CreateAttributeIndex (static_cast<Int32> (p.value.real)), "gdlParameter"));
        } else {
            item.Add ("dimension1", p.dim1); item.Add ("dimension2", p.dim2);
            const auto& values = item.AddList<double> ("arrayValues");
            if (p.value.array != nullptr) {
                GSSize n = BMGetHandleSize (p.value.array) / sizeof (double);
                for (GSSize k = 0; k < n; ++k) values (reinterpret_cast<double*> (*p.value.array)[k]);
            }
        }
        list (item);
    }
}
void Symbol (GS::ObjectState& bindings, GS::ObjectState& relationships, const API_Guid& owner, const API_Guid& symbol) {
    bindings.Add ("source", "NATIVE_SYMBOL_AND_TYPED_GDL_PARAMETERS");
    bindings.Add ("nativeSymbolGuid", APIGuidToString (symbol));
    relationships.Add ("hostGuid", APIGuidToString (owner));
}
void StoryNames (API_NavigatorItem item, std::map<Int32, GS::UniString>& names, std::map<Int32, GS::UniString>& displays, int depth = 0) {
    if (item.itemType == API_StoryNavItem) {
        names[item.floorNum] = GS::UniString (item.uName);
        displays[item.floorNum] = GS::UniString (item.uiId) + " " + GS::UniString (item.uName);
        return;
    }
    if (depth >= 4) return;
    item.mapId = API_ProjectMap;
    GS::Array<API_NavigatorItem> children;
    if (ACAPI_Navigator_GetNavigatorChildrenItems (&item, &children) == NoError)
        for (const auto& child : children) StoryNames (child, names, displays, depth + 1);
}
GS::ObjectState Element (const API_Elem_Head& h) {
    GS::ObjectState os ("guid", APIGuidToString (h.guid), "type", GetElementTypeNonLocalizedName (h.type.typeID),
                        "nativeTypeId", static_cast<Int32> (h.type.typeID), "homeStory", h.floorInd);
    API_Element e = {}; e.header.guid = h.guid;
    GSErrCode err = ACAPI_Element_Get (&e);
    GS::ObjectState bindings ("api", "ACAPI_Element_Get", "coverage", "NATIVE_FIELDS_AVAILABLE_FOR_TYPE");
    GS::ObjectState placement ("coordinateNote", "Native reference fields retain their API meaning; physical vertices are absolute project XYZ.");
    GS::ObjectState relationships;
    if (err != NoError) { os.Add ("nativeElementReadError", static_cast<Int32> (err)); }
    else switch (h.type.typeID) {
    case API_WallID:
        Structure (bindings, e.wall.modelElemStructureType, e.wall.buildingMaterial, e.wall.composite, e.wall.profileAttr, "wall.structure");
        bindings.Add ("refMat", Override (e.wall.refMat, "wall.refMat"));
        bindings.Add ("oppMat", Override (e.wall.oppMat, "wall.oppMat"));
        bindings.Add ("sidMat", Override (e.wall.sidMat, "wall.sidMat"));
        placement.Add ("referenceGeometry", GS::ObjectState ("kind", "WallReferenceLine", "begin", XY (e.wall.begC), "end", XY (e.wall.endC),
            "arcAngle", e.wall.angle, "referenceLineLocation", static_cast<Int32> (e.wall.referenceLineLocation), "offset", e.wall.offset,
            "bottomOffsetFromHomeStory", e.wall.bottomOffset, "height", e.wall.height, "thickness", e.wall.thickness, "flipped", e.wall.flipped));
        break;
    case API_SlabID:
        Structure (bindings, e.slab.modelElemStructureType, e.slab.buildingMaterial, e.slab.composite, API_AttributeIndex {}, "slab.structure");
        bindings.Add ("topMat", Override (e.slab.topMat, "slab.topMat")); bindings.Add ("sidMat", Override (e.slab.sideMat, "slab.sideMat")); bindings.Add ("botMat", Override (e.slab.botMat, "slab.botMat"));
        placement.Add ("referenceGeometry", GS::ObjectState ("levelFromHomeStory", e.slab.level, "referencePlaneLocation", static_cast<Int32> (e.slab.referencePlaneLocation), "thickness", e.slab.thickness));
        break;
    case API_RoofID:
    case API_ShellID: {
        const API_ShellBaseType& s = h.type.typeID == API_RoofID ? e.roof.shellBase : e.shell.shellBase;
        Structure (bindings, s.modelElemStructureType, s.buildingMaterial, s.composite, API_AttributeIndex {}, "shellBase.structure");
        bindings.Add ("topMat", Override (s.topMat, "shellBase.topMat")); bindings.Add ("sidMat", Override (s.sidMat, "shellBase.sidMat")); bindings.Add ("botMat", Override (s.botMat, "shellBase.botMat"));
        if (h.type.typeID == API_RoofID) {
            GS::ObjectState r ("roofClass", static_cast<Int32> (e.roof.roofClass));
            if (e.roof.roofClass == API_PlaneRoofID) { const auto& p = e.roof.u.planeRoof;
                r.Add ("baseLine", GS::ObjectState ("begin", XY (p.baseLine.c1), "end", XY (p.baseLine.c2)));
                r.Add ("slopeAngle", p.angle); r.Add ("posSign", p.posSign);
            }
            placement.Add ("referenceGeometry", r);
        }
        break;
    }
    case API_WindowID: case API_DoorID:
        relationships.Add ("hostGuid", APIGuidToString (e.window.owner));
        bindings.Add ("source", "GDL_LIBRARY_PART_AND_PARAMETERS"); bindings.Add ("libraryPartIndex", e.window.openingBase.libInd);
        placement.Add ("referenceGeometry", GS::ObjectState ("centerOffsetAlongHost", e.window.objLoc, "sillHeight", e.window.lower,
            "width", e.window.openingBase.width, "height", e.window.openingBase.height, "refSide", e.window.openingBase.refSide, "reflected", e.window.openingBase.reflected));
        break;
    case API_SkylightID:
        relationships.Add ("hostGuid", APIGuidToString (e.skylight.owner));
        bindings.Add ("source", "GDL_LIBRARY_PART_AND_PARAMETERS"); bindings.Add ("libraryPartIndex", e.skylight.openingBase.libInd);
        placement.Add ("referenceGeometry", GS::ObjectState ("anchorPosition", XY (e.skylight.anchorPosition), "anchorLevel", e.skylight.anchorLevel, "azimuthAngle", e.skylight.azimuthAngle, "elevationAngle", e.skylight.elevationAngle));
        break;
    case API_OpeningID: {
        auto opening = ACAPI::Element::Opening::Get (ACAPI::UniqueID (h.guid, ACAPI_GetToken ()));
        if (opening.IsOk ()) {
            auto parent = opening->GetParentElement ();
            if (parent.IsOk ()) relationships.Add ("hostGuid", parent->GetGuid ().ToUniString ());
        }
        bindings.Add ("source", "VOID_CUTS_HOST; surface source belongs to host");
        break;
    }
    case API_ObjectID: case API_LampID:
        bindings.Add ("source", e.object.useObjMaterials ? "GDL_LIBRARY_PART_AND_PARAMETERS" : "ELEMENT_SURFACE_OVERRIDE");
        bindings.Add ("useObjMaterials", e.object.useObjMaterials); bindings.Add ("surface", Attribute (API_MaterialID, e.object.mat, "object.mat")); bindings.Add ("libraryPartIndex", e.object.libInd);
        if (e.object.owner != APINULLGuid) relationships.Add ("hostGuid", APIGuidToString (e.object.owner));
        placement.Add ("referenceGeometry", GS::ObjectState ("position", XY (e.object.pos), "levelFromHomeStory", e.object.level, "angle", e.object.angle, "xRatio", e.object.xRatio, "yRatio", e.object.yRatio, "reflected", e.object.reflected));
        break;
    case API_BeamID:
        placement.Add ("referenceGeometry", GS::ObjectState ("begin", XY (e.beam.begC), "end", XY (e.beam.endC), "levelFromHomeStory", e.beam.level));
        bindings.Add ("source", "SEGMENT_ATTRIBUTES"); break;
    case API_ColumnID:
        placement.Add ("referenceGeometry", GS::ObjectState ("origin", XY (e.column.origoPos), "bottomOffsetFromHomeStory", e.column.bottomOffset));
        bindings.Add ("source", "SEGMENT_ATTRIBUTES"); break;
    case API_BeamSegmentID: {
        const auto& s = e.beamSegment;
        Structure (bindings, s.assemblySegmentData.modelElemStructureType, s.assemblySegmentData.buildingMaterial, API_AttributeIndex {}, s.assemblySegmentData.profileAttr, "beamSegment.assemblySegmentData");
        relationships.Add ("hostGuid", APIGuidToString (s.owner));
        bindings.Add ("leftMaterial", Override (s.leftMaterial, "beamSegment.leftMaterial")); bindings.Add ("topMaterial", Override (s.topMaterial, "beamSegment.topMaterial"));
        bindings.Add ("rightMaterial", Override (s.rightMaterial, "beamSegment.rightMaterial")); bindings.Add ("bottomMaterial", Override (s.bottomMaterial, "beamSegment.bottomMaterial"));
        bindings.Add ("endsMaterial", Override (s.endsMaterial, "beamSegment.endsMaterial")); break;
    }
    case API_ColumnSegmentID: {
        const auto& s = e.columnSegment;
        Structure (bindings, s.assemblySegmentData.modelElemStructureType, s.assemblySegmentData.buildingMaterial, API_AttributeIndex {}, s.assemblySegmentData.profileAttr, "columnSegment.assemblySegmentData");
        relationships.Add ("hostGuid", APIGuidToString (s.owner));
        bindings.Add ("extrusionSurfaceMaterial", Override (s.extrusionSurfaceMaterial, "columnSegment.extrusionSurfaceMaterial")); bindings.Add ("endsMaterial", Override (s.endsMaterial, "columnSegment.endsMaterial")); break;
    }
    case API_MorphID: {
        bindings.Add ("buildingMaterial", Attribute (API_BuildingMaterialID, e.morph.buildingMaterial, "morph.buildingMaterial"));
        bindings.Add ("material", Override (e.morph.material, "morph.material (non-customized faces)"));
        bindings.Add ("customFaceAssignments", "effective surfaces are in resultant mesh; custom Morph face source is not expanded");
        GS::ObjectState p ("levelFromHomeStory", e.morph.level);
        const auto& t = p.AddList<double> ("placementTransform"); for (double v : e.morph.tranmat.tmx) t (v);
        placement.Add ("referenceGeometry", p); break;
    }
    case API_MeshID:
        bindings.Add ("buildingMaterial", Attribute (API_BuildingMaterialID, e.mesh.buildingMaterial, "mesh.buildingMaterial"));
        bindings.Add ("topMat", Override (e.mesh.topMat, "mesh.topMat")); bindings.Add ("sideMat", Override (e.mesh.sideMat, "mesh.sideMat")); bindings.Add ("botMat", Override (e.mesh.botMat, "mesh.botMat"));
        placement.Add ("referenceGeometry", GS::ObjectState ("levelFromHomeStory", e.mesh.level, "skirtLevel", e.mesh.skirtLevel)); break;
    case API_CurtainWallFrameID:
        bindings.Add ("buildingMaterial", Attribute (API_BuildingMaterialID, e.cwFrame.buildingMaterial, "cwFrame.buildingMaterial"));
        bindings.Add ("surface", Attribute (API_MaterialID, e.cwFrame.material, "cwFrame.material")); bindings.Add ("useOwnMaterial", e.cwFrame.useOwnMaterial);
        bindings.Add ("libraryPartIndex", e.cwFrame.libInd);
        relationships.Add ("hostGuid", APIGuidToString (e.cwFrame.owner));
        placement.Add ("referenceGeometry", GS::ObjectState ("begin", XYZ (e.cwFrame.begC.x, e.cwFrame.begC.y, e.cwFrame.begC.z), "end", XYZ (e.cwFrame.endC.x, e.cwFrame.endC.y, e.cwFrame.endC.z))); break;
    case API_CurtainWallPanelID:
        bindings.Add ("buildingMaterial", Attribute (API_BuildingMaterialID, e.cwPanel.buildingMaterial, "cwPanel.buildingMaterial"));
        bindings.Add ("outerSurfaceMaterial", Override (e.cwPanel.outerSurfaceMaterial, "cwPanel.outerSurfaceMaterial"));
        bindings.Add ("innerSurfaceMaterial", Override (e.cwPanel.innerSurfaceMaterial, "cwPanel.innerSurfaceMaterial"));
        bindings.Add ("cutSurfaceMaterial", Override (e.cwPanel.cutSurfaceMaterial, "cwPanel.cutSurfaceMaterial"));
        bindings.Add ("libraryPartIndex", e.cwPanel.libInd); relationships.Add ("hostGuid", APIGuidToString (e.cwPanel.owner)); break;
    case API_ZoneID:
        bindings.Add ("surface", Attribute (API_MaterialID, e.zone.material, "zone.material")); bindings.Add ("oneMaterial", e.zone.oneMat); break;
    case API_TreadID: Symbol (bindings, relationships, e.stairTread.owner, e.stairTread.libId); break;
    case API_RiserID: Symbol (bindings, relationships, e.stairRiser.owner, e.stairRiser.libId); break;
    case API_StairStructureID:
        relationships.Add ("hostGuid", APIGuidToString (e.stairStructure.owner));
        bindings.Add ("structureType", static_cast<Int32> (e.stairStructure.structType));
        if (e.stairStructure.structType == APIST_Monolith) {
            const auto& s = e.stairStructure.data.monolith;
            bindings.Add ("source", "NATIVE_MONOLITH_STAIR_STRUCTURE");
            bindings.Add ("buildingMaterial", Attribute (API_BuildingMaterialID, s.buildingMaterial, "stairStructure.data.monolith.buildingMaterial"));
            bindings.Add ("topMaterial", Override (s.topMaterial, "stairStructure.data.monolith.topMaterial"));
            bindings.Add ("leftMaterial", Override (s.leftMaterial, "stairStructure.data.monolith.leftMaterial"));
            bindings.Add ("rightMaterial", Override (s.rightMaterial, "stairStructure.data.monolith.rightMaterial"));
            bindings.Add ("bottomMaterial", Override (s.bottomMaterial, "stairStructure.data.monolith.bottomMaterial"));
            bindings.Add ("surfaceMaterial", Attribute (API_MaterialID, s.surfaceMaterial, "stairStructure.data.monolith.surfaceMaterial"));
            bindings.Add ("materialsChained", s.materialsChained);
        } else {
            bindings.Add ("source", "NATIVE_SYMBOL_AND_TYPED_GDL_PARAMETERS");
            bindings.Add ("nativeSymbolGuid", APIGuidToString (e.stairStructure.libId));
        }
        break;
    case API_RailingBalusterID: Symbol (bindings, relationships, e.railingBaluster.owner, e.railingBaluster.symbID); break;
    case API_RailingInnerPostID: Symbol (bindings, relationships, e.railingInnerPost.owner, e.railingInnerPost.symbID); break;
    case API_RailingPostID: Symbol (bindings, relationships, e.railingPost.owner, e.railingPost.symbID); break;
    case API_RailingToprailID: Symbol (bindings, relationships, e.railingToprail.owner, e.railingToprail.symbID); break;
    case API_RailingHandrailID: Symbol (bindings, relationships, e.railingHandrail.owner, e.railingHandrail.symbID); break;
    case API_RailingRailID: Symbol (bindings, relationships, e.railingRail.owner, e.railingRail.symbID); break;
    case API_RailingToprailEndID: Symbol (bindings, relationships, e.railingToprailEnd.owner, e.railingToprailEnd.symbID); break;
    case API_RailingHandrailEndID: Symbol (bindings, relationships, e.railingHandrailEnd.owner, e.railingHandrailEnd.symbID); break;
    case API_RailingRailEndID: Symbol (bindings, relationships, e.railingRailEnd.owner, e.railingRailEnd.symbID); break;
    case API_RailingToprailConnectionID: Symbol (bindings, relationships, e.railingToprailConnection.owner, e.railingToprailConnection.symbID); break;
    case API_RailingHandrailConnectionID: Symbol (bindings, relationships, e.railingHandrailConnection.owner, e.railingHandrailConnection.symbID); break;
    case API_RailingRailConnectionID: Symbol (bindings, relationships, e.railingRailConnection.owner, e.railingRailConnection.symbID); break;
    default: bindings.Add ("source", "TYPE_SPECIFIC_FIELDS_NOT_EXTRACTED; effective face surfaces remain available"); break;
    }
    if (err == NoError && !(h.type.typeID == API_StairStructureID && e.stairStructure.structType == APIST_Monolith) && (h.type.typeID == API_ObjectID || h.type.typeID == API_LampID || h.type.typeID == API_WindowID || h.type.typeID == API_DoorID || h.type.typeID == API_SkylightID || h.type.typeID == API_CurtainWallFrameID || h.type.typeID == API_CurtainWallPanelID || (h.type.typeID >= API_RiserID && h.type.typeID <= API_RailingRailConnectionID)))
        MaterialParameters (e, bindings);
    os.Add ("materialBindings", bindings); os.Add ("placement", placement); os.Add ("relationships", relationships);
    return os;
}
}

GetModelDumpV1Command::GetModelDumpV1Command () : CommandBase (CommonSchema::NotUsed) {}
GS::String GetModelDumpV1Command::GetName () const { return "GetModelDumpV1"; }
GS::Optional<GS::UniString> GetModelDumpV1Command::GetInputParametersSchema () const { return R"({"type":"object","additionalProperties":false})"; }
GS::Optional<GS::UniString> GetModelDumpV1Command::GetRawResponseSchema () const { return R"({"type":"object"})"; }
GS::ObjectState GetModelDumpV1Command::Execute (const GS::ObjectState&, GS::ProcessControl&) const {
    const auto start = std::chrono::steady_clock::now ();
    GS::ObjectState out ("schemaVersion", 1, "units", "m", "coordinateSystem", "ABSOLUTE_PROJECT_XYZ",
        "geometryScope", "ALL_AVAILABLE_BODIES_IN_REGENERATED_3D_VIEW; existing layer/design-option/3D filters remain in force",
        "vertexIndexBase", 0, "representation", "ARCHICAD_RESULTANT_POLYGON_MODEL");
    API_StoryInfo si = {}; GSErrCode err = ACAPI_ProjectSetting_GetStorySettings (&si);
    if (err != NoError) return CreateErrorResponse (err, "GetStorySettings");
    std::map<Int32, GS::UniString> storyNames, storyDisplays;
    API_NavigatorSet nav = {}; nav.mapId = API_ProjectMap; Int32 navIndex = 0;
    if (ACAPI_Navigator_GetNavigatorSet (&nav, &navIndex) == NoError) {
        API_NavigatorItem root = {};
        if (ACAPI_Navigator_GetNavigatorItem (&nav.rootGuid, &root) == NoError) StoryNames (root, storyNames, storyDisplays);
    }
    const auto& stories = out.AddList<GS::ObjectState> ("stories");
    for (int i = 0; i <= si.lastStory - si.firstStory; ++i) {
        const auto& s = (*si.data)[i]; GS::UniString name (s.uName);
        GS::ObjectState story ("index", s.index, "nativeStoryName", name, "elevation", s.level);
        if (name.IsEmpty () && storyNames.find (s.index) != storyNames.end ()) name = storyNames[s.index];
        story.Add ("name", name);
        if (storyDisplays.find (s.index) != storyDisplays.end ()) story.Add ("displayName", storyDisplays[s.index]);
        stories (story);
    }
    BMKillHandle (reinterpret_cast<GSHandle*> (&si.data));
    std::map<std::string, API_Elem_Head> heads;
    GS::Array<API_Guid> ids; err = ACAPI_Element_GetElemList (API_ZombieElemID, &ids);
    if (err != NoError) return CreateErrorResponse (err, "GetElemList");
    for (const auto& guid : ids) { API_Elem_Head h = {}; h.guid = guid; if (ACAPI_Element_GetHeader (&h) == NoError) heads[Key (guid)] = h; }
    // Rebuild the current project's model, never open/switch/save a PLN.
    err = ACAPI_View_ShowAllIn3D (); if (err != NoError) return CreateErrorResponse (err, "ShowAllIn3D");
    bool regenerate = true; err = ACAPI_View_Rebuild (&regenerate); if (err != NoError) return CreateErrorResponse (err, "Regenerate3D");
    out.Add ("regenerated3D", true);
    void* oldSight = nullptr;
    err = ACAPI_Sight_SelectSight (nullptr, &oldSight);
    if (err != NoError) return CreateErrorResponse (err, "Select3DWindowSight");
    const GS::OnExit restoreSight ([&] () { ACAPI_Sight_SelectSight (oldSight, nullptr); });
    Int32 count = 0; err = ACAPI_ModelAccess_GetNum (API_BodyID, &count);
    if (err != NoError) return CreateErrorResponse (err, "GetNum(API_BodyID)");
    out.Add ("nativeBodySlots", count);
    const auto& bodies = out.AddList<GS::ObjectState> ("bodies");
    const auto& deleted = out.AddList<Int32> ("deletedBodySlots");
    std::set<Int32> materialIds;
    for (Int32 i = 1; i <= count; ++i) {
        API_Component3D c = {}; err = Component (API_BodyID, i, c);
        if (err == APIERR_DELETED) { deleted (i); continue; }
        if (err != NoError) return CreateErrorResponse (err, "GetComponent(Body)");
        const API_BodyType b = c.body;
        if (heads.find (Key (b.parent.guid)) == heads.end ()) {
            API_Elem_Head h = b.parent;
            ACAPI_Element_GetHeader (&h);
            heads[Key (b.parent.guid)] = h;
        }
        GS::ObjectState body ("nativeBodyIndex", i, "parentGuid", APIGuidToString (b.parent.guid), "status", b.status,
            "closed", (b.status & APIBody_Closed) != 0, "curved", (b.status & APIBody_Curved) != 0);
        const auto& matrix = body.AddList<double> ("transform"); for (double v : b.tranmat.tmx) matrix (v);
        const auto& vertices = body.AddList<GS::ObjectState> ("vertices");
        const double* m = b.tranmat.tmx;
        for (Int32 n = 1; n <= b.nVert; ++n) {
            err = Component (API_VertID, n, c); if (err != NoError) return CreateErrorResponse (err, "GetComponent(Vertex)");
            const auto& p = c.vert;
            vertices (XYZ (m[0]*p.x+m[1]*p.y+m[2]*p.z+m[3], m[4]*p.x+m[5]*p.y+m[6]*p.z+m[7], m[8]*p.x+m[9]*p.y+m[10]*p.z+m[11]));
        }
        std::vector<API_EdgeType> edgeData (b.nEdge + 1);
        const auto& edges = body.AddList<GS::ObjectState> ("edges");
        for (Int32 n = 1; n <= b.nEdge; ++n) {
            err = Component (API_EdgeID, n, c); if (err != NoError) return CreateErrorResponse (err, "GetComponent(Edge)");
            edgeData[n] = c.edge; edges (GS::ObjectState ("vertices", GS::Array<Int32> {c.edge.vert1-1, c.edge.vert2-1}, "nativeStatus", c.edge.status));
        }
        std::vector<Int32> pedgs (b.nPedg + 1);
        for (Int32 n = 1; n <= b.nPedg; ++n) { err = Component (API_PedgID, n, c); if (err != NoError) return CreateErrorResponse (err, "GetComponent(Pedg)"); pedgs[n] = c.pedg.pedg; }
        const auto& normals = body.AddList<GS::ObjectState> ("localNormals");
        for (Int32 n = 1; n <= b.nVect; ++n) { err = Component (API_VectID, n, c); if (err != NoError) return CreateErrorResponse (err, "GetComponent(Normal)"); normals (XYZ (c.vect.x, c.vect.y, c.vect.z)); }
        const auto& faces = body.AddList<GS::ObjectState> ("faces");
        for (Int32 n = 1; n <= b.nPgon; ++n) {
            err = Component (API_PgonID, n, c); if (err != NoError) return CreateErrorResponse (err, "GetComponent(Face)");
            const auto& p = c.pgon;
            GS::ObjectState f ("nativeFaceIndex", n, "materialId", p.iumat, "signedLocalNormalIndex", p.ivect, "nativeStatus", p.status);
            GS::Array<GS::Array<Int32>> contours; GS::Array<Int32> contour; GS::Array<Int32> refs;
            for (Int32 k = p.fpedg; k <= p.lpedg; ++k) {
                if (k < 1 || k > b.nPedg) return CreateErrorResponse (APIERR_BADINDEX, "Face edge reference out of range");
                Int32 ref = pedgs[k]; refs.Push (ref);
                if (ref == 0) { if (!contour.IsEmpty ()) contours.Push (contour); contour.Clear (); continue; }
                Int32 e = ref < 0 ? -ref : ref;
                if (e < 1 || e > b.nEdge) return CreateErrorResponse (APIERR_BADINDEX, "Face edge out of range");
                contour.Push ((ref > 0 ? edgeData[e].vert1 : edgeData[e].vert2) - 1);
            }
            if (!contour.IsEmpty ()) contours.Push (contour);
            f.Add ("contours", contours); f.Add ("signedNativeEdgeReferences", refs);
            faces (f); materialIds.insert (p.iumat);
        }
        bodies (body);
    }
    const auto& elements = out.AddList<GS::ObjectState> ("elements");
    for (const auto& item : heads) elements (Element (item.second));
    const auto& materials = out.AddList<GS::ObjectState> ("materials");
    for (Int32 id : materialIds) {
        API_Component3D c = {}; err = Component (API_UmatID, id, c);
        if (err != NoError) return CreateErrorResponse (err, "GetComponent(Material)");
        const auto& mat = c.umat.mater;
        const Int32 attrIndex = GetAttributeIndex (mat.head.index);
        GS::UniString name = mat.head.uniStringNamePtr != nullptr ? *mat.head.uniStringNamePtr : GS::UniString (mat.head.name);
        GS::ObjectState m ("id", id, "modelMaterialIndex", id, "attributeIndex", attrIndex, "name", name,
            "source", attrIndex == 0 ? "gdl" : "attribute", "color", GS::ObjectState ("r", mat.surfaceRGB.f_red, "g", mat.surfaceRGB.f_green, "b", mat.surfaceRGB.f_blue),
            "transparencyPercent", mat.transpPc, "nativeMaterialType", static_cast<Int32> (mat.mtype));
        if (attrIndex != 0) m.Add ("attribute", Attribute (API_MaterialID, mat.head.index, "API_UmatType.mater.head.index"));
        GS::ObjectState texture ("name", GS::UniString (mat.texture.texName), "missing", mat.texture.missingPict,
            "xSize", mat.texture.xSize, "ySize", mat.texture.ySize, "rotation", mat.texture.rotAng);
        if (mat.texture.fileLoc != nullptr) texture.Add ("reference", mat.texture.fileLoc->ToDisplayText ());
        m.Add ("texture", texture); materials (m);
        delete c.umat.mater.texture.fileLoc;
        delete c.umat.mater.head.uniStringNamePtr;
    }
    out.Add ("nativeSeconds", std::chrono::duration<double> (std::chrono::steady_clock::now () - start).count ());
    return out;
}
