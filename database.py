import motor.motor_asyncio
from config import Config

# Connection Setup
client = motor.motor_asyncio.AsyncIOMotorClient(Config.MONGO_URI)
db = client.status_db

# Collections
bots_col = db.mpbots
users_col = db.users_settings

# --- BOTS MANAGEMENT ---

async def add_bot(user_id, name, url, username):
    """Bot ko specific user_id ke under save karne ke liye"""
    await bots_col.update_one(
        {"user_id": user_id, "name": name}, 
        {"$set": {
            "user_id": user_id,
            "name": name, 
            "url": url, 
            "username": username,
            "status": "✅ Online"
        }}, 
        upsert=True
    )

async def remove_bot(user_id, name):
    """Sirf us user ka bot delete hoga"""
    await bots_col.delete_one({"user_id": user_id, "name": name})

async def get_user_bots(user_id):
    """Dashboard ke liye sirf 1 user ke bots nikalna"""
    return bots_col.find({"user_id": user_id})

async def get_all_monitored_bots():
    """Global loop ke liye saare bots fetch karna"""
    return bots_col.find({})

# --- USER SETTINGS & PRODUCTION LOGIC ---

async def update_user_settings(user_id, interval=300, post_link=None):
    """
    User ki settings update karna:
    - interval: seconds mein (120 = 2min, 300 = 5min)
    - post_link: Telegram channel ka message link jahan status dikhega
    """
    update_data = {"user_id": user_id}
    if interval:
        update_data["interval"] = interval
    if post_link:
        update_data["post_link"] = post_link

    await users_col.update_one(
        {"user_id": user_id},
        {"$set": update_data},
        upsert=True
    )

async def get_user_config(user_id):
    """User ka interval aur post_link fetch karne ke liye"""
    return await users_col.find_one({"user_id": user_id})

async def get_all_users_with_settings():
    """Loop ke liye saare users ki configurations nikalna"""
    return users_col.find({})