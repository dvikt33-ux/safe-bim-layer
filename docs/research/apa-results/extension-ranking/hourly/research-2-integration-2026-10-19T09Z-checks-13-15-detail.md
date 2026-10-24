# APA №2 09Z — уточнение checks 13–15
13. xref.embed, ezdxf v1.4.5 xref.py L340: loads modelspace, FileNotFoundError/DXFVersionError possible. DEFER; next version fixture.
14. xref.define, xref.py L209: overlay does not transitively propagate, attach does. ADAPTER record flags; next nested fixture.
15. units.conversion_factor, units.py L180: target_factor/source_factor; unsupported raises TypeError, invalid enum ValueError. ADAPTER explicit unit map; next unitless.
Sources: https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/xref.py and https://github.com/mozman/ezdxf/blob/v1.4.5/src/ezdxf/units.py
