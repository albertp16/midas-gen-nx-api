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
            "PLACE": 12
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
                1
            ]
        },
        "LOAD_CASE_NAMES": [
            "Ex +(ST)"
        ]
    }
}

# irregular = {
#     "Argument": {
#         "COUNTRY_CODE": "NSCP2015",
#         "STORY_DRIFT_METHOD": "Max.DriftofOuterExtremePoints",
#         "STORY_STIFFNESS_METHOD": "1/StoryDriftRatio"
#         # "SEISMIC_BEHAVIOR_FACTOR": "3orbelow"  # optional
#     }
# }

file_open = MidasAPI("POST", "/doc/open", file_loc)
print("OPEN RESPONSE:", file_open)
run = MidasAPI("POST", "/doc/ANAL", {})
reaction_out = MidasAPI("POST", "/post/TABLE", reaction)
print("REACTION RESPONSE:", reaction_out)





