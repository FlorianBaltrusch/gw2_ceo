"""Write the whole site as static files: pages, stylesheets, scripts, images
and every JSON document the pages read. Only /calculate and /chatlink/*
need the Python API; the static site calls them at --api.

    PYTHONPATH=. .venv/bin/python generate_site.py --out dist --api https://api.gw2ceo.com

Host the dist folder anywhere that serves files (GitHub Pages, a Render
static site, any web server); run the Flask app as the API with
CEO_SITE_ORIGIN set to the site's origin (see DEPLOY.md)."""
import argparse
import json
import re
import shutil
from pathlib import Path

import gw2ceo.general_data as gd
from gw2ceo import builds, sitedata
from gw2ceo.icons import ensure_icon
from gw2ceo.paths import ICONS, PROFESSION_IMAGES, ROOT, STATIC

# the page each URL serves; a folder with index.html per build slug keeps
# deep links working without server-side rewrites
PAGES = {"index.html": "landing.html", "ceo/index.html": "index.html",
         "builds/index.html": "builds.html", "impressum/index.html": "impressum.html",
         "404.html": "404.html"}   # static hosts (GitHub Pages, Render) serve it for unknown paths


def build(out: Path, api_base: str = "") -> dict:
    """Write the site into `out` (replaced). Returns counts for the log."""
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    # static files, with the API location written into config.js
    shutil.copytree(STATIC, out / "static")
    (out / "static" / "config.js").write_text(
        f'// written by generate_site.py\nwindow.CEO_API_BASE = {json.dumps(api_base.rstrip("/"))};\n')
    shutil.copy(STATIC / "favicon.ico", out / "favicon.ico")
    (out / "theme.css").write_text(sitedata.theme_css())
    shutil.copytree(PROFESSION_IMAGES, out / "profession-images")

    # pages
    for target, source in PAGES.items():
        (out / target).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(STATIC / source, out / target)

    # data documents
    data = out / "data"
    documents = {"professions.json": sitedata.professions()}
    for profession in gd.PROFESSION_ORDER:
        documents[f"specializations/{profession}.json"] = sitedata.specializations(profession)
        documents[f"traits/{profession}.json"] = sitedata.traits(profession)
        documents[f"heal-skills/{profession}.json"] = sitedata.heal_skills(profession)
    library = builds.load_all()
    documents["builds.json"] = sitedata.builds_list(library)
    for item in library:
        documents[f"builds/{item['slug']}.json"] = sitedata.build_detail(item)
        page = out / "builds" / item["slug"] / "index.html"
        page.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(STATIC / "builds.html", page)
    for name, text in documents.items():
        (data / name).parent.mkdir(parents=True, exist_ok=True)
        (data / name).write_text(text)

    # every icon the documents or the scripts reference
    referenced = set()
    for text in documents.values():
        referenced.update(re.findall(r"/icons/([^\"?\\]+)", text))
    referenced.update(f"{trait_id}.png" for trait_id in gd.traits["id"].unique())   # optimizer trait list
    referenced.update(f"tango_{profession}.png" for profession in gd.PROFESSION_ORDER)
    (out / "icons").mkdir()
    missing = []
    for filename in sorted(referenced):
        if ensure_icon(filename):
            shutil.copy(ICONS / filename, out / "icons" / filename)
        else:
            missing.append(filename)
    return {"pages": len(PAGES) + len(library), "documents": len(documents),
            "icons": len(referenced) - len(missing), "missing_icons": missing}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", default=str(ROOT / "dist"), help="output folder (replaced)")
    parser.add_argument("--api", default="", help="URL of the API service, e.g. https://api.gw2ceo.com")
    args = parser.parse_args()
    summary = build(Path(args.out), args.api)
    print(f"{args.out}: {summary['pages']} pages, {summary['documents']} data documents, {summary['icons']} icons"
          + (f"; could not fetch {summary['missing_icons']}" if summary["missing_icons"] else ""))
