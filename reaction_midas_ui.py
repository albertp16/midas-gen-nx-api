import requests
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import matplotlib.patheffects as pe
import plotly.graph_objects as go
import plotly.io as pio
import math

# =========================================================
# MIDAS Open API
# =========================================================
def MidasAPI(method, command, body=None):
    base_url = "https://moa-engineers.midasit.com:443/gen"

    # Put your regenerated MIDAS API key here
    mapi_key = "eyJ1ciI6IkFsYmVydFBhbW9uYWciLCJwZyI6ImdlbiIsImNuIjoiQldiby12dG1RQSJ9.12b57179a60ebf634b50081504bdf1a45e158893fd8306ce0b78ed5a9ef557ed"


    url = base_url + command
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": mapi_key
    }

    method = method.upper()

    if method == "POST":
        response = requests.post(url=url, headers=headers, json=body)
    elif method == "PUT":
        response = requests.put(url=url, headers=headers, json=body)
    elif method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url=url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    print(f"{method} {command} -> {response.status_code}")

    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
        print("Response text:", response.text)
        raise
    except Exception:
        print("Non-JSON response:", response.text)
        raise

# =========================================================
# USER SETTINGS
# =========================================================
LOAD_CASE_NAME = "SDL(ST)"
FORCE_COMPONENT = "FZ"   # FX, FY, FZ, MX, MY, MZ
EXPORT_PATH = r"C:\Users\alber\Desktop\4S Apartment\results\output.JSON"
PLOTLY_HTML_PATH = r"C:\Users\alber\Desktop\4S Apartment\results\FZ_3D_Reaction_Plot.html"

Z_TOL = 1e-6
FILTER_ZERO_REACTION = True
ZERO_FORCE_TOL = 1e-8

TARGET_BINS = 7
SHOW_MATPLOTLIB_2D = True
SHOW_PLOTLY_3D = True
AUTO_OPEN_PLOTLY_HTML = True

# Plotly label control
SHOW_ALL_NODE_LABELS = False      # False = cleaner presentation
TOP_N_LABELS = 8                  # number of biggest abs reactions to label
SHOW_MAX_MIN_ONLY = True

# =========================================================
# ANALYSIS
# =========================================================
def runAnalysis():
    print("Performing Run Analysis in MIDAS Gen...")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis completed.")

# =========================================================
# NODE EXTRACTION
# =========================================================
def get_all_nodes_xyz(data):
    """
    Returns a list: [[node_id, X, Y, Z], ...]
    """
    nodes = data.get("NODE", {})
    result = []
    for nid, node in nodes.items():
        result.append([int(nid), float(node["X"]), float(node["Y"]), float(node["Z"])])
    result.sort(key=lambda x: x[0])
    return result

def get_lowest_z_nodes(data, tol=1e-6):
    """
    Returns:
        z_min, [[node_id, X, Y, Z], ...] for all nodes at lowest Z
    """
    all_nodes = get_all_nodes_xyz(data)
    if not all_nodes:
        raise ValueError("No node data found.")

    z_values = [row[3] for row in all_nodes]
    z_min = min(z_values)
    lowest_nodes = [row for row in all_nodes if abs(row[3] - z_min) <= tol]
    return z_min, lowest_nodes

# =========================================================
# REACTION TABLE REQUEST
# =========================================================
def build_reaction_request(node_ids, load_case_name, export_path):
    return {
        "Argument": {
            "TABLE_NAME": "Reaction(Global)",
            "TABLE_TYPE": "REACTIONG",
            "EXPORT_PATH": export_path,
            "UNIT": {
                "FORCE": "kN",
                "DIST": "m"
            },
            "STYLES": {
                "FORMAT": "Fixed",
                "PLACE": 3
            },
            "COMPONENTS": [
                "Node", "Load", "FX", "FY", "FZ", "MX", "MY", "MZ", "Mb"
            ],
            "NODE_ELEMS": {
                "KEYS": node_ids
            },
            "LOAD_CASE_NAMES": [load_case_name]
        }
    }

# =========================================================
# REACTION EXTRACTION
# =========================================================
def getforce(node_ids, force_type, reaction_data):
    """
    Extract reaction force/moment from Reaction(Global) table.
    Returns: [[node_id, force_value], ...]
    """
    table = reaction_data.get("Reaction(Global)", {})
    head = table.get("HEAD", [])
    rows = table.get("DATA", [])

    force_type = force_type.upper()
    if force_type not in head:
        raise ValueError(f"Force type '{force_type}' not found in table header.")

    idx_node = head.index("Node")
    idx_force = head.index(force_type)

    node_ids_str = set(str(n) for n in node_ids)
    result = []

    for row in rows:
        node = str(row[idx_node])
        if node in node_ids_str:
            try:
                result.append([int(node), float(row[idx_force])])
            except Exception:
                pass

    return result

def combine_node_xyz_force(coord_data, force_data, filter_zero=True, zero_tol=1e-8):
    """
    coord_data : [[node, X, Y, Z], ...]
    force_data : [[node, force], ...]
    return     : [[node, X, Y, Z, force], ...]
    """
    force_dict = {node: force for node, force in force_data}
    combined = []

    for node, x, y, z in coord_data:
        if node in force_dict:
            f = force_dict[node]
            if filter_zero and abs(f) <= zero_tol:
                continue
            combined.append([node, x, y, z, f])

    return combined

# =========================================================
# NICE BIN FUNCTIONS
# =========================================================
def _nice_step(data_range, target_bins):
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
    vmin = float(np.min(values))
    vmax = float(np.max(values))

    if np.isclose(vmin, vmax):
        return np.array([vmin, vmax + 1e-9])

    step = _nice_step(vmax - vmin, target_bins)
    lo = math.floor(vmin / step) * step
    hi = math.ceil(vmax / step) * step
    edges = np.arange(lo, hi + step * 0.5, step)

    if len(edges) < 2:
        edges = np.array([lo, hi])

    return edges

# =========================================================
# 2D MATPLOTLIB PLOT
# =========================================================
def plot_force_plan_simplified(
    node_xy_force,
    title="Foundation Reactions (kN)",
    unit="kN",
    target_bins=7,
    size_scale=1100,
    min_size=180,
    alpha=0.85,
    edge_lw=0.8,
    node_fontsize=9,
    node_offset=(10, 0),
    fig_size=(9, 9),
    equal_aspect=True,
    show=True
):
    """
    node_xy_force: [[node, X, Y, Z, force], ...]
    """
    arr = np.array(node_xy_force, dtype=float)
    if arr.size == 0:
        raise ValueError("node_xy_force is empty.")

    nodes = arr[:, 0].astype(int)
    xs = arr[:, 1]
    ys = arr[:, 2]
    zs = arr[:, 3]
    f = arr[:, 4]

    bin_edges = auto_bin_edges(f, target_bins=target_bins)
    ncolors = len(bin_edges) - 1

    base = plt.get_cmap("turbo") if "turbo" in plt.colormaps() else plt.get_cmap("jet")
    colors = [base(i / max(1, ncolors - 1)) for i in range(ncolors)]
    cmap = ListedColormap(colors)
    norm = BoundaryNorm(bin_edges, ncolors)

    f_abs = np.abs(f)
    denom = float(np.max(f_abs)) if np.max(f_abs) != 0 else 1.0
    sizes = min_size + size_scale * (f_abs / denom)

    i_max = int(np.argmax(f))
    i_min = int(np.argmin(f))

    fig, ax = plt.subplots(figsize=fig_size, dpi=150)

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

    mids = 0.5 * (bin_edges[:-1] + bin_edges[1:])
    cbar = fig.colorbar(sc, ax=ax, fraction=0.035, pad=0.02, ticks=mids)
    cbar.ax.set_yticklabels(
        [f"{lo:.0f} - {hi:.0f}" for lo, hi in zip(bin_edges[:-1], bin_edges[1:])]
    )
    cbar.set_label(f"Reaction ({unit})")

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

    ax.scatter(
        [xs[i_max]], [ys[i_max]],
        s=[sizes[i_max] * 1.12],
        facecolors="none",
        edgecolors="red",
        linewidths=2.6,
        zorder=9
    )
    ax.scatter(
        [xs[i_min]], [ys[i_min]],
        s=[sizes[i_min] * 1.12],
        facecolors="none",
        edgecolors="blue",
        linewidths=2.6,
        zorder=9
    )

    ax.annotate(
        f"MAX {f[i_max]:.2f} {unit}",
        xy=(xs[i_max], ys[i_max]),
        xytext=(16, 12),
        textcoords="offset points",
        color="red",
        fontsize=9.5,
        weight="bold",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="red", lw=1.3),
        arrowprops=dict(arrowstyle="->", color="red", lw=1.3),
        zorder=20
    )

    ax.annotate(
        f"MIN {f[i_min]:.2f} {unit}",
        xy=(xs[i_min], ys[i_min]),
        xytext=(16, -16),
        textcoords="offset points",
        color="blue",
        fontsize=9.5,
        weight="bold",
        bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="blue", lw=1.3),
        arrowprops=dict(arrowstyle="->", color="blue", lw=1.3),
        zorder=20
    )

    z_unique = np.unique(np.round(zs, 6))
    z_text = f"Z level = {z_unique[0]:.3f} m" if len(z_unique) == 1 else "Multiple Z levels"

    ax.set_title(f"{title}\n{z_text}", fontsize=12, weight="bold")
    ax.set_xlabel("X Coordinate (m)")
    ax.set_ylabel("Y Coordinate (m)")
    ax.grid(True, alpha=0.22)
    ax.set_axisbelow(True)

    if equal_aspect:
        ax.set_aspect("equal", adjustable="box")

    xpad = (xs.max() - xs.min()) * 0.12 if xs.max() != xs.min() else 1.0
    ypad = (ys.max() - ys.min()) * 0.12 if ys.max() != ys.min() else 1.0
    ax.set_xlim(xs.min() - xpad, xs.max() + xpad)
    ax.set_ylim(ys.min() - ypad, ys.max() + ypad)

    plt.tight_layout()

    if show:
        plt.show()

    return fig, ax, bin_edges

# =========================================================
# PLOTLY 3D HELPERS
# =========================================================
def interpolate_color(val, vmin, vmax, colorscale=None):
    if colorscale is None:
        colorscale = [
            [0.00, "#440154"],
            [0.17, "#3b528b"],
            [0.33, "#21918c"],
            [0.50, "#5ec962"],
            [0.67, "#fde725"],
            [0.83, "#f8961e"],
            [1.00, "#d00000"],
        ]

    if vmax == vmin:
        return colorscale[-1][1]

    t = (val - vmin) / (vmax - vmin)
    t = max(0.0, min(1.0, t))

    for idx in range(len(colorscale) - 1):
        t0, c0 = colorscale[idx]
        t1, c1 = colorscale[idx + 1]
        if t0 <= t <= t1:
            frac = 0 if t1 == t0 else (t - t0) / (t1 - t0)

            def hex_to_rgb(h):
                h = h.lstrip("#")
                return tuple(int(h[j:j + 2], 16) for j in (0, 2, 4))

            r0, g0, b0 = hex_to_rgb(c0)
            r1, g1, b1 = hex_to_rgb(c1)

            r = int(r0 + frac * (r1 - r0))
            g = int(g0 + frac * (g1 - g0))
            b = int(b0 + frac * (b1 - b0))
            return f"rgb({r},{g},{b})"

    return colorscale[-1][1]

def add_3d_bar(fig, x, y, z0, dz, dx, dy, color, opacity=0.96):
    x0 = x - dx / 2
    x1 = x + dx / 2
    y0 = y - dy / 2
    y1 = y + dy / 2
    z1 = z0 + dz

    vertices = np.array([
        [x0, y0, z0],  # 0
        [x1, y0, z0],  # 1
        [x1, y1, z0],  # 2
        [x0, y1, z0],  # 3
        [x0, y0, z1],  # 4
        [x1, y0, z1],  # 5
        [x1, y1, z1],  # 6
        [x0, y1, z1],  # 7
    ])

    i = [0, 0, 0, 1, 1, 2, 4, 4, 5, 5, 6, 7]
    j = [1, 2, 3, 2, 5, 3, 5, 7, 6, 1, 7, 4]
    k = [2, 3, 4, 5, 6, 6, 6, 6, 7, 5, 3, 0]

    fig.add_trace(go.Mesh3d(
        x=vertices[:, 0],
        y=vertices[:, 1],
        z=vertices[:, 2],
        i=i,
        j=j,
        k=k,
        color=color,
        opacity=opacity,
        flatshading=True,
        hoverinfo="skip",
        showscale=False
    ))

# =========================================================
# PLOTLY 3D MAIN PLOT
# =========================================================
def plot_force_3d_plotly(
    node_xy_force,
    title="Foundation Reactions at Lowest Z Nodes",
    unit="kN",
    html_path=None,
    auto_open=True,
    show_all_node_labels=False,
    top_n_labels=8,
    show_max_min_only=True
):
    """
    node_xy_force: [[node, X, Y, Z, force], ...]
    """
    arr = np.array(node_xy_force, dtype=float)
    if arr.size == 0:
        raise ValueError("node_xy_force is empty.")

    nodes = arr[:, 0].astype(int)
    xs = arr[:, 1]
    ys = arr[:, 2]
    f = arr[:, 4]

    x_min, x_max = float(np.min(xs)), float(np.max(xs))
    y_min, y_max = float(np.min(ys)), float(np.max(ys))
    f_min, f_max = float(np.min(f)), float(np.max(f))

    x_range = max(x_max - x_min, 1.0)
    y_range = max(y_max - y_min, 1.0)
    z_range_raw = max(abs(f_min), abs(f_max), 1.0)

    f_abs = np.abs(f)
    fmax_abs = max(np.max(f_abs), 1.0)
    vmin = float(np.min(f_abs))
    vmax = float(np.max(f_abs))

    unique_x = np.unique(np.round(xs, 6))
    unique_y = np.unique(np.round(ys, 6))

    if len(unique_x) > 1:
        dx = 0.45 * np.min(np.diff(np.sort(unique_x)))
    else:
        dx = x_range * 0.08

    if len(unique_y) > 1:
        dy = 0.45 * np.min(np.diff(np.sort(unique_y)))
    else:
        dy = y_range * 0.08

    dx = max(dx, 0.60)
    dy = max(dy, 0.60)

    sort_idx = np.argsort(np.abs(f))
    nodes_s = nodes[sort_idx]
    xs_s = xs[sort_idx]
    ys_s = ys[sort_idx]
    f_s = f[sort_idx]

    fig = go.Figure()

    # Determine which nodes get text labels
    label_nodes = set()
    if show_all_node_labels:
        label_nodes = set(nodes.tolist())
    else:
        top_idx = np.argsort(np.abs(f))[-top_n_labels:]
        label_nodes = set(nodes[top_idx].tolist())

    # Add bars
    for node, x, y, force in zip(nodes_s, xs_s, ys_s, f_s):
        color = interpolate_color(abs(force), vmin, vmax)

        if force >= 0:
            z0 = 0.0
            dz = float(force)
        else:
            z0 = float(force)
            dz = abs(float(force))

        add_3d_bar(fig, x, y, z0, dz, dx, dy, color, opacity=0.96)

        if node in label_nodes and not show_max_min_only:
            label_z = force + 0.025 * fmax_abs if force >= 0 else force - 0.025 * fmax_abs
            fig.add_trace(go.Scatter3d(
                x=[x],
                y=[y],
                z=[label_z],
                mode="text",
                text=[f"N{node}<br>{force:.0f}"],
                textfont=dict(size=8, color="black"),
                showlegend=False,
                hoverinfo="skip"
            ))

    # Ground plane
    xpad = max(x_range * 0.10, 2.0)
    ypad = max(y_range * 0.10, 2.0)

    plane_x = [x_min - xpad, x_max + xpad, x_max + xpad, x_min - xpad]
    plane_y = [y_min - ypad, y_min - ypad, y_max + ypad, y_max + ypad]
    plane_z = [0, 0, 0, 0]

    fig.add_trace(go.Mesh3d(
        x=plane_x,
        y=plane_y,
        z=plane_z,
        i=[0, 0],
        j=[1, 2],
        k=[2, 3],
        color="lightgray",
        opacity=0.16,
        hoverinfo="skip",
        showscale=False
    ))

    # Max / min callout
    i_max = int(np.argmax(f))
    i_min = int(np.argmin(f))

    fig.add_trace(go.Scatter3d(
        x=[xs[i_max]],
        y=[ys[i_max]],
        z=[f[i_max] + 0.10 * fmax_abs],
        mode="text",
        text=[f"MAX = {f[i_max]:.2f} {unit}"],
        textfont=dict(size=12, color="red"),
        showlegend=False,
        hoverinfo="skip"
    ))

    fig.add_trace(go.Scatter3d(
        x=[xs[i_min]],
        y=[ys[i_min]],
        z=[f[i_min] - 0.10 * fmax_abs if f[i_min] < 0 else 0.10 * fmax_abs],
        mode="text",
        text=[f"MIN = {f[i_min]:.2f} {unit}"],
        textfont=dict(size=12, color="blue"),
        showlegend=False,
        hoverinfo="skip"
    ))

    # Invisible hover / colorbar trace
    fig.add_trace(go.Scatter3d(
        x=xs,
        y=ys,
        z=np.where(f >= 0, f, 0),
        mode="markers",
        marker=dict(
            size=4,
            color=np.abs(f),
            colorscale="Turbo",
            cmin=vmin,
            cmax=vmax,
            colorbar=dict(
                title=f"Reaction ({unit})",
                thickness=18,
                len=0.78,
                x=1.02
            ),
            showscale=True,
            opacity=0.02
        ),
        hovertemplate=(
            "Node: %{text}<br>"
            "X: %{x:.3f} m<br>"
            "Y: %{y:.3f} m<br>"
            f"Reaction: %{{customdata:.3f}} {unit}<extra></extra>"
        ),
        text=[str(n) for n in nodes],
        customdata=f,
        showlegend=False
    ))

    # Better aspect ratio
    base_xy = max(x_range, y_range)
    z_visual = min(z_range_raw, 0.65 * base_xy)

    aspect_x = x_range / base_xy
    aspect_y = y_range / base_xy
    aspect_z = z_visual / base_xy

    aspect_x = max(aspect_x, 0.9)
    aspect_y = max(aspect_y, 0.9)
    aspect_z = max(aspect_z, 0.45)

    z_low = min(f_min - 0.12 * fmax_abs, -0.05 * fmax_abs if f_min < 0 else 0)
    z_high = f_max + 0.15 * fmax_abs

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=22)
        ),
        scene=dict(
            xaxis=dict(
                title="X Coordinate (m)",
                range=[x_min - xpad, x_max + xpad],
                backgroundcolor="rgb(245,245,245)",
                showbackground=True,
                gridcolor="lightgray",
                zeroline=False
            ),
            yaxis=dict(
                title="Y Coordinate (m)",
                range=[y_min - ypad, y_max + ypad],
                backgroundcolor="rgb(245,245,245)",
                showbackground=True,
                gridcolor="lightgray",
                zeroline=False
            ),
            zaxis=dict(
                title=f"Reaction ({unit})",
                range=[z_low, z_high],
                backgroundcolor="rgb(250,250,250)",
                showbackground=True,
                gridcolor="lightgray",
                zeroline=True,
                zerolinecolor="black",
                zerolinewidth=4
            ),
            aspectmode="manual",
            aspectratio=dict(
                x=aspect_x * 1.35,
                y=aspect_y * 1.35,
                z=aspect_z * 0.90
            ),
            camera=dict(
                eye=dict(x=1.85, y=1.65, z=0.95),
                center=dict(x=0.0, y=0.0, z=-0.05)
            )
        ),
        template="plotly_white",
        margin=dict(l=20, r=20, t=70, b=20),
        width=1400,
        height=850
    )

    if html_path:
        pio.write_html(fig, file=html_path, auto_open=auto_open)
        print(f"Plotly HTML saved to: {html_path}")

    fig.show()
    return fig

# =========================================================
# SUMMARY TABLE
# =========================================================
def print_top_reactions(foundation_data, force_component, top_n=10):
    print(f"\n=== TOP {top_n} ABSOLUTE {force_component} REACTIONS ===")
    for row in sorted(foundation_data, key=lambda r: abs(r[4]), reverse=True)[:top_n]:
        print(
            f"Node {int(row[0])} | "
            f"X={row[1]:.3f} m | "
            f"Y={row[2]:.3f} m | "
            f"Z={row[3]:.3f} m | "
            f"{force_component}={row[4]:.3f}"
        )

# =========================================================
# MAIN WORKFLOW
# =========================================================
def main():
    # 1. Read node database
    node_data = MidasAPI("GET", "/db/node", {})

    # 2. Detect lowest Z nodes automatically
    z_min, lowest_nodes_data = get_lowest_z_nodes(node_data, tol=Z_TOL)
    lowest_node_ids = [row[0] for row in lowest_nodes_data]

    print("\n=== LOWEST Z NODE DETECTION ===")
    print(f"Lowest Z level : {z_min:.6f}")
    print(f"Node count     : {len(lowest_node_ids)}")
    print(f"Node IDs       : {lowest_node_ids}")

    # 3. Run analysis
    runAnalysis()

    # 4. Request reaction table
    reaction_request = build_reaction_request(
        node_ids=lowest_node_ids,
        load_case_name=LOAD_CASE_NAME,
        export_path=EXPORT_PATH
    )
    reaction_out = MidasAPI("POST", "/post/TABLE", reaction_request)

    print("\nREACTION RESPONSE KEYS:")
    print(reaction_out.keys())

    # 5. Extract selected force component
    force_out = getforce(lowest_node_ids, FORCE_COMPONENT, reaction_out)

    print(f"\n=== EXTRACTED {FORCE_COMPONENT} REACTIONS ===")
    print(force_out)

    # 6. Merge coordinates + reaction
    foundation_data = combine_node_xyz_force(
        lowest_nodes_data,
        force_out,
        filter_zero=FILTER_ZERO_REACTION,
        zero_tol=ZERO_FORCE_TOL
    )

    if not foundation_data:
        raise ValueError(
            "No foundation data found after combining node coordinates and reactions.\n"
            "Check whether lowest Z nodes really have supports/reactions.\n"
            "You may also try FILTER_ZERO_REACTION = False."
        )

    print("\n=== FOUNDATION DATA ===")
    for row in foundation_data:
        print(row)

    # 7. Summary
    print_top_reactions(foundation_data, FORCE_COMPONENT, top_n=10)

    # 8. Unit label
    unit_label = "kN" if FORCE_COMPONENT in ["FX", "FY", "FZ"] else "kN.m"

    # 9. 2D plan plot
    if SHOW_MATPLOTLIB_2D:
        plot_force_plan_simplified(
            foundation_data,
            title=f"{FORCE_COMPONENT} Reactions at Lowest Z Nodes",
            unit=unit_label,
            target_bins=TARGET_BINS,
            fig_size=(9, 9),
            show=True
        )

    # 10. 3D plotly plot
    if SHOW_PLOTLY_3D:
        plot_force_3d_plotly(
            foundation_data,
            title=f"{FORCE_COMPONENT} Reactions at Lowest Z Nodes",
            unit=unit_label,
            html_path=PLOTLY_HTML_PATH,
            auto_open=AUTO_OPEN_PLOTLY_HTML,
            show_all_node_labels=SHOW_ALL_NODE_LABELS,
            top_n_labels=TOP_N_LABELS,
            show_max_min_only=SHOW_MAX_MIN_ONLY
        )

# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    main()