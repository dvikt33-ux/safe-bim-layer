# APA №2 01Z — проверки 22–24: MINSERT/XCLIP
ezdxf v1.4.5 MIT; APA C1 branch SOURCE.
S1 https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/disassemble.py
S2 https://github.com/dvikt33-ux/safe-bim-layer/blob/feature/apa-ac29-dxf-geometry-c1-20261018/scripts/apa_dxf_geometry_c1.py

22. Вопрос: 2×3 даёт 6 дочерних? S1:568–575 `entity.mcount>1 → recursive_decompose(entity.multi_insert())`. Кодовая логика поддерживает 6, но fixture NOT_RUN. Далее группировка.
23. Вопрос: C1 выдаёт 6 assemblies? S2:34–75 собирает весь `recursive_decompose([parent])` в один `assembly`, `groups[digest].append` один раз на parent, выдаёт только группы len>1. Один MINSERT ≠ 6 repeatedAssemblies. ADAPTER минимальный cell audit, не новый parser. Далее clipping.
24. Вопрос: применяется ли XCLIP? S1:563 прямо говорит NO. Готовый clipping путь `ezdxf.addons.drawing.frontend`:883–913; JSON provenance mapping NOT_FOUND. Не считать скрытую геометрию видимой. Далее Hotlink.
