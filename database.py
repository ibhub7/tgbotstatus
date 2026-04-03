import motor.motor_asyncio
from config import Config

# Initialize MongoDB Client 
client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
db = client.status_db

# Collections 
bots_col = db.mpbots
users_settings = db.users_settings
registered_users = db.registered_users 

# --- 𝙳𝙰𝚃𝙰𝙱𝙰𝚂𝙴 𝙸𝙽𝙸𝚃𝙸𝙰𝙻𝙸𝚉𝙰𝚃𝙸𝙾𝙽 ---
async def init_db():
    """Run this on startup for faster queries and data integrity"""
    await bots_col.create_index([("user_id", 1), ("name", 1)], unique=True)
    await registered_users.create_index("user_id", unique=True)

# --- 𝙱𝙾𝚃𝚂 𝙼𝙰𝙽𝙰𝙶𝙴𝙼𝙴𝙽𝚃 ---
async def add_bot(user_id, name, url, username):
    """Add or update a monitored bot"""
    return await bots_col.update_one(
        {"user_id": user_id, "name": name}, 
        {"$set": {
            "user_id": user_id, "name": name, "url": url, 
            "username": username, "status": "✅ Online"
        }}, upsert=True
    )

async def remove_bot(user_id, username):
    """Remove a specific bot using its username"""
    return await bots_col.delete_one({"user_id": user_id, "username": username})

async def get_user_bots(user_id):
    """Returns a cursor of bots for a specific user"""
    return bots_col.find({"user_id": user_id})

async def delete_all_user_bots(user_id):
    """Resets user account by deleting all their bots"""
    return await bots_col.delete_many({"user_id": user_id})

# --- 𝚄𝚂𝙴𝚁 𝚂𝙴𝚃𝚃𝙸𝙽𝙶𝚂 ---
async def get_user_config(user_id):
    return await users_settings.find_one({"user_id": user_id})

async def get_user_config_web(user_id):
    return await get_user_config(user_id)

async def update_user_settings(user_id, ping_interval=None, msg_interval=None, post_link=None):
    data = {}
    if ping_interval is not None: data["ping_interval"] = ping_interval
    if msg_interval is not None: data["msg_interval"] = msg_interval
    if post_link is not None: data["post_link"] = post_link
    await users_settings.update_one({"user_id": user_id}, {"$set": data}, upsert=True)

async def reset_user_intervals(user_id):
    """𝚁𝙴𝙼𝙾𝚅𝙴𝚂 𝙲𝚄𝚂𝚃𝙾𝙼 𝚃𝙸𝙼𝙸𝙽𝙶𝚂 𝚂𝙾 𝚂𝚈𝚂𝚃𝙴𝙼 𝚄𝚂𝙴𝚂 𝙲𝙾𝙽𝙵𝙸𝙶 𝙳𝙴𝙵𝙰𝚄𝙻𝚃𝚂"""
    return await users_settings.update_one(
        {"user_id": user_id}, 
        {"$unset": {"ping_interval": "", "msg_interval": ""}}
    )

async def add_user(user_id):
    await registered_users.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

async def get_all_users():
    return registered_users.find({})