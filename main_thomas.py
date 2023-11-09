import json
import numpy as np
from docplex.cp.model import *


with open("./instances/large.json") as json_file:
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
print("len(s_type)", len("s_type"))
print("n_land_s_cable", len("land_s_cables"))


def const_cost():
    c_cost = 0
    # construction substation
    for sp, substation in enumerate(substations):
        for s in range(nb_s):
            c_cost += (
                (substation["type_s"] != nb_s)
                * (substation["type_s"] == s)
                * s_type[s]["cost"]
            )  # problème quand la substation n'est pas construite
            c_cost += (substation["type_s"] != nb_s) * (
                land_s_cables[s]["fixed_cost"]
                + land_s_cables[s]["variable_cost"]
                * np.sqrt((s_loc[s]["x"]) ** 2 + (s_loc[s]["y"]) ** 2)
            )
    z_id = -1
    for z_cable in z_cables:
        z_id += 1
        for k in range(nb_s):
            c_cost += (z_cable["s_id"] == k) * (
                param["fixed_cost_cable"]
                + param["variable_cost_cable"]
                * np.sqrt(
                    (s_loc[k]["x"] - wind_turbines[z_id]["x"]) ** 2
                    + (wind_turbines[z_id]["y"] - s_loc[k]["y"]) ** 2
                )
            )
    print("c_cost", c_cost)
    return c_cost


def op_cost():
    return 0


def cost_function(z_cables, substations):
    return op_cost(substations, z_cables) + const_cost(substations, z_cables)


def cplexsolve():
    # MODEL
    model = CpoModel(name="sujet6-kiro")

    substations = [
        model.integer_var_dict(
            ["type_s", "type_c"],
            min=0,
            name="substation" + str(i),
        )
        for i in range(nb_substations)
    ]
    z_cables = [
        model.integer_var_dict(
            ["s_id"],
            min=0,
            name="z_" + str(i),
        )
        for i in range(nb_turbines)
    ]
    y_cable = [
        model.integer_var_dict(
            ["s_1", "s_2", "type"],
            min=0,
            name="y_" + str(i),
        )
        for i in range(nb_substations)
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
    # construction_cost

    # construction cable turbine

    # construction cable land

    # construction cable inter sub

    # OPTIMIZE
    model.minimize(cost_function(z_cables, substations))
    # SOLVE
    model.solve(TimeLimit=10)


cplexsolve()
