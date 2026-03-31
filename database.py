import motor.motor_asyncio
from config import Config

client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
db = client.status_db

# Collections
bots_col = db.mpbots
users_settings = db.users_settings
registered_users = db.registered_users 

# --- DATABASE INITIALIZATION ---
async def init_db():
    """Run this on startup for faster queries"""
    await bots_col.create_index([("user_id", 1), ("name", 1)], unique=True)
    await registered_users.create_index("user_id", unique=True)

# --- BOTS MANAGEMENT ---
async def add_bot(user_id, name, url, username):
    await bots_col.update_one(
        {"user_id": user_id, "name": name}, 
        {"$set": {
            "user_id": user_id, "name": name, "url": url, 
            "username": username, "status": "✅ Online"
        }}, upsert=True
    )

async def remove_bot(user_id, name):
    await bots_col.delete_one({"user_id": user_id, "name": name})

async def get_user_bots(user_id):
    return bots_col.find({"user_id": user_id})

async def delete_all_user_bots(user_id):
    """Resets user account"""
    return await bots_col.delete_many({"user_id": user_id})

# --- USER SETTINGS ---
async def get_user_config(user_id):
    return await users_settings.find_one({"user_id": user_id})

# --- USER SETTINGS & BROADCAST ---
async def add_user(user_id):
    """Save user for broadcast when they /start"""
    await registered_users.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

async def get_all_users():
    """Returns a cursor of all registered users for broadcasting"""
    return registered_users.find({})

async def update_user_settings(user_id, interval=None, post_link=None):
    data = {}
    if interval: data["interval"] = interval
    if post_link: data["post_link"] = post_link
    await users_settings.update_one({"user_id": user_id}, {"$set": data}, upsert=True)
    
async def delete_all_user_bots(user_id):
    """Useful if a user wants to reset their account"""
    await bots_col.delete_many({"user_id": user_id})

async def get_user_config_web(user_id):
    """Alias for dashboard to prevent import errors"""
    return await get_user_config(user_id)

async def update_user_settings(user_id, interval=None, post_link=None):
    data = {}
    if interval: data["interval"] = interval
    if post_link: data["post_link"] = post_link
    await users_settings.update_one({"user_id": user_id}, {"$set": data}, upsert=True)