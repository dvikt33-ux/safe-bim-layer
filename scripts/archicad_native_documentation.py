"""Native drawing evidence readers; all writes use the existing documentation writer.

GUID domains, projection coordinates, model XYZ and semantic acceptance remain
separate. No renderer, schedule engine or second BIM executor.
"""
import math
from pathlib import Path
import hashlib
import archicad_bim_documentation as D

def view_coverage(api,view_guid,selected_guids,expected_type):
    if expected_type not in ('SectionItem','ElevationItem','InteriorElevationItem'):
        raise ValueError('NATIVE_DOCUMENTATION_VIEW_TYPE_REQUIRED')
    trees=[api('GetNavigatorItemTree',{'navigatorMapId':m}) for m in ('ProjectMap','PublicViewMap')]
    items=[x for tree in trees for x in D.flatten(tree) if D.item_guid(x)==view_guid.lower()]
    if len(items)!=1 or items[0].get('type')!=expected_type:raise ValueError('NATIVE_DOCUMENTATION_VIEW_IDENTITY_MISMATCH')
    db=D.read_database(api,view_guid);reply=api('GetSectionElements',{'databases':[db]})
    if any(r.get('success') is not True for r in reply.get('executionResultForDatabases',[])):
        raise ValueError('NATIVE_DOCUMENTATION_DATABASE_READ_FAILED')
    selected={g.lower() for g in selected_guids};owners=reply.get('sectionElements',[])
    matched=[x for x in owners if x['ownerElementId']['guid'].lower() in selected]
    return {'status':'NATIVE_VIEW_GEOMETRY_PRESENT' if matched else 'NATIVE_VIEW_EMPTY_OR_OUTSIDE_SCOPE',
        'viewGuid':view_guid.lower(),'nativeType':expected_type,'database':db,
        'ownerCount':len(owners),'selectedOwnerCount':len(matched),'selectedOwners':matched,
        'coverageMeaning':'Visible native owners only; occluded elements need not appear on one exterior view',
        'allVerticalPrimitives':'NOT_VERIFIED','normativeAcceptance':False}

def dimension_graphics(api,guid,owner_lookup,model_version):
    rows=api('GetDimensionData',{'elements':[{'elementId':{'guid':guid}}]}).get('dimensionsData',[])
    if len(rows)!=1 or 'error' in rows[0]:raise ValueError('NATIVE_DIMENSION_READ_FAILED')
    row=rows[0];points=row.get('witnessPoints',[])
    if len(points)<2:raise ValueError('NATIVE_DIMENSION_WITNESS_POINTS_MISSING')
    normalized=[]
    for point in points:
        xy=point.get('coordinate',{});base=point.get('baseElementId',{}).get('guid','').lower()
        if set(xy)!={'x','y'} or any(type(v) not in (int,float) or not math.isfinite(v) for v in xy.values()):
            raise ValueError('NATIVE_DIMENSION_COORDINATE_INVALID')
        if base not in owner_lookup:raise ValueError('NATIVE_DIMENSION_SOURCE_OWNER_NOT_VERIFIED')
        normalized.append({'drawingXYMeters':xy,'dimensionPosition':point['dimensionPosition'],
            'nativeReportedValue':point['dimensionValue'],'sectionElementGuid':base,
            'modelOwnerGuid':owner_lookup[base].lower()})
    return {'status':'NATIVE_ASSOCIATIVE_DIMENSION_COORDINATES_PASS','guid':guid.lower(),
        'modelVersion':model_version,'coordinateSystem':'Active native section/elevation drawing2D, not project XYZ',
        'points':normalized,'coordinate3DField':'Drawing memo loc3D is not proof of project-world coordinates',
        'allVerticalPrimitives':'NOT_VERIFIED','normativeAcceptance':False}

def drawing_link(api,guid,expected_source_guid):
    rows=api('GetDetailsOfElements',{'elements':[{'elementId':{'guid':guid}}],'fields':['type','details']}).get('detailsOfElements',[])
    if len(rows)!=1 or rows[0].get('type')!='Drawing':raise ValueError('NATIVE_DRAWING_NOT_CONFIRMED')
    details=rows[0]['details']
    actual=details.get('navigatorItemId',{}).get('guid','').lower()
    matched=actual==expected_source_guid.lower()
    return {'status':'NATIVE_LINKED_DRAWING_PASS' if matched else 'NATIVE_DRAWING_LINK_METADATA_NOT_VERIFIED','elementGuid':guid.lower(),'requestedSourceViewGuid':expected_source_guid.lower(),'nativeReportedLinkGuid':actual,
        'sourceIdentity':'MATCH' if matched else 'DIFFERENT_GUID_REQUIRES_INDEPENDENT_BEHAVIOR_PROOF',
        'boundsPaperMeters':details.get('bounds'),'scaleRatio':details.get('drawingScale'),
        'nativeElementAndNavigatorGuidDomains':'DISTINCT_DO_NOT_REQUIRE_EQUALITY'}

def schedule_inventory(api):
    rows=[x for x in D.flatten(api('GetNavigatorItemTree',{'navigatorMapId':'ProjectMap'})) if x.get('type')=='ScheduleItem']
    return {'status':'NATIVE_SCHEDULE_DEFINITIONS_DISCOVERED','definitions':[
        {'navigatorGuid':D.item_guid(x),'source':x.get('sourceNavigatorItemId'),'name':x.get('name'),
         'nameEncoding':'NOT_VERIFIED' if '\ufffd' in x.get('name','') else 'AVAILABLE'} for x in rows],
        'nativeRows':'NOT_VERIFIED_NO_INSTALLED_ROW_CONTRACT','configureScheme':'UNSUPPORTED_INSTALLED_CONTRACT',
        'csvSpecifications':'Existing adapter remains the shared fact output; no duplicate schedule engine'}

def drawing_graphics(api,guid,requested_source_guid,model_version):
    """Read native vector fill contours as drawn on the Layout, not BIM boxes.

    The provider calls the field floorPlanPolygons even for Drawing elements.
    These are actual regenerated2D contours of the native Drawing. Line/text
    primitives and per-contour model owner identities are not exposed.
    """
    rows=api('GetDetailsOfElements',{'elements':[{'elementId':{'guid':guid}}],
        'fields':['type','details','floorPlanPolygons']}).get('detailsOfElements',[])
    if len(rows)!=1 or rows[0].get('type')!='Drawing':raise ValueError('NATIVE_DRAWING_GRAPHICS_UNAVAILABLE')
    row=rows[0];details=row['details'];polygons=row.get('floorPlanPolygons',[])
    if not polygons:
        return {'status': 'NATIVE_DRAWING_VECTOR_COORDINATES_NOT_VERIFIED',
            'elementGuid': guid.lower(), 'requestedSourceViewGuid': requested_source_guid.lower(),
            'modelVersion': model_version, 'contourCount': 0,
            'reason': 'Installed provider exposes no fill contours for this Drawing; use independent native PDF readback.',
            'allVerticalPrimitives': 'NOT_VERIFIED'}
    for polygon in polygons:
        points=polygon.get('coordinates',[])
        if len(points)<3 or any(set(p)!={'x','y'} or any(type(v) not in (int,float) or not math.isfinite(v) for v in p.values()) for p in points):
            raise ValueError('NATIVE_DRAWING_VECTOR_COORDINATES_INVALID')
    scale=details['ratio']*details['drawingScale'];offset=details['modelOffset'];angle=details['angle'];pos=details['pos']
    view_polygons=[]
    if scale>0 and offset=={'x':0,'y':0}:
        ca,sa=math.cos(angle),math.sin(angle)
        for polygon in polygons:
            coords=[]
            for p in polygon['coordinates']:
                dx,dy=p['x']-pos['x'],p['y']-pos['y']
                coords.append({'u':(ca*dx+sa*dy)/scale,'v':(-sa*dx+ca*dy)/scale})
            view_polygons.append({'coordinates':coords})
    return {'status':'NATIVE_DRAWING_VECTOR_COORDINATES_PASS','elementGuid':guid.lower(),
        'requestedSourceViewGuid':requested_source_guid.lower(),'nativeReportedLinkGuid':details['navigatorItemId']['guid'],
        'modelVersion':model_version,'coordinateSystem':'Native Layout paperXY meters',
        'polygonsPaper':polygons,'contourCount':len(polygons),'nativeDrawingTransform':{'position':pos,'angle':angle,'scale':scale,'modelOffset':offset},
        'derivedViewPolygons':view_polygons,'derivedViewMeaning':'Inverse native Drawing transform; drawing axesUV, not project XYZ. Check against native dimension witnesses.',
        'derivedViewCoordinates': 'CANDIDATE_REQUIRES_NATIVE_WITNESS_CHECK',
        'ownerPerContour':'NOT_EXPOSED','lineAndTextPrimitives':'NOT_EXPOSED','allVerticalPrimitives':'NOT_VERIFIED'}


def projection_span_check(expected_span, actual_coordinates, tolerance=1e-5):
    """Compare actual native drawing extent on an independently verified axis.

    The source scope and projection axis must be established by the caller.
    Owner counts or model boxes alone are never drawing proof. This detects
    cropping without accepting hidden features or engineering suitability.
    """
    values = list(expected_span) + list(actual_coordinates) + [tolerance]
    if (len(expected_span) != 2 or expected_span[0] >= expected_span[1] or
            not actual_coordinates or tolerance < 0 or
            any(type(v) not in (int, float) or not math.isfinite(v) for v in values)):
        raise ValueError('NATIVE_PROJECTION_SPAN_INPUT_INVALID')
    actual = [min(actual_coordinates), max(actual_coordinates)]
    complete = all(abs(a - b) <= tolerance for a, b in zip(expected_span, actual))
    return {'status': 'NATIVE_PROJECTION_HORIZONTAL_SPAN_PASS' if complete else
            'NATIVE_PROJECTION_HORIZONTAL_SPAN_NOT_VERIFIED',
        'expectedSpanMeters': list(expected_span), 'actualSpanMeters': actual,
        'toleranceMeters': tolerance, 'completeDrawingAcceptance': 'NOT_IMPLIED',
        'requiresIndependentProjectionAxisAndSourceScope': True}

def publication_files(folder):
    root = Path(folder).resolve()
    if not root.is_dir():
        raise ValueError('NATIVE_EXPORT_NO_FILE')
    files = []
    for file in root.rglob('*'):
        if file.resolve() != file:
            raise ValueError('NATIVE_EXPORT_PATH_ESCAPE')
        if not file.is_file():continue
        raw=file.read_bytes()
        if not raw:raise ValueError('NATIVE_EXPORT_EMPTY_FILE')
        files.append({'name':file.relative_to(root).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),
            'pdfSignature':raw.startswith(b'%PDF-')})
    if not files:raise ValueError('NATIVE_EXPORT_NO_FILE')
    return {'status':'NATIVE_FILE_BYTES_READBACK_PASS','files':sorted(files, key=lambda row: row['name']),
        'selectedPublisherSubset':'NOT_VERIFIED_UNTIL_FILE_PAGES_ARE_CHECKED','readyDrawingAcceptance':'REQUIRES_RENDER_AND_SOURCE_SCOPE_CHECK'}


def read_two_storey_sheet(folder, layout_name, story_labels):
    """Read a one-sheet A2 export with two named vector plan panels."""
    import unicodedata

    import pymupdf

    def canonical(text):
        return " ".join(unicodedata.normalize("NFKC", text).casefold().split())

    labels = [canonical(label) for label in story_labels]
    title = canonical(layout_name)
    if len(labels) != 2 or not all(labels) or len(set(labels)) != 2 or len(title) < 3:
        raise ValueError("PUBLISHER_TWO_DISTINCT_STORY_LABELS_AND_LAYOUT_NAME_REQUIRED")
    files = publication_files(folder)["files"]
    if len(files) != 1 or not files[0]["pdfSignature"] or Path(files[0]["name"]).suffix.casefold() != ".pdf":
        raise ValueError("PUBLISHER_ONE_EXPORTED_PDF_REQUIRED")
    file = files[0]
    basename = canonical(Path(file["name"]).stem)
    if basename != title and not basename.endswith(" " + title):
        raise ValueError("PUBLISHER_EXPORTED_LAYOUT_NAME_MISMATCH")
    payload = (Path(folder).resolve() / file["name"]).read_bytes()
    if hashlib.sha256(payload).hexdigest() != file["sha256"]:
        raise ValueError("PUBLISHER_PDF_CHANGED_DURING_READBACK")
    with pymupdf.open(stream=payload, filetype="pdf") as doc:
        if not doc.is_pdf or doc.is_repaired or doc.needs_pass or doc.page_count != 1:
            raise ValueError("PUBLISHER_EXACTLY_ONE_READABLE_PAGE_REQUIRED")
        page = doc[0]
        paper = [round(points * 25.4 / 72, 2) for points in (page.rect.width, page.rect.height)]
        if any(abs(measured - expected) > 1 for measured, expected in zip(paper, [594, 420])):
            raise ValueError("PUBLISHER_EXPECTED_LANDSCAPE_A2")
        transform = page.rotation_matrix
        lines = [(canonical("".join(span["text"] for span in line["spans"])),
                  pymupdf.Rect(line["bbox"]) * transform)
                 for block in page.get_text("dict", flags=pymupdf.TEXTFLAGS_DICT & ~pymupdf.TEXT_PRESERVE_IMAGES)["blocks"]
                 for line in block.get("lines", [])]
        vector = [item["rect"] * transform for item in page.get_drawings()
                  if len(item["items"]) > 1 or any(segment[0] in {"re", "qu"} for segment in item["items"])]
        midpoint = page.rect.x0 + page.rect.width / 2
        panels = []
        for index, label in enumerate(labels):
            left, right = (page.rect.x0, midpoint) if index == 0 else (midpoint, page.rect.x1)
            region = pymupdf.Rect(left, page.rect.y0, right, page.rect.y1)
            marks = [bounds for text, bounds in lines if text == label]
            if len(marks) != 1 or not region.contains(marks[0]):
                raise ValueError("PUBLISHER_STORY_TITLE_MISSING_OR_OUTSIDE_PANEL: " + story_labels[index])
            paths = {tuple(bounds) for bounds in vector if region.contains(bounds)
                     and bounds.width >= 8 and bounds.height >= 8}
            if len(paths) < 2:
                raise ValueError("PUBLISHER_STORY_PANEL_VECTOR_CONTENT_REQUIRED: " + story_labels[index])
            panels.append(dict(label=story_labels[index], vectorPathCount=len(paths)))
    return dict(status="PUBLISHER_PDF_CONTENT_CHECKED", sourceFile=file, paperMM=paper, pageCount=1,
                layoutName=layout_name, panels=panels,
                drawingSourceVerification="REQUIRES_NATIVE_LAYOUT_AND_PUBLISHER_READBACK"), payload
