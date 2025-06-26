from pydantic import BaseModel
import json

class Item(BaseModel):
    name: str
    description: str | None = None
    price: float
    tax: float | None = None
    tags: list[str] = []

item = Item(name="Example Item", price=10.99, tax=0.5)

# Using model_dump_json()
item_json_str = item.model_dump_json()
print(item_json_str)

# Using model_dump() and json.dumps()
item_dict = item.model_dump()
item_json_str = json.dumps(item_dict)
print(item_dict)

# Using model_dump() with include/exclude
item_json_str = json.dumps(item.model_dump(exclude={'tax'}))
print(item_json_str)