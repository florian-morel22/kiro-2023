import json

from docplex.cp.model import *

import matplotlib.pyplot as plt


instance = "large"

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

print(nb_s_s_cables)

print("nb_s", nb_s)
print("nb_t", nb_t)


def op_cost(substations, z_cables):
    return 0


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

    # SOLVE
    res = model.solve(TimeLimit=10)

    if res:
        for i, _ in enumerate(z_cables):
            print(
                f"La turbine {i+1} est relié à la substation {res[z_cables[i]['s_id']]+1}"
            )
        for i, _ in enumerate(substations):
            if res[substations[i]["type_s"]] == nb_s:
                print(f"La location {i+1} est vide")
            elif res[substations[i]["linked_s"]] == nb_s:
                print(
                    f"La substation {i+1} est de type {res[substations[i]['type_s']]+1} et n'est pas connecté à une autre substation"
                )
                if res[substations[i]["type_linked_s"]] != nb_s_s_cables:
                    print(
                        f"ERREUR : Elle a un cable de type {res[substations[i]['type_linked_s']]+1}"
                    )
            else:
                print(
                    f"La substation {i+1} est de type {res[substations[i]['type_s']]+1} et a un cable de type {res[substations[i]['type_c']]+1}. Elle est connecté à la subsation {res[substations[i]['linked_s']]+1} avec un cable de type {res[substations[i]['type_linked_s']]+1}"
                )

            # if (
            #     res[substations[i]["linked_s"]] < nb_s
            #     and res[substations[i]["type_linked_s"]] < nb_s_s_cables
            # ):
            #     print(
            #         f"La substation {i+1} est de type {res[substations[i]['type_s']]+1} et a un cable de type {res[substations[i]['type_c']]+1}. Elle est connecté à la subsation {res[substations[i]['linked_s']]+1} avec un cable de type {res[substations[i]['type_linked_s']]+1}"
            #     )
            # else:
            #     print(
            #         f"La substation {i+1} est de type {res[substations[i]['type_s']]+1} et a un cable de type {res[substations[i]['type_c']]+1}. Elle n'est pas connecté à une autre substation"
            #     )

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
