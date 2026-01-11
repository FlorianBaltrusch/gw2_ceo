import pandas as pd
import numpy as np
from flask import Flask, request, Response
from collections import Counter

from gw.dtypes import BuildConstraints
from gw.professions import Elementalist, Mesmer
from gw.calculate import calc_ep

pd.options.mode.chained_assignment = None


app = Flask(__name__)


@app.route("/calculate")
def calculate():


    match (request.args["profession"]):
        case "mesmer":
            ReqProfession = Mesmer
        case "elementalist":
            ReqProfession = Elementalist
        case _:
            raise


    profession = ReqProfession(request.args.getlist("traits[]"))

    armor = request.args.getlist("armor[]")
    armor = [armor.replace("1","").replace("2","") for armor in armor]
    armor = Counter(armor)
    num_ascended = [armor[type] for type in ["onehanded", "twohanded", "chest", "legs", "head", "shoulders", "gloves", "boots", "amulet", "ring", "accessory", "back-item"]]

    constraints = BuildConstraints(
        gear_environment=request.args.get("parameters"),
        weapon_type=request.args.get("handedness"),
        
        num_ascended=np.array(num_ascended),  # One-handed, Two-handed, Chest, Legs, Head, Shoulders, Gloves, Boots, Amulet, Ring, Accessory, Back item
    #    num_ascended=np.full(12, 2),

        food=True,
        utility=True,

        fury=request.args.get("fury")=="true",
        might=int(request.args.get("might"))
    )


    suggestion = calc_ep(profession, constraints)

    return Response(suggestion.to_json(), mimetype='application/json')
