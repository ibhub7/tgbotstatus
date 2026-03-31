import re, asyncio, logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pyrogram.errors import FloodWait
from database import (
    add_bot, remove_bot, get_user_bots, 
    update_user_settings, get_user_config, 
    add_user, get_all_users, bots_col,
    registered_users
) 
from config import Config

logger = logging.getLogger("MonitorBot")

# --- 𝙸𝙽𝚂𝚃𝙰𝙽𝚃 𝚂𝚈𝙽𝙲 𝙷𝙴𝙻𝙿𝙴𝚁 ---
async def refresh_monitor(user_id):
    """Refreshes the monitor task without restarting the whole bot"""
    try:
        from bot import active_tasks, monitor_user_task
        if user_id in active_tasks: 
            active_tasks[user_id].cancel()
        
        cfg = await get_user_config(user_id)
        if cfg:
            inv, lnk = cfg.get('interval', 300), cfg.get('post_link')
            active_tasks[user_id] = asyncio.create_task(monitor_user_task(user_id, inv, lnk))
            logger.info(f"Refreshed task for {user_id}")
    except Exception as e:
        logger.error(f"Refresh Error: {e}")

def get_dash_url(user_id):
    """Generates a secure WebApp URL with the access key"""
    base_url = "https://infinity-monitor-bot-ug.koyeb.app"
    return f"{base_url}/dashboard/{user_id}?key={Config.WEB_ACCESS_KEY}"

# --- 𝚂𝚃𝙰𝚁𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 ---
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    await add_user(user_id)
    dashboard_url = get_dash_url(user_id)
    
    image_url = "https://i.ibb.co/nM2Bcjg8/photo-2026-03-28-14-53-24-7622319747731816468.jpg" 
    
    text = (
        f"<a href='{image_url}'>👋</a> ʜᴇʟʟᴏ {message.from_user.mention}!\n\n"
        f"<blockquote>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ <b>ʙᴏᴛ ᴍᴏɴɪᴛᴏʀ ᴘʀᴏ</b>. ɪ ᴄᴀɴ ᴛʀᴀᴄᴋ ʏᴏᴜʀ ʙᴏᴛs ᴜᴘᴛɪᴍᴇ ᴀɴᴅ "
        f"sᴇɴᴅ ɪɴsᴛᴀɴᴛ ᴀʟᴇʀᴛs ɪғ ᴛʜᴇʏ ɢᴏ ᴏғғʟɪɴᴇ. 🚀</blockquote>\n\n"
        f"📊 <b>ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ᴅᴀsʜʙᴏᴀʀᴅ ɪs ʀᴇᴀᴅʏ!</b>"
    )
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ᴏᴘᴇɴ ᴅᴀsʜʙᴏᴀʀᴅ", web_app=WebAppInfo(url=dashboard_url))],
        [InlineKeyboardButton("❓ ʜᴇʟᴘ ᴍᴇɴᴜ", callback_data="show_help")]
    ])
    
    await message.reply(
        text, 
        reply_markup=reply_markup, 
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=False,
        invert_media=True
    )

# --- 𝙻𝙸𝚂𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 ---
@Client.on_message(filters.command("list") & filters.private)
async def list_cmd(client, message):
    user_id = message.from_user.id
    cursor = await get_user_bots(user_id)
    user_bots = await cursor.to_list(length=100)

    if not user_bots:
        return await message.reply("❌ <b>ʏᴏᴜ ʜᴀᴠᴇ ɴᴏ ʙᴏᴛs ᴀᴅᴅᴇᴅ.</b>")

    # Header as seen in the image
    text = "📋 <b>ʏᴏᴜʀ ᴍᴏɴɪᴛᴏʀᴇᴅ ʙᴏᴛs</b>\n\n"
    
    for i, b in enumerate(user_bots, 1):
        name = b.get('name', 'Unknown')
        username = b.get('username', 'bot')
        status = b.get('status', '❌ Offline')
        
        # Determine the status icon based on the status string
        icon = "✅" if "Online" in status else "❌"
        
        # Format matching the image:
        # 1. Number and Bold Bot Name (Hyperlinked to Telegram DM)
        # 2. Blockquote with a yellow-style bar and Small Caps status text
        text += (
            f"{i}. <b><a href='https://t.me/{username}'>{name}</a></b>\n"
            f"<blockquote>sᴛᴀᴛᴜs: {status}</blockquote>\n\n"
        )
    
    await message.reply(
        text, 
        parse_mode=enums.ParseMode.HTML, 
        disable_web_page_preview=True
    )

# --- 𝙻𝙾𝙶𝚂 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 (𝙾𝚆𝙽𝙴𝚁 𝙾𝙽𝙻𝚈) ---
@Client.on_message(filters.command("logs") & filters.user(Config.OWNER_ID))
async def logs_cmd(client, message):
    try:
        with open("bot.log", "r") as f:
            lines = f.readlines()
            last_logs = "".join(lines[-15:])
            await message.reply(f"📄 <b>ʀᴇᴄᴇɴᴛ sʏsᴛᴇᴍ ʟᴏɢs:</b>\n\n<code>{last_logs}</code>", parse_mode=enums.ParseMode.HTML)
    except FileNotFoundError:
        await message.reply("❌ <b>ʟᴏɢ ғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ.</b>")

# --- 𝙰𝙳𝙳 𝙱𝙾𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 ---
@Client.on_message(filters.command("addbot") & filters.private)
async def on_add(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) < 3: 
        return await message.reply("❌ ᴜsᴀɢᴇ: <code>/addbot @Username URL</code>")
    
    username, url = args[1].replace("@", ""), args[2]
    progress = await message.reply("⚙️ ᴘʀᴏᴄᴇssɪɴɢ...")
    
    try:
        target_bot = await client.get_users(username)
        await add_bot(user_id, target_bot.first_name, url, username) 
        await refresh_monitor(user_id)
        
        await progress.edit(
            f"✅ <b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴀᴅᴅᴇᴅ!</b>\n\n"
            f"<blockquote>🤖 ʙᴏᴛ: <code>{target_bot.first_name}</code>\n"
            f"📡 sᴛᴀᴛᴜs: ᴍᴏɴɪᴛᴏʀɪɴɢ sᴛᴀʀᴛᴇᴅ</blockquote>"
        )
    except Exception as e: 
        await progress.edit(f"❌ ᴇʀʀᴏʀ: <code>{e}</code>")

# --- 𝚁𝙴𝙼𝙾𝚅𝙴 𝙱𝙾𝚃 ---
@Client.on_message(filters.command("removebot") & filters.private)
async def on_remove(client, message):
    user_id = message.from_user.id
    match = re.search(r'"([^"]+)"', message.text)
    name = match.group(1).strip() if match else message.text.split(None, 1)[1] if len(message.command) > 1 else None
    
    if not name:
        return await message.reply("❌ ᴜsᴀɢᴇ: <code>/removebot \"Bot Name\"</code>")

    await remove_bot(user_id, name)
    await refresh_monitor(user_id)
    await message.reply(f"🗑️ <b>sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ:</b> <code>{name}</code>")

# --- 𝚂𝙴𝚃 𝙸𝙽𝚃𝙴𝚁𝚅𝙰𝙻 ---
@Client.on_message(filters.command("set_interval") & filters.private)
async def set_interval(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    
    if len(args) < 2 or args[1] not in ["2", "5"]: 
        return await message.reply("⚠️ ᴘʟᴇᴀsᴇ ᴜsᴇ: <code>/set_interval 2</code> ᴏʀ <code>5</code>")
    
    await update_user_settings(user_id, interval=int(args[1])*60)
    await refresh_monitor(user_id)
    
    await message.reply(
        f"⚙️ <b>ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴ ᴜᴘᴅᴀᴛᴇᴅ!</b>\n"
        f"<blockquote>ʏᴏᴜʀ ʙᴏᴛs ᴡɪʟʟ ʙᴇ ᴄʜᴇᴄᴋᴇᴅ ᴇᴠᴇʀʏ <b>{args[1]} ᴍɪɴᴜᴛᴇs</b>.</blockquote>"
    )

# --- 𝚂𝙴𝚃 𝙻𝙸𝙽𝙺 ---
@Client.on_message(filters.command("set_link") & filters.private)
async def on_set_link(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply("❌ ᴜsᴀɢᴇ: <code>/set_link POST_URL</code>")
    
    link = message.text.split(None, 1)[1]
    await update_user_settings(user_id, post_link=link)
    await refresh_monitor(user_id)
    await message.reply("✅ <b>sᴛᴀᴛᴜs ʟɪɴᴋ ᴜᴘᴅᴀᴛᴇᴅ!</b>\n<blockquote>ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ᴡɪʟʟ ɴᴏᴡ ʙᴇ ᴜᴘᴅᴀᴛᴇᴅ ʟɪᴠᴇ.</blockquote>")

# --- 𝙷𝙴𝙻𝙿 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 ---
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    help_text = (
        "📖 <b>ʙᴏᴛ ᴍᴏɴɪᴛᴏʀ ᴘʀᴏ - ᴜsᴇʀ ᴍᴀɴᴜᴀʟ</b>\n\n"
        "🚀 <b>ǫᴜɪᴄᴋ sᴇᴛᴜᴘ:</b>\n"
        "<blockquote>𝟷. ᴀᴅᴅ ʙᴏᴛ ᴀs ᴀᴅᴍɪɴ ɪɴ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ.\n"
        "𝟸. ᴄᴏᴘʏ ᴀ ᴍᴇssᴀɢᴇ ʟɪɴᴋ ғʀᴏᴍ ᴛʜᴀᴛ ᴄʜᴀɴɴᴇʟ.\n"
        "𝟹. ᴜsᴇ <code>/set_link</code> + ᴛʜᴀᴛ ʟɪɴᴋ.\n"
        "𝟺. ᴜsᴇ <code>/addbot</code> @username URL.</blockquote>\n\n"
        "📊 <b>ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        "• <b>/addbot</b> - ᴀᴅᴅ ʙᴏᴛ ᴛᴏ ʟɪsᴛ\n"
        "• <b>/removebot</b> - ʀᴇᴍᴏᴠᴇ ᴀ ʙᴏᴛ\n"
        "• <b>/list</b> - sʜᴏᴡ ᴀʟʟ ʏᴏᴜʀ ʙᴏᴛs\n"
        "• <b>/set_interval</b> - sᴇᴛ 𝟸/𝟻 ᴍɪɴ ᴄʜᴇᴄᴋs\n"
        "• <b>/dashboard</b> - ɢᴇᴛ ʏᴏᴜʀ ᴡᴇʙ ʟɪɴᴋ\n"
        "• <b>/logs</b> - ᴠɪᴇᴡ sʏsᴛᴇᴍ ʟᴏɢs"
    )
    await message.reply(help_text, parse_mode=enums.ParseMode.HTML, disable_web_page_preview=True)

# --- 𝙱𝚁𝙾𝙰𝙳𝙲𝙰𝚂𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 ---
@Client.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast_handler(client, message):
    if not message.reply_to_message: 
        return await message.reply("⚠️ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.")
    
    status_msg = await message.reply("📡 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ...")
    all_users = await get_all_users()
    count, failed = 0, 0
    
    async for user in all_users:
        try:
            await message.reply_to_message.copy(user['user_id'])
            count += 1
            await asyncio.sleep(0.05)
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await message.reply_to_message.copy(user['user_id'])
            count += 1
        except Exception: 
            failed += 1
            
    await status_msg.edit(
        f"📢 <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n"
        f"<blockquote>✅ sᴇɴᴛ ᴛᴏ: <code>{count}</code>\n"
        f"❌ ғᴀɪʟᴇᴅ: <code>{failed}</code></blockquote>"
    )

# --- 𝙳𝙰𝚂𝙷𝙱𝙾𝙰𝚁𝙳 & 𝚂𝚃𝙰𝚃𝚄𝚂 ---
@Client.on_message(filters.command("dashboard") & filters.private)
async def dash_cmd(client, message):
    user_id = message.from_user.id
    url = get_dash_url(user_id)
    await message.reply(
        "📊 <b>ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ᴅᴀsʜʙᴏᴀʀᴅ</b>\n\n"
        "ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ʙᴏᴛs ɪɴ ᴀ ᴍᴏᴅᴇʀɴ ᴡᴇʙ ɪɴᴛᴇʀғᴀᴄᴇ.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🌐 ᴏᴘᴇɴ ᴡᴇʙ ᴅᴀsʜʙᴏᴀʀᴅ", web_app=WebAppInfo(url=url))]
        ])
    )

@Client.on_message(filters.command("status") & filters.user(Config.OWNER_ID))
async def status_handler(client, message):
    base_url = "https://infinity-monitor-bot-ug.koyeb.app"
    user_id = message.from_user.id
    stats_url = f"{base_url}/stats"
    dash_url = f"{base_url}/dashboard/{user_id}"

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 View Global Stats", url=stats_url)],
        [InlineKeyboardButton("🖥 Open My Dashboard", url=dash_url)]
    ])

    await message.reply_text(
        "📊 <b>ʙᴏᴛ ᴍᴏɴɪᴛᴏʀɪɴɢ sʏsᴛᴇᴍ</b>\n\nᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴏɴɪᴛᴏʀ ʏᴏᴜʀ ʙᴏᴛs ᴏʀ ᴠɪᴇᴡ ɢʟᴏʙᴀʟ ɴᴇᴛᴡᴏʀᴋ sᴛᴀᴛɪsᴛɪᴄs.",
        reply_markup=keyboard,
        parse_mode=enums.ParseMode.HTML
    )

# --- SHOW HELP (BUTTON CALLBACK) ---
@Client.on_callback_query(filters.regex("show_help"))
async def show_help_cb(client, callback_query):
    help_text = (
        "📖 <b>ʙᴏᴛ ᴍᴏɴɪᴛᴏʀ ᴘʀᴏ - ᴜsᴇʀ ᴍᴀɴᴜᴀʟ</b>\n\n"
        "🚀 <b>ǫᴜɪᴄᴋ sᴇᴛᴜᴘ:</b>\n"
        "<blockquote>𝟷. ᴀᴅᴅ ʙᴏᴛ ᴀs ᴀᴅᴍɪɴ ɪɴ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ.\n"
        "𝟸. ᴄᴏᴘʏ ᴀ ᴍᴇssᴀɢᴇ ʟɪɴᴋ.\n"
        "𝟹. ᴜsᴇ <code>/set_link</code> + ʟɪɴᴋ.\n"
        "𝟺. ᴜsᴇ <code>/addbot</code> @username URL.</blockquote>\n\n"
        "📊 <b>ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        "• /addbot - ᴀᴅᴅ ʙᴏᴛ\n"
        "• /removebot - ʀᴇᴍᴏᴠᴇ ʙᴏᴛ\n"
        "• /list - ʟɪsᴛ ʙᴏᴛs\n"
        "• /set_interval - 2/5 ᴍɪɴ\n"
        "• /dashboard - ᴡᴇʙ ᴜɪ\n"
        "• /logs - ᴏᴡɴᴇʀ"
    )

    await callback_query.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Understand", callback_data="close_help")]
        ]),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

    await callback_query.answer()

# --- STATS COMMAND (OWNER ONLY) ---
@Client.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def stats_cmd(client, message):
    try:
        # Fast counts (no loops 🚀)
        total_users = await registered_users.count_documents({})
        total_bots = await bots_col.count_documents({})

        # Status breakdown
        online_bots = await bots_col.count_documents({
            "status": {"$regex": "Online"}
        })
        offline_bots = total_bots - online_bots

        # Unique users who added bots (pro stat 🔥)
        unique_bot_users = len(await bots_col.distinct("user_id"))

        text = (
            "📊 <b>ʙᴏᴛ sᴛᴀᴛs ᴅᴀsʜʙᴏᴀʀᴅ</b>\n\n"
            f"<blockquote>"
            f"👥 ᴛᴏᴛᴀʟ ᴜsᴇʀs: <b>{total_users}</b>\n"
            f"🧑‍💻 ᴀᴄᴛɪᴠᴇ ᴜsᴇʀs: <b>{unique_bot_users}</b>\n\n"
            f"🤖 ᴛᴏᴛᴀʟ ʙᴏᴛs: <b>{total_bots}</b>\n"
            f"🟢 ᴏɴʟɪɴᴇ: <b>{online_bots}</b>\n"
            f"🔴 ᴏғғʟɪɴᴇ: <b>{offline_bots}</b>"
            f"</blockquote>"
        )

        await message.reply(
            text,
            parse_mode=enums.ParseMode.HTML
        )

    except Exception as e:
        await message.reply(f"❌ Error: <code>{e}</code>")

# --- SHOW HELP (BUTTON CALLBACK) ---
@Client.on_callback_query(filters.regex("show_help"))
async def show_help_cb(client, callback_query):
    help_text = (
        "📖 <b>ʙᴏᴛ ᴍᴏɴɪᴛᴏʀ ᴘʀᴏ - ᴜsᴇʀ ᴍᴀɴᴜᴀʟ</b>\n\n"
        "🚀 <b>ǫᴜɪᴄᴋ sᴇᴛᴜᴘ:</b>\n"
        "<blockquote>𝟷. ᴀᴅᴅ ʙᴏᴛ ᴀs ᴀᴅᴍɪɴ ɪɴ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ.\n"
        "𝟸. ᴄᴏᴘʏ ᴀ ᴍᴇssᴀɢᴇ ʟɪɴᴋ.\n"
        "𝟹. ᴜsᴇ <code>/set_link</code> + ʟɪɴᴋ.\n"
        "𝟺. ᴜsᴇ <code>/addbot</code> @username URL.</blockquote>\n\n"
        "📊 <b>ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        "• /addbot - ᴀᴅᴅ ʙᴏᴛ\n"
        "• /removebot - ʀᴇᴍᴏᴠᴇ ʙᴏᴛ\n"
        "• /list - ʟɪsᴛ ʙᴏᴛs\n"
        "• /set_interval - 2/5 ᴍɪɴ\n"
        "• /dashboard - ᴡᴇʙ ᴜɪ\n"
        "• /logs - ᴏᴡɴᴇʀ"
    )

    await callback_query.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ Understand", callback_data="close_help")]
        ]),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

    await callback_query.answer()

# --- CLOSE HELP ---
@Client.on_callback_query(filters.regex("close_help"))
async def close_help_cb(client, callback_query):
    await callback_query.message.delete()
    await callback_query.answer("Thanks ✅")