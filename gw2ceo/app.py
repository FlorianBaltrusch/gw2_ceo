import os
import sys
import threading

# the package must be importable whatever the working directory is, also
# when a deployment starts "gunicorn app:app" from inside this folder
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import pandas as pd
from flask import Flask, Response, abort, jsonify, redirect, request, send_from_directory

import gw2ceo.general_data as gd
from gw2ceo import buildlink, builds, sitedata
from gw2ceo.icons import ensure_icon
from gw2ceo.paths import ICONS, PROFESSION_IMAGES, STATIC
from gw2ceo.solve import solve

pd.options.mode.chained_assignment = None


app = Flask(__name__, static_folder=str(STATIC), static_url_path="/static")

# a static front end hosted elsewhere calls /calculate and /chatlink/* across
# origins: allow it (CEO_SITE_ORIGIN narrows it to that site; the API holds
# nothing private and uses no cookies)
SITE_ORIGIN = os.environ.get("CEO_SITE_ORIGIN", "*")


@app.after_request
def allow_site_origin(response):
    response.headers.setdefault("Access-Control-Allow-Origin", SITE_ORIGIN)
    return response

# only the (many, immutable-ish) game images get a long browser cache;
# HTML/CSS/JS must always revalidate so updates show up on a normal refresh
IMAGE_CACHE_SECONDS = 3600

@app.errorhandler(404)
def not_found(error):
    """Pages get the site's own not-found page; data and image paths keep
    the plain 404 the scripts test for."""
    if request.path.startswith(("/data/", "/icons/", "/profession-images/", "/static/", "/calculate", "/chatlink/")):
        return error
    return app.send_static_file("404.html"), 404


@app.route("/")
def landing():
    """The two doors: build your own (the optimizer) or browse the site's
    builds. Deep links from before the landing page existed carried the
    optimizer's query on the root - send them on."""
    if request.args.get("profession"):
        return redirect("/ceo?" + request.query_string.decode(), code=302)
    return app.send_static_file("landing.html")


@app.route("/favicon.ico")
def favicon():
    """Browsers ask for this path on their own, whatever the pages declare."""
    return app.send_static_file("favicon.ico")


@app.route("/ceo")
def optimizer():
    return app.send_static_file("index.html")


@app.route("/impressum")
def impressum():
    """Legal notice and privacy statement (German law: § 5 DDG, DSGVO)."""
    return app.send_static_file("impressum.html")


@app.route("/builds")
@app.route("/builds/<slug>")
def builds_page(slug=None):
    """One page renders both the list and a single build, from the URL."""
    return app.send_static_file("builds.html")


# ---------- the site's builds (builds/*.toml) ----------

_build_cache: dict = {"stamp": None, "builds": []}
_build_lock = threading.Lock()


def build_library() -> list[dict]:
    """The decoded builds, reloaded whenever a file in builds/ changes (so
    editing a build while the dev server runs needs no restart). Loading is
    lazy because it may hit the GW2 API for uncached traits/skills."""
    folder = builds.BUILDS_DIR
    names = sorted(name for name in os.listdir(folder) if name.endswith(".toml")) \
        if os.path.isdir(folder) else []
    stamp = tuple((name, os.path.getmtime(os.path.join(folder, name))) for name in names)
    with _build_lock:  # a request during the start-up warm-up waits instead of loading twice
        if stamp != _build_cache["stamp"]:
            _build_cache["builds"] = builds.load_all()
            _build_cache["stamp"] = stamp
        return _build_cache["builds"]


# warm the build catalogue right after start, so the first visitor never
# waits for the decoding and solving (a few seconds without the disk cache)
def _warm_builds():
    try:
        build_library()
    except Exception:  # noqa: BLE001 - a broken build file or no network must not kill the server
        pass


threading.Thread(target=_warm_builds, name="warm-builds", daemon=True).start()


# ---------- the fixed-per-deploy documents (also written by generate_site.py) ----------

def _json(text: str) -> Response:
    return Response(text, mimetype="application/json")


@app.route("/data/builds.json")
def builds_list():
    return _json(sitedata.builds_list(build_library()))


@app.route("/data/builds/<slug>.json")
def build_detail(slug):
    for build in build_library():
        if build["slug"] == slug:
            return _json(sitedata.build_detail(build))
    abort(404)


@app.route("/data/professions.json")
def professions():
    return _json(sitedata.professions())


@app.route("/data/specializations/<profession>.json")
def specializations(profession):
    return _json(sitedata.specializations(profession))


@app.route("/data/traits/<profession>.json")
def traits(profession):
    return _json(sitedata.traits(profession))


@app.route("/data/heal-skills/<profession>.json")
def heal_skills(profession):
    return _json(sitedata.heal_skills(profession))


@app.route("/theme.css")
def theme_css():
    return Response(sitedata.theme_css(), mimetype="text/css")


@app.route("/profession-images/<folder>/<filename>")
def profession_image(folder, filename):
    return send_from_directory(str(PROFESSION_IMAGES),
                               os.path.join(folder, filename),
                               max_age=IMAGE_CACHE_SECONDS)


@app.route("/icons/<filename>")
def icon(filename):
    """Locally cached game images (tracked in git); anything missing is
    downloaded on demand."""
    if not ensure_icon(filename):
        return jsonify({"error": f"unknown or unreachable icon: {filename}"}), 404
    return send_from_directory(str(ICONS),
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
