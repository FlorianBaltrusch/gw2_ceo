"""The HTTP surface through Flask's test client: pages, data endpoints,
images, the solver endpoint."""
import json

import gw2ceo.general_data as gd
from tests.unit.conftest import build_args


def test_pages(client):
    assert b"browse ours" in client.get("/").data
    assert b"site-selection" in client.get("/ceo").data
    assert b"site-left" in client.get("/builds").data
    assert b"site-left" in client.get("/builds/raid-power-chronomancer").data
    page = client.get("/impressum").data
    assert b'id="impressum"' in page and b'id="privacy"' in page and b"info@gw2ceo.com" in page
    assert client.get("/?profession=Guardian&spec=Firebrand").status_code == 302
    for path in ("/", "/ceo", "/builds", "/impressum"):
        head = client.get(path).data
        assert b'name="theme-color"' in head and b"viewport-fit=cover" in head, path


def test_static_and_images(client):
    assert b".site-bar" in client.get("/static/style.css").data
    assert b"--theme-dark" in client.get("/theme.css").data
    assert client.get("/favicon.ico").content_type.startswith("image/")
    assert client.get("/icons/tango_Guardian.png").content_type == "image/png"
    assert client.get("/icons/spec_bg_48.png").content_type == "image/png"
    assert client.get("/profession-images/freigestellt/01_guardian.PNG").content_type.startswith("image/")
    assert client.get("/icons/no_such_icon.png").status_code == 404


def test_data_endpoints(client):
    assert json.loads(client.get("/professions").data) == gd.PROFESSION_ORDER
    specs = json.loads(client.get("/specializations?profession=Elementalist").data)
    assert {s["name"] for s in specs if s["elite"]} >= {"Tempest", "Weaver", "Catalyst", "Evoker"}
    traits = json.loads(client.get("/traits?profession=Thief").data)
    assert traits and all(row["profession"] == "Thief" for row in traits)


def test_builds_api(client):
    listing = json.loads(client.get("/api/builds").data)
    assert len(listing) >= 28 and listing[0]["profession"] == "Elementalist"
    detail = json.loads(client.get("/api/builds/ow-power-vindicator").data)
    assert detail["legends"]["land"][0]["name"] == "Alliance"
    assert len(detail["lines"]) == 3 and detail["gear"]["mode"] == "crit"
    assert client.get("/api/builds/does-not-exist").status_code == 404


def test_chatlink_endpoints(client):
    link = "[&DQYfHSkvMBvHEscSywClEr4BwxJyAHQSJgCZEgAAAAAAAAAAAAAAAAAAAAADWQBWAGcAAA==]"
    decoded = json.loads(client.get("/chatlink/decode", query_string={"link": link}).data)
    assert decoded["profession"] == "Elementalist" and decoded["elite_spec"] == "Tempest"
    assert decoded["selectable_ids"]
    assert client.get("/chatlink/decode?link=nonsense").status_code == 400


def test_calculate_hits_the_cap(client):
    args = build_args("raid-power-deadeye")
    response = client.get("/calculate", query_string=list(args.items(multi=True)))
    assert response.status_code == 200
    result = json.loads(response.data)
    assert result["exact"] is True and abs(result["crit_pct"] - 100) < 1e-6
    assert result["equipment"] and result["rune"]
    assert client.get("/calculate?mode=crit").status_code == 400
