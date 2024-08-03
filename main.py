import os

from fastapi import FastAPI, HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from bson import ObjectId
import uvicorn

app = FastAPI()

# db setup
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.inventory
collection = db.items

class Item(BaseModel):
    name: str
    count: int
    partnum: str

class ItemDbo(Item):
    id: str

def item_helper(item) -> dict:
    return {
        "id": str(item["_id"]),
        "name": item["name"],
        "count": item["count"],
        "partnum": item["partnum"]
    }

@app.get("/items/", response_model=list[ItemDbo])
async def get_items():
    items = await collection.find().to_list(100)
    return [item_helper(item) for item in items]

@app.post("/items/", response_model=ItemDbo)
async def create_item(item: Item):
    new_item = await collection.insert_one(item.dict())
    created_item = await collection.find_one({"_id": new_item.inserted_id})
    return item_helper(created_item)

@app.get("/items/{item_id}", response_model=ItemDbo)
async def get_item(item_id: str):
    item = await collection.find_one({"_id": ObjectId(item_id)})
    if item:
        return item_helper(item)
    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/items/{item_id}", response_model=ItemDbo)
async def update_item(item_id: str, item: Item):
    updated_item = await collection.find_one_and_update(
        {"_id": ObjectId(item_id)},
        {"$set": item.dict()},
        return_document=True
    )
    if updated_item:
        return item_helper(updated_item)
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    delete_result = await collection.delete_one({"_id": ObjectId(item_id)})
    if delete_result.deleted_count:
        return {"message": "Item deleted successfully"}
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)