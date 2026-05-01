# MIDAS Gen NX API Dashboard

A web-based structural engineering dashboard that interfaces with MIDAS Gen via its REST API for post-processing analysis results, visualizing reactions, plotting story drift / displacement, performing ACI beam design, capturing mode-shape screenshots, and running NSCP 2015 / ASCE 7 irregularity checks.

## Features

### Dashboard (index.html)
- **API Connection** - Connect to MIDAS Gen using MAPI-Key with live connection status
- **Overview** - Model statistics (nodes, elements, materials, sections), run analysis with status indicator
- **Drift & Displacement** *(merged tab)* - Single sidebar entry with a Result Type toggle:
  - Plot story drift ratios with allowable limit overlay, scale factor and response modification factor inputs, X/Y/Both/Mix direction modes
  - Plot story displacements per direction
  - Show/hide values, download chart as PNG, multi-load-case overlay
- **Reaction Forces** - 2D plan view and 3D bar chart of foundation reactions with all force components (FX, FY, FZ, MX, MY, MZ), download images, full data table
- **Beam Results** - ACI beam design following BEAM DESIGNER format:
  - Headers: id, length, width, height, fc, fy, fys, nib/nmb/njb, nit/nmt/njt, db, shear (future), moment demand/capacity/ratio, status
  - Editable per-beam: width, height, fc, fy, nib, db (double-click to edit)
  - Rerun design with per-element overrides without re-fetching API data
  - Pass/Fail status badge, copy to clipboard, export CSV
- **Column Results** - Column force/stress/deformation tables
- **Vibration Modes** - Modal analysis results + mode-shape screenshots:
  - Eigenvalue + Participation Vector tables with banded MIDAS-style headers
  - Probe button to test alternative TABLE_TYPE candidates
  - **Mode Shape Screenshots** - capture 3D iso + plan view JPGs per mode via `POST /view/capture` (canonical SDK schema with full `MODE_SHAPE` / `UNDEFORMED` / `LEGEND` / `CONTOUR` field set)
    - Configurable mode count, name prefix, 3D angle, image size
    - Optional contour + legend overlay (`NUM_OF_COLOR: 12`, `COLOR_TYPE: "rgb"`)
    - Per-image click-to-download or "Download All" with staggered triggers
    - Flask side-channel: `/api/capture-dir` + `/api/local-image` reads MIDAS's exported JPGs from `%TEMP%/midas_capture/` back into the page
- **Irregularity Check** - NSCP 2015 / ASCE 7 vertical and torsional irregularity tables:
  - **Direction tab** at the top (Both / X Only / Y Only) filters every direction-aware panel without re-fetching
  - Raw API tables: Story Drift X, Story Drift Y, Story Mass (the only irregularity-related tables Gen NX exposes via `/post/TABLE`)
  - **Computed checks** (client-side per NSCP 208.4.5):
    - **Torsional Irregularity** (1a / 1b) - max-drift / CoM-drift ratio with NSCP thresholds 1.2 / 1.4
    - **Stiffness / Soft Story** (1a / 1b) - K = h/Δ via the `1/StoryDriftRatio` method, with `0.7 Ku1` and `0.8 Ku123` threshold columns matching the native MIDAS layout
    - **Weight / Mass Irregularity** (Type 2) - 1.5× adjacent threshold, NSCP roof-exemption rule applied, columns mirror the native *Result-[Weight Irregularity Check]* window
    - **Capacity / Weak Story** (5a / 5b) - manual strength input table (Gen NX doesn't expose `STORY_SHEAR`); auto-populates with story names from the drift fetch, then computes ratios on Compute Check
  - Probe button cycles candidate TABLE_TYPE strings (35+ variants) for diagnostic purposes
  - **CSV download** - per-panel button auto-injected into each result panel header, plus a single "Download All CSVs" toolbar button (RFC-4180 escaped, one file per visible panel)
  - Native-style irregular-row highlighting (orange / bold) applied to every check table
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
