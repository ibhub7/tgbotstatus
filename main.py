import os
import asyncio
import aiohttp
import logging
import re
from datetime import datetime
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

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client.status_db.bots
bot = Client("MonitorBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

async def check_bots():
    await bot.start()
    while True:
        status_text = "🌐 **Live Bot Status Report**\n"
        status_text += f"Last Updated: `{datetime.now().strftime('%H:%M:%S')}`\n\n"
        
        async for target in db.find():
            try:
                async with aiohttp.ClientSession() as session:
                    # Only pinging the URL now
                    async with session.get(target['url'], timeout=15) as resp:
                        web_status = "✅ Online" if resp.status == 200 else f"⚠️ {resp.status}"
                
                status_text += f"🤖 **{target['name']}**\n├ Status: {web_status}\n└ [Link]({target['url']})\n\n"
            except Exception as e:
                status_text += f"🤖 **{target['name']}**\n└ ❌ **Offline/Error**\n\n"

        try:
            await bot.edit_message_text(STATUS_CHANNEL_ID, STATUS_MESSAGE_ID, status_text, disable_web_page_preview=True)
        except Exception as e:
            logger.error(f"Edit Error: {e}")
            
        await asyncio.sleep(60)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(check_bots())
    yield
    task.cancel()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health(): return {"status": "running"}

# --- UPDATED COMMANDS ---

@bot.on_message(filters.command("addbot") & filters.private)
async def add_bot_logic(client, message):
    # Expected format: /addbot "Bot Name" https://url.com
    # Uses regex to find text inside quotes for the name
    input_text = message.text.split(maxsplit=1)
    if len(input_text) < 2:
        return await message.reply("Usage: `/addbot \"Bot Name\" URL`")

    # Extract name between quotes and the URL following it
    match = re.search(r'"([^"]+)"\s+(https?://\S+)', message.text)
    if match:
        name = match.group(1)
        url = match.group(2)
        await db.update_one({"name": name}, {"$set": {"url": url}}, upsert=True)
        await message.reply(f"✅ Now monitoring: **{name}**\nURL: {url}")
    else:
        await message.reply("❌ Error! Please use quotes for the name.\nExample: `/addbot \"Pro Movie Bot\" https://link.com` ")

@bot.on_message(filters.command("removebot") & filters.private)
async def remove_bot_logic(client, message):
    # Usage: /removebot "Bot Name"
    match = re.search(r'"([^"]+)"', message.text)
    if match:
        name = match.group(1)
        result = await db.delete_one({"name": name})
        if result.deleted_count:
            await message.reply(f"🗑 Removed **{name}** from database.")
        else:
            await message.reply("❌ Bot not found.")
    else:
        await message.reply("Usage: `/removebot \"Bot Name\"` (Use quotes)")