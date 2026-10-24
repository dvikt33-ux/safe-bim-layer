# APA №2 22Z — проверки 16–18
16. Почему C1 не даёт видимую DXF геометрию? ezdxf v1.4.5 disassemble.py L556–566: recursive_decompose игнорирует XCLIP. BLOCKED для видимости. Далее: граница.
17. Есть граница? ezdxf xclip.py L138–183: XClip.get_wcs_clipping_path() выдаёт двумерный контур с признаком инверсии. REUSE, не готовая геометрия. Далее: механизм.
18. Есть готовый механизм? ezdxf addons/drawing/frontend.py L882–912: XClip + find_best_clipping_shape/make_inverted_clipping_shape, push/pop. REUSE через штатный Frontend; далее: JSON.
Источник: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/addons/drawing/frontend.py
