# Template — live run record

Copy this file to the target name, fill it in from the actual run, commit it
under `bimexec/results/`. Do not fill it in from memory or from documentation.

Target names:

- read-only baseline: `WORK_LIVE_BASELINE_YYYY-MM-DD.md`
- T0A: `T0A_RUN_YYYY-MM-DD.md` (and commit `capability_matrix.json` next to it)

---

## Run identity

```
Run date (UTC)        :
Operator              : ChatGPT/Work on Windows
Repository branch     : arena/t0-probes
Commit SHA tested     :
Archicad version/build:
Tapir add-on version  :
Project (.pln)        :
Active API port       :
```

## Required summary fields (from `bimexec/HANDOFF_WORK.md`)

```
PROBES_PRESENT  : yes|no
ACTIVE_PORT     :
PROJECT         :
TAPIR_VERSION   :
MCP_OK          : yes|no
MCP_MODE        : verdicts|full|unknown
WALL_SAMPLE_OK  : yes|no
MUTATIONS       : 0
BLOCKERS        :
```

`MUTATIONS` must be `0`. Any non-zero value means a write happened and the run
must be reported as an incident, not as a result.

## T0A execution

```
Command               :
Exit code             :
Backend that answered :
```

## Capability verdicts (copy from the T0A console)

```
  project_identity            :
  stories_index_map           :
  list_guids                  :
  count_by_type               :
  elements_by_type            :
  wall_geometry_endpoints     :
  layer_name_via_property     :
  read_element_id             :
  read_custom_property        :
  search_scan                 :
  tapir_native_prefix_search  :
  tapir_read_commands         :
  tapir_addon_version         :
  mcp_tools_list              :
```

## Derived facts

```
duplicate_detection           :
readable marker carriers      :
element_id address for T0B    :
create_wall.production_safe   : false
GUID chosen for T0B           :
```

## Decision

```
T0A go / no-go                :
Reason (if no-go)             :
T0B authorised (yes/no)       :
Authorised by                 :
```

Go/no-go criteria: `bimexec/docs/T0_RESULTS.md` §3. All seven must hold.
T0B is a separate, explicit authorisation — it is never implied by a T0A go.
