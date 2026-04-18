# -*- coding: utf-8 -*-
"""
Created on Sat Jan 17 16:08:00 2026

@author: alber
"""

# function for MIDAS Open API

import requests
import pandas as pd

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

beam_anal_force = {
        "Argument": {
            "TABLE_NAME": "BeamForce",
            "TABLE_TYPE": "BEAMFORCE",
            "UNIT": {
                "FORCE": "kN",
                "DIST": "m"
            },
            "STYLES": {
                "FORMAT": "Fixed",
                "PLACE": 3
            },
            "COMPONENTS": [
                "Elem",
                "Load",
                "Part",
                "Axial",
                "Shear-y",
                "Shear-z",
                "Torsion",
                "Moment-y",
                "Moment-z",
                "Bi-Moment",
                "T-Moment",
                "W-Moment"
            ],
            "NODE_ELEMS": {
                "KEYS": [
                    1,
                    2,
                    3
                ]
            },
            "LOAD_CASE_NAMES": [
                "RC ENV_STR (CB:max)"
            ],
            "PARTS": [
                "PartI",
                "PartJ"
            ]
        }
    }

run = MidasAPI("POST", "/doc/ANAL", {})
beam_anal_out = MidasAPI("POST", "/post/TABLE", beam_anal_force)
df = pd.DataFrame(beam_anal_out["BeamForce"]["DATA"], columns=beam_anal_out["BeamForce"]["HEAD"])
print(df)