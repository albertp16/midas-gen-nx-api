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

    if method == "POST":
        response = requests.post(url=url, headers=headers, json=body)
    elif method == "PUT":
        response = requests.put(url=url, headers=headers, json=body)
    elif method == "GET":
        response = requests.get(url=url, headers=headers)
    elif method == "DELETE":
        response = requests.delete(url=url, headers=headers)
    else:
        raise ValueError(f"Unsupported HTTP method: {method}")

    print(f"{method} {command} -> {response.status_code}")

    try:
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print("HTTP Error:", e)
        print("Response text:", response.text)
        raise
    except Exception:
        print("Non-JSON response:", response.text)
        raise


# =========================================================
# GET SECTION DB
# =========================================================
def get_sect_db():
    res = MidasAPI("GET", "/db/SECT")
    return res.get("SECT", {})


# =========================================================
# INTERPRET SIZE
# vSIZE[0] = HEIGHT
# vSIZE[1] = WIDTH
# MIDAS values appear to be in meters, so convert to mm
# =========================================================
def interpret_size(shape, vsize):
    if not vsize or len(vsize) < 2:
        return None, None, None

    try:
        height_mm = round(float(vsize[0]) * 1000)
        width_mm = round(float(vsize[1]) * 1000)

        if shape == "SB":
            return height_mm, width_mm, f"{width_mm}x{height_mm}"

        return height_mm, width_mm, f"{width_mm}x{height_mm}"

    except Exception:
        return None, None, str(vsize)


# =========================================================
# GET ALL SECTIONS
# =========================================================
def get_all_sections_clean():
    sect_db = get_sect_db()
    results = []

    for sid, sect in sect_db.items():
        sect_before = sect.get("SECT_BEFORE", {})
        sect_i = sect_before.get("SECT_I", {})

        shape = sect_before.get("SHAPE")
        datatype = sect_before.get("DATATYPE")
        vsize = sect_i.get("vSIZE", [])

        height_mm, width_mm, size_text = interpret_size(shape, vsize)

        results.append({
            "ID": int(sid),
            "Name": sect.get("SECT_NAME"),
            "Shape": shape,
            "DataType": datatype,
            "Height_mm": height_mm,
            "Width_mm": width_mm,
            "Size": size_text
        })

    df = pd.DataFrame(results)

    if not df.empty:
        df = df.sort_values("ID").reset_index(drop=True)

    return df


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    df = get_all_sections_clean()

    print("\n=== SECTION DIMENSIONS ===")
    print(df.to_string(index=False))