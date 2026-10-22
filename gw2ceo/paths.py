"""Where the repository's files are, anchored to this package's location so
the app finds its data from any working directory (main.py from the
repository root, gunicorn from wherever the deployment starts it)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
ICONS = ASSETS / "icons"
API_CACHE = ASSETS / "api-cache"
BUILDS = ROOT / "builds"
STATIC = ROOT / "static"
PROFESSION_IMAGES = ROOT / "profession_images"
PACKAGE = ROOT / "gw2ceo"
