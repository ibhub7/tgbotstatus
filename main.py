import os
import asyncio
import aiohttp
import logging
from datetime import datetime
from contextlib import asynccontextmanager
from fastapi import FastAPI
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv()

# --- LOGGING SETUP ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("MonitorBot")

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
    logger.info("Starting Telegram Bot client...")
    await bot.start()
    logger.info("Bot client started. Entering status check loop.")
    
    while True:
        status_text = "🌐 **Live Bot Status Report**\n"
        status_text += f"Last Updated: `{datetime.now().strftime('%H:%M:%S')}`\n\n"
        
        bot_count = 0
        async for target in db.find():
            bot_count += 1
            logger.info(f"Checking status for: {target['name']} ({target['url']})")
            
            try:
                async with aiohttp.ClientSession() as session:
                    # Check Web URL
                    async with session.get(target['url'], timeout=10) as resp:
                        web = "✅" if resp.status == 200 else "❌"
                        logger.info(f"Web check for {target['name']}: {resp.status}")
                    
                    # Check API
                    tg_api = f"https://api.telegram.org/bot{target['token']}/getMe"
                    async with session.get(tg_api) as resp:
                        api = "✅" if resp.status == 200 else "❌"
                        logger.info(f"API check for {target['name']}: {resp.status}")
                
                status_text += f"🤖 **{target['name']}**\n├ Host: {web} | API: {api}\n└ [Link]({target['url']})\n\n"
            except Exception as e:
                logger.error(f"Error checking {target['name']}: {e}")
                status_text += f"🤖 **{target['name']}**\n└ ❌ **Down/Error**\n\n"

        if bot_count == 0:
            logger.warning("No bots found in database to monitor.")
            status_text += "_No bots added yet. Use /addbot in private._"

        try:
            await bot.edit_message_text(STATUS_CHANNEL_ID, STATUS_MESSAGE_ID, status_text, disable_web_page_preview=True)
            logger.info("Status message updated successfully in channel.")
        except Exception as e:
            logger.error(f"Failed to edit status message: {e}")
            
        await asyncio.sleep(60)

# --- WEB APP ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Start background task
    task = asyncio.create_task(check_bots())
    yield
    # Cleanup
    task.cancel()
    await bot.stop()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health_check():
    return {"status": "Monitor is Running", "timestamp": datetime.now().isoformat()}

@bot.on_message(filters.command("addbot") & filters.private)
async def add_bot_logic(client, message):
    try:
        _, name, url, token = message.text.split(maxsplit=3)
        await db.update_one({"name": name}, {"$set": {"url": url, "token": token}}, upsert=True)
        logger.info(f"User {message.from_user.id} added/updated bot: {name}")
        await message.reply(f"✅ Monitoring **{name}**")
    except Exception as e:
        logger.warning(f"Failed addbot attempt by {message.from_user.id}: {e}")
        await message.reply("Usage: `/addbot Name URL Token`")