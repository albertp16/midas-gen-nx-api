# -*- coding: utf-8 -*-
"""
Created on Sun Mar 22 20:12:20 2026

@author: alber
"""

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

    response.raise_for_status()
    return response.json()


# =========================================================
# GET STORY DATA
# Endpoint: /db/STOR
# =========================================================
story_data = MidasAPI("GET", "/db/STOR")

print("Raw response:")
print(story_data)

# =========================================================
# Convert to DataFrame
# =========================================================
# Usually the returned records are under a key like "STOR"
stor_dict = story_data.get("STOR", {})

rows = []
for story_id, story_info in stor_dict.items():
    row = {"ID": story_id}
    row.update(story_info)
    rows.append(row)

df_story = pd.DataFrame(rows)

# Optional: sort by story level if available
if "STORY_LEVEL" in df_story.columns:
    df_story = df_story.sort_values("STORY_LEVEL").reset_index(drop=True)

print("\nStory Data Table:")
print(df_story)