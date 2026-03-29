import re, asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from database import (
    add_bot, remove_bot, get_user_bots, 
    update_user_settings, get_user_config, 
    add_user, get_all_users
)
from config import Config

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
    except ImportError:
        pass

def get_dash_url(user_id):
    return f"https://infinity-monitor-bot-ug.koyeb.app/dashboard/{user_id}"

# --- 𝚂𝚃𝙰𝚁𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 ---
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    await add_user(user_id)
    dashboard_url = get_dash_url(user_id)
    
    text = (
        f"👋 ʜᴇʟʟᴏ {message.from_user.mention}!\n\n"
        f"<blockquote>ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ <b>ʙᴏᴛ ᴍᴏɴɪᴛᴏʀ ᴘʀᴏ</b>. ɪ ᴄᴀɴ ᴛʀᴀᴄᴋ ʏᴏᴜʀ ʙᴏᴛs ᴜᴘᴛɪᴍᴇ ᴀɴᴅ "
        f"sᴇɴᴅ ɪɴsᴛᴀɴᴛ ᴀʟᴇʀᴛs ɪғ ᴛʜᴇʏ ɢᴏ ᴏғғʟɪɴᴇ. 🚀</blockquote>\n\n"
        f"📊 <b>ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ᴅᴀsʜʙᴏᴀʀᴅ ɪs ʀᴇᴀᴅʏ!</b>"
    )
    
    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 ᴏᴘᴇɴ ᴅᴀsʜʙᴏᴀʀᴅ", web_app=WebAppInfo(url=dashboard_url))],
        [InlineKeyboardButton("❓ ʜᴇʟᴘ ᴍᴇɴᴜ", callback_data="show_help")]
    ])
    
    await message.reply(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)

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

# --- 𝙱𝚁𝙾𝙰𝙳𝙲𝙰𝚂𝚃 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 ---
@Client.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast_handler(client, message):
    if not message.reply_to_message: 
        return await message.reply("⚠️ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʙʀᴏᴀᴅᴄᴀsᴛ.")
    
    status_msg = await message.reply("📡 ʙʀᴏᴀᴅᴄᴀsᴛɪɴɢ ɪɴ ᴘʀᴏɢʀᴇss...")
    all_users = await get_all_users()
    count, failed = 0, 0
    
    async for user in all_users:
        try:
            await message.reply_to_message.copy(user['user_id'])
            count += 1
            await asyncio.sleep(0.3)
        except: 
            failed += 1
            
    await status_msg.edit(
        f"📢 <b>ʙʀᴏᴀᴅᴄᴀsᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n"
        f"<blockquote>✅ sᴇɴᴛ ᴛᴏ: <code>{count}</code>\n"
        f"❌ ғᴀɪʟᴇᴅ: <code>{failed}</code></blockquote>"
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

# --- 𝙻𝙸𝚂𝚃 𝙱𝙾𝚃𝚂 ---
@Client.on_message(filters.command("list") & filters.private)
async def list_bots(client, message):
    user_id = message.from_user.id
    cursor = await get_user_bots(user_id)
    bot_list = await cursor.to_list(length=None)
    
    if not bot_list:
        return await message.reply("❌ ʏᴏᴜʀ ᴍᴏɴɪᴛᴏʀɪɴɢ ʟɪsᴛ ɪs ᴇᴍᴘᴛʏ.")

    res = f"📋 <b>ʏᴏᴜʀ ᴍᴏɴɪᴛᴏʀᴇᴅ ʙᴏᴛs</b>\n\n"
    for i, bot in enumerate(bot_list, 1):
        res += f"{i}. <b>{bot['name']}</b>\n<blockquote>sᴛᴀᴛᴜs: {bot['status']}</blockquote>\n"
    
    await message.reply(res)

# --- 𝚁𝙴𝙼𝙾𝚅𝙴 𝙱𝙾𝚃 ---
@Client.on_message(filters.command("removebot") & filters.private)
async def on_remove(client, message):
    user_id = message.from_user.id
    match = re.search(r'"([^"]+)"', message.text)
    
    if match:
        name = match.group(1).strip()
        await remove_bot(user_id, name)
        await refresh_monitor(user_id)
        await message.reply(f"🗑️ <b>sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ:</b> <code>{name}</code>")
    else:
        await message.reply("❌ ᴜsᴀɢᴇ: <code>/removebot \"Bot Name\"</code>")

# --- 𝚂𝙴𝚃 𝙻𝙸𝙽Ｋ ---
@Client.on_message(filters.command("set_link") & filters.private)
async def on_set_link(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply("❌ ᴜsᴀɢᴇ: <code>/set_link POST_URL</code>")
    
    link = message.text.split(None, 1)[1]
    await update_user_settings(user_id, post_link=link)
    await refresh_monitor(user_id)
    await message.reply("✅ <b>sᴛᴀᴛᴜs ʟɪɴᴋ ᴜᴘᴅᴀᴛᴇᴅ!</b>\n<blockquote>ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ᴡɪʟʟ ɴᴏᴡ ʙᴇ ᴜᴘᴅᴀᴛᴇᴅ ʟɪᴠᴇ.</blockquote>")

# --- 𝙷𝙴𝙻𝙿 𝙲𝙾𝙼𝙼𝙰𝙽𝙳 𝚆𝙸𝚃𝙷 𝚂𝙴𝚃𝚄𝙿 𝙶𝚄𝙸𝙳𝙴 ---
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    help_text = (
        "📖 <b>ʙᴏᴛ ᴍᴏɴɪᴛᴏʀ ᴘʀᴏ - ᴜsᴇʀ ᴍᴀɴᴜᴀʟ</b>\n\n"
        
        "🚀 <b>ǫᴜɪᴄᴋ sᴇᴛᴜᴘ ɢᴜɪᴅᴇ:</b>\n"
        "<blockquote>𝟷. ᴀᴅᴅ ʙᴏᴛ ᴀs ᴀᴅᴍɪɴ ɪɴ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟ.\n"
        "𝟸. ᴄʜᴀɴɴᴇʟ ᴍᴇɪɴ ᴇᴋ ᴅᴜᴍᴍʏ ᴍᴇssᴀɢᴇ (ᴇ.ɢ. '.') ᴋᴀʀᴇɪɴ ᴀᴜʀ ᴜsᴋᴀ ʟɪɴᴋ ᴄᴏᴘʏ ᴋᴀʀᴇɪɴ.\n"
        "𝟹. ᴜsᴇ <code>/set_link ʏᴏᴜʀ_ᴘᴏsᴛ_ʟɪɴᴋ</code> ᴛᴏ ᴄᴏɴɴᴇᴄᴛ.\n"
        "𝟺. ᴜsᴇ <code>/addbot @ᴜsᴇʀɴᴀᴍᴇ ᴜʀʟ</code> ᴛᴏ sᴛᴀʀᴛ ᴍᴏɴɪᴛᴏʀɪɴɢ.</blockquote>\n\n"
        
        "✨ <b>ᴍᴏɴɪᴛᴏʀɪɴɢ ᴄᴏᴍᴍᴀɴᴅs:</b>\n"
        "<blockquote>• <code>/addbot @username URL</code>\n"
        "<i>ᴀᴅᴅ ᴀ ʙᴏᴛ ᴛᴏ ʏᴏᴜʀ ᴘᴇʀsᴏɴᴀʟ ʟɪsᴛ.</i>\n\n"
        "• <code>/removebot \"Bot Name\"</code>\n"
        "<i>ʀᴇᴍᴏᴠᴇ ᴜsɪɴɢ ɴᴀᴍᴇ ɪɴsɪᴅᴇ ǫᴜᴏᴛᴇs.</i>\n\n"
        "• <code>/list</code>\n"
        "<i>sʜᴏᴡ ᴀʟʟ ʏᴏᴜʀ ʀᴇɢɪsᴛᴇʀᴇᴅ ʙᴏᴛs.</i></blockquote>\n\n"
        
        "⚙️ <b>ᴄᴏɴғɪɢᴜʀᴀᴛɪᴏɴs:</b>\n"
        "<blockquote>• <code>/set_interval 2</code>\n"
        "<i>sᴇᴛ ᴄʜᴇᴄᴋ ᴛɪᴍᴇ ᴛᴏ 𝟸 ᴏʀ 𝟻 ᴍɪɴᴜᴛᴇs.</i>\n\n"
        "• <code>/set_link ᴘᴏsᴛ_ᴜʀʟ</code>\n"
        "<i>ʟɪɴᴋ ᴀ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ ғᴏʀ ʟɪᴠᴇ ᴜᴘᴅᴀᴛᴇs.</i></blockquote>\n\n"
        
        "📊 <b>ᴡᴇʙ ᴅᴀsʜʙᴏᴀʀᴅ:</b>\n"
        "<blockquote>• <code>/dashboard</code>\n"
        "<i>ɢᴇᴛ ʏᴏᴜʀ ᴜɴɪǫᴜᴇ ᴘʀɪᴠᴀᴛᴇ ʟɪɴᴋ.</i></blockquote>\n\n"
        
        "⚠️ <b>ɴᴏᴛᴇ:</b> ᴀʟᴡᴀʏs ᴜsᴇ <code>https://</code> ɪɴ ʏᴏᴜʀ ʙᴏᴛ ᴇɴᴅᴘᴏɪɴᴛ ᴜʀʟ."
    )
    
    await message.reply(
        help_text, 
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )