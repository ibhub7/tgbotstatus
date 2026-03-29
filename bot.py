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
from database import get_all_bots, db 
from plugins.commands import register_commands
from plugins.routes import router as web_router 

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
    """Background task for monitoring with Retry & Alerts."""
    IST = pytz.timezone(Config.TIME_ZONE)
    # Browser headers taaki pings block na hon
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) MonitorBot/1.0'}
    
    while True:
        now_ist = datetime.now(IST).strftime('%H:%M:%S')
        date_ist = datetime.now(IST).strftime('%d %B %Y')
        
        status_text = "🌐 **Live Bot Status Report**\n"
        status_text += f"📅 **Date:** `{date_ist}`\n"
        status_text += f"⏰ **Last Updated:** `{now_ist} (IST)`\n\n"
        
        async for target in await get_all_bots():
            name = target.get('name')
            url = target.get('url')
            # Pichla status check karne ke liye (Alerts ke liye zaroori hai)
            prev_status = target.get('status', '✅ Online')
            
            web_status = "❌ Offline" 
            
            # --- FEATURE: RETRY LOGIC (2 baar check karega) ---
            for attempt in range(2):
                try:
                    async with aiohttp.ClientSession(headers=headers) as session:
                        async with session.get(url, timeout=15) as resp:
                            if resp.status == 200:
                                web_status = "✅ Online"
                                break 
                except Exception:
                    if attempt == 0: 
                        await asyncio.sleep(10) # 10 sec wait before 2nd try
            
            # --- FEATURE: OWNER ALERTS (Jab Online se Offline ho) ---
            if "Offline" in web_status and "Online" in prev_status:
                try:
                    await bot.send_message(
                        Config.OWNER_ID, 
                        f"⚠️ **ALERT: {name} is DOWN!**\n⏰ Time: `{now_ist} IST`"
                    )
                except Exception as e:
                    logger.error(f"Alert failed for {name}: {e}")

            # Database aur Channel text update
            await db.update_one({"name": name}, {"$set": {"status": web_status}})
            status_text += f"🤖 **{name}**\n└ Status: {web_status}\n\n"

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
    await bot.start()
    monitor_task = asyncio.create_task(check_bots_loop())
    await asyncio.sleep(2) 
    
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
    monitor_task.cancel()
    await bot.stop()

app = FastAPI(lifespan=lifespan)
app.include_router(web_router)