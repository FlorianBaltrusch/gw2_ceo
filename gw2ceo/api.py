import os
import json
import requests


def get_api_data(path: str):
    dir_path = os.path.join("assets", "api-cache", *path.split("/"))
    file_path = os.path.join(dir_path, "data.json")
    if os.path.isfile(file_path):
        return json.load(open(file_path))
    else:
        data = requests.get(
            "https://api.guildwars2.com/v2/" + path + "?v=latest"
        ).json()
        os.makedirs(dir_path, exist_ok=True)
        json.dump(data, open(file_path, "w"))
        return data


def get_api_data_bulk(endpoint: str, ids: list, chunk_size: int = 200):
    """Fetch many ids from one endpoint, sharing the per-id disk cache of get_api_data."""
    items = {}
    missing = []
    for id in ids:
        file_path = os.path.join("assets", "api-cache", endpoint, str(id), "data.json")
        if os.path.isfile(file_path):
            items[id] = json.load(open(file_path))
        else:
            missing.append(id)

    for chunk_start in range(0, len(missing), chunk_size):
        chunk = missing[chunk_start:chunk_start + chunk_size]
        response = requests.get(
            "https://api.guildwars2.com/v2/" + endpoint
            + "?ids=" + ",".join(str(id) for id in chunk) + "&v=latest"
        ).json()
        for item in response:
            dir_path = os.path.join("assets", "api-cache", endpoint, str(item["id"]))
            os.makedirs(dir_path, exist_ok=True)
            json.dump(item, open(os.path.join(dir_path, "data.json"), "w"))
            items[item["id"]] = item

    return [items[id] for id in ids if id in items]

