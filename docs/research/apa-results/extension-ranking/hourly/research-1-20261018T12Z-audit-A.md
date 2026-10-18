# APA 12Z — independent audit A: PDF provenance + geometry

AP-2026 SHA256 2cf28450e868a5c742511fe40e6d0f061c9210744cb4f43875e0d7839725c55b, 20p, cadastre 28:05:010814:34, Amur region. KR-2022 SHA256 75b3064dec93245a986e5060540651acfa5d6a87fd1a137d5b46eb591a7462e1, 24p, cadastre 50:08:0060222:468, Moscow region. Different projects; never combine coordinates without matching title/project identity.

PyMuPDF and pdfplumber independently read KR-12 PDF page14. Formula mm=pt*25.4/72*50. Block1.7: 34 labels=14355mm; overall815.242pt=14379.963mm; left gap24.994mm. Block1.8: 19 labels=9230mm; overall526.112pt=9280.031mm; left/right gaps24.994mm. Independent pdfplumber coordinates agree at displayed 0.001pt. This confirms PDF dimension endpoints, not actual wall axes or an Archicad opening error.

Anchor points block1.7: x203.744pt=0m, x205.161pt=0.025m, x1018.986pt=14.380m. Block1.8: x347.382pt=0m, x348.799pt=0.025m, x872.077pt=9.255m, x873.494pt=9.280m. Local axes only.
