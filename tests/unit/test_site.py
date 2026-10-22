"""generate_site.py writes a complete static site."""
import json
import re

import generate_site


def test_static_site_is_complete(tmp_path, catalogue):
    out = tmp_path / "dist"
    summary = generate_site.build(out, api_base="https://api.example.org/")
    assert not summary["missing_icons"], summary["missing_icons"]

    for page in ("index.html", "ceo/index.html", "builds/index.html", "impressum/index.html", "404.html", "favicon.ico", "theme.css"):
        assert (out / page).is_file(), page
    for build in catalogue:
        assert (out / "builds" / build["slug"] / "index.html").is_file(), build["slug"]
        assert (out / "data" / "builds" / f"{build['slug']}.json").is_file(), build["slug"]
    assert (out / "static" / "config.js").read_text().strip().endswith('window.CEO_API_BASE = "https://api.example.org";')
    assert "--theme-dark" in (out / "theme.css").read_text()
    assert (out / "profession-images" / "freigestellt").is_dir()

    listing = json.loads((out / "data" / "builds.json").read_text())
    assert len(listing) == len(catalogue)
    assert json.loads((out / "data" / "professions.json").read_text())[0] == "Elementalist"
    assert (out / "data" / "specializations" / "Elementalist.json").is_file()
    assert (out / "data" / "traits" / "Thief.json").is_file()
    assert (out / "data" / "heal-skills" / "Guardian.json").is_file()

    # every icon any document points at is in the site
    referenced = set()
    for path in (out / "data").rglob("*.json"):
        referenced.update(re.findall(r"/icons/([^\"?\\\\]+)", path.read_text()))
    assert referenced and all((out / "icons" / name).is_file() for name in referenced)
