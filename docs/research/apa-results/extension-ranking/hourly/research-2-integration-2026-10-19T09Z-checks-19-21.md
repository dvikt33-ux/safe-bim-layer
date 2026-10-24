# APA №2 09Z checks 19-21
SOURCE ONLY. Primary: https://github.com/mozman/ezdxf ; https://github.com/jsvine/pdfplumber ; https://github.com/IfcOpenShell/IfcOpenShell .
19 Hyperlinks? page.py L338 filters annots where uri non-null. A PDF URI is not BIM GUID. ADAPTER ANNOTATION_NOT_HOST; next link/nonlink fixture.
20 PDF coordinate? page.py L349 point2coord includes mediabox offsets and Y inversion. ADAPTER explicit page frame; next rotated mediabox.
21 PDF crop? page.py L545 CroppedPage; within_bbox retains only fully contained objects. REUSE derived-only, not raw geometry; next boundary fixture.
