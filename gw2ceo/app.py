import os

import pandas as pd
from flask import Flask, Response, abort, jsonify, redirect, request, send_from_directory

import gw2ceo.general_data as gd
from gw2ceo import buildlink, builds, custom_colors
from gw2ceo.icons import ensure_icon
from gw2ceo.solve import solve

pd.options.mode.chained_assignment = None


# the server is started from the repository root (like the CSV loading assumes)
app = Flask(__name__, static_folder=os.path.abspath("static"), static_url_path="/static")

# only the (many, immutable-ish) game images get a long browser cache;
# HTML/CSS/JS must always revalidate so updates show up on a normal refresh
IMAGE_CACHE_SECONDS = 3600

@app.route("/")
def landing():
    """The two doors: build your own (the optimizer) or browse the curated
    builds. Deep links from before the landing page existed carried the
    optimizer's query on the root - send them on."""
    if request.args.get("profession"):
        return redirect("/ceo?" + request.query_string.decode(), code=302)
    return app.send_static_file("landing.html")


@app.route("/ceo")
def optimizer():
    return app.send_static_file("index.html")


@app.route("/builds")
@app.route("/builds/<slug>")
def builds_page(slug=None):
    """One page renders both the list and a single build, from the URL."""
    return app.send_static_file("builds.html")


# ---------- curated builds (builds/*.toml) ----------

_build_cache: dict = {"stamp": None, "builds": []}


def build_library() -> list[dict]:
    """The decoded builds, reloaded whenever a file in builds/ changes (so
    editing a build while the dev server runs needs no restart). Loading is
    lazy because it may hit the GW2 API for uncached traits/skills."""
    folder = builds.BUILDS_DIR
    names = sorted(name for name in os.listdir(folder) if name.endswith(".toml")) \
        if os.path.isdir(folder) else []
    stamp = tuple((name, os.path.getmtime(os.path.join(folder, name))) for name in names)
    if stamp != _build_cache["stamp"]:
        _build_cache["builds"] = builds.load_all()
        _build_cache["stamp"] = stamp
    return _build_cache["builds"]


@app.route("/api/builds")
def builds_list():
    return jsonify([builds.summary(build) for build in build_library()])


@app.route("/api/builds/<slug>")
def build_detail(slug):
    for build in build_library():
        if build["slug"] == slug:
            return jsonify(build)
    abort(404)


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
        but always fetch a fresh copy when the image content changes. Missing
        files are downloaded first (fresh clones have an empty cache)."""
        ensure_icon(filename)
        path = os.path.join("assets", "icons", filename)
        version = int(os.path.getmtime(path)) if os.path.isfile(path) else 0
        return f"/icons/{filename}?v={version}"

    def spec_icon(row):
        # only elite specs (and professions) have wiki tango icons; core
        # trait lines fall back to their hexagon icon directly
        if row["elite"] and ensure_icon(f"tango_{row['name']}.png"):
            return versioned_icon(f"tango_{row['name']}.png")
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


@app.route("/heal-skills")
def heal_skills():
    """Healing skills with their K = base/coefficient ratio for the boon
    mode's healing-profile slider, filtered by ?profession=... (rows without
    a profession, like the regeneration boon, apply to everyone)."""
    table: pd.DataFrame = gd.heal_skills
    profession = request.args.get("profession", "")
    universal = table["profession"].fillna("") == ""
    table = table.loc[universal
                      | (table["profession"].str.lower() == profession.lower())]
    return Response(table.to_json(orient="records"), mimetype="application/json")


@app.route("/icons/<filename>")
def icon(filename):
    """Locally cached game images; missing files are downloaded on demand
    (the cache is gitignored, so fresh clones start empty)."""
    if not ensure_icon(filename):
        return jsonify({"error": f"unknown or unreachable icon: {filename}"}), 404
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
        return jsonify(solve(request.args))
    except (ValueError, NotImplementedError) as error:
        return jsonify({"error": str(error)}), 400
