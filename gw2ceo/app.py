import os

import numpy as np
import pandas as pd
from flask import Flask, jsonify, request, Response, send_from_directory
from collections import Counter

import gw2ceo.general_data as gd
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.calculate import calc_ep
from gw2ceo.profession import Profession

pd.options.mode.chained_assignment = None


# the server is started from the repository root (like the CSV loading assumes)
app = Flask(__name__, static_folder=os.path.abspath("static"), static_url_path="/static")

ARMOR_SLOTS = ["onehanded", "twohanded", "chest", "legs", "head", "shoulders",
               "gloves", "boots", "amulet", "ring", "accessory", "back-item"]


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/profession-images/<folder>/<filename>")
def profession_image(folder, filename):
    return send_from_directory(os.path.abspath("profession_images"),
                               os.path.join(folder, filename))


@app.route("/professions")
def professions():
    return jsonify(sorted(gd.traits["profession"].unique()))


@app.route("/specializations")
def specializations():
    """Specializations with icon/background image paths, filtered by ?profession=..."""
    table = gd.specializations
    profession = request.args.get("profession")
    if profession:
        table = table[table["profession"].str.lower() == profession.lower()]
    table = table.assign(
        icon="/icons/spec_" + table["id"].astype(str) + ".png",
        background="/icons/spec_bg_" + table["id"].astype(str) + ".png",
    )
    return Response(table.to_json(orient="records"), mimetype="application/json")


@app.route("/traits")
def traits():
    """Selectable traits/skills, optionally filtered by ?profession=..."""
    table = gd.traits
    profession = request.args.get("profession")
    if profession:
        table = table[table["profession"].str.lower() == profession.lower()]
    return Response(table.to_json(orient="records"), mimetype="application/json")


@app.route("/icons/<filename>")
def icon(filename):
    """Locally cached trait/specialization images (filled by generate_traits.py)."""
    return send_from_directory(os.path.abspath(os.path.join("assets", "icons")),
                               filename)


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
