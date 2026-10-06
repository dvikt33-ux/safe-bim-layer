# Layer Registry v0.1

This registry deliberately stays small. Layer is used for visibility, locking and intersection behavior, not as a replacement for Classification, Properties, Renovation or Design Options.

Important Archicad behavior:
- each element belongs to one layer;
- Doors, Windows and Openings follow their host Wall layer rather than having independent layers;
- Layer Combinations save layer states for Views;
- intersection group participates in automatic element cleanup.

Therefore the template does NOT create per-floor, per-material, per-color or per-renovation layers.

Core model prefixes:
AR / KR / VK / OV / EOM / SS / PB / TX / GP

Support prefixes:
REF / DOC / QA

Production geometry is forbidden on the built-in Archicad Layer.

See layer-registry-v0.1.yaml for the exact layer list and combinations.
