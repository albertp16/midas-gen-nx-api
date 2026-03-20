# -*- coding: utf-8 -*-
"""
Created on Sun Jan 11 00:05:32 2026

@author: alber
"""


import requests


# function for MIDAS Open API
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

    print(method, command, response.status_code)
    return response.json()

# Unit Setting
unit_dist = "M"     # M, CM, MM, IN, FT
unit_force = "KN"   # KN, N, KGF, TONF, LBF, KIPS

file_loc = {
    "Argument": r"C:\Users\alber\Desktop\4S Apartment\midas\jawod_4s.mgbx"
}

export_path = r"C:\Users\alber\Desktop\4S Apartment\midas\mode.jpg"

baem_obj = {
    "Argument": {
        "TABLE_TYPE": "BEAMDESIGNFORCES",
        "UNIT": {
            "FORCE": "KN",
            "DIST": "M"
        },
        "STYLES": {
            "FORMAT": "Fixed",
            "PLACE": 3
        },
        "PARTS": [
            "PartI",
            "PartJ"
        ],
        "COMPONENTS": [
            "Memb",
            "Part",
            "LComName",
            "Type",
            "Fz",
            "Mx",
            "My(-)",
            "My(+)"
        ]
    }
}


rc_input = {
    "DCON": {
        "1": {
            "DGNCODE": "NSCP 2015"
        }
    }
}


def runAnalysis():
    print("Performing Run Analysis in Midas Gen")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis is completed!!!")
    
# file_open = MidasAPI("POST", "/doc/open", file_loc)
# print("OPEN RESPONSE:", file_open)
node_data = MidasAPI("GET", "/db/node", {})
# print(node_data)
runAnalysis()
# design = MidasAPI("POST", "/db/dcon", rc_input)
# print(design)

reaction_out = MidasAPI("POST", "/post/TABLE", baem_obj)
print(reaction_out)

