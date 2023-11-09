import json

from docplex.cp.model import *


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

    # SOLVE
    model.solve(TimeLimit=10)


cplexsolve()
