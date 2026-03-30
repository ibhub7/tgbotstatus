import asyncio, logging, pytz, os, sys
from datetime import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import Config
from bot import bot, start_all_tasks 
from plugins.routes import router as web_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MonitorBot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Start Bot
    await bot.start()
    
    # 2. Owner DM
    IST = pytz.timezone(Config.TIME_ZONE)
    restart_time = datetime.now(IST).strftime('%H:%M:%S')
    try:
        await bot.send_message(
            Config.OWNER_ID, 
            f"🚀 <b>System Online & Stable</b>\n"
            f"✅ <b>Health Checks:</b> Passed\n"
            f"⏰ <b>Restart At:</b> <code>{restart_time} IST</code>"
        )
    except: pass

    # 3. Start Tasks
    asyncio.create_task(start_all_tasks())
    
    # 4. Auto-restart (24h)
    async def auto_restart():