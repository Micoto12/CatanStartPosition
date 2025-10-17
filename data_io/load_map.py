import json

def load_map_from_json(filename="map_data.json"):
    with open(filename, "r", encoding="utf-8") as f:
        data = json.load(f)
    map_data = {}
    for key, value in data["hexes"].items():
        q, r = map(int, key.split(","))
        map_data[(q, r)] = value
    return map_data