import json
from pathlib import Path


def load_items(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data["items"]


def get_unclaimed_items(items):
    return [item for item in items if item.get("status") == "unclaimed"]


def save_result(result, filename):
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)
