import requests
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

    # always print raw text first when debugging
    print("Raw response:")
    print(response.text)

    try:
        result = response.json()
    except Exception:
        response.raise_for_status()
        return None

    print("JSON response:")
    print(json.dumps(result, indent=2))
    response.raise_for_status()
    return result


# -----------------------------------
# 1) Read existing structure groups
# -----------------------------------
def get_structure_groups():
    print("Getting existing Structure Groups...")
    return MidasAPI("GET", "/db/GRUP")


# -----------------------------------
# 2) Create structure group
# -----------------------------------
def create_structure_group(group_id, name, p_type=0, n_list=None, e_list=None):
    if n_list is None:
        n_list = []
    if e_list is None:
        e_list = []

    body = {
        "Assign": {
            str(group_id): {
                "NAME": name,
                "P_TYPE": p_type,
                "N_LIST": n_list,
                "E_LIST": e_list
            }
        }
    }

    print("Creating Structure Group...")
    print(json.dumps(body, indent=2))
    return MidasAPI("POST", "/db/GRUP", body)


# -----------------------------------
# 3) Update structure group
# -----------------------------------
def update_structure_group(group_id, name, p_type=0, n_list=None, e_list=None):
    if n_list is None:
        n_list = []
    if e_list is None:
        e_list = []

    body = {
        "Assign": {
            str(group_id): {
                "NAME": name,
                "P_TYPE": p_type,
                "N_LIST": n_list,
                "E_LIST": e_list
            }
        }
    }

    print("Updating Structure Group...")
    print(json.dumps(body, indent=2))
    return MidasAPI("PUT", "/db/GRUP", body)


# -----------------------------------
# TEST FLOW
# -----------------------------------
# Step 1: check whether endpoint responds
try:
    get_out = get_structure_groups()
    print("GET OUTPUT:")
    print(get_out)
except Exception as e:
    print("GET failed:")
    print(e)

# Step 2: try smallest valid payload first
# use EMPTY lists first to isolate whether bad IDs are causing 400
try:
    create_out = create_structure_group(
        group_id=999,
        name="TEST_GROUP",
        p_type=0,
        n_list=[],
        e_list=[]
    )
    print("CREATE OUTPUT:")
    print(create_out)
except Exception as e:
    print("CREATE failed:")
    print(e)

# Step 3: if empty works, try real IDs
# try:
#     create_out = create_structure_group(
#         group_id=1000,
#         name="CENTER_",
#         p_type=0,
#         n_list=[1, 2, 3],
#         e_list=[1, 2, 3]
#     )
#     print("CREATE OUTPUT:")
#     print(create_out)
# except Exception as e:
#     print("CREATE with IDs failed:")
#     print(e)