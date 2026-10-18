# APA AC29 DXF source geometry C1

Three new independent operations, using ezdxf 1.4.5 recursive_decompose and
make_path on the existing APA DynamicCommands router:

- DXFWorldPaths: decomposes nested INSERT/DIMENSION geometry, applies upstream
  transforms, records WCS path commands and parent handle/type/layer provenance.
- DXFClosedContours: closed path candidates with coordinates and explicit
  uncertainty for later use by the existing planner. No native element creation.
- DXFRepeatedAssemblies: finds translation-equivalent converted path collections
  across INSERTs, including different block names. Rotation and scale remain
  significant. A repeated signature is a candidate, not semantic family evidence.

Namespace AddOn.APADXFGeometryC1. Parameters: a (DXF), output (new JSON).
Register with `apa_dxf_geometry_c1.register(existing_router)`. Source SHA is
checked before/after the subprocess; the JSON disk receipt and adapter SHA are
read back. Existing V1 interpreter and V2 file/hash guards are reused.

## Contracts and limitations

Exact installed ezdxf 1.4.5 source and MIT license inspected. Official API:
https://ezdxf.readthedocs.io/en/stable/disassemble.html
https://ezdxf.readthedocs.io/en/stable/path.html

Source coordinates retain drawing units ($INSUNITS code); scale/semantics are
uncalibrated. Coordinates round to nine decimal places. Curve paths may be
Bezier approximations; `pointRoles` records the upstream command tuple field
order (end, ctrl/ctrl1/ctrl2). No curve flattening or area/dimension inference.
Unsupported generated types are counted. Upstream decomposition does not apply
XCLIP and may omit unsupported source geometry; source assembly completeness
is explicitly unverified. Holes, planarity, intersections, winding and BIM
meaning are not established by closed paths. Arrays are bounded to 5000, total
counts and truncation are exposed; decomposition stops at 50000 entities.

This extends V1 DXFVectors (simple modelspace primitives) and V2 block insertion
facts with transformed paths and geometric candidates; it does not duplicate
block/attribute, text, dimension or layer inventory commands already present.

## Verification

Eight real-vendor tests on Windows: rotated/scaled INSERT WCS coordinates,
closed contours, geometric alias block grouping, unsupported text reporting,
curve approximation declaration, decomposition bound, output/parameter guards,
and preservation of all 24 existing contracts (27 after registration).
CI runs these eight plus 25 B1/B2 and 21 V2 tests on Windows Python 3.11/3.12.

SOURCE VERIFIED / OFFLINE PASS / BUILD Python. INSTALLED/LIVE/ACCEPTED need their
own receipts. No source DXF, original PLN/APX, installed core or main edits.
PDF lossless extraction from PR #154 is reused; this package adds DXF operations.
