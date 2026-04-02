import re, asyncio, logging, sys, os
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from pyrogram.errors import FloodWait
from database import (
    add_bot, remove_bot, get_user_bots, 
    update_user_settings, get_user_config, 
    add_user, get_all_users, bots_col,
    registered_users, delete_all_user_bots
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

# --- 𝙻𝙾𝙶𝚂 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 (𝚂𝙴𝙽𝙳 𝙰𝚂 𝙵𝙸𝙻𝙴) ---
@Client.on_message(filters.command("logs") & filters.user(Config.OWNER_ID))
async def logs_cmd(client, message):
    log_file = "bot.log"
    
    if os.path.exists(log_file):
        if os.path.getsize(log_file) > 0:
            await message.reply_document(
                document=log_file,
                caption="📄 <b>sʏsᴛᴇᴍ ʟᴏɢ ғɪʟᴇ</b>\n<blockquote>Here are the latest internal logs.</blockquote>",
                parse_mode=enums.ParseMode.HTML
            )
        else:
            await message.reply("📭 <b>ʟᴏɢ ғɪʟᴇ ɪs ᴇᴍᴘᴛʏ.</b>")
    else:
        await message.reply("❌ <b>ʟᴏɢ ғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ ᴏɴ sᴇʀᴠᴇʀ.</b>")

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

# --- 𝚁𝙴𝙼𝙾𝚅𝙴 𝙱𝙾𝚃 (𝙵𝙸𝚇𝙴𝙳) ---
@Client.on_message(filters.command("removebot") & filters.private)
async def on_remove(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply("❌ ᴜsᴀɢᴇ: <code>/removebot @username</code>")

    # Clean the username (remove @ if present)
    target_username = message.command[1].replace("@", "")

    res = await remove_bot(user_id, target_username)
    if res.deleted_count > 0:
        await refresh_monitor(user_id)
        await message.reply(f"🗑️ <b>sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ:</b> <code>@{target_username}</code>")
    else:
        await message.reply(f"⚠️ <b>ɴᴏᴛ ғᴏᴜɴᴅ:</b> <code>@{target_username}</code> ɪs ɴᴏᴛ ɪɴ ʏᴏᴜʀ ʟɪsᴛ.")


# --- 𝙳𝙴𝙻𝙴𝚃𝙴 𝙰𝙻𝙻 𝙱𝙾𝚃𝚂 ---
@Client.on_message(filters.command("deleteall") & filters.private)
async def delete_all_cmd(client, message):
    user_id = message.from_user.id
    if "confirm" not in message.text.lower():
        return await message.reply("⚠️ <b>ᴀʀᴇ ʏᴏᴜ sᴜʀᴇ?</b>\n\nᴛʜɪs ᴡɪʟʟ ʀᴇᴍᴏᴠᴇ ALL ʏᴏᴜʀ ᴍᴏɴɪᴛᴏʀᴇᴅ ʙᴏᴛs.\nᴛʏᴘᴇ <code>/deleteall confirm</code> ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ.")

    res = await delete_all_user_bots(user_id)
    await refresh_monitor(user_id)
    await message.reply(f"💥 <b>ᴀʟʟ ʙᴏᴛs ᴘᴜʀɢᴇᴅ!</b>\n<blockquote>ʀᴇᴍᴏᴠᴇᴅ <code>{res.deleted_count}</code> ʙᴏᴛs ғʀᴏᴍ ʏᴏᴜʀ ᴀᴄᴄᴏᴜɴᴛ.</blockquote>")


# --- 𝙸𝙳, 𝙸𝙽𝙵𝙾, 𝙵𝙸𝙽𝙵𝙾 ---
@Client.on_message(filters.command("id"))
async def get_id(client, message):
    text = f"👤 <b>ʏᴏᴜʀ ɪᴅ:</b> <code>{message.from_user.id}</code>\n"
    if message.chat.type != enums.ChatType.PRIVATE:
        text += f"👥 <b>ɢʀᴏᴜᴘ ɪᴅ:</b> <code>{message.chat.id}</code>"
    await message.reply(text)

@Client.on_message(filters.command("info"))
async def get_info(client, message):
    user = message.from_user
    if len(message.command) > 1:
        try: user = await client.get_users(message.command[1])
        except Exception as e: return await message.reply(f"❌ ᴇʀʀᴏʀ: {e}")

    await message.reply(
        f"📋 <b>ᴜsᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>\n"
        f"<blockquote>👤 ɴᴀᴍᴇ: {user.first_name}\n🆔 ɪᴅ: <code>{user.id}</code>\n🔗 @{user.username or 'None'}</blockquote>"
    )

# --- 𝙵𝙾𝚁𝚆𝙰𝚁𝙳 𝙸𝙽𝙵𝙾 (𝙴𝙽𝙷𝙰𝙽𝙲𝙴𝙳) ---
@Client.on_message(filters.command("finfo") & filters.private)
async def get_finfo(client, message):
    msg = message.reply_to_message

    if not msg or not (msg.forward_from or msg.forward_sender_name or msg.forward_from_chat):
        return await message.reply("⚠️ ʀᴇᴘʟʏ ᴛᴏ ᴀ <b>ғᴏʀᴡᴀʀᴅᴇᴅ</b> ᴍᴇssᴀɢᴇ ᴛᴏ ɢᴇᴛ sᴏᴜʀᴄᴇ ɪɴғᴏ.")

    # Case 1: Real User (Privacy Off)
    if msg.forward_from:
        f = msg.forward_from
        return await message.reply(
            f"✉️ <b>ғᴏʀᴡᴀʀᴅ sᴏᴜʀᴄᴇ</b>\n"
            f"<blockquote>👤 ɴᴀᴍᴇ: <a href='tg://user?id={f.id}'>{f.first_name}</a>\n"
            f"🆔 ɪᴅ: <code>{f.id}</code></blockquote>",
            disable_web_page_preview=True
        )

    # Case 2: User with Privacy Enabled
    elif msg.forward_sender_name:
        return await message.reply(
            f"✉️ <b>ғᴏʀᴡᴀʀᴅ sᴏᴜʀᴄᴇ</b>\n"
            f"<blockquote>👤 ɴᴀᴍᴇ: {msg.forward_sender_name}\n"
            f"🆔 ɪᴅ: <code>ʜɪᴅᴅᴇɴ ʙʏ ᴜsᴇʀ</code></blockquote>"
        )

    # Case 3: Channel or Group
    elif msg.forward_from_chat:
        chat = msg.forward_from_chat
        return await message.reply(
            f"✉️ <b>ғᴏʀᴡᴀʀᴅ sᴏᴜʀᴄᴇ</b>\n"
            f"<blockquote>📢 sᴏᴜʀᴄᴇ: {chat.title}\n"
            f"🆔 ɪᴅ: <code>{chat.id}</code></blockquote>"
        )

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
        "📊 <b>ᴀᴠᴀɪʟᴀʙʟᴇ ᴄᴏᴍᴍᴀɴᴅs:</b>\n\n"
        "• /addbot <code>@ᴜsᴇʀɴᴀᴍᴇ URL</code> — ᴀᴅᴅ ᴀ ɴᴇᴡ ʙᴏᴛ ᴛᴏ ᴍᴏɴɪᴛᴏʀɪɴɢ ʟɪsᴛ\n"
        "• /removebot <code>\"@ᴜsᴇʀɴᴀᴍᴇ\"</code> — ʀᴇᴍᴏᴠᴇ ᴀ sᴘᴇᴄɪғɪᴄ ʙᴏᴛ ʙʏ ɪᴛs ɴᴀᴍᴇ\n"
        "• /deleteall <code>confirm</code> — ᴘᴜʀɢᴇ ᴀʟʟ ʏᴏᴜʀ ᴀᴅᴅᴇᴅ ʙᴏᴛs ᴀᴛ ᴏɴᴄᴇ\n"
        "• /list — sʜᴏᴡ ᴀʟʟ ʏᴏᴜʀ ᴍᴏɴɪᴛᴏʀᴇᴅ ʙᴏᴛs ᴀɴᴅ sᴛᴀᴛᴜs\n"
        "• /set_interval <code>𝟸/𝟻</code> — ᴄʜᴏᴏsᴇ ᴄʜᴇᴄᴋɪɴɢ ᴅᴇʟᴀʏ ɪɴ ᴍɪɴᴜᴛᴇs\n"
        "• /dashboard — ɢᴇᴛ ʏᴏᴜʀ sᴇᴄᴜʀᴇ ᴡᴇʙ ɪɴᴛᴇʀғᴀᴄᴇ ʟɪɴᴋ\n"
        "• /id — ɢᴇᴛ ʏᴏᴜʀ ᴜsᴇʀ ɪᴅ ᴀɴᴅ ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ ɪᴅ\n"
        "• /info <code>@ᴜsᴇʀ</code> — ᴠɪᴇᴡ ᴅᴇᴛᴀɪʟᴇᴅ ɪɴғᴏ ᴀʙᴏᴜᴛ ᴀ ᴜsᴇʀ\n"
        "• /finfo (ʀᴇᴘʟʏ) — ɢᴇᴛ sᴏᴜʀᴄᴇ ɪᴅ ᴏғ ᴀ ғᴏʀᴡᴀʀᴅᴇᴅ ᴍᴇssᴀɢᴇ\n"
        "• /logs — ᴠɪᴇᴡ sʏsᴛᴇᴍ ʟᴏɢs (ᴏᴡɴᴇʀ ᴏɴʟʏ)"
    )
    await message.reply(
        help_text, 
        parse_mode=enums.ParseMode.HTML, 
        disable_web_page_preview=True
    )

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

## --- SHOW HELP (BUTTON CALLBACK UPDATED) ---
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
        "• /addbot - ᴀᴅᴅ ɴᴇᴡ ʙᴏᴛ\n"
        "• /removebot - ᴅᴇʟᴇᴛᴇ ʙᴏᴛ\n"
        "• /deleteall - ᴡɪᴘᴇ ᴀʟʟ\n"
        "• /list - sʜᴏᴡ ʟɪsᴛ\n"
        "• /set_interval - sᴇᴛ ᴛɪᴍᴇ\n"
        "• /dashboard - ᴡᴇʙ ᴜɪ\n"
        "• /id, /info, /finfo - ᴜᴛɪʟs"
    )

    await callback_query.message.edit_text(
        help_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✅ ᴜɴᴅᴇʀsᴛᴀɴᴅ", callback_data="close_help")]
        ]),
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )
    await callback_query.answer()

# --- STATS COMMAND (OWNER ONLY) ---
@Client.on_message(filters.command("stats") & filters.user(Config.OWNER_ID))
async def stats_cmd(client, message):
    try:
        total_users = await registered_users.count_documents({})
        total_bots = await bots_col.count_documents({})
        online_bots = await bots_col.count_documents({"status": {"$regex": "Online"}})
        offline_bots = total_bots - online_bots
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

# --- 𝚁𝙴𝚂𝚃𝙰𝚁𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 (𝙾𝚆𝙽𝙴𝚁 𝙾𝙽𝙻𝚈) ---
@Client.on_message(filters.command("restart") & filters.user(Config.OWNER_ID))
async def restart_bot(client, message):
    msg = await message.reply("🔄 <b>ᴘʀᴏᴄᴇssɪɴɢ ʀᴇʙᴏᴏᴛ...</b>")
    try:
        from bot import active_tasks
        for task in active_tasks.values(): task.cancel()
    except Exception: pass

    await msg.edit("🚀 <b>ʙᴏᴛ ɪs ʀᴇsᴛᴀʀᴛɪɴɢ!</b>")
    await client.stop()
    os.execl(sys.executable, sys.executable, *sys.argv)

# --- CLOSE HELP ---
@Client.on_callback_query(filters.regex("close_help"))
async def close_help_cb(client, callback_query):
    await callback_query.message.delete()
    await callback_query.answer("Thanks ✅")