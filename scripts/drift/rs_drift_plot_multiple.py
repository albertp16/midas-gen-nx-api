import requests
import pandas as pd
import matplotlib.pyplot as plt
import re
import numpy as np

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


def runAnalysis():
    print("Performing Run Analysis in Midas Gen...")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis completed.")


def story_no(s):
    s = str(s).strip().upper()
    if "ROOF" in s:
        return 999
    m = re.search(r"(\d+)", s)
    return int(m.group(1)) if m else -1


def get_story_drift_df(load_case_name, table_type="STORY_DRIFT_X"):
    drift_obj = {
        "Argument": {
            "TABLE_TYPE": table_type,
            "UNIT": {
                "FORCE": "KN",
                "DIST": "MM"
            },
            "LOAD_CASE_NAMES": [load_case_name],
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

    drift_out = MidasAPI("POST", "/post/TABLE", drift_obj)

    headers = drift_out["empty"]["HEAD"]
    data = drift_out["empty"]["DATA"]
    df = pd.DataFrame(data, columns=headers)

    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except:
            pass

    df["StoryNo"] = df["Story"].apply(story_no)
    df = df.sort_values("StoryNo")

    return df


# -----------------------------------
# MAIN
# -----------------------------------
runAnalysis()

load_cases = ["RS-M(RS)"]
col_ratio = "Maximum Drift of All Vertical Elements/Story Drift Ratio"
col_height = "Story Height"

plot_frames = []

for lc in load_cases:
    df = get_story_drift_df(lc, table_type="STORY_DRIFT_X").copy()

    # convert height to meters
    df[col_height] = df[col_height].astype(float) / 1000.0

    # cumulative elevation
    df["Elevation_m"] = df[col_height].cumsum()

    df["LoadCase"] = lc

    # reciprocal drift = 1 / drift ratio
    df["ReciprocalDrift"] = np.where(
        df[col_ratio].astype(float) > 0,
        1.0 / df[col_ratio].astype(float),
        np.nan
    )

    plot_frames.append(df)

df_all = pd.concat(plot_frames, ignore_index=True)

# allowable drift ratio and reciprocal
allowable_ratio = 0.025
allowable_recip = 1.0 / allowable_ratio

# -----------------------------------
# PLOT
# -----------------------------------
plt.figure(figsize=(7, 9))

for lc in load_cases:
    temp = df_all[df_all["LoadCase"] == lc].sort_values("Elevation_m")
    x = temp["ReciprocalDrift"]
    y = temp["Elevation_m"]

    plt.plot(x, y, marker="o", linewidth=2, markersize=5, label=lc)

plt.axvline(
    allowable_recip,
    linestyle="--",
    linewidth=1.8,
    label="Elastic Drift Limit"
)

plt.xlabel("1 / Drift Ratio")
plt.ylabel("Elevation (m)")
plt.title("Seismic Drift Values Response Spectrum Case")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.show()