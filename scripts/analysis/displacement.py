import requests
import pandas as pd
import matplotlib.pyplot as plt
import re
import json

# -----------------------------------
# MIDAS Open API function
# -----------------------------------
def MidasAPI(method, command, body=None):
    base_url = "https://moa-engineers.midasit.com:443/gen"
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
        raise ValueError(f"Unsupported method: {method}")

    print(f"{method} {command} -> {response.status_code}")

    try:
        result = response.json()
    except Exception:
        print("Raw response text:")
        print(response.text)
        response.raise_for_status()

    print("JSON response:")
    print(json.dumps(result, indent=2))

    response.raise_for_status()
    return result


# -----------------------------------
# Run analysis
# -----------------------------------
def runAnalysis():
    print("Performing Run Analysis in Midas Gen...")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis completed.")


# -----------------------------------
# Story displacement request
# try the SAME load case that already works in drift
# -----------------------------------
# disp_obj = {
#     "Argument": {
#         "TABLE_NAME": "STORY_DISPLACEMENT_X",
#         "TABLE_TYPE": "STORY_DISPLACEMENT_X",
#         "UNIT": {
#             "FORCE": "KN",
#             "DIST": "MM"
#         },
#         "LOAD_CASE_NAMES": ["Ex(ST)"],
#         "STYLES": {
#             "FORMAT": "FIXED",
#             "PLACE": 5
#         }
#     }
# }

disp_obj = {
    "Argument": {
        "TABLE_NAME": "STORY_DISPLACEMENT_X",
        "TABLE_TYPE": "STORY_DISPLACEMENT_X",
        "UNIT": {
            "FORCE": "kN",
            "DIST": "m"
        },
        "STYLES": {
            "FORMAT": "Fixed",
            "PLACE": 4
        },
        "LOAD_CASE_NAMES": [
            "Ex (ST)"
        ]
    }
}  

# -----------------------------------
# Run and get results
# -----------------------------------
runAnalysis()
disp_out = MidasAPI("POST", "/post/TABLE", disp_obj)
print(disp_out)
