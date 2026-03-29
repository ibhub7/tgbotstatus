import asyncio
import aiohttp
import logging
from datetime import datetime
import pytz

from fastapi import FastAPI
from contextlib import asynccontextmanager
from pyrogram import Client

from config import Config
from database import get_all_bots
from plugins.commands import register_commands

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MonitorBot")

bot = Client(
    "MonitorBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

# Register our commands
register_commands(bot)

async def check_bots_loop():
    await bot.start()
    IST = pytz.timezone(Config.TIME_ZONE)
    
    while True:
        now_ist = datetime.now(IST).strftime('%H:%M:%S')
        date_ist = datetime.now(IST).strftime('%d %B %Y')
        
        status_text = "🌐 **Live Bot Status Report**\n"
        status_text += f"📅 **Date:** `{date_ist}`\n"
        status_text += f"⏰ **Last Updated:** `{now_ist} (IST)`\n\n"
        
        async for target in await get_all_bots():
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(target['url'], timeout=15) as resp:
                        web_status = "✅ **Online**" if resp.status == 200 else f"⚠️ **Code {resp.status}**"
                
                status_text += f"🤖 **{target['name']}**\n└ Status: {web_status}\n\n"
            except Exception:
                status_text += f"🤖 **{target['name']}**\n└ Status: ❌ **Offline**\n\n"

        status_text += f"🔄 _Next update in {Config.CHECK_INTERVAL // 60} minutes..._"

        try:
            await bot.edit_message_text(Config.STATUS_CHANNEL_ID, Config.STATUS_MESSAGE_ID, status_text)
            logger.info(f"Updated status message at {now_ist}")
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            
        await asyncio.sleep(Config.CHECK_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(check_bots_loop())
    yield
    task.cancel()
    await bot.stop()

app = FastAPI(lifespan=lifespan)

@app.get("/")
async def health():
    return {"status": "Monitor is running"}
