import json

import numpy as np

from docplex.cp.model import *

import matplotlib.pyplot as plt


instance = "toy"

with open(f"./instances/{instance}.json") as json_file:
    data = json.load(json_file)

s_loc = data["substation_locations"]
s_type = data["substation_types"]
land_s_cables = data["land_substation_cable_types"]
s_s_cables = data["substation_substation_cable_types"]
wind_turbines = data["wind_turbines"]
wind_scenarios = data["wind_scenarios"]
param = data["general_parameters"]

nb_wind_scenarios = len(wind_scenarios)

nb_s = len(s_loc)
nb_t = len(wind_turbines)

nb_s_s_cables = len(s_s_cables)
nb_land_s_cables = len(land_s_cables)
nb_s_type = len(s_type)

print(nb_s_s_cables)

print("nb_s", nb_s)
print("nb_t", nb_t)


def const_cost(substations, z_cables):
    c_cost = 0
    # # construction substation
    # for sp, substation in enumerate(substations):
    #     for s in range(nb_s_type):
    #         c_cost += (
    #             (substation["type_s"] != nb_s)
    #             * (substation["type_s"] == s)
    #             * s_type[s]["cost"]
    #         )  # problème quand la substation n'est pas construite
    #         c_cost += (substation["type_s"] != nb_s) * (
    #             land_s_cables[s]["fixed_cost"]
    #             + land_s_cables[s]["variable_cost"]
    #             * np.sqrt((s_loc[sp]["x"]) ** 2 + (s_loc[sp]["y"]) ** 2)
    #         )
    # z_id = -1
    # for z_cable in z_cables:
    #     z_id += 1
    #     for k in range(nb_s):
    #         c_cost += (z_cable["s_id"] == k) * (
    #             param["fixed_cost_cable"]
    #             + param["variable_cost_cable"]
    #             * np.sqrt(
    #                 (s_loc[k]["x"] - wind_turbines[z_id]["x"]) ** 2
    #                 + (wind_turbines[z_id]["y"] - s_loc[k]["y"]) ** 2
    #             )
    #         )
    # print("c_cost", c_cost)
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
    return c_cost


def compute_Cf(w, z_cables, v, substations):
    res1 = 0
    pw = w["power_generation"]

    a = pw * sum((z_cable["s_id"] == v) for z_cable in z_cables)
    b = 0
    for substation in substations:
        for q in s_s_cables:
            b += (substation["type_linked_s"] + 1 == q["id"]) * q["rating"]
    res1 = max(0, a - b)

    # res2
    for v_, substation_ in enumerate(substations):
        pp = pw * sum((z_cable["s_id"] == v_) for z_cable in z_cables)
        gg = sum(
            q["rating"] * (substations[v]["type_linked_s"] + 1 == q["id"])
            for q in s_s_cables
        )
        mm = pw * sum((z_cable["s_id"] == v) for z_cable in z_cables)
        nn = sum((substation_["type_s"] + 1 == s["id"]) * s["rating"] for s in s_type)
        ll = sum(
            q["rating"] * (substations[v]["type_c"] + 1 == q["id"])
            for q in land_s_cables
        )

        res2_ = max(0, pp + min(gg, mm) - min(nn, ll))

        res2 = res2_ * (substations[v]["linked_s"] == v_)

    return res1 + res2


def compute_pf(v, substations, z_cables):
    res = 0
    for s in s_type:
        res += (substations[v]["type_s"] + 1 == s["id"]) * s["probability_of_failure"]
    for q in land_s_cables:
        res += (substations[v]["type_c"] + 1 == q["id"]) * q["probability_of_failure"]
    return res


def compute_cc(C):
    c0 = param["curtailing_cost"]
    cp = param["curtailing_penalty"]
    Cmax = param["maximum_curtailing"]
    return c0 * C + cp * max(0, C - Cmax)


def op_cost(substations, z_cables):
    for w in wind_scenarios:
        pw = w["probability"]

        res = 0

        for v, substation in enumerate(substations):
            pf = compute_pf(v, substations, z_cables)
            Cf = compute_Cf(w, z_cables, v, substations)

            res += pf * compute_cc(Cf)

    op_cost_thomas = 1
    c_cost = 0
    for scenario in range(nb_wind_scenarios):
        for sp, substation in enumerate(substations):
            for s in range(nb_s_type):
                op_cost_thomas -= (
                    (substation["type_s"] != nb_s)
                    * (substation["type_s"] == s)
                    * s_type[s]["probability_of_failure"]
                )
        c_cost += op_cost_thomas * compute_cc(v_C_n(z_cables, substations, scenario))

    res = (res + c_cost) * pw
    return res


def cost_function(z_cables, substations):
    return op_cost(substations, z_cables) + const_cost(substations, z_cables)


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
    model.minimize(cost_function(z_cables, substations))

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
