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

When unsure of a DB key or schema, check the [midas-civil-python SDK source](https://github.com/MIDASIT-Co-Ltd/midas-civil-python/blob/main/midas_civil/_load.py) — each class has `create()` / `get()` / `delete()` methods that name the exact endpoint, plus a `json()` classmethod that shows the payload shape. Verified so far:

| Feature | Method | Endpoint | Schema notes |
|---|---|---|---|
| Static load cases | GET | `/db/stld` | Returns `{STLD: {<id>: {NAME, TYPE, DESC}}}` |
| Load combinations (general) | GET | `/db/lcom-gen` | |
| Response spectrum cases | GET | `/db/splc` | May 404 if none defined |
| Floor Load Type | PUT | `/db/FBLD` | Body: `{Assign: {<id>: {NAME, DESC, ITEM: [{LCNAME, FLOOR_LOAD, OPT_SUB_BEAM_WEIGHT}]}}}`. `LCNAME` must match an existing static load case name. No `iCOLOR` field — color is GUI-only. |
| Group | POST/PUT | `/db/GRUP` | See `scripts/data/group.py` |
| Reaction table query | POST | `/post/TABLE` | Body wrapped in `Argument` (TABLE_NAME, TABLE_TYPE, COMPONENTS, NODE_ELEMS) |

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
