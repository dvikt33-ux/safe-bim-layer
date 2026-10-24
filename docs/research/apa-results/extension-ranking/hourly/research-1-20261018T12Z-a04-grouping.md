# APA 12Z checks 21–26 — status and grouping API

21. PR162 nativeCallsIfAuthorized=1/2 per assembly, nativeModelWrites=0. This counts graph commands, not underlying ACAPI calls; no measured speedup.

22. GitHub fetch_issue: PR128,154,159,160,162 all OPEN on 2026-10-18. PR code not verified merged to main; local installation unknown.

23. Tapir 1.5.9 AddOnMain.cpp registers MoveElements 1.0.2, RotateElements 1.5.3, CreateGroups 1.4.0, group reads 1.5.6, GetDetailsOfElements 1.5.7. Installed 1.5.10 NOT_VERIFIED.

24. common_schema_definitions.js ElementOrGroupIds minItems=2, optional parentGroupId; GroupIdOrError union. Nested groups supported in source, not live-tested.

25. ElementGroupingCommands.cpp calls ACAPI_Grouping_CreateGroup for each group; per-item errors coexist with overall NoError. Need indexed readback.

26. GetGroupsOfElements gives direct group; ungrouped APIERR_GENERAL. GetElementsOfGroups lists direct members, not recursive subtree. Do not flatten by assumption.
