import asyncio, aiohttp, logging, pytz
from datetime import datetime
from pyrogram import Client, enums
from pyrogram.errors import MessageNotModified, FloodWait
from config import Config
from database import bots_col, users_settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("MonitorBot")

active_tasks = {}

bot = Client(
    "MonitorBot", 
    api_id=Config.API_ID, 
    api_hash=Config.API_HASH, 
    bot_token=Config.BOT_TOKEN, 
    plugins=dict(root="plugins"), 
    in_memory=True,
    sleep_threshold=60 
)

def parse_tg_link(link):
    try:
        parts = link.split('/')
        msg_id = int(parts[-1])
        chat_val = parts[-2]
        chat_id = int(f"-100{chat_val}") if chat_val.isdigit() else f"@{chat_val}"
        return chat_id, msg_id
    except: 
        return None, None

async def monitor_user_task(user_id, interval, post_link):
    IST = pytz.timezone(Config.TIME_ZONE)
    headers = {'User-Agent': 'MonitorBot/3.0'}
    while True:
        try:
            now_ist = datetime.now(IST).strftime('%d/%m/%Y\n%H:%M:%S')
            status_text = (
                "🌐 <b>ʟɪᴠᴇ ʙᴏᴛ sᴛᴀᴛᴜs</b>\n"
                f"⏰ <b>ʟᴀsᴛ sʏɴᴄ:</b> <code>{now_ist} IST</code>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            )

            cursor = bots_col.find({"user_id": user_id})
            user_bots = await cursor.to_list(length=None) 
            
            if not user_bots:
                await asyncio.sleep(600)
                continue

            for target in user_bots:
                name, url, username = target['name'], target['url'], target.get('username', 'bot')
                prev_status = target.get('status', '✅ Online')
                web_status = "❌ Offline"

                try:
                    async with aiohttp.ClientSession(headers=headers) as session:
                        async with session.get(url, timeout=10) as resp:
                            if resp.status == 200:
                                web_status = "✅ Online"
                except:
                    pass

                # --- NEW: STATUS CHANGE ALERTS ---
                if web_status != prev_status:
                    if "Offline" in web_status:
                        alert = f"⚠️ <b>ᴀʟᴇʀᴛ: {name} ɪs ᴅᴏᴡɴ!</b>"
                    else:
                        alert = f"✅ <b>ʀᴇᴄᴏᴠᴇʀᴇᴅ: {name} ɪs ʙᴀᴄᴋ ᴏɴʟɪɴᴇ!</b>"
                    
                    try:
                        await bot.send_message(user_id, alert)
                    except:
                        pass

                await bots_col.update_one(
                    {"user_id": user_id, "name": name},
                    {"$set": {"status": web_status}}
                )
                
                icon = "🟢" if "Online" in web_status else "🔴"
                status_text += (
                    f"{icon} <b><a href='https://t.me/{username}'>{name}</a></b>\n"
                    f"   └ sᴛᴀᴛᴜs: {web_status}\n\n"
                )

            status_text += "━━━━━━━━━━━━━━━━━━━━━━━\n"
            status_text += f"🔄 <i>ᴀᴜᴛᴏ ʀᴇғʀᴇsʜ ᴇᴠᴇʀʏ {interval//60} ᴍɪɴ</i>"

            if post_link:
                cid, mid = parse_tg_link(post_link)
                if cid and mid:
                    try:
                        await bot.edit_message_text(cid, mid, status_text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                    except (MessageNotModified, FloodWait):
                        pass

        except Exception as e:
            logger.error(f"Task Error {user_id}: {e}")

        await asyncio.sleep(interval)

async def start_all_tasks():
    uids = await bots_col.distinct("user_id")
    for uid in uids:
        cfg = await users_settings.find_one({"user_id": uid})
        inv = cfg.get('interval', 300) if cfg else 300
        lnk = cfg.get('post_link') if cfg else None
        if uid not in active_tasks or active_tasks[uid].done():
            active_tasks[uid] = asyncio.create_task(monitor_user_task(uid, inv, lnk))
    logger.info(f"Initialized {len(uids)} monitoring tasks.")