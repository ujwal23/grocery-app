import json
import os
from models import GroceryItem

FILE_NAME = "data.json"
CURRENCY = "₹"


def load_data():
    if not os.path.exists(FILE_NAME):
        return []

    try:
        with open(FILE_NAME, "r") as file:
            raw = json.load(file)
            return [GroceryItem.from_dict(item) for item in raw]

    except (json.JSONDecodeError, KeyError):
        print("Warning: data file is corrupted. Starting fresh.")
        return []


def save_data(grocery_list):
    with open(FILE_NAME, "w") as file:
        data = [item.to_dict() for item in grocery_list]
        json.dump(data, file, indent=4)