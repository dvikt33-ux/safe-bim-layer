"""APA PDF layered-floorplan benchmark inputs, source-only, NO Archicad writes.

Layer statistics count native PDF paths, NEVER BIM elements. The raster input
remains full-color and includes all layers; we do not claim layer-masked PNG.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys


def sha256(source):
    h=hashlib.sha256()
    with source.open("rb") as f:
        for data in iter(lambda:f.read(1<<20), b""):
            h.update(data)
    return h.hexdigest()


def classify_layer(name):
    name=name.casefold()
    if re.search(r"стен|перегород",name):return "wall_or_partition_graphics"
    if re.search(r"мебел|интерьер",name):return "furniture_graphics"
    if "зона" in name:return "zone_graphics"
    if re.search(r"размер|оси",name):return "dimension_or_axis_graphics"
    return "other_graphics"


def extract(source, page, roi, out_dir, dpi=144):
    import pymupdf
    if page<1 or not (72<=dpi<=400):
        raise ValueError("PAGE_OR_DPI_INVALID")
    if len(roi)!=4 or not(roi[0]<roi[2] and roi[1]<roi[3]):
        raise ValueError("CLIP_INVALID")
    source=Path(source).resolve(strict=True)
    out_dir=Path(out_dir)
    if source.suffix.casefold()!=".pdf" or not source.is_file():
        raise ValueError("SOURCE_PDF_REQUIRED")
    if out_dir.exists():
        raise ValueError("RESULT_FOLDER_ALREADY_EXISTS")
    before=sha256(source)
    with pymupdf.open(source) as doc:
        if page>len(doc):raise ValueError("PAGE_NOT_FOUND")
        pg=doc[page-1]
        rect=pymupdf.Rect(*roi)
        if not pg.rect.contains(rect):
            raise ValueError("CLIP_OUTSIDE_PDF_PAGE")
        paths=pg.get_cdrawings(extended=True)
        counts=Counter(
            str(p.get("layer")) if p.get("layer") else "UNLAYERED"
            for p in paths if p.get("type") in ("s","f","fs")
        )
        ocg=sorted({v.get("name","") for v in doc.get_ocgs().values()})
        structural=[
            {"name":k,"pathCount":v} for k,v in counts.items()
            if classify_layer(k)=="wall_or_partition_graphics"
        ]
        pix=pg.get_pixmap(matrix=pymupdf.Matrix(dpi/72,dpi/72),clip=rect,alpha=False)
        if pix.width*pix.height>30_000_000:
            raise ValueError("RENDER_TOO_LARGE")
        result={
            "schema":"APA_PDF_LAYERED_FLOORPLAN_EVIDENCE_V1",
            "status":"SOURCE_ONLY_NOT_BIM_ACCEPTANCE",
            "sourceName":source.name,"sourceSHA256":before,
            "pdfPage":page,"pdfPageCount":len(doc),
            "pdfPointsClip":[float(x) for x in roi],
            "rasterDpi":dpi,"rasterPixelSize":[pix.width,pix.height],
            "pdfPointsToPixels":dpi/72,"ocgLayerNames":ocg,
            "layerPathCounts":dict(sorted(counts.items())),
            "structuralLayerCounts":sorted(structural,key=lambda x:x["name"]),
            "ocgPresent":bool(ocg),
            "pixelCoordinatesAreNotBuildingMetres":True,
            "pathCountsAreNotBIMElementCounts":True,
            "rasterLayerFilterApplied":False,
            "rasterIncludesDimensionsAndFurnitureWherePresent":True,
            "nativeCalls":0,"modelWrites":0,"sourceModified":False,
        }
    if sha256(source)!=before:
        raise ValueError("SOURCE_MUTATED_DURING_READ")
    out_dir.mkdir(parents=True,exist_ok=False)
    png=out_dir/"floorplan.png"
    evidence=out_dir/"evidence.json"
    with png.open("xb") as f:
        f.write(pix.tobytes("png"))
    result["rasterSHA256"]=sha256(png)
    with evidence.open("x",encoding="utf-8") as f:
        json.dump(result,f,ensure_ascii=True,indent=2)
        f.write("\n")
    result["outputImage"]=str(png)
    result["outputEvidence"]=str(evidence)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf",type=Path,required=True)
    p.add_argument("--page",type=int,required=True)
    p.add_argument("--clip",type=float,nargs=4,required=True,metavar=("X0","Y0","X1","Y1"))
    p.add_argument("--out",type=Path,required=True)
    p.add_argument("--dpi",type=int,default=144)
    a=p.parse_args()
    v=extract(a.pdf,a.page,tuple(a.clip),a.out,a.dpi)
    print(json.dumps(v,ensure_ascii=True,indent=2))


if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("APA_PLAN_PREPARE_BLOCKED:"+type(exc).__name__+":"+str(exc),file=sys.stderr)
        sys.exit(2)
