# -*- coding: utf-8 -*-
"""
Created on Sat Jan 10 23:13:48 2026

@author: albert pamonag
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



mode_input = {
    "Argument": {
        "CURRENT_MODE": "VibrationModeShapes",
        "LOAD_CASE_COMB": {
            "NAME": "mode1"
        },
        "COMPONENTS": {
            "COMP": "Md-XYZ"
        },
        "TYPE_OF_DISPLAY": {
            "VALUES": {
                "OPT_CHECK": True,
                "DECIMAL_PT": 5
            }
        }
    }
}


reaction = {
    "Argument": {
        "CURRENT_MODE": "ReactionForces/Moments",
        "LOAD_CASE_COMB": {
            "TYPE": "ST",
            "MINMAX": "max",
            "NAME": "DL",
            "STEP_INDEX": 1
        },
        "COMPONENTS": {
            "COMP": "Fxyz",
            "OPT_LOCAL_CHECK": True
        },
        "TYPE_OF_DISPLAY": {
            "VALUES": {
                "OPT_CHECK": True
            },
            "LEGEND": {
                "OPT_CHECK": True
            },
            "ARROW_SCALE_FACTOR": 1.0
        }
    }
}


capture = {
    "Argument": {
        "SET_MODE": "post",
        "SET_HIDDEN": True,
        "EXPORT_PATH": r"C:\Users\alber\Desktop\4S Apartment\midas\mode.jpg",
        "HEIGHT": 800,
        "WIDTH": 800,
        "ACTIVE": {
            "ACTIVE_MODE": "Active",
        },
        "ANGLE": {
            "HORIZONTAL": 30,
            "VERTICAL": 30
        },
        "DISPLAY": {
            "NODE": {
                "NODE": True,
                "NODE_NUMBER": False
            },
            "PERSPECTIVE": True,
            "ZOOM_LEVEL": 100,
            "BGCOLOR_TOP": {
                "R": 255,
                "G": 125,
                "B": 125
            }
        },
        "RESULT_GRAPHIC": {
            "CURRENT_MODE": "VibrationModeShapes",
            "LOAD_CASE_COMB": {
                "NAME": "Mode3"
        },
        "COMPONENTS": {
            "COMP": "Md-XYZ"
        },
        "TYPE_OF_DISPLAY": {
            "MODE_SHAPE": True,
            "UNDEFORMED": True,
            "LEGEND": {
                "OPT_CHECK": True,
                "POSITION": "right",
                "VALUE_EXP": False,
                "DECIMAL_PT": 3
                },
        },
      "CONTOUR": {
        "OPT_CHECK": False
      }
    
        }
    }
}




def runAnalysis():
    print("Performing Run Analysis in Midas Gen")
    MidasAPI("POST", "/doc/ANAL", {})
    print("Analysis is completed!!!")
# irregular = {
#     "Argument": {
#         "COUNTRY_CODE": "NSCP2015",
#         "STORY_DRIFT_METHOD": "Max.DriftofOuterExtremePoints",
#         "STORY_STIFFNESS_METHOD": "1/StoryDriftRatio"
#         # "SEISMIC_BEHAVIOR_FACTOR": "3orbelow"  # optional
#     }
# }



file_open = MidasAPI("POST", "/doc/open", file_loc)
# print("OPEN RESPONSE:", file_open)
# node_data = MidasAPI("GET", "/db/node", {})
# print(node_data)
runAnalysis()
# mode = MidasAPI("POST", "/view/resultgraphic", reaction)
cap = MidasAPI("POST", "/view/capture", capture)
print(cap)


