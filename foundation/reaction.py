import requests
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import matplotlib.patheffects as pe
import math

# function for MIDAS Open API
def MidasAPI(method, command, body=None):
    base_url = "https://moa-engineers.midasit.com:443/gen"
    mapi_key = "eyJ1ciI6IkFsYmVydFBhbW9uYWciLCJwZyI6ImdlbiIsImNuIjoiQldiby12dG1RQSJ9.12b57179a60ebf634b50081504bdf1a45e158893fd8306ce0b78ed5a9ef557ed"

    url = base_url + command
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": mapi_key
    }

    if method == "POST":
        response = requests.post(url=url, headers=headers, json=body)
    elif method == "PUT":
        response = requests.put(url=url, headers=headers, json=body)
    elif method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url=url, headers=headers)

    print(method, command, response.status_code)
    return response.json()

# Unit Setting
unit_dist = "M"     # M, CM, MM, IN, FT
unit_force = "KN"   # KN, N, KGF, TONF, LBF, KIPS

file_loc = {
    "Argument": r"C:\Users\alber\Desktop\4S Apartment\midas\jawod_4s.mgbx"
}


reaction = {
    "Argument": {
        "TABLE_NAME": "Reaction(Global)",
        "TABLE_TYPE": "REACTIONG",
        "EXPORT_PATH": r"C:\Users\alber\Desktop\4S Apartment\results\output.JSON",
        "UNIT": {
            "FORCE": "kN",
            "DIST": "m"
        },
        "STYLES": {
            "FORMAT": "Fixed",
            "PLACE": 2
        },
        "COMPONENTS": [
            "Node",
            "Load",
            "FX",
            "FY",
            "FZ",
            "MX",
            "MY",
            "MZ",
            "Mb"
        ],
        "NODE_ELEMS": {
            "KEYS": [
                1,2,3,4,5,6,7,8,9,10,11,12,13,14,15
            ]
        },
        "LOAD_CASE_NAMES": [
            "SDL(ST)"
        ]
    }
}


def runAnalysis():
    print("Performing Run Analysis in Midas Gen")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis is completed!!!")
# irregular = {
#     "Argument": {
#         "COUNTRY_CODE": "NSCP2015",
#         "STORY_DRIFT_METHOD": "Max.DriftofOuterExtremePoints",
#         "STORY_STIFFNESS_METHOD": "1/StoryDriftRatio"
#         # "SEISMIC_BEHAVIOR_FACTOR": "3orbelow"  # optional
#     }
# }



file_open = MidasAPI("POST", "/doc/open", file_loc)
# print("OPEN RESPONSE:", file_open)
node_data = MidasAPI("GET", "/db/node", {})
# print(node_data)
runAnalysis()
# run = MidasAPI("POST", "/doc/ANAL", {})
reaction_out = MidasAPI("POST", "/post/TABLE", reaction)
print("REACTION RESPONSE:", reaction_out)

def getCoordinate(node_ids, data):
    """
    Returns [node_id, X, Y] for given node IDs
    """
    nodes = data.get("NODE", {})
    result = []

    for nid in node_ids:
        key = str(nid)  # node IDs are stored as strings
        if key in nodes:
            node = nodes[key]
            result.append([nid, node["X"], node["Y"]])

    return result

coord_out = getCoordinate([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], node_data)

def getforce(node_ids, force_type, data):
    """
    Extracts reaction force/moment for specified nodes and force type.
    force_type: 'FX', 'FY', 'FZ', 'MX', 'MY', 'MZ' (case-insensitive)
    """
    table = data.get("Reaction(Global)", {})
    head = table.get("HEAD", [])
    rows = table.get("DATA", [])

    force_type = force_type.upper()

    if force_type not in head:
        raise ValueError(f"Force type '{force_type}' not found in data header")

    idx_node = head.index("Node")
    idx_force = head.index(force_type)

    result = []
    node_ids_str = set(str(n) for n in node_ids)

    for row in rows:
        node = row[idx_node]
        if node in node_ids_str:
            result.append([int(node), float(row[idx_force])])

    return result


force_out = getforce([1,2,3,4,5,6,7,8,9,10,11,12,13,14,15], "FZ", reaction_out)
print(force_out)
def combine_node_xy_force(coord_data, force_data):
    """
    coord_data : [[node, X, Y], ...]
    force_data : [[node, force], ...]

    return     : [[node, X, Y, force], ...]
    """
    # Convert force list to dict for fast lookup
    force_dict = {node: force for node, force in force_data}

    combined = []
    for node, x, y in coord_data:
        if node in force_dict:
            combined.append([node, x, y, force_dict[node]])

    return combined

foundation_data = combine_node_xy_force(coord_out, force_out)
# print(foundation_data)

def _nice_step(data_range, target_bins):
    """Pick a 'nice' step size (1, 2, 2.5, 5 * 10^n) near data_range/target_bins."""
    if data_range <= 0:
        return 1.0
    raw = data_range / max(1, target_bins)
    exp = 10 ** math.floor(math.log10(raw))
    frac = raw / exp
    if frac <= 1:
        nice = 1
    elif frac <= 2:
        nice = 2
    elif frac <= 2.5:
        nice = 2.5
    elif frac <= 5:
        nice = 5
    else:
        nice = 10
    return nice * exp

def auto_bin_edges(values, target_bins=7):
    """Return rounded bin edges covering values with 'nice' step size."""
    vmin = float(np.min(values))
    vmax = float(np.max(values))
    if np.isclose(vmin, vmax):
        return np.array([vmin, vmax + 1e-9])

    step = _nice_step(vmax - vmin, target_bins)
    lo = math.floor(vmin / step) * step
    hi = math.ceil(vmax / step) * step

    # ensure at least 2 edges
    edges = np.arange(lo, hi + step * 0.5, step)
    if len(edges) < 2:
        edges = np.array([lo, hi])
    return edges

def plot_force_plan_simplified(
    node_xy_force,
    title="Axial Reactions (kN)",
    unit="kN",
    target_bins=7,            # auto bins count (approx)
    # bubble sizing
    size_scale=1100,
    min_size=180,
    alpha=0.85,
    edge_lw=0.8,
    # node labels
    node_fontsize=9,
    node_offset=(10, 0),      # label to right
    # layout
    fig_size=(12.5, 5.6),
    equal_aspect=True,
    show=True
):
    """
    node_xy_force: [[node, X, Y, force], ...]

    - Auto bin edges with nice rounded ranges
    - No force values inside circles
    - Node IDs only (no 'N' prefix)
    - Discrete colorbar with bin labels
    - MAX/MIN callouts with values
    """
    arr = np.array(node_xy_force, dtype=float)
    if arr.size == 0:
        raise ValueError("node_xy_force is empty.")

    nodes = arr[:, 0].astype(int)
    xs    = arr[:, 1]
    ys    = arr[:, 2]
    f     = arr[:, 3]

    # ----- auto bins -----
    bin_edges = auto_bin_edges(f, target_bins=target_bins)
    ncolors = len(bin_edges) - 1

    base = plt.get_cmap("turbo") if "turbo" in plt.colormaps() else plt.get_cmap("jet")
    colors = [base(i / max(1, ncolors - 1)) for i in range(ncolors)]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bin_edges, ncolors)

    # ----- bubble sizes -----
    f_abs = np.abs(f)
    denom = float(np.max(f_abs)) if np.max(f_abs) != 0 else 1.0
    sizes = min_size + size_scale * (f_abs / denom)

    # ----- max/min -----
    i_max = int(np.argmax(f))
    i_min = int(np.argmin(f))

    fig, ax = plt.subplots(figsize=fig_size, dpi=150)

    # ----- scatter -----
    sc = ax.scatter(
        xs, ys,
        c=f,
        s=sizes,
        cmap=cmap,
        norm=norm,
        alpha=alpha,
        edgecolors="k",
        linewidths=edge_lw,
        zorder=3
    )

    # ----- discrete colorbar (range labels) -----
    mids = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    cbar = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02, ticks=mids)
    cbar.ax.set_yticklabels([f"{lo:.0f} - {hi:.0f}" for lo, hi in zip(bin_edges[:-1], bin_edges[1:])])
    cbar.set_label(f"Reaction ({unit})")

    # ----- node ID beside circle (no 'N') -----
    for n, x, y in zip(nodes, xs, ys):
        ax.annotate(
            f"{n}",
            xy=(x, y),
            xytext=node_offset,
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=node_fontsize,
            color="black",
            path_effects=[pe.withStroke(linewidth=2.8, foreground="white")],
            zorder=8
        )

    # ----- highlight MAX/MIN rings + callouts -----
    ax.scatter([xs[i_max]], [ys[i_max]], s=[sizes[i_max]*1.12],
               facecolors="none", edgecolors="red", linewidths=2.6, zorder=9)
    ax.scatter([xs[i_min]], [ys[i_min]], s=[sizes[i_min]*1.12],
               facecolors="none", edgecolors="blue", linewidths=2.6, zorder=9)

    ax.annotate(
        f"MAX {f[i_max]:.2f} {unit}",
        xy=(xs[i_max], ys[i_max]),
        xytext=(16, 12), textcoords="offset points",
        color="red", fontsize=9.5, weight="bold",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="red", lw=1.3),
        arrowprops=dict(arrowstyle="->", color="red", lw=1.3),
        zorder=20
    )
    ax.annotate(
        f"MIN {f[i_min]:.2f} {unit}",
        xy=(xs[i_min], ys[i_min]),
        xytext=(16, -16), textcoords="offset points",
        color="blue", fontsize=9.5, weight="bold",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="blue", lw=1.3),
        arrowprops=dict(arrowstyle="->", color="blue", lw=1.3),
        zorder=20
    )

    # ----- axes style -----
    ax.set_title(title, fontsize=12, weight="bold")
    ax.set_xlabel("X Coordinates")
    ax.set_ylabel("Y Coordinates")
    ax.grid(True, alpha=0.22)
    ax.set_axisbelow(True)

    if equal_aspect:
        ax.set_aspect("equal", adjustable="box")

    # padding
    xpad = (xs.max() - xs.min()) * 0.12 if xs.max() != xs.min() else 1.0
    ypad = (ys.max() - ys.min()) * 0.12 if ys.max() != ys.min() else 1.0
    ax.set_xlim(xs.min() - xpad, xs.max() + xpad)
    ax.set_ylim(ys.min() - ypad, ys.max() + ypad)

    plt.tight_layout()
    if show:
        plt.show()

    return fig, ax, bin_edges


fig, ax, bin_edges = plot_force_plan_simplified(
    foundation_data,
    title="Axial Reactions (kN)",
    unit="kN",
    target_bins=7,
    fig_size=(9, 9)
)

