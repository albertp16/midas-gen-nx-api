import requests
import json

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
MAPI_KEY = "eyJ1ciI6IkFsYmVydFBhbW9uYWciLCJwZyI6ImdlbiIsImNuIjoiQldiby12dG1RQSJ9.12b57179a60ebf634b50081504bdf1a45e158893fd8306ce0b78ed5a9ef557ed"


def MidasAPI(method, command, body=None):
    url = BASE_URL + command
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": MAPI_KEY
    }

    method = method.upper()
    if method == "GET":
        r = requests.get(url, headers=headers)
    elif method == "POST":
        r = requests.post(url, headers=headers, json=body)
    elif method == "PUT":
        r = requests.put(url, headers=headers, json=body)
    elif method == "DELETE":
        r = requests.delete(url, headers=headers, json=body)
    else:
        raise ValueError(f"Unsupported method: {method}")

    print(f"{method} {command} -> {r.status_code}")
    print(r.text)
    r.raise_for_status()

    if r.text.strip():
        return r.json()
    return {}

# 1) open the exact model first
open_out = MidasAPI("POST", "/doc/OPEN", {
    "Argument": r"C:\path\to\your_model.mgb"
})

# 2) optional: verify there are elements / sections in the file
elem_out = MidasAPI("GET", "/db/ELEM")

# 3) read RCHK
rchk_out = MidasAPI("GET", "/db/RCHK")

# 4) interpret response
if rchk_out.get("message") == "error status":
    print("RCHK exists, but the current model has no readable rebar-checking data.")
    print("Check in MIDAS UI: Design > RC Design > Rebar Input for Checking")
elif "RCHK" in rchk_out:
    print(json.dumps(rchk_out["RCHK"], indent=2))
else:
    print("Unexpected response:", rchk_out)