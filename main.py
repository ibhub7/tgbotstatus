import asyncio, logging, pytz, os, sys
from datetime import datetime
from fastapi import FastAPI
from contextlib import asynccontextmanager

from config import Config
from bot import bot, start_all_tasks 
from plugins.routes import router as web_router

# Update logging to handle file output for the /logs command
logging.basicConfig(
    level=logging.INFO, 
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("MonitorBot")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Start the Telegram Bot
    await bot.start()
    logger.info("Telegram Bot Started!")
    
    # 2. Notify Owner (Persistence check)
    IST = pytz.timezone(Config.TIME_ZONE)
    restart_time = datetime.now(IST).strftime('%H:%M:%S')
    try:
        await bot.send_message(
            Config.OWNER_ID, 
            f"🚀 <b>sʏsᴛᴇᴍ ᴏɴʟɪɴᴇ & sᴛᴀʙʟᴇ</b>\n"
            f"✅ <b>ʜᴇᴀʟᴛʜ ᴄʜᴇᴄᴋs:</b> ᴘᴀssᴇᴅ\n"
            f"⏰ <b>ʀᴇsᴛᴀʀᴛ ᴀᴛ:</b> <code>{restart_time} IST</code>"
        )
    except Exception as e:
        logger.error(f"Failed to send Owner DM: {e}")

    # 3. Start Background Monitoring Tasks
    asyncio.create_task(start_all_tasks())
    
    # 4. Auto-restart Logic  (Triggers every 24 hours)
    async def auto_restart():
        await asyncio.sleep(24 * 3600)
        logger.info("Performing scheduled 24h restart...")
        os.execv(sys.executable, ['python'] + sys.argv)
    
    asyncio.create_task(auto_restart())
    
    yield
    # 5. Clean Shutdown
    logger.info("Stopping Bot...")
    await bot.stop()

# --- INITIALIZE APP ---
app = FastAPI(lifespan=lifespan)

# --- INCLUDE WEB ROUTES ---
# This connects your dashboard and homepage to the FastAPI app
app.include_router(web_router)