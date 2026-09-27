# External technology integration audit — 10 passes

Goal: identify technologies that can increase Safe BIM function/speed without creating a second unsafe write path.

No live Archicad writes were performed.

## Pass 1 — Tapir 1.5.9 remains the primary execution backend

Tapir already exposes the broadest usable JSON surface found in this research for AC29: model creation/modification, relations, docs, navigator, favorites, libraries, properties/classifications, Design Options, SEO/trims, MEP, issues/BCF, Teamwork and more.

It is open source, so Safe BIM can inspect the exact C++ mapping to ACAPI and build semantic verifiers around it.

Verdict: **PRIMARY BACKEND**.

## Pass 2 — Graphisoft Automation API is a useful compatibility/read layer, not the main expansion route

Graphisoft's official Automation API communicates over HTTP/JSON and provides a Python wrapper. Graphisoft describes it as workflow automation, historically focused on documentation automation.

Official source:
https://archicadapi.graphisoft.com/getting-started-with-archicad-python-connection

Safe BIM already uses/has investigated this ecosystem. It is valuable for official baseline operations and compatibility checks, but Tapir exposes substantially more ACAPI functionality needed by this project.

Verdict: **SECONDARY / FALLBACK / REFERENCE**, not a reason to split production writes across two backends.

## Pass 3 — native C++ Add-On API is the ultimate capability layer, but not currently the practical Safe BIM extension path

Graphisoft describes the Add-On API as the most powerful extension technology with access to nearly everything in Archicad.

Official overview:
https://archicadapi.graphisoft.com/archicad-extension-and-automation-technologies

The user already encountered the registered Developer ID/signing/distribution constraint for a custom `.apx` in licensed Archicad. Safe BIM should therefore first exploit Tapir's signed/open add-on rather than duplicate it with a custom production add-on.

Verdict: **FUTURE LAST-RESORT BACKEND** only for capabilities that cannot be reached through Tapir or supported external workflows.

## Pass 4 — Grasshopper–Archicad Live Connection is powerful for parametric design

Graphisoft AC29 documentation confirms the official Grasshopper–Archicad Live Connection creates real BIM elements and supports Rhino 7/8.

Official AC29 guide:
https://help.graphisoft.com/AC/29/INT/GC.pdf

This is high value for freeform/parametric authoring, but direct Live Connection writes would bypass Safe BIM's exact receipt/reconciliation runtime.

Verdict: **GEOMETRY/DESIGN FRONTEND, NOT A PRODUCTION SAFE-BIM WRITE BACKEND**.

Safe integration options:

- use Grasshopper to generate coordinates/curves/parameters, then compile them to a Safe BIM recipe;
- use it for human design exploration in a disposable/option branch, then reconstruct approved output through certified Safe BIM operations;
- never treat an uncontrolled GH mutation as Safe BIM-owned merely because geometry matches.

## Pass 5 — Tapir Grasshopper plugin is useful as a schema/UI reference

The Tapir repository includes a substantial Grasshopper plugin wrapping Tapir commands. The 1.5.8 -> 1.5.9 delta added/expanded components for element creation, details, hotlinks, libraries, Design Options, trims and more.

Repository:
https://github.com/ENZYME-APD/tapir-archicad-automation/tree/1.5.9/grasshopper-plugin

Its value to Safe BIM is mainly:

- proven parameter mapping examples;
- discoverability/UI patterns;
- a parametric authoring frontend.

Direct GH command execution still needs Safe BIM ownership semantics if used for production mutation.

Verdict: **REFERENCE / OPTIONAL FRONTEND**.

## Pass 6 — GDL + LP_XMLConverter is the strongest no-custom-APX functional expansion

Graphisoft officially ships `LP_XMLConverter` with Archicad. GDL can create native parametric library parts with 3D, 2D, parameters, UI and properties. Tapir can load/inventory/place these parts.

Official sources:
- https://gdl.graphisoft.com/tips-and-tricks/how-to-use-the-lp_xmlconverter-tool/
- https://gdl.graphisoft.com/gdl-basics/about-gdl/

Detailed Safe BIM integration audit:
`../05_expansion_candidates/PARAMETRIC_GDL_LIBRARY_FACTORY.md`.

Verdict: **HIGH-PRIORITY EXPANSION** for reusable single logical objects.

## Pass 7 — BIBIM is valuable for source patterns, not for replacing the safety kernel

Repository `SquareZero-Inc/bibim-archicad` is open source and contains:

- direct Archicad tool catalog/handlers;
- context summary/history/token components;
- OpenAI/Claude/Gemini/local-provider patterns;
- a local provider targeting OpenAI-compatible `/models` and `/chat/completions`;
- UI/bridge architecture.

Repository:
https://github.com/SquareZero-Inc/bibim-archicad

Useful patterns can be borrowed/reimplemented, especially context summarization, local provider lifecycle boundary and UX.

However BIBIM does not replace Safe BIM's durable receipt/reconciliation semantics.

Verdict: **REFERENCE / OPTIONAL AI UX SOURCE**.

## Pass 8 — progressive MCP discovery is useful for AI ergonomics, but raw execution must remain behind certification

`SzamosiMate/tapir-archicad-MCP` exposes a progressive mode where the model initially sees only discovery/schema/execute tools instead of roughly 191 individual Archicad tools.

Repository:
https://github.com/SzamosiMate/tapir-archicad-MCP

This is exactly the right pattern for reducing prompt/tool overhead.

Safe BIM adaptation:

- AI discovers **certified Safe BIM capabilities**, not arbitrary Tapir writes;
- schema retrieval comes from the capability manifest;
- execute dispatches only registered SafeBIMOperations;
- raw Tapir read-only access may be exposed separately;
- raw Tapir writes are never available to the LLM.

Verdict: **HIGH-PRIORITY AI TOOL-DISCOVERY PATTERN**.

## Pass 9 — IFC/BCF are interoperability/QA channels, not ownership channels

Tapir 1.5.9 already exposes IFC and Archicad Issue/BCF workflows. These can connect external QA, issue exchange and cross-file identity.

They should not become a parallel model mutation engine unless a separate backend is explicitly certified.

Archicad GUID receipt remains the ownership basis for an in-project Safe BIM transaction; IFC IDs and BCF issue IDs are interoperability identities.

Verdict: **HIGH VALUE FOR QA/EXCHANGE, LOW VALUE AS CORE WRITE BACKEND**.

## Pass 10 — final integration architecture

Recommended backend/frontend topology:

```text
Natural language / UI / selected elements / Grasshopper geometry / schedules
                |
                v
        Project Recipe compiler
                |
      certified capability manifest
                |
                v
       Safe BIM safety runtime
                |
                v
        Tapir 1.5.9 JSON/ACAPI
                |
                v
             Archicad 29
```

Side systems:

- GDL/HSF + LP_XMLConverter -> compiled library content -> Tapir loads/places it;
- Hotlink `.mod` catalog -> Tapir instances repeated assemblies;
- IFC/BCF -> exchange/QA;
- MCP-style progressive discovery -> AI frontend only;
- BIBIM -> source/reference patterns;
- Grasshopper -> geometry/parametric authoring source;
- official Automation API -> compatibility/reference/fallback reads.

# Integration audit

## Technologies worth integrating now

1. Tapir 1.5.9 exact schema/source pin.
2. Project Recipe + capability manifest.
3. Favorites + project profile.
4. Hotlink module catalog.
5. ScriptUI/selection/highlight/point-pick UX.
6. GDL/HSF parametric component factory.
7. MCP-style progressive certified-tool discovery.
8. read-only event/cache/QA acceleration.

## Technologies to keep optional

- Grasshopper frontend;
- BIBIM-derived UI/provider patterns;
- IFC/BCF external workflow;
- MEP high-risk multi-object operations after separate certification.

## Technologies not justified as a new production write backend now

- a custom Safe BIM C++ `.apx` duplicating Tapir;
- unrestricted raw MCP->Tapir writes;
- direct AI->Archicad tool calling without deterministic Safe BIM mediation.

This topology maximizes reach while keeping exactly one production safety authority.
