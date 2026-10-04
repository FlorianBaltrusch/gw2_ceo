import json
import os

import requests

# the disk cache is read once per process: the builds decode the same
# traits, skills and professions over and over (thousands of small files)
_memory: dict[str, object] = {}


def _read_cached(path: str):
    """The cached JSON for an API path (e.g. "traits/1952"), from memory,
    else from disk (and remembered); None when not cached yet."""
    if path in _memory:
        return _memory[path]
    file_path = os.path.join("assets", "api-cache", *path.split("/"), "data.json")
    if os.path.isfile(file_path):
        with open(file_path) as file:
            data = json.load(file)
        _memory[path] = data
        return data
    return None


def _store(path: str, data) -> None:
    dir_path = os.path.join("assets", "api-cache", *path.split("/"))
    os.makedirs(dir_path, exist_ok=True)
    with open(os.path.join(dir_path, "data.json"), "w") as file:
        json.dump(data, file)
    _memory[path] = data


def get_api_data(path: str):
    data = _read_cached(path)
    if data is not None:
        return data
    data = requests.get("https://api.guildwars2.com/v2/" + path + "?v=latest").json()
    _store(path, data)
    return data


def get_api_data_bulk(endpoint: str, ids: list, chunk_size: int = 200):
    """Fetch many ids from one endpoint, sharing the per-id cache of get_api_data."""
    items = {}
    missing = []
    for id in ids:
        data = _read_cached(f"{endpoint}/{id}")
        if data is not None:
            items[id] = data
        else:
            missing.append(id)

    for chunk_start in range(0, len(missing), chunk_size):
        chunk = missing[chunk_start:chunk_start + chunk_size]
        response = requests.get(
            "https://api.guildwars2.com/v2/" + endpoint
            + "?ids=" + ",".join(str(id) for id in chunk) + "&v=latest"
        ).json()
        for item in response:
            _store(f"{endpoint}/{item['id']}", item)
            items[item["id"]] = item

    return [items[id] for id in ids if id in items]

