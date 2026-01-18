import os
import json
import requests


def get_api_data(path: str):
    dir_path = os.path.join("assets", "api-cache", *path.split("/"))
    file_path = os.path.join(dir_path, "data.json")
    if os.path.isfile(file_path):
        print("File Access")
        return json.load(open(file_path))
    else:
        print("Online Access")
        data = requests.get(
            "https://api.guildwars2.com/v2/" + path + "?v=latest"
        ).json()
        os.makedirs(dir_path, exist_ok=True)
        json.dump(data, open(file_path, "w"))
        return data

