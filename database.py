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
    """Run this on startup for faster queries and data integrity """
    # Ensures no duplicate bot names for the same user 
    await bots_col.create_index([("user_id", 1), ("name", 1)], unique=True)
    # Fast lookup for registered users 
    await registered_users.create_index("user_id", unique=True)

# --- 𝙱𝙾𝚃𝚂 𝙼𝙰𝙽𝙰𝙶𝙴𝙼𝙴𝙽𝚃 ---
async def add_bot(user_id, name, url, username):
    """Add or update a monitored bot """
    await bots_col.update_one(
        {"user_id": user_id, "name": name}, 
        {"$set": {
            "user_id": user_id, "name": name, "url": url, 
            "username": username, "status": "✅ Online"
        }}, upsert=True
    )

async def remove_bot(user_id, name):
    """Remove a specific bot """
    await bots_col.delete_one({"user_id": user_id, "name": name})

async def get_user_bots(user_id):
    """Returns a cursor of bots for a specific user """
    return bots_col.find({"user_id": user_id})

async def delete_all_user_bots(user_id):
    """Resets user account by deleting all their bots """
    return await bots_col.delete_many({"user_id": user_id})

# --- 𝚄𝚂𝙴𝚁 𝚂𝙴𝚃𝚃𝙸𝙽𝙶𝚂 ---
async def get_user_config(user_id):
    """Fetch interval and post link settings """
    return await users_settings.find_one({"user_id": user_id})

async def get_user_config_web(user_id):
    """Alias for dashboard routes """
    return await get_user_config(user_id)

async def update_user_settings(user_id, interval=None, post_link=None):
    """Update monitoring interval or live post link """
    data = {}
    if interval is not None: data["interval"] = interval
    if post_link is not None: data["post_link"] = post_link
    await users_settings.update_one({"user_id": user_id}, {"$set": data}, upsert=True)

# --- 𝚁𝙴𝙶𝙸𝚂𝚃𝙴𝚁𝙴𝙳 𝚄𝚂𝙴𝚁𝚂 (𝙱𝚁𝙾𝙰𝙳𝙲𝙰𝚂𝚃) ---
async def add_user(user_id):
    """Save user for broadcast when they interact with the bot """
    await registered_users.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}}, upsert=True)

async def get_all_users():
    """Returns a cursor of all users for broadcasting messages """
    return registered_users.find({})