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
# =========================================================
def interpret_size(shape, vsize):
    if not vsize:
        return None

    try:
        if shape in ["RECT", "SB"]:
            b = vsize[0]
            h = vsize[1]
            return f"{int(b)}x{int(h)}"

        elif shape in ["I", "H"]:
            h = vsize[0]
            b = vsize[1]
            return f"H{int(h)}x{int(b)}"

        elif shape == "C":
            h = vsize[0]
            b = vsize[1]
            return f"C{int(h)}x{int(b)}"

        else:
            return str(vsize)

    except Exception:
        return str(vsize)


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
        vsize = sect_i.get("vSIZE")

        size_clean = interpret_size(shape, vsize)

        results.append({
            "ID": int(sid),
            "Name": sect.get("SECT_NAME"),
            "Shape": shape,
            "Size": size_clean
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