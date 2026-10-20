# APA №2 — SOURCE проверки 11–15

11. [ezdxf1.4.5 disassemble.py](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py#L542-L579): recursive_decompose игнорирует XCLIP. Вердикт RAW≠VISIBLE; next 2D clip.
12. [ezdxf1.4.5 xclip.py](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xclip.py): XClip(insert), enabled/inverted/get_wcs_clipping_path. Вердикт REUSE metadata; next WCS/Block fixture.
13. [ezdxf1.4.5 clipping](https://ezdxf.readthedocs.io/en/stable/math/clipping.html): Convex/Concave/InvertedClippingPolygon2d, clip_line/polyline/polygon; inverted требует outer_bounds. Вердикт ADAPTER_PARTIAL; next unsupported 3D.
14. [disassemble](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py)+[xclip](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xclip.py): единый source-handle-preserving nested XCLIP pipeline в проверенных API NOT_FOUND. Минимальный glue — provenance+type dispatch, не свой движок; next oracle.
15. [ezdxf1.4.5 disassemble.py](https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py#L570-L579): MINSERT через multi_insert уже готов. Вердикт REUSE; next row/col provenance.
