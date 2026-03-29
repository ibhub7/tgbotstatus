import os
import asyncio
import aiohttp
import logging
import re
from datetime import datetime
import pytz  # Make sure to add 'pytz' to requirements.txt

from contextlib import asynccontextmanager
from fastapi import FastAPI
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MonitorBot")

# --- CONFIG ---
API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
MONGO_URI = os.getenv("MONGO_URI", "")
STATUS_CHANNEL_ID = int(os.getenv("STATUS_CHANNEL_ID", 0))
STATUS_MESSAGE_ID = int(os.getenv("STATUS_MESSAGE_ID", 0))
TIME_ZONE = "Asia/Kolkata"

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.status_db.bots
bot = Client("MonitorBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def check_bots():
    await bot.start()
    IST = pytz.timezone(TIME_ZONE)
    
    while True:
        # Get current time in Kolkata
        now_ist = datetime.now(IST).strftime('%H:%M:%S')
        date_ist = datetime.now(IST).strftime('%d %B %Y')
        
        status_text = "🌐 **Live Bot Status Report**\n"
        status_text += f"📅 Date: `{date_ist}`\n"
        status_text += f"⏰ Last Updated: `{now_ist} (IST)`\n\n"
        
        async for target in db.find():
            try:
                async with aiohttp.ClientSession() as session:
                    # Ping URL (Koyeb/Render)
                    async with session.get(target['url'], timeout=15) as resp:
                        web_status = "✅ Online" if resp.status == 200 else f"⚠️ Code {resp.status}"
                
                status_text += f"🤖 **{target['name']}**\n├ Status: {web_status}\n└ [Link]({target['url']})\n\n"
            except Exception:
                status_text += f"🤖 **{target['name']}**\n└ ❌ **Offline/Error**\n\n"

        status_text += "🔄 _Next update in 5 minutes..._"

        try:
            # This EDITS the message ID you provided in the ENV
            await bot.edit_message_text(STATUS_CHANNEL_ID, STATUS_MESSAGE_ID, status_text, disable_web_page_preview=True)
            logger.info(f"Updated status message at {now_ist}")
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            
        # Wait for 5 minutes (300 seconds)
        await asyncio.sleep(300)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(check_bots())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health(): return {"status": "running"}

# --- COMMANDS FOR MULTI-STRING NAMES ---

@bot.on_message(filters.command("addbot") & filters.private)
async def add_bot_logic(client, message):
    # Matches: /addbot "Multi Word Name" https://url.com
    match = re.search(r'"([^"]+)"\s+(https?://\S+)', message.text)
    if match:
        name, url = match.group(1), match.group(2)
        await db.update_one({"name": name}, {"$set": {"url": url}}, upsert=True)
        await message.reply(f"✅ Added **{name}** to the 5-min monitor cycle.")
    else:
        await message.reply("Format: `/addbot \"Bot Name\" URL` (Use quotes for names)")

@bot.on_message(filters.command("removebot") & filters.private)
async def remove_bot_logic(client, message):
    match = re.search(r'"([^"]+)"', message.text)
    if match:
        name = match.group(1)
        await db.delete_one({"name": name})
        await message.reply(f"🗑 Removed **{name}**.")
    else:
        await message.reply("Format: `/removebot \"Bot Name\"` (Use quotes)")