import json
import os
from collections import Counter

import numpy as np
import pandas as pd
from flask import Flask, Response, jsonify, request, send_from_directory

import gw2ceo.general_data as gd
from gw2ceo import buildlink, custom_colors
from gw2ceo.calculate import calc_ep
from gw2ceo.dtypes import BuildConstraints
from gw2ceo.gearselect import GearSelect
from gw2ceo.profession import Profession

pd.options.mode.chained_assignment = None


# the server is started from the repository root (like the CSV loading assumes)
app = Flask(__name__, static_folder=os.path.abspath("static"), static_url_path="/static")

# only the (many, immutable-ish) game images get a long browser cache;
# HTML/CSS/JS must always revalidate so updates show up on a normal refresh
IMAGE_CACHE_SECONDS = 3600

ARMOR_SLOTS = ["onehanded", "twohanded", "chest", "legs", "head", "shoulders",
               "gloves", "boots", "amulet", "ring", "accessory", "back-item"]


@app.route("/")
def index():
    return app.send_static_file("index.html")


@app.route("/theme.css")
def theme_css():
    """CSS variables generated from gw2ceo/custom_colors.py (single source of truth)."""
    colors = {name: value for name, value in vars(custom_colors).items()
              if isinstance(value, str) and value.startswith("#")}
    lines = [f"  --{name.replace('_', '-')}: {value[:7]};" for name, value in colors.items()]
    lines += ["  --alpha-strong: 70%;", "  --alpha-soft: 30%;"]
    css = ":root {\n" + "\n".join(lines) + "\n}\n"
    return Response(css, mimetype="text/css")


@app.route("/profession-images/<folder>/<filename>")
def profession_image(folder, filename):
    return send_from_directory(os.path.abspath("profession_images"),
                               os.path.join(folder, filename),
                               max_age=IMAGE_CACHE_SECONDS)


@app.route("/professions")
def professions():
    return jsonify(sorted(gd.traits["profession"].unique()))


@app.route("/specializations")
def specializations():
    """Specializations with icon/background image paths, filtered by ?profession=..."""
    table: pd.DataFrame = gd.specializations
    profession = request.args.get("profession")
    if profession:
        table = table.loc[table["profession"].str.lower() == profession.lower()]

    def versioned_icon(filename):
        """Icon URL stamped with the file's mtime, so browsers can cache long
        but always fetch a fresh copy when the image content changes."""
        path = os.path.join("assets", "icons", filename)
        return f"/icons/{filename}?v={int(os.path.getmtime(path))}"

    def spec_icon(row):
        tango = f"tango_{row['name']}.png"
        if os.path.isfile(os.path.join("assets", "icons", tango)):
            return versioned_icon(tango)
        return versioned_icon(f"spec_{row['id']}.png")

    table = table.assign(
        icon=table.apply(spec_icon, axis=1),
        background=table["id"].apply(lambda spec_id: versioned_icon(f"spec_bg_{spec_id}.png")),
    )
    return Response(table.to_json(orient="records"), mimetype="application/json")


@app.route("/traits")
def traits():
    """Selectable traits/skills, optionally filtered by ?profession=..."""
    table: pd.DataFrame = gd.traits
    profession = request.args.get("profession")
    if profession:
        table = table.loc[table["profession"].str.lower() == profession.lower()]
    return Response(table.to_json(orient="records"), mimetype="application/json")


@app.route("/icons/<filename>")
def icon(filename):
    """Locally cached trait/specialization images (filled by generate_traits.py)."""
    return send_from_directory(os.path.abspath(os.path.join("assets", "icons")),
                               filename, max_age=IMAGE_CACHE_SECONDS)


@app.route("/chatlink/decode")
def chatlink_decode():
    try:
        return jsonify(buildlink.decode(request.args.get("link", "")))
    except (ValueError, KeyError, IndexError) as error:
        return jsonify({"error": str(error) or "Could not decode this chat link."}), 400


@app.route("/chatlink/encode")
def chatlink_encode():
    try:
        selected = [int(trait_id) for trait_id in request.args.getlist("traits[]")]
        link = buildlink.encode(request.args.get("profession", ""), selected)
    except (ValueError, KeyError, IndexError) as error:
        return jsonify({"error": str(error) or "Could not encode a chat link."}), 400
    return jsonify({"link": link})


@app.route("/calculate")
def calculate():
    try:
        trait_ids = [int(trait_id) for trait_id in request.args.getlist("traits[]")]
        profession = Profession(trait_ids, profession=request.args.get("profession"))

        armor = request.args.getlist("armor[]")
        armor = [piece.replace("1", "").replace("2", "") for piece in armor]
        counts = Counter(armor)
        num_ascended = [counts[slot] for slot in ARMOR_SLOTS]

        gear_environment = request.args.get("parameters")
        if gear_environment not in ("3p", "4p"):
            raise ValueError("parameters must be '3p' or '4p'")
        weapon_type = request.args.get("handedness")
        if weapon_type not in ("1h", "2h"):
            raise ValueError("handedness must be '1h' or '2h'")

        constraints = BuildConstraints(
            gear_environment=gear_environment,
            weapon_type=weapon_type,

            num_ascended=np.array(num_ascended),  # order as in ARMOR_SLOTS

            food=request.args.get("food", "true") == "true",
            utility=request.args.get("utility", "true") == "true",

            fury=request.args.get("fury") == "true",
            might=int(request.args.get("might", "25"))
        )

        suggestion = calc_ep(profession, constraints)
    except (ValueError, NotImplementedError) as error:
        return jsonify({"error": str(error)}), 400

    result = json.loads(suggestion.to_json())
    result["total_infusions"] = int(gd.num_infusions(constraints.num_ascended,
                                                     constraints.weapon_type))

    # concrete per-slot assignment: how many pieces of each group carry
    # precision as major stat
    gear = GearSelect(constraints)
    assignment = next(gear.get_equipment(suggestion["armor_precision"]), None)
    result["equipment"] = None
    if assignment is not None:
        groups = [(label, int(count), int(major))
                  for (label, count), major in zip(gear.groups, assignment)
                  if count > 0]

        # the rarity suffix only matters when a slot family actually mixes
        # rarities (e.g. one ascended and one exotic ring); otherwise the
        # label would just echo the user's own toggles
        def family(label):
            return label.removesuffix(" (ascended)").removesuffix(" (exotic)")

        families = Counter(family(label) for label, _, _ in groups)
        result["equipment"] = [
            {"slot": family(label) if families[family(label)] == 1 else label,
             "pieces": pieces, "precision_major": major}
            for label, pieces, major in groups
        ]
    return jsonify(result)
