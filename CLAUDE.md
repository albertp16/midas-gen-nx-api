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
- **Demo/** — contains Claude Code worktrees (`.claude/worktrees/...`). Do not reorganize or clean this directory.
- **`.ipynb_checkpoints/`** is gitignored; don't touch.

## When adding a new script

Place it in the matching `scripts/<category>/` folder. If none fits, add a new subfolder rather than dropping it at the root. Update README.md's script index.

## Pending / known issues

- `scripts/beam/beam_data.py` has a hardcoded `MAPI_KEY`. Rotate or move to env before sharing.
