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


def cplexsolve():
    # MODEL
    model = CpoModel(name="sujet6-kiro")

    # SOLVE
    model.solve(TimeLimit=10)


cplexsolve()
