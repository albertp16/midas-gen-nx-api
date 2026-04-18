import requests
import pandas as pd

# =========================================================
# MIDAS Open API
# =========================================================
def MidasAPI(method, command, body=None):
    base_url = "https://moa-engineers.midasit.com:443/gen"
    mapi_key = "eyJ1ciI6IkFsYmVydFBhbW9uYWciLCJwZyI6ImdlbiIsImNuIjoiQldiby12dG1RQSJ9.12b57179a60ebf634b50081504bdf1a45e158893fd8306ce0b78ed5a9ef557ed"

    url = base_url + command
    headers = {
        "Content-Type": "application/json",
        "MAPI-Key": mapi_key
    }

    method = method.upper()

    if method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "POST":
        response = requests.post(url=url, headers=headers, json=body)
    elif method == "PUT":
        response = requests.put(url=url, headers=headers, json=body)
    elif method == "DELETE":
        response = requests.delete(url=url, headers=headers)
    else:
        raise ValueError(f"Unsupported method: {method}")

    # Better error reporting
    if not response.ok:
        print("Status Code:", response.status_code)
        print("Response Text:", response.text)
        response.raise_for_status()

    return response.json()


# =========================================================
# GET MEMBER ASSIGNMENT
# Endpoint: /db/MEMB
# =========================================================
member_data = MidasAPI("GET", "/db/MEMB")

print("Raw response:")
print(member_data)

# =========================================================
# Convert to DataFrame
# =========================================================
# Usually the returned records are under "MEMB" or similar
memb_dict = member_data.get("MEMB", member_data.get("Assign", {}))

rows = []
for member_id, member_info in memb_dict.items():
    rows.append({
        "Member_ID": int(member_id),
        "AELEM": member_info.get("AELEM", []),
        "bREVERSE": member_info.get("bREVERSE", False)
    })

df_member = pd.DataFrame(rows)

print("\nMember Assignment Table:")
print(df_member)