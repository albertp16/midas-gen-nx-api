# -*- coding: utf-8 -*-
"""
Created on Sat Jan 17 15:33:40 2026

@author: albert pamonag
"""

import requests


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

def runAnalysis():
    print("Performing Run Analysis in Midas Gen")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis is completed!!!")

runAnalysis()
node_data = MidasAPI("GET", "/db/node", {})
# print(node_data)
element_data = MidasAPI("GET", "/db/elem", {})
# print(element_data)

import math

def _node_xyz(node_dict, node_id):
    """Return (x,y,z) tuple for a node_id, or None if not found."""
    n = node_dict.get(str(node_id)) or node_dict.get(int(node_id), None)
    if not n:
        return None
    return (float(n["X"]), float(n["Y"]), float(n["Z"]))

def element_lengths(nodes_payload, elems_payload, unit="m", include_types=("BEAM",)):
    """
    Compute element lengths based on NODE coordinates.

    Parameters
    ----------
    nodes_payload : dict
        e.g. {"NODE": {...}}
    elems_payload : dict
        e.g. {"ELEM": {...}}
    unit : str
        Just a label for printing ("m", "mm", etc.)
    include_types : tuple[str]
        Element TYPE filter (e.g., ("BEAM","TRUSS")).

    Returns
    -------
    rows : list[dict]
        Each row has: ElemID, Type, iNode, jNode, L(<unit>), Sect, Matl
    summary : dict
        Counts and totals.
    """
    node_dict = nodes_payload.get("NODE", {})
    elem_dict = elems_payload.get("ELEM", {})

    rows = []
    skipped = []

    for eid_str, e in elem_dict.items():
        etype = e.get("TYPE", "")
        if include_types and etype not in include_types:
            continue

        # MIDAS style: NODE array typically begins with [i, j, ...]
        conn = e.get("NODE", [])
        if not conn or len(conn) < 2:
            skipped.append((eid_str, "No/short NODE connectivity"))
            continue

        i_id, j_id = conn[0], conn[1]

        # Some entries might use 0 as placeholder (not a real node)
        if i_id in (0, "0") or j_id in (0, "0"):
            skipped.append((eid_str, f"Invalid end node (i={i_id}, j={j_id})"))
            continue

        pi = _node_xyz(node_dict, i_id)
        pj = _node_xyz(node_dict, j_id)

        if pi is None or pj is None:
            skipped.append((eid_str, f"Missing node coord (i={i_id}, j={j_id})"))
            continue

        dx = pj[0] - pi[0]
        dy = pj[1] - pi[1]
        dz = pj[2] - pi[2]
        L = math.sqrt(dx*dx + dy*dy + dz*dz)

        rows.append({
            "ElemID": int(eid_str),
            "Type": etype,
            "iNode": int(i_id),
            "jNode": int(j_id),
            f"L({unit})": L,
            "Sect": e.get("SECT", None),
            "Matl": e.get("MATL", None),
        })

    rows.sort(key=lambda r: r["ElemID"])

    total_len = sum(r[f"L({unit})"] for r in rows)
    summary = {
        "count": len(rows),
        "skipped": len(skipped),
        f"total_L({unit})": total_len,
        "skipped_details": skipped[:20],  # preview only
    }
    return rows, summary


# -----------------------------
# USAGE (paste your dicts here)
# -----------------------------
nodes_payload = node_data  # your first dict: {"NODE": {...}}
elems_payload = element_data  # your second dict: {"ELEM": {...}}

rows, summary = element_lengths(nodes_payload, elems_payload, unit="m", include_types=("BEAM",))
print("Summary:", summary)
for r in rows[:293]:
    print(r)


# element_data = MidasAPI("GET", "/db/elem", {})
# print(element_data)

# code = {
#     "Assign": {
#         "1": {
#             "DGNCODE": "NSCP 2015"
#         }
#     }
# }

# print(MidasAPI("GET", "/db/dcon",code))

# test = {
#     "Argument": {
#         "TABLE_TYPE": "BEAMFORCES",
#         "EXPORT_PATH": r"C:\Users\alber\Desktop\4S Apartment\midas\beam.JSON",
#         "UNIT": {
#             "FORCE": "KN",
#             "DIST": "M"
#         },
#         "STYLES": {
#             "FORMAT": "Fixed",
#             "PLACE": 3
#         },
#         "NODE_ELEMS": {
#             "KEYS": [
#                 177
#             ]
#         },
#         "PARTS": [
#             "PartI",
#             "PartJ"
#         ],
#         "LOAD_CASE_NAMES": [
#             "DL(ST)"
#         ],
#         "COMPONENTS": [
#             "Memb",
#             "Part",
#             "LComName",
#             "Type",
#             "Fz",
#             "Mx",
#             "My(-)",
#             "My(+)"
#         ]
#     }
# }

# table_beam = MidasAPI("POST", "/post/table", test)
# print(table_beam)