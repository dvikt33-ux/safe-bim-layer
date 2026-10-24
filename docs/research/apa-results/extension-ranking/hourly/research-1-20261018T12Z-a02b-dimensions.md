# APA 12Z checks 11–14 — KR-12 block 1.8

11. 19 printed segment values sum 9230 mm, overall dimension 9280 mm; residual 50 mm. Counteraudit: do not treat residual as a measured wall thickness.

12. PyMuPDF: overall y662.498 x347.382 to873.494, length 526.112 pt = 9280.031 mm at M1:50. Counteraudit: PDF geometry, not BIM/world origin.

13. Segmented y639.821 x348.799 to872.077; left and right offsets 24.994 mm each. 25+9230+25=9280. Counteraudit: wall centerline not established.

14. pdfplumber 0.11.9 independently reproduced PyMuPDF 1.26.7 total/segment line coordinates (rounded 0.001 pt). Counteraudit: two parsers share one source PDF, not independent field measurements.
