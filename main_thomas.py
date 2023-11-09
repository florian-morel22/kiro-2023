import json

from docplex.cp.model import *


with open("./instances/toy.json") as json_file:
    data = json.load(json_file)

s_loc = data["substation_locations"]
s_type = data["substation_types"]
land_s_cables = data["land_substation_cable_types"]
s_s_cables = data["substation_substation_cable_types"]
wind_turbines = data["wind_turbines"]
wind_scenarios = data["wind_scenarios"]
param = data["general_parameters"]

nb_s = len(s_loc)
nb_t = len(wind_turbines)

print("nb_s", nb_s)
print("nb_t", nb_t)
print("len(s_type)",len("s_type"))
print("n_land_s_cable",len("land_s_cables"))

def cplexsolve():
    # MODEL
    model = CpoModel(name="sujet6-kiro")

    # VARIABLES
    substations = [
        model.integer_var_dict(
            ["type_s", "type_c", "linked_s"],
            min=0,
            name="substation" + str(i),
        )
        for i in range(nb_s)
    ]
    z_cables = [
        model.integer_var_dict(
            ["s_id"],
            min=0,
            name="z_" + str(i),
        )
        for i in range(nb_t)
    ]

     # CONSTRAINTS

    for z_cable in z_cables:
        model.add(
            if_then(z_cable["s_id"] == k, substations[k]["type_s"] > 0)
            for k in range(nb_s)
        )

    for s, substation in enumerate(substations):
        for sp, substationp in enumerate(substations):
            if s != sp:
                model.add(
                    if_then(substation["linked_s"] == sp, substationp["linked_s"] == s)
                )

    model.add(
        substation["type_c"] <= len("land_s_cables") for substation in substations
    )
    model.add(substation["linked_s"] <= nb_s for substation in substations)
    model.add(substation["type_s"] <= len("s_type") for substation in substations)
    model.add(z_cable["s_id"] <= nb_s for z_cable in z_cables)

    # COST
        #construction_cost
    c_cost=0
            #construction substation
    for substation in substations :
        if(substation["type_s"]!=nb_s):
            c_cost+=s_type[substation["type_s"]]["cost"]
        print(c_cost)
            #construction cable turbine

            #construction cable land

            #construction cable inter sub


    # SOLVE
    res = model.solve(TimeLimit=10)

    if res:
        for i, _ in enumerate(z_cables):
            print(
                f"La turbine {i} est relié à la substation {res[z_cables[i]['s_id']]}"
            )
        for i, _ in enumerate(substations):
            print(
                f"La substation {i} est de type{res[substations[i]['type_s']]} et a un cable de type {res[substations[i]['type_c']]} et est connecté à la subsation {res[substations[i]['linked_s']]}"
            )

cplexsolve()
