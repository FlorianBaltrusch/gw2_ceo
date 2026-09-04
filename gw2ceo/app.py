import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, Response
from collections import Counter

import gw2ceo.general_data as gd
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.calculate import calc_ep
from gw2ceo.profession import Profession

pd.options.mode.chained_assignment = None


app = Flask(__name__)

ARMOR_SLOTS = ["onehanded", "twohanded", "chest", "legs", "head", "shoulders",
               "gloves", "boots", "amulet", "ring", "accessory", "back-item"]


@app.route("/professions")
def professions():
    return jsonify(sorted(gd.traits["profession"].unique()))


@app.route("/traits")
def traits():
    """Selectable traits/skills, optionally filtered by ?profession=..."""
    table = gd.traits
    profession = request.args.get("profession")
    if profession:
        table = table[table["profession"].str.lower() == profession.lower()]
    return Response(table.to_json(orient="records"), mimetype="application/json")


@app.route("/calculate")
def calculate():
    trait_ids = [int(trait_id) for trait_id in request.args.getlist("traits[]")]
    profession = Profession(trait_ids, profession=request.args.get("profession"))

    armor = request.args.getlist("armor[]")
    armor = [piece.replace("1", "").replace("2", "") for piece in armor]
    armor = Counter(armor)
    num_ascended = [armor[slot] for slot in ARMOR_SLOTS]

    constraints = BuildConstraints(
        gear_environment=request.args.get("parameters"),
        weapon_type=request.args.get("handedness"),

        num_ascended=np.array(num_ascended),  # order as in ARMOR_SLOTS

        food=True,
        utility=True,

        fury=request.args.get("fury") == "true",
        might=int(request.args.get("might"))
    )

    suggestion = calc_ep(profession, constraints)

    return Response(suggestion.to_json(), mimetype='application/json')
