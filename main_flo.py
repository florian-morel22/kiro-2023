import json

from docplex.cp.model import *


def cplexsolve():

    # MODEL
    model = CpoModel(name="sujet6-kiro")

    # SOLVE
    model.solve(TimeLimit=10)
    

cplexsolve()