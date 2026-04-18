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


def runAnalysis():
    print("Performing Run Analysis in Midas Gen...")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis completed.")


def story_no(s):
    s = str(s).strip().upper()
    if "BASE" in s:
        return 0
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

load_cases = ["Ex(ST)", "EX +(ST)","EX -(ST)"]
col_ratio = "Maximum Drift of All Vertical Elements/Story Drift Ratio"

plot_frames = []

for lc in load_cases:
    df = get_story_drift_df(lc, table_type="STORY_DRIFT_X")

    base_row = pd.DataFrame([{
        "Story": "Base",
        "StoryNo": 0,
        col_ratio: 0.0
    }])

    df_plot = pd.concat([base_row, df], ignore_index=True)
    df_plot = df_plot.sort_values("StoryNo").copy()
    df_plot["LoadCase"] = lc

    plot_frames.append(df_plot)

df_all = pd.concat(plot_frames, ignore_index=True)

# Use one reference list of stories for y-axis
story_ref = (
    df_all[["StoryNo", "Story"]]
    .drop_duplicates()
    .sort_values("StoryNo")
)

# Give roof a better numeric spacing
story_ref["PlotY"] = range(len(story_ref))

story_map = dict(zip(story_ref["StoryNo"], story_ref["PlotY"]))
label_map = dict(zip(story_ref["PlotY"], story_ref["Story"]))

df_all["PlotY"] = df_all["StoryNo"].map(story_map)

# -----------------------------------
# PLOT
# -----------------------------------
plt.figure(figsize=(7, 9))

for lc in load_cases:
    temp = df_all[df_all["LoadCase"] == lc].sort_values("PlotY")
    x = temp[col_ratio].astype(float).abs()
    y = temp["PlotY"]

    plt.plot(x, y, marker="o", linewidth=2, markersize=5, label=lc)

plt.axvline(0.020, linestyle="--", linewidth=1.5, label="Allowable Drift")

plt.yticks(story_ref["PlotY"], story_ref["Story"])
plt.xlabel("Drift Ratio")
plt.ylabel("Story")
plt.title("Story Drift Ratio - X Direction")
plt.grid(True, linestyle="--", alpha=0.4)
plt.legend()
plt.tight_layout()
plt.show()