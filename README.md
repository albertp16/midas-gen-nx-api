# MIDAS Gen NX API Dashboard

A web-based structural engineering dashboard that interfaces with MIDAS Gen via its REST API for post-processing analysis results, visualizing reactions, story drift, and performing ACI beam design.

## Features

### Dashboard (index.html)
- **API Connection** - Connect to MIDAS Gen using MAPI-Key with live connection status
- **Overview** - Model statistics (nodes, elements, materials, sections), run analysis with status indicator
- **Story Drift** - Plot drift ratios for multiple load cases (X/Y direction) with allowable limit overlay, show/hide values toggle, download as image
- **Reaction Forces** - 2D plan view and 3D bar chart of foundation reactions with all force components (FX, FY, FZ, MX, MY, MZ), download images, full data table
- **Beam Results** - ACI beam design following BEAM DESIGNER format:
  - Headers: id, length, width, height, fc, fy, fys, nib/nmb/njb, nit/nmt/njt, db, shear (future), moment demand/capacity/ratio, status
  - Editable per-beam: width, height, fc, fy, nib, db (double-click to edit)
  - Rerun design with per-element overrides without re-fetching API data
  - Pass/Fail status badge, copy to clipboard, export CSV
- **Column Results** - Column force/stress/deformation tables
- **Floor Load Type** - Define superimposed dead load (SDL) and live load (LL) per occupancy and write to MIDAS:
  - Two Excel-like tables (SDL with sub-loads Topping & Tiles / Duct / Ceiling / Others, auto-totaled; LL with single value)
  - Click-to-edit cells, Tab/arrow nav, paste TSV blocks from Excel
  - Two delivery paths from the same data:
    - **API write** — `PUT /db/FBLD` with `{Assign: {<id>: {NAME, DESC, ITEM: [{LCNAME, FLOOR_LOAD, OPT_SUB_BEAM_WEIGHT}]}}}` (schema verified against the [midas-civil-python SDK](https://github.com/MIDASIT-Co-Ltd/midas-civil-python))
    - **MGT generator** — produces a `*FLOADTYPE` block ready to paste into MIDAS Tools → MGT Command Shell
  - Probe Endpoint button GET-tests candidate DB keys when MIDAS rejects
  - In-app feedback panel: compose a message, attach the last MIDAS response/payload, and copy to clipboard
- **Fiber Automation** - Fiber section analysis workflow

### 3D Reaction Visualization
- Solid box rendering with proper back-face culling and face shading
- Mouse drag rotation, scroll wheel zoom, touch support
- Isometric default view (25 deg tilt, -45 deg rotation)
- Max/Min callouts with node labels

### Python Scripts
Standalone MIDAS API utilities under `scripts/`:

**`scripts/beam/`** — RC beam design
- `beam.py` — Concrete beam design (rebar area, flexural capacity)
- `beam_solver.py` — ACI beam solver (beta factor, strain analysis, reduction factors)
- `beam_force.py` — Extract beam forces from MIDAS API
- `beam_data.py` — Fetch beam element data
- `shear_capacity.py` — Transverse shear validation

**`scripts/drift/`** — Story drift
- `drift_plot.py` — Single load case story drift plot
- `drift_plot_multiple.py` — Multi-case story drift comparison
- `rs_drift_plot_multiple.py` — Response spectrum drift analysis
- `drift.ipynb` — Drift exploration notebook

**`scripts/reaction/`** — Foundation reactions
- `reaction.py` — 2D reaction force visualization
- `reaction_midas_ui.py` — Advanced 3D reaction with auto-foundation detection

**`scripts/analysis/`** — Model analysis
- `modes.py` — Vibration mode analysis and screenshots
- `irregularity.py` — Building irregularity checks
- `displacement.py` — Nodal displacement extraction
- `check.py` — Raw drift check data

**`scripts/data/`** — MIDAS data fetchers
- `section_data.py`, `story_data_api.py`, `group.py`
- `member_length.py`, `member_assignment.py`
- `testing.py` — Section payload sample

## Usage

1. Open `index.html` in a browser
2. Enter your MIDAS Gen MAPI-Key and click **Connect**
3. Navigate using the sidebar to access different result modules
4. Run Analysis from the Overview page, then fetch results from each tab

## Units

- Force: kN
- Distance: m (API), mm (beam design inputs)
- Moment: kN.m

## Requirements

- MIDAS Gen with API access enabled
- Modern web browser (Chrome, Edge, Firefox)
- Python 3.x with `requests`, `pandas`, `matplotlib`, `plotly` (for standalone scripts)

## License

See [LICENSE](LICENSE) file.
