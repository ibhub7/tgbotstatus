import asyncio, aiohttp, logging, pytz, time
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

async def monitor_user_task(user_id, ping_interval, msg_interval, post_link):
    IST = pytz.timezone(Config.TIME_ZONE)
    headers = {'User-Agent': 'MonitorBot/3.0'}
    last_msg_update = 0  

    while True:
        try:
            now_ts = time.time()
            cursor = bots_col.find({"user_id": user_id})
            user_bots = await cursor.to_list(length=None) 
            
            if not user_bots:
                await asyncio.sleep(60)
                continue

            # --- 𝟷. ᴘɪɴɢ ᴘʜᴀꜱᴇ (ᴜʀʟ ᴄʜᴇᴄᴋ) ---
            for target in user_bots:
                name, url, username = target['name'], target['url'], target.get('username', 'bot')
                # Updated to Small Caps
                prev_status = target.get('status', '✅ ᴏɴʟɪɴᴇ')
                web_status = "❌ ᴏꜰꜰʟɪɴᴇ"

                try:
                    async with aiohttp.ClientSession(headers=headers) as session:
                        async with session.get(url, timeout=10) as resp:
                            if resp.status == 200:
                                web_status = "✅ ᴏɴʟɪɴᴇ"
                except:
                    pass

                # ɪɴꜱᴛᴀɴᴛ ᴀʟᴇʀᴛ ᴏɴ ꜱᴛᴀᴛᴜꜱ ᴄʜᴀɴɢᴇ
                if web_status != prev_status:
                    if "ᴏꜰꜰʟɪɴᴇ" in web_status:
                        alert = f"⚠️ <b>ᴀʟᴇʀᴛ: {name} ɪꜱ ᴅᴏᴡɴ!</b>"
                    else:
                        alert = f"✅ <b>ʀᴇᴄᴏᴠᴇʀᴇᴅ: {name} ɪꜱ ʙᴀᴄᴋ ᴏɴʟɪɴᴇ!</b>"
                    
                    try:
                        await bot.send_message(user_id, alert)
                    except:
                        pass

                    # ᴜᴘᴅᴀᴛᴇ ꜱᴛᴀᴛᴜꜱ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ ɪᴍᴍᴇᴅɪᴀᴛᴇʟʏ
                    await bots_col.update_one(
                        {"user_id": user_id, "name": name},
                        {"$set": {"status": web_status}}
                    )

            # --- 𝟸. ᴍᴇꜱꜱᴀɢᴇ ᴜᴘᴅᴀᴛᴇ ᴘʜᴀꜱᴇ ---
            if post_link and (now_ts - last_msg_update >= msg_interval):
                now_ist = datetime.now(IST).strftime('%d/%m/%Y\n%H:%M:%S')
                
                status_text = (
                    "🌐 <b>ʟɪᴠᴇ ʙᴏᴛ ꜱᴛᴀᴛᴜꜱ</b>\n"
                    f"⏰ <b>ʟᴀꜱᴛ ꜱʏɴᴄ:</b>\n<code>{now_ist} IST</code>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
                )

                updated_bots = await bots_col.find({"user_id": user_id}).to_list(length=None)
                for b in updated_bots:
                    icon = "🟢" if "ᴏɴʟɪɴᴇ" in b['status'] else "🔴"
                    status_text += (
                        f"{icon} <b><a href='https://t.me/{b.get('username','bot')}'>{b['name']}</a></b>\n"
                        f"   └ ꜱᴛᴀᴛᴜꜱ: {b['status']}\n\n"
                    )

                status_text += "━━━━━━━━━━━━━━━━━━━━━━━\n"
                #status_text += f"🛰 ᴘɪɴɢ: {ping_interval//60}ᴍ | 🔄 ᴜᴘᴅᴀᴛᴇ: {msg_interval//60}ᴍ"
                status_text += f"🔄 ᴀᴜᴛᴏ ʀᴇꜰʀᴇꜱʜ: {msg_interval//60}ᴍ ɪɴᴛᴇʀᴠᴀʟ"

                cid, mid = parse_tg_link(post_link)
                if cid and mid:
                    try:
                        await bot.edit_message_text(cid, mid, status_text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)
                        last_msg_update = now_ts 
                    except (MessageNotModified, FloodWait):
                        pass

        except Exception as e:
            logger.error(f"ᴛᴀꜱᴋ ᴇʀʀᴏʀ {user_id}: {e}")

        await asyncio.sleep(ping_interval)

async def start_all_tasks():
    uids = await bots_col.distinct("user_id")
    for uid in uids:
        cfg = await users_settings.find_one({"user_id": uid})
        p_inv = cfg.get('ping_interval', Config.DEFAULT_PING) if cfg else Config.DEFAULT_PING
        m_inv = cfg.get('msg_interval', Config.DEFAULT_MSG) if cfg else Config.DEFAULT_MSG
        lnk = cfg.get('post_link') if cfg else None
        
        if uid not in active_tasks or active_tasks[uid].done():
            active_tasks[uid] = asyncio.create_task(monitor_user_task(uid, p_inv, m_inv, lnk))
            
    logger.info(f"ɪɴɪᴛɪᴀʟɪᴢᴇᴅ {len(uids)} ᴍᴏɴɪᴛᴏʀɪɴɢ ᴛᴀꜱᴋꜱ ᴡɪᴛʜ ᴅᴜᴀʟ ɪɴᴛᴇʀᴠᴀʟꜱ.")