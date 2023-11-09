import json
import numpy as np
from docplex.cp.model import *

instance = "small"

with open(f"./instances/{instance}.json") as json_file:
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

nb_s_s_cables = len(s_s_cables)
nb_land_s_cables = len(land_s_cables)
nb_s_type = len(s_type)

nb_wind_scenarios = len(wind_scenarios)
print("nb_s", nb_s)
print("nb_t", nb_t)
print("len(s_type)", len("s_type"))
print("n_land_s_cable", len("land_s_cables"))


def v_C_n(z_cables, substations, scenario):
    c_n = 0
    for sp, substation in enumerate(substations):
        z_id = -1
        for z_cable in z_cables:
            z_id += 1
            c_n += wind_scenarios[scenario]["power_generation"] * (
                z_cable["s_id"] == sp
            )
            # construction cable turbine

        c_n1 = 0
        c_n2 = 0
        for type_s in range(nb_s_type):
            c_n1 += (
                (substation["type_s"] != nb_s)
                * (substation["type_linked_s"] == type_s)
                * s_type[type_s]["rating"]
            )

        for type_s_s in range(nb_s_s_cables):
            for s in range(nb_s):
                c_n2 += (
                    (substation["type_s"] != nb_s)
                    * (substation["type_linked_s"] == type_s_s)
                    * (substation["linked_s"] == s)
                    * (s_s_cables[type_s_s]["rating"])
                )
        c_n -= min(c_n1, c_n2)

    return c_n


def cplexsolve():
    # MODEL
    model = CpoModel(name="sujet6-kiro")

    # VARIABLES
    substations = [
        model.integer_var_dict(
            ["type_s", "type_c", "linked_s", "type_linked_s"],
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

    model.add(substation["type_c"] < nb_land_s_cables for substation in substations)
    model.add(substation["linked_s"] <= nb_s for substation in substations)
    model.add(
        substation["type_linked_s"] <= nb_s_s_cables for substation in substations
    )
    model.add(substation["type_s"] < len(s_type) for substation in substations)
    model.add(z_cable["s_id"] < nb_s for z_cable in z_cables)

    for z_cable in z_cables:
        model.add(
            if_then(z_cable["s_id"] == k, substations[k]["type_s"] < nb_s)
            for k in range(nb_s)
        )

    for s, substation in enumerate(substations):
        model.add(substation["linked_s"] != s)
        model.add(
            if_then(
                substation["linked_s"] == nb_s,
                substation["type_linked_s"] == nb_s_s_cables,
            )
        )
        model.add(
            if_then(
                substation["linked_s"] < nb_s,
                substation["type_linked_s"] < nb_s_s_cables,
            )
        )

    for s, substation in enumerate(substations):
        for sp, substationp in enumerate(substations):
            if s != sp:
                model.add(
                    if_then(
                        substation["linked_s"] == sp,
                        substationp["linked_s"] == s,
                    )
                )
                model.add(
                    if_then(
                        substation["linked_s"] == sp,
                        substation["type_linked_s"] == substationp["type_linked_s"],
                    )
                )

    # COST
    # construction_cost
    c_cost = 0
    # construction substation
    for sp, substation in enumerate(substations):
        for s in range(nb_s_type):
            c_cost += (
                (substation["type_s"] != nb_s)
                * (substation["type_s"] == s)
                * s_type[s]["cost"]
            )

            c_cost += (
                (substation["type_s"] != nb_s)
                * (substation["type_c"] == s)
                * (
                    land_s_cables[s]["fixed_cost"]
                    + land_s_cables[s]["variable_cost"]
                    * np.sqrt((s_loc[sp]["x"]) ** 2 + (s_loc[sp]["y"]) ** 2)
                )
            )
        for type_s_s in range(nb_s_s_cables):
            for s in range(nb_s):
                c_cost += (
                    0.5
                    * (substation["type_s"] != nb_s)
                    * (substation["type_linked_s"] == type_s_s)
                    * (substation["linked_s"] == s)
                    * (
                        s_s_cables[type_s_s]["fixed_cost"]
                        + s_s_cables[type_s_s]["variable_cost"]
                        * np.sqrt(
                            (s_loc[sp]["x"] - s_loc[s]["x"]) ** 2
                            + (s_loc[sp]["y"] - s_loc[s]["y"]) ** 2
                        )
                    )
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

            # construction cable land

            # construction cable inter sub

    # boucle scénario
    op_cost_thomas = 1
    for scenario in range(nb_wind_scenarios):
        for sp, substation in enumerate(substations):
            for s in range(nb_s_type):
                op_cost_thomas -= (
                    (substation["type_s"] != nb_s)
                    * (substation["type_s"] == s)
                    * s_type[s]["probability_of_failure"]
                )
        c_cost += (
            op_cost_thomas
            * param["curtailing_cost"]
            * v_C_n(z_cables, substations, scenario)
        )

    # OPTIMIZE
    # model.minimize(c_cost)
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
    output = {
        "substations": [],
        "substation_substation_cables": [],
        "turbines": [],
    }

    for s, substation in enumerate(substations):
        if res[substations[s]["type_s"]] < nb_s:
            output["substations"].append(
                {
                    "id": s + 1,
                    "land_cable_type": res[substations[s]["type_c"]] + 1,
                    "substation_type": res[substations[s]["type_s"]] + 1,
                }
            )

        link1 = [k["substation_id"] for k in output["substation_substation_cables"]]
        link2 = [
            k["other_substation_id"] for k in output["substation_substation_cables"]
        ]

        if (
            res[substations[s]["linked_s"]] < nb_s
            and s + 1 not in link1
            and s + 1 not in link2
        ):
            output["substation_substation_cables"].append(
                {
                    "substation_id": s + 1,
                    "other_substation_id": res[substations[s]["linked_s"]] + 1,
                    "cable_type": res[substations[s]["type_linked_s"]] + 1,
                }
            )

    for t, turbine in enumerate(z_cables):
        output["turbines"].append(
            {
                "id": t + 1,
                "substation_id": res[z_cables[t]["s_id"]] + 1,
            }
        )

    with open(f"output_{instance}.json", "w") as outfile:
        json.dump(output, outfile)


cplexsolve()


print(f"A respecter :")
print(f"type de substation max: {nb_s_type}")
print(f"type de cable max: {nb_land_s_cables}")
print(f"type cable with other substation max: {nb_s_s_cables}")
