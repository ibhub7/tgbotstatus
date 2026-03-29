from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

client = AsyncIOMotorClient(Config.MONGO_URI)
db = client.status_db.bots

async def add_bot(name, url, username):
    await db.update_one(
        {"username": username}, 
        {"$set": {"name": name, "url": url, "username": username}}, 
        upsert=True
    )

async def remove_bot(name):
    return await db.delete_one({"name": name})

async def get_all_bots():
    return db.find()