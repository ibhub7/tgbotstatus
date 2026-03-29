import os
import asyncio
import aiohttp
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# --- CONFIG ---
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID", 0))
STATUS_MESSAGE_ID = int(os.getenv("STATUS_MESSAGE_ID", 0))

# --- DB & BOT SETUP ---
db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.status_db.bots
bot = Client("MonitorBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- BACKGROUND TASK ---
async def check_bots():
    await bot.start()
    while True:
        status_text = "🌐 **Live Bot Status Report**\n"
        status_text += f"Last Updated: `{datetime.now().strftime('%H:%M:%S')}`\n\n"
        
        async for target in db.find():
            try:
                async with aiohttp.ClientSession() as session:
                    # Check URL
                    async with session.get(target['url'], timeout=10) as resp:
                        web = "✅" if resp.status == 200 else "❌"
                    # Check API
                    async with session.get(f"https://api.telegram.org/bot{target['token']}/getMe") as resp:
                        api = "✅" if resp.status == 200 else "❌"
                
                status_text += f"🤖 **{target['name']}**\n├ Host: {web} | API: {api}\n└ [Link]({target['url']})\n\n"
            except:
                status_text += f"🤖 **{target['name']}**\n└ ❌ **Down/Error**\n\n"

        try:
            await bot.edit_message_text(STATUS_CHANNEL_ID, STATUS_MESSAGE_ID, status_text, disable_web_page_preview=True)
        except: pass
        await asyncio.sleep(60)

# --- WEB APP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    loop = asyncio.get_event_loop()
    loop.create_task(check_bots())
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health_check():
    return {"status": "Monitor is Running"}

@bot.on_message(filters.command("addbot") & filters.private)
async def add_bot_logic(client, message):
    try:
        _, name, url, token = message.text.split(maxsplit=3)
        await db.update_one({"name": name}, {"$set": {"url": url, "token": token}}, upsert=True)
        await message.reply(f"✅ Monitoring **{name}**")
    except:
        await message.reply("Usage: `/addbot Name URL Token`")
