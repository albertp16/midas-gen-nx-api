import requests
import pandas as pd
import matplotlib.pyplot as plt
import re

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
    response.raise_for_status()
    return response.json()


# -----------------------------------
# Run analysis
# -----------------------------------
def runAnalysis():
    print("Performing Run Analysis in Midas Gen...")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis completed.")


# -----------------------------------
# Drift request
# -----------------------------------
drift_obj = {
    "Argument": {
        "TABLE_TYPE": "STORY_DRIFT_X",
        "UNIT": {
            "FORCE": "KN",
            "DIST": "MM"
        },
        "LOAD_CASE_NAMES": ["Ex(ST)"],
        "STYLES": {
            "FORMAT": "FIXED",
            "PLACE": 5
        },
        "ADDITIONAL": {
            "SET_STORY_DRIFT_PARAMS": {
                "RESPONSE_MOD_FACTOR_CHECK": True,
                "SCALE_FACTOR_VALUE": 5.95,
                "ALLOWABLE_RATIO": 0.025
            }
        }
    }
}

# -----------------------------------
# Run and get results
# -----------------------------------
runAnalysis()
drift_out = MidasAPI("POST", "/post/TABLE", drift_obj)
print("DRIFT RESPONSE:", drift_out)

headers = drift_out["empty"]["HEAD"]
data = drift_out["empty"]["DATA"]

df = pd.DataFrame(data, columns=headers)

# safer numeric conversion
for col in df.columns:
    df[col] = pd.to_numeric(df[col], errors="ignore")

# -----------------------------------
# Story sorting
# -----------------------------------
def story_no(s):
    s = str(s).strip().upper()

    if "ROOF" in s:
        return 999
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else -1

df["StoryNo"] = df["Story"].apply(story_no)
df = df.sort_values("StoryNo")

# -----------------------------------
# Correct column names from API
# -----------------------------------
col_max_ratio = "Maximum Drift of All Vertical Elements/Story Drift Ratio"
col_com_ratio = "Drift at the Center of Mass/Story Drift Ratio"

# -----------------------------------
# Add base point (0,0)
# -----------------------------------
base_row = pd.DataFrame([{
    "Story": "Base",
    "StoryNo": 0,
    col_max_ratio: 0.0,
    col_com_ratio: 0.0
}])

df_plot = pd.concat([base_row, df], ignore_index=True)
df_plot = df_plot.sort_values("StoryNo")

x1 = df_plot[col_max_ratio].astype(float).abs()
x2 = df_plot[col_com_ratio].astype(float).abs()
y = df_plot["Story"]

# -----------------------------------
# Plot
# -----------------------------------
plt.figure(figsize=(10, 10))
plt.plot(x1, y, marker="o", linewidth=2, label="Max Vertical Elements")
# plt.plot(x2, y, marker="s", linewidth=2, label="Center of Mass")
plt.axvline(0.020, linestyle="--", linewidth=1.5, label="Allowable Drift = 0.020")

plt.xlabel("Drift Ratio")
plt.ylabel("Story")
plt.title("Story Drift Ratio - X Direction")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()