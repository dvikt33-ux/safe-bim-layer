# SOURCE checks 11–15

11. Tapir IFCCommands.cpp tag 1.5.9 L141–194: GetGlobalId/GetExternalGlobalId return ifcId/externalIFCId or error. Verdict: dual IDs; next Merge.
12. Graphisoft AC29 IFC Merge generates new GlobalId and retains original as External IFC ID. Source: https://help.graphisoft.com/AC/29/INT/_AC29_Help/121_IFC/121_IFC-5.htm. Verdict: preserve pair; next APA.
13. PR165 source L112–133 nativeGuidMappingChecked=false. Verdict: Tapir read-only bridge fills a gap; next receipt.
14. PR165 installed-smoke receipt blob 92c664ef: count=12, SYNTHETIC_IFC4_DXF, nativeCalls=0, plnWrites=0. Verdict: not LIVE; next completeness.
15. PR165 L20–21,76–80: MAX_SOURCE_BYTES=4GiB, SAMPLE_LIMIT=5000, truncated flag. Verdict: sample not full inventory; next DXF.
