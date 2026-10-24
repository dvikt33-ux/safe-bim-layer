# APA 18Z — counter-audit A: evidence and versions
Independent check of 30 source findings:
- ezdxf source tag v1.4.5, runtime untested.
- IfcOpenShell geolocation source tag v0.8.0, pinned 0.8.5 source NOT_VERIFIED; never transfer signatures.
- Tapir upstream 1.5.9 differs from local 1.5.10; PR164 records old Router catalog 1.5.8.
- PR165 reports installed opt-in 12/12 synthetic smoke in a committed receipt; this researcher did not verify local installation.
- SAF 1.7.3 Apache-2.0 does not override transitive EPPlus licence change in v5+.
- BCF.js repository archived; IfcOpenShell BCF2.1 fix PR8390 open.
- occt-import-js source version 0.0.24 does not prove per-part placement matrices.
SOURCE=PARTIAL_VERIFIED; OFFLINE/BUILD/LIVE=NOT_RUN; INSTALLED=PR165_RECEIPT_ONLY; ACCEPTED=NO.
