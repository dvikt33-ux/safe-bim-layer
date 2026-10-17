"""APA Semantic V1: three isolated, source-only vendor analyses. NO PLN writes.

Operational commands:
  pdf-paths: PyMuPDF native paths/layers/clips/groups + graphic clusters.
  pdf-raster: render one PDF page to a new PNG with known pixel-point scale.
  openbim: official OpenBIM FloorPlan AI inference_api.FloorplanSegmenter.
  raster2seq: floorplan-back's official parse_floorplan.py CLI.

ML vendors must be installed separately by the operator; never download weights
or install dependencies on demand. Results have PIXEL units, never BIM metres.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

SCHEMA = "APA_SEMANTIC_SOURCE_EVIDENCE_V1"
OPERATIONS = {"pdf-paths", "pdf-raster", "openbim", "raster2seq"}
KINDS = {"pdf-paths": {".pdf"}, "pdf-raster": {".pdf"},
         "openbim": {".png", ".jpg", ".jpeg"},
         "raster2seq": {".png", ".jpg", ".jpeg"}}


def require(test, reason):
    if not test:
        raise ValueError(reason)


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def finite(v):
    require(math.isfinite(v), "NONFINITE_VENDOR_GEOMETRY")
    return v


def plain(value):
    """Losslessly normalize PyMuPDF geometry without stringify/repr fallbacks."""
    if value is None or isinstance(value, (bool, str, int)):
        return value
    if isinstance(value, float):
        return finite(value)
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    if isinstance(value, dict):
        return {str(k): plain(v) for k, v in value.items()}
    if hasattr(value, "ul") and hasattr(value, "ur") and hasattr(value, "ll") and hasattr(value, "lr"):
        return {"quad": [plain(value.ul), plain(value.ur),
                         plain(value.ll), plain(value.lr)]}
    if all(hasattr(value, p) for p in ("x0", "y0", "x1", "y1")):
        return [finite(float(value.x0)), finite(float(value.y0)),
                finite(float(value.x1)), finite(float(value.y1))]
    if all(hasattr(value, p) for p in ("x", "y")):
        return [finite(float(value.x)), finite(float(value.y))]
    raise TypeError("UNSUPPORTED_PYMUPDF_GEOMETRY:" + type(value).__name__)


def pdf_paths(source, page_no):
    import pymupdf
    require(page_no >= 1, "PDF_PAGE_MUST_BE_ONE_BASED")
    with pymupdf.open(str(source)) as doc:
        require(page_no <= len(doc), "PDF_PAGE_NOT_FOUND")
        page = doc[page_no - 1]
        original = page.get_cdrawings(extended=True)
        drawings = page.get_drawings()
        # PyMuPDF's stock grouping: bounding rectangles, not BIM entities.
        clusters = page.cluster_drawings(drawings=drawings)
        serialized = [plain(x) for x in original]
        return {
            "page": page_no,
            "pageCount": len(doc),
            "sizePt": [page.rect.width, page.rect.height],
            "coordinateSystem": "PDF_POINTS_TOP_LEFT_NOT_BIM_METRES",
            "pathCount": len(serialized),
            "paths": serialized,
            "clusterCount": len(clusters),
            "clusterBoundsPt": [plain(r) for r in clusters],
            "layers": sorted({str(p["layer"]) for p in original
                              if p.get("layer") is not None}),
            "ocgNames": sorted(str(x.get("name", "")) for x in
                               (doc.get_ocgs() or {}).values()),
            "extraction": "PyMuPDF.Page.get_cdrawings(extended=True)",
            "clustering": "PyMuPDF.Page.cluster_drawings",
            "clustersAreBIMElements": False,
            "scaleConfirmed": False,
            "truncated": False,
        }



def pdf_raster(source, page_no, output):
    import pymupdf
    require(page_no >= 1, "PDF_PAGE_MUST_BE_ONE_BASED")
    png = output.with_suffix(".png")
    require(not png.exists() and png != source
            and png.parent == output.parent,
            "PDF_RASTER_DESTINATION_ALREADY_EXISTS")
    with pymupdf.open(str(source)) as doc:
        require(page_no <= len(doc), "PDF_PAGE_NOT_FOUND")
        page = doc[page_no - 1]
        scale = 2.0  # 144 DPI for nominal 72-pt PDF space.
        width = int(math.ceil(page.rect.width * scale))
        height = int(math.ceil(page.rect.height * scale))
        require(width > 0 and height > 0
                and width * height <= 30_000_000,
                "PDF_RASTER_TOO_LARGE_SELECT_A_SMALLER_SOURCE")
        pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale),
                              colorspace=pymupdf.csRGB, alpha=False)
        # New file only; no source modification.
        with png.open("xb") as fd:
            fd.write(pix.tobytes("png"))
        return {"page": page_no, "pageCount": len(doc),
                "imageFile": str(png), "imageSHA256": digest(png),
                "imageSizePx": [pix.width, pix.height],
                "pointsToPixels": scale,
                "sourceCoordinates": "PDF_POINTS_TOP_LEFT",
                "rasterCoordinates": "IMAGE_PIXELS_TOP_LEFT",
                "modelRealWorldScale": "NOT_VERIFIED"}


def read_verified_ml_model(config_file, vendor):
    require(config_file is not None, "ML_VENDOR_CONFIG_NOT_INSTALLED")
    path = Path(config_file).resolve(strict=True)
    conf = json.loads(path.read_text(encoding="utf-8"))
    require(conf.get("schema") == "APA_SEMANTIC_ML_VENDOR_CONFIG_V1",
            "ML_VENDOR_CONFIG_INVALID")
    item = conf.get(vendor)
    require(isinstance(item, dict), "ML_VENDOR_NOT_CONFIGURED:" + vendor)
    exe = Path(item["python"]).resolve(strict=True)
    root = Path(item["root"]).resolve(strict=True)
    model = Path(item["model"]).resolve(strict=True)
    require(exe.is_file() and root.is_dir() and model.is_file(),
            "ML_VENDOR_PATH_INVALID")
    require(digest(model) == item.get("modelSHA256"),
            "ML_MODEL_HASH_MISMATCH")
    require(len(str(exe)) < 1024 and len(str(root)) < 1024,
            "ML_VENDOR_PATH_TOO_LONG")
    return exe, root, model


def openbim_infer(source, config, output):
    exe, root, model = read_verified_ml_model(config, "openbim")
    require(model.suffix.lower() == ".pt"
            and (root / "inference_api.py").is_file(),
            "OPENBIM_EXPECTS_OFFICIAL_INFERENCE_API_AND_PT")
    with tempfile.TemporaryDirectory(prefix="apa-openbim-") as td:
        vendor_json = Path(td) / "prediction.json"
        cmd = [str(exe), str(Path(__file__).resolve()), "_vendor_openbim",
               "--a", str(source), "--output", str(vendor_json),
               "--vendor-root", str(root), "--model", str(model)]
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=1200,
                           cwd=str(root))
        require(p.returncode == 0 and vendor_json.is_file(),
                "OPENBIM_VENDOR_INFERENCE_FAILED:" + p.stderr[-700:])
        output_data = json.loads(vendor_json.read_text(encoding="utf-8"))
    require(set(output_data) >= {"imageSizePx", "classPixelCounts"},
            "OPENBIM_RESULT_SCHEMA_MISMATCH")
    return {**output_data, "vendor": "Chunling1/OpenBIM-FloorPlan-AI",
            "engineeringAcceptance": "NOT_VERIFIED",
            "scaleConfirmed": False}


def _vendor_openbim(source, vendor_root, model, output):
    """Runs only inside the explicitly configured trusted vendor interpreter.

    The upstream model uses torch.load(weights_only=False): ONLY owner-approved
    checkpoints. The caller verifies SHA256 but SHA alone does not grant trust.
    """
    sys.path.insert(0, str(vendor_root))
    from inference_api import FloorplanSegmenter
    import numpy as np
    import cv2
    system = FloorplanSegmenter(model_path=str(model), device="cpu")
    pred = system.predict(str(source), use_preprocessing=True)
    mask = pred["mask"]
    require(mask.ndim == 2, "OPENBIM_PREDICTION_MASK_NOT_2D")
    classes = ("background", "wall", "window", "door")
    counts = {name: int(np.count_nonzero(mask == i))
              for i, name in enumerate(classes)}
    require(sum(counts.values()) == int(mask.size),
            "OPENBIM_CLASS_PIXEL_COUNT_MISMATCH")
    regions = {}
    for class_id, name in [(1, "wall"), (2, "window"), (3, "door")]:
        binary = (mask == class_id).astype("uint8")
        n, labels, stats, centers = cv2.connectedComponentsWithStats(binary)
        regions[name] = [
            {"bboxPx": [int(stats[i, cv2.CC_STAT_LEFT]),
                        int(stats[i, cv2.CC_STAT_TOP]),
                        int(stats[i, cv2.CC_STAT_WIDTH]),
                        int(stats[i, cv2.CC_STAT_HEIGHT])],
             "areaPx": int(stats[i, cv2.CC_STAT_AREA])}
            for i in range(1, n)
        ]
    data = {"imageSizePx": [int(mask.shape[1]), int(mask.shape[0])],
            "classPixelCounts": counts, "regions": regions,
            "sourceCoordinates": "IMAGE_TOP_LEFT_PIXELS",
            "requiresHumanReview": True}
    with output.open("x", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, allow_nan=False)


def raster2seq_infer(source, config):
    exe, root, model = read_verified_ml_model(config, "raster2seq")
    script = root / "scripts" / "parse_floorplan.py"
    require(script.is_file() and model.name == "checkpoint.pth"
            and model.parent.name == "cubicasa5k",
            "RASTER2SEQ_OFFICIAL_CKPT_LAYOUT_REQUIRED")
    with tempfile.TemporaryDirectory(prefix="apa-raster2seq-") as td:
        dest = Path(td) / "parsed.json"
        environment = dict(os.environ)
        environment.update({
            "HF_HUB_OFFLINE": "1",
            "HF_HUB_DISABLE_TELEMETRY": "1",
            "FLOORPLAN_MODEL_CACHE_DIR": str(model.parents[2]),
            "FLOORPLAN_MODEL_DEVICE": "cpu",
            "FLOORPLAN_DEBUG": "false",
        })
        # Only the vendor's public CLI is called: no copied inference algorithm.
        p = subprocess.run([str(exe), str(script), str(source), str(dest)],
                           cwd=str(root), env=environment,
                           text=True, capture_output=True, timeout=1800)
        require(p.returncode == 0 and dest.is_file(),
                "RASTER2SEQ_VENDOR_INFERENCE_FAILED:" + p.stderr[-700:])
        data = json.loads(dest.read_text(encoding="utf-8"))
    require(isinstance(data.get("walls"), list)
            and isinstance(data.get("rooms"), list)
            and isinstance(data.get("openings"), list)
            and isinstance(data.get("vertices"), list),
            "RASTER2SEQ_FLOORPLAN_SCHEMA_INVALID")
    wall_ids = {w["id"] for w in data["walls"]}
    vertex_ids = {v["id"] for v in data["vertices"]}
    require(all(w["start_vertex_id"] in vertex_ids
                and w["end_vertex_id"] in vertex_ids
                for w in data["walls"])
            and all(o["wall_id"] in wall_ids
                    for o in data["openings"]),
            "RASTER2SEQ_WALL_GRAPH_INCONSISTENT")
    return {"vendor": "Takheer/floorplan-back + Cornell Raster2Seq",
            "floorplan": data,
            "counts": {k: len(data[k])
                       for k in ("rooms", "walls", "vertices", "openings")},
            "sourceCoordinates": "IMAGE_TOP_LEFT_PIXELS",
            "scaleConfirmed": False,
            "engineeringAcceptance": "NOT_VERIFIED"}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("action", choices=[*sorted(OPERATIONS), "_vendor_openbim"])
    p.add_argument("--a", required=True)
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--output", required=True)
    p.add_argument("--ml-config")
    p.add_argument("--vendor-root")
    p.add_argument("--model")
    args = p.parse_args(argv)
    src = Path(args.a).resolve(strict=True)
    dest = Path(args.output).resolve()
    require(src.is_file() and dest.suffix.lower() == ".json"
            and dest.parent.is_dir() and not dest.exists()
            and dest != src, "SEMANTIC_INPUT_OR_NEW_OUTPUT_INVALID")
    if args.action == "_vendor_openbim":
        require(src.suffix.lower() in {".png", ".jpg", ".jpeg"},
                "VENDOR_IMAGE_SUFFIX_INVALID")
        _vendor_openbim(src, Path(args.vendor_root), Path(args.model), dest)
        return
    require(src.suffix.lower() in KINDS[args.action],
            "SEMANTIC_INPUT_SUFFIX_INVALID")
    require(src.stat().st_size <= 1024**3, "SEMANTIC_SOURCE_OVER_1GB")
    if args.action == "pdf-paths":
        result = pdf_paths(src, args.page)
    elif args.action == "pdf-raster":
        result = pdf_raster(src, args.page, dest)
    elif args.action == "openbim":
        result = openbim_infer(src, args.ml_config, dest)
    else:
        result = raster2seq_infer(src, args.ml_config)
    envelope = {
        "schema": SCHEMA,
        "status": "SOURCE_ONLY_NOT_BIM_ACCEPTANCE",
        "action": args.action,
        "sources": [{"name": src.name, "sha256": digest(src)}],
        "result": result,
        "nativeCalls": 0, "modelWrites": 0,
        "sourceNotModified": True,
    }
    with dest.open("x", encoding="utf-8") as fd:
        json.dump(envelope, fd, ensure_ascii=False, allow_nan=False)
        fd.write("\n")
    print("APA_SEMANTIC_REPORT_CREATED:" + str(dest))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("APA_SEMANTIC_BLOCKED:" + type(exc).__name__ + ":" + str(exc),
              file=sys.stderr)
        sys.exit(2)
