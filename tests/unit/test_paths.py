"""The app finds its files from any working directory (the deployment
starts gunicorn from wherever it likes)."""
import json
import os
import subprocess
import sys


def test_paths_are_anchored_to_the_package(root):
    from gw2ceo import paths
    assert paths.ROOT == root
    for folder in (paths.ASSETS, paths.ICONS, paths.API_CACHE, paths.BUILDS, paths.STATIC, paths.PROFESSION_IMAGES):
        assert folder.is_absolute() and folder.is_dir(), folder


def test_app_serves_from_a_foreign_working_directory(root, tmp_path):
    code = ("import sys, json; sys.path.insert(0, sys.argv[1]); from gw2ceo.app import app; "
            "c = app.test_client(); "
            "print(len(json.loads(c.get('/data/builds.json').data)), c.get('/static/style.css').status_code, "
            "c.get('/icons/tango_Guardian.png').status_code)")
    out = subprocess.run([sys.executable, "-c", code, str(root)], cwd=tmp_path, capture_output=True, text=True,
                         env={**os.environ, "PYTHONPATH": ""})
    assert out.returncode == 0, out.stderr[-800:]
    count, css, icon = out.stdout.split()
    assert int(count) >= 28 and css == "200" and icon == "200"


def test_app_loads_as_flat_module_inside_the_package(root, tmp_path):
    """gunicorn app:app started inside gw2ceo/."""
    code = ("import sys, json; sys.path.insert(0, ''); from app import app; "
            "print(len(json.loads(app.test_client().get('/data/builds.json').data)))")
    out = subprocess.run([sys.executable, "-c", code], cwd=root / "gw2ceo", capture_output=True, text=True,
                         env={**os.environ, "PYTHONPATH": ""})
    assert out.returncode == 0, out.stderr[-800:]
    assert int(out.stdout.strip()) >= 28
