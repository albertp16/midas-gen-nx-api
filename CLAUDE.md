# CLAUDE.md

Guidance for Claude Code when working in this repository.

## Project

**MIDAS Gen NX API Dashboard** — a web dashboard + Python script collection that interfaces with MIDAS Gen via its REST API (`https://moa-engineers.midasit.com:443/gen`) for post-processing structural analysis results.

Two layers:
1. **Web app** — Flask backend (`server.py`) + single-page frontend (`index.html`) that proxies MAPI-Key-authenticated requests to MIDAS.
2. **Standalone scripts** — Python utilities under `scripts/` for ad-hoc analysis (drift, reactions, beam design, section/member data).

## Architecture

- **`server.py`** — Flask app, serves `index.html` as static, exposes `/api/proxy?endpoint=...` which forwards to `MIDAS_BASE_URL` with the caller's `MAPI-Key` header. No business logic server-side.
- **`index.html`** — Single ~275KB file containing all UI, styles, and JS. All structural calcs (beam solver, reaction rendering, drift plotting) are ported inline from Python scripts. When scripts change, mirror the logic here — comments like `// ported from beam_solver.py` mark the port points.
- **`scripts/`** — Each subfolder is a standalone utility group. Scripts do not import each other; each is runnable on its own and hits the MIDAS API directly.
- **Units** — Force kN, distance m (API) / mm (beam inputs), moment kN·m.

## Directory layout

```
├── server.py, index.html         # Web app (keep at root — Flask serves from ".")
├── Dockerfile, Procfile, railway.json, requirements.txt, package.json
├── Demo/                         # Claude Code worktrees (leave alone)
└── scripts/
    ├── beam/        # RC beam design (ACI): beam, beam_solver, beam_force, beam_data, shear_capacity
    ├── drift/       # Story drift plots + notebook
    ├── reaction/    # 2D/3D foundation reaction viz
    ├── analysis/    # modes, irregularity, displacement, check
    └── data/        # MIDAS data fetchers: section, story, group, member_*, testing
```

## Common commands

```bash
py server.py              # Run Flask dev server (port 5000)
npm start                 # Same, via package.json
docker build -t midas .   # Build container
```

Standalone scripts are invoked directly: `py scripts/beam/beam_solver.py`.

## Conventions

- **No cross-script imports** — each script in `scripts/` is self-contained. Don't introduce a shared utils module unless the user asks; the scripts evolve independently.
- **MAPI-Key handling** — in the web app, the key is read from the browser and forwarded via header. In standalone scripts it's often hardcoded at the top (see `scripts/beam/beam_data.py`). Do not commit new hardcoded keys; flag existing ones if asked.
- **Frontend edits** — `index.html` is a single file with inline `<script>`. Preserve the structure; use Edit (not Write) for surgical changes. Calcs ported from Python must stay in sync with their script of origin.
- **Theme** — `index.html` is light-only. The page sets `<html data-theme="light">` and there is no toggle. Dark `:root` variables remain in the CSS but are unreachable; if you re-introduce dark mode, restore the toggle button + JS that were removed.
- **Demo/** — contains Claude Code worktrees (`.claude/worktrees/...`). Do not reorganize or clean this directory.
- **`.ipynb_checkpoints/`** is gitignored; don't touch.

## MIDAS API endpoints (verified)

### Where to look first when researching the API

When you don't know an endpoint URL, payload shape, TABLE_TYPE string, or DB key, check these sources in this order:

1. **[MIDAS API Online Manual](https://support.midasuser.com/hc/ko/articles/33016922742937-MIDAS-API-Online-Manual)** — official reference (Korean locale path; auto-translates / mirrors via the same article ID for other locales). Use it for endpoint listings and conceptual overviews. Note: MIDASIT's own help center sometimes 403s anonymous fetches; if WebFetch blocks, fall back to the SDK sources below or use the [English manual root](https://manual.midasuser.com).

2. **[midas-gen-python SDK source](https://github.com/MIDASIT-Co-Ltd/midas-gen-python)** — closest to this project's target (Gen NX). Useful files:
   - `midas_gen/_view.py` — `/view/capture` payload (RESULT_GRAPHIC.CURRENT_MODE, TYPE_OF_DISPLAY, MODE_SHAPE/UNDEFORMED/LEGEND/CONTOUR `_json()` shapes). The `VibrationModeShapes()` static method shows the canonical mode-shape capture payload.
   - `midas_gen/_result_table.py` — every supported `/post/TABLE` TABLE_TYPE the SDK exposes (REACTIONG, BEAMFORCE, PLATEFORCE…). If a TABLE_TYPE isn't in this file, it's almost certainly not exposed by the API even if MIDAS GUI shows the table.
   - `midas_gen/_load.py` — DB endpoints (load cases, fiber materials, etc.).

3. **[midas-civil-python SDK source](https://github.com/MIDASIT-Co-Ltd/midas-civil-python)** — broader coverage; schema patterns often match Gen NX even when the SDK isn't published for Gen. Especially `_view.py` and `_result_table.py` mirror Gen.

### Known API gaps in Gen NX (confirmed empirically via Probe buttons)

The MIDAS GUI surfaces several Result Tables that `/post/TABLE` does **not**. When the user asks for a feature that maps to one of these, the workflow is: client-side derivation from raw data tables, or a clipboard-paste import from the GUI's result window.

- **Torsional / Stiffness / Capacity Irregularity Check tables** — none exposed. Only the raw underlying tables work: `STORY_DRIFT_X`, `STORY_DRIFT_Y`, `STORY_MASS`. Probed names that all return `"error creating utbl. (ex PostMode ...)"`: `TORSIONALIRREGULARITYCHECK`, `STIFFNESSIRREGULARITYCHECK`, `WEIGHTIRREGULARITYCHECK`, `CAPACITYIRREGULARITYCHECK`, plus 50+ STORY_*_X/Y variants. The Irregularity tab in `index.html` derives Torsional + Stiffness + Mass NSCP 2015 checks client-side; Capacity uses a manual-input table with a "Paste from MIDAS" clipboard-bridge button as the practical workaround.
- **Story shear, story strength, per-column shear capacity** — not exposed. If a feature needs these, prefer paste-from-GUI or computed proxies over chasing TABLE_TYPE candidates.

### Verified endpoints

When unsure of a DB key or schema, the SDK `create()` / `get()` / `delete()` methods name the exact endpoint, and the `json()` classmethod shows the payload shape. Verified so far:

| Feature | Method | Endpoint | Schema notes |
|---|---|---|---|
| Static load cases | GET | `/db/stld` | Returns `{STLD: {<id>: {NAME, TYPE, DESC}}}` |
| Load combinations (general) | GET | `/db/lcom-gen` | |
| Response spectrum cases | GET | `/db/splc` | May 404 if none defined |
| Floor Load Type | PUT | `/db/FBLD` | Body: `{Assign: {<id>: {NAME, DESC, ITEM: [{LCNAME, FLOOR_LOAD, OPT_SUB_BEAM_WEIGHT}]}}}`. `LCNAME` must match an existing static load case name. No `iCOLOR` field — color is GUI-only. |
| Group | POST/PUT | `/db/GRUP` | See `scripts/data/group.py` |
| Reaction table query | POST | `/post/TABLE` | Body wrapped in `Argument` (TABLE_NAME, TABLE_TYPE, COMPONENTS, NODE_ELEMS) |
| Fiber Division of Section | PUT | `/db/FIBR` | Confirmed via Probe (lowercase `/db/fibr` also works). Schema: per-item `{NAME, SECT_KEY, ASSIGN_TYPE, FIMP_NAME[<=6], FIBR_BASE[], OPT_MONITORED_FIBER, MONITORED_FIBER}`. Each `FIBR_BASE` entry: `{FIBR_BASE_KEY, REBAR_NAME, AREA, CENTER_Y, CENTER_Z, FIBER_MATL_ID, AREA_CONSIDER_REBAR, OPT_IS_REBAR, POINT_Y[], POINT_Z[]}`. `FIBER_MATL_ID` is **1-based** into `FIMP_NAME`. **Dependency**: FIMP records named in `FIMP_NAME[]` MUST already exist in the model (write `/db/FIMP` first) and `SECT_KEY` must reference an existing section. Rejected aliases: `/db/FIBER-DIV`, `/db/FBDV`, `/db/FBDIV`, `/db/SECDIV`, `/db/FIBDIV`. |
| Inelastic Material Properties (Fiber) | PUT | `/db/FIMP` | Confirmed via Probe. **Not** `/db/IMFM` as the SDK's `mapi.py` suggests — that returns `error status`. Other rejected aliases: `/db/INEL`, `/db/MATL-INEL`, `/db/INELMAT`, `/db/IFM`. |

MIDAS often returns HTTP 200 with `{"message": "error status"}` on schema/endpoint errors. Treat that body as a failure (`isMidasError()` in `index.html`).

## Floor Load Type tab — design notes

- Two editable tables (SDL with 4 sub-load columns + Total, LL with 1 value column) pre-populated with sane defaults from the typical commercial floor pattern.
- Tables share `setupExcelTable(tbodyId, onAfterPaste)` — delegated paste/keyboard handlers on `tbody`. The handlers survive `innerHTML` re-renders, so `setup` only runs once per table on `DOMContentLoaded`.
- SDL+LL rows for the same `(occupancy, level)` are merged into one floor load type with multiple `ITEM` entries — keeps the count of types small and matches MIDAS's "one type per location" convention.
- An MGT generator alternative (`generateMgtCommand`) produces the `*FLOADTYPE` block exactly as it appears in MIDAS's MGT Command Shell. Use it when the API path is uncertain or when the user wants a readable artifact to commit/share.
- The feedback panel (`copyFeedbackToClipboard`, `attachLastResponse`) is a generic in-app channel: user types a message, optionally attaches the last MIDAS request/response/payload (cached in `lastFloorLoadResult` / `lastFloorLoadPayload`), copies to clipboard, pastes into chat.

## When adding a new script

Place it in the matching `scripts/<category>/` folder. If none fits, add a new subfolder rather than dropping it at the root. Update README.md's script index.

## Pending / known issues

- `scripts/beam/beam_data.py` has a hardcoded `MAPI_KEY`. Rotate or move to env before sharing.
