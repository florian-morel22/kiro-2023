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

    model.add(
        substation["type_c"] <= len("land_s_cables") for substation in substations
    )
    model.add(substation["linked_s"] <= nb_s for substation in substations)
    model.add(substation["type_s"] <= len("s_type") for substation in substations)
    model.add(z_cable["s_id"] <= nb_s for z_cable in z_cables)

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

    # COST

    # SOLVE
    model.solve(TimeLimit=10)


cplexsolve()
