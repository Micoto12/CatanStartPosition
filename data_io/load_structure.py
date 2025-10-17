import json

def load_structure(filename="structure.json"):
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)