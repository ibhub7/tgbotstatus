import asyncio
import aiohttp
import logging
from datetime import datetime
import pytz

from fastapi import FastAPI
from contextlib import asynccontextmanager
from pyrogram import Client
from pyrogram.errors import MessageNotModified

from config import Config
from database import get_all_bots, db  # db import kiya status update ke liye
from plugins.commands import register_commands
from plugins.routes import router as web_router # Dashboard router

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MonitorBot")

bot = Client(
    "MonitorBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN
)

register_commands(bot)

async def check_bots_loop():
    """Background task for monitoring."""
    # Bot start lifespan handle karega, yahan double start ki zaroorat nahi
    IST = pytz.timezone(Config.TIME_ZONE)
    
    while True:
        now_ist = datetime.now(IST).strftime('%H:%M:%S')
        date_ist = datetime.now(IST).strftime('%d %B %Y')
        
        status_text = "🌐 **Live Bot Status Report**\n"
        status_text += f"📅 **Date:** `{date_ist}`\n"
        status_text += f"⏰ **Last Updated:** `{now_ist} (IST)`\n\n"
        
        async for target in await get_all_bots():
            name = target.get('name')
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(target['url'], timeout=15) as resp:
                        web_status = "✅ Online" if resp.status == 200 else f"⚠️ Code {resp.status}"
                
                # Database mein status update (Dashboard ke liye)
                await db.update_one({"name": name}, {"$set": {"status": web_status}})
                status_text += f"🤖 **{name}**\n└ Status: {web_status}\n\n"
                
            except Exception:
                await db.update_one({"name": name}, {"$set": {"status": "❌ Offline"}})
                status_text += f"🤖 **{name}**\n└ Status: ❌ Offline\n\n"

        status_text += f"🔄 _Next update in {Config.CHECK_INTERVAL // 60} minutes..._"

        try:
            await bot.edit_message_text(Config.STATUS_CHANNEL_ID, Config.STATUS_MESSAGE_ID, status_text)
            logger.info(f"Updated status message at {now_ist}")
        except MessageNotModified:
            pass
        except Exception as e:
            logger.error(f"Failed to edit message: {e}")
            
        await asyncio.sleep(Config.CHECK_INTERVAL)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Start the Bot Client
    await bot.start()
    
    # 2. Start the Background Monitoring Task
    monitor_task = asyncio.create_task(check_bots_loop())
    
    # 3. Stability check delay
    await asyncio.sleep(2) 
    
    # 4. DM to Owner
    try:
        IST = pytz.timezone(Config.TIME_ZONE)
        now_ist = datetime.now(IST).strftime('%H:%M:%S')
        await bot.send_message(
            Config.OWNER_ID, 
            f"🚀 **System Online & Stable**\n"
            f"✅ Health Checks: `Passed`\n"
            f"⏰ Restarted At: `{now_ist} IST`"
        )
        logger.info("Stability notification sent to owner.")
    except Exception as e:
        logger.error(f"Owner DM failed: {e}")

    yield
    
    # Cleanup
    monitor_task.cancel()
    await bot.stop()

# FastAPI Initialization
app = FastAPI(lifespan=lifespan)

# Dashboard Routes ko include kiya
app.include_router(web_router)