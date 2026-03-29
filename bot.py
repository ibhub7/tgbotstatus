import asyncio
import aiohttp
import logging
import re
import os
import sys
from datetime import datetime
import pytz

from fastapi import FastAPI
from contextlib import asynccontextmanager
from pyrogram import Client, enums
from pyrogram.errors import MessageNotModified, FloodWait

from config import Config
from database import get_user_bots, get_all_users_with_settings, bots_col
from plugins.routes import router as web_router 

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MonitorBot")

# --- GLOBAL TASK MANAGER ---
# Isse commands.py se access kiya ja sakega
active_tasks = {}

bot = Client(
    "MonitorBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins"),
    in_memory=True
)

# --- HELPER: PARSE TELEGRAM LINK ---
def parse_tg_link(link):
    try:
        parts = link.split('/')
        msg_id = int(parts[-1])
        chat_val = parts[-2]
        if chat_val.isdigit():
            chat_id = int(f"-100{chat_val}")
        else:
            chat_id = f"@{chat_val}"
        return chat_id, msg_id
    except:
        return None, None

# --- CORE MONITORING FUNCTION ---
async def monitor_user_task(user_id, interval, post_link):
    """Har user ke liye alag se chalne wala task"""
    IST = pytz.timezone(Config.TIME_ZONE)
    headers = {'User-Agent': 'Mozilla/5.0 MonitorBot/2.0'}
    
    while True:
        try:
            now_ist = datetime.now(IST).strftime('%H:%M:%S')
            status_text = f"🌐 <b>Live Status Report</b>\n⏰ <b>Sync:</b> <code>{now_ist} IST</code>\n\n"
            
            cursor = await get_user_bots(user_id)
            user_bots = await cursor.to_list(length=None)
            
            if not user_bots:
                await asyncio.sleep(600)
                continue

            for target in user_bots:
                name = target.get('name')
                url = target.get('url')
                username = target.get('username', 'bot')
                prev_status = target.get('status', '✅ Online')
                
                web_status = "❌ Offline"
                try:
                    async with aiohttp.ClientSession(headers=headers) as session:
                        async with session.get(url, timeout=10) as resp:
                            if resp.status == 200: web_status = "✅ Online"
                except:
                    pass

                await bots_col.update_one({"user_id": user_id, "name": name}, {"$set": {"status": web_status}})
                status_text += f"🤖 <b><a href='https://t.me/{username}'>{name}</a></b>: {web_status}\n"

                if "Offline" in web_status and "Online" in prev_status:
                    try:
                        await bot.send_message(user_id, f"⚠️ <b>ALERT: {name} is DOWN!</b>")
                    except: pass

            if post_link:
                chat_id, msg_id = parse_tg_link(post_link)
                if chat_id and msg_id:
                    try:
                        await bot.edit_message_text(chat_id, msg_id, status_text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                    except MessageNotModified: pass
                    except FloodWait as e: await asyncio.sleep(e.value)
                    except Exception as e: logger.error(f"Channel update failed for {user_id}: {e}")

        except Exception as e:
            logger.error(f"Error in task for {user_id}: {e}")
        
        await asyncio.sleep(interval)

# --- STARTUP LOGIC ---
async def start_all_tasks():
    cursor = await get_all_users_with_settings()
    async for user_cfg in cursor:
        uid = user_cfg['user_id']
        inv = user_cfg.get('interval', 300)
        lnk = user_cfg.get('post_link')
        active_tasks[uid] = asyncio.create_task(monitor_user_task(uid, inv, lnk))

@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.start()
    asyncio.create_task(start_all_tasks())
    
    # --- 24 HOUR AUTO-RESTART LOGIC ---
    async def auto_restart():
        await asyncio.sleep(24 * 3600) 
        logger.info("24 Hours Completed: Restarting Bot to sync all data...")
        os.execv(sys.executable, ['python'] + sys.argv)
        
    asyncio.create_task(auto_restart())
    
    logger.info("SaaS Monitor Engine & Auto-Restart Task Started")
    yield
    for task in active_tasks.values():
        task.cancel()
    await bot.stop()

app = FastAPI(lifespan=lifespan)
app.include_router(web_router)