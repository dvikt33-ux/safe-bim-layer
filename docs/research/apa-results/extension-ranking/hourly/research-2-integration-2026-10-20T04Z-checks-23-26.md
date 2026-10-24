# APA №2 04Z — проверки 23–26

23. Tapir issue399: AC29 JPN build4006, addon1.4.0 CreateExt=-2130313110 даже с favorite. Не переносить на build5101; далее локальный negative fixture.
24. CreateOpenings создаёт hole, не GDL Window/Door. REJECT как семантическую замену.
25. ezdxf1.4.5 XClip.get_wcs_clipping_path: WCS XY, только 2D. ADAPTER; далее WCS/units.
26. ezdxf.math.clipping: ConcaveClippingPolygon2d и InvertedClippingPolygon2d; outer_bounds должен покрывать content. REUSE; далее inverted fixture.
