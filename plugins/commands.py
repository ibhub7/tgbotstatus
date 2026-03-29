import re
import asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

# Database functions
from database import (
    add_bot, 
    remove_bot, 
    get_user_bots, 
    update_user_settings, 
    get_user_config
)
from config import Config

# --- INSTANT SYNC HELPER ---
# Note: bot.py se active_tasks aur monitor_user_task import kiye hain
async def refresh_monitor(user_id):
    """User ka monitor task turant update/restart karne ke liye"""
    from bot import active_tasks, monitor_user_task
    
    # Purana task cancel karo agar chal raha hai
    if user_id in active_tasks:
        active_tasks[user_id].cancel()
    
    # Nayi settings DB se fetch karo
    cfg = await get_user_config(user_id)
    if cfg:
        inv = cfg.get('interval', 300)
        lnk = cfg.get('post_link')
        # Naya task background mein shuru karo
        active_tasks[user_id] = asyncio.create_task(monitor_user_task(user_id, inv, lnk))

# Helper function for Dashboard URL
def get_dash_url(user_id):
    base_url = "https://infinity-monitor-bot-ug.koyeb.app"
    return f"{base_url}/dashboard/{user_id}"

# --- START COMMAND ---
@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    dashboard_url = get_dash_url(user_id)

    text = (
        f"👋 <b>Hello {message.from_user.mention}!</b>\n\n"
        "Welcome to <b>Bot Monitor Pro (SaaS)</b>. I can track your bots' uptime "
        "and alert you if they go offline.\n\n"
        "📊 <b>Personal Dashboard:</b> Click the button below to see your bots."
    )

    reply_markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌐 My Web Dashboard", web_app=WebAppInfo(url=dashboard_url))],
        [
            InlineKeyboardButton("📢 Channel", url="https://t.me/infinity_botzz"),
            InlineKeyboardButton("❓ Help Menu", callback_data="show_help")
        ]
    ])

    await message.reply(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)

# --- HELP COMMAND WITH BLOCKQUOTES ---
@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    help_text = (
        "📖 <b>Bot Monitor Pro - User Manual</b>\n\n"
        "🤖 <b>Bot Management</b>\n"
        "<blockquote>/addbot @user https://url.com\n"
        "<i>Add a bot to your personal monitoring list.</i></blockquote>\n"
        "<blockquote>/removebot \"Bot Name\"\n"
        "<i>Remove a bot using its name inside quotes.</i></blockquote>\n"
        "<blockquote>/list\n"
        "<i>See all bots registered under your UserID.</i></blockquote>\n\n"
        "⚙️ <b>Personal Settings</b>\n"
        "<blockquote>/set_interval 2\n"
        "<i>Set ping interval to 2 or 5 minutes.</i></blockquote>\n"
        "<blockquote>/set_link https://t.me/c/123/45\n"
        "<i>Link a Telegram post for live status updates.</i></blockquote>\n\n"
        "📊 <b>Monitoring Dashboard</b>\n"
        "<blockquote>/dashboard\n"
        "<i>Get your unique, private web dashboard link.</i></blockquote>"
    )

    await message.reply(
        help_text, 
        parse_mode=enums.ParseMode.HTML,
        disable_web_page_preview=True
    )

# --- ADD BOT COMMAND ---
@Client.on_message(filters.command("addbot") & filters.private)
async def on_add(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 3:
        return await message.reply("❌ <b>Usage:</b> <code>/addbot @Username https://url.com</code>")

    username = args[1].replace("@", "")
    url = args[2]

    try:
        target_bot = await client.get_users(username)
        await add_bot(user_id, target_bot.first_name, url, username) 
        
        # --- INSTANT SYNC ---
        await refresh_monitor(user_id)
        
        await message.reply(f"✅ <b>{target_bot.first_name}</b> added and monitoring started instantly!")
    except Exception as e:
        await message.reply(f"❌ <b>Error:</b> <code>{e}</code>")

# --- SETTINGS: INTERVAL ---
@Client.on_message(filters.command("set_interval") & filters.private)
async def set_interval(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2 or args[1] not in ["2", "5"]:
        return await message.reply("❌ <b>Usage:</b> <code>/set_interval 2</code> or <code>5</code>")

    interval_sec = int(args[1]) * 60
    await update_user_settings(user_id, interval=interval_sec)
    
    # --- INSTANT SYNC ---
    await refresh_monitor(user_id)
    
    await message.reply(f"✅ Interval set to <b>{args[1]} minutes</b> and applied.")

# --- SETTINGS: CHANNEL LINK ---
@Client.on_message(filters.command("set_link") & filters.private)
async def set_link(client, message):
    user_id = message.from_user.id
    if len(message.command) < 2:
        return await message.reply("❌ <b>Usage:</b> <code>/set_link POST_URL</code>")
    
    link = message.text.split(None, 1)[1]
    await update_user_settings(user_id, post_link=link)
    
    # --- INSTANT SYNC ---
    await refresh_monitor(user_id)
    
    await message.reply("✅ Status post link updated and sync enabled.")

# --- LIST BOTS ---
@Client.on_message(filters.command("list") & filters.private)
async def list_bots(client, message):
    user_id = message.from_user.id
    cursor = await get_user_bots(user_id)
    bot_list = await cursor.to_list(length=None)
    
    if not bot_list:
        return await message.reply("❌ Your monitoring list is empty.")

    res = f"📋 <b>Your Bots ({len(bot_list)}):</b>\n\n"
    for bot in bot_list:
        res += f"• <b>{bot['name']}</b>: {bot['status']}\n"
    await message.reply(res)

# --- REMOVE BOT ---
@Client.on_message(filters.command("removebot") & filters.private)
async def on_remove(client, message):
    user_id = message.from_user.id
    match = re.search(r'"([^"]+)"', message.text)
    if match:
        name = match.group(1).strip()
        await remove_bot(user_id, name)
        
        # --- INSTANT SYNC ---
        await refresh_monitor(user_id)
        
        await message.reply(f"🗑 <b>{name}</b> removed from your monitoring list.")
    else:
        await message.reply("❌ Use: <code>/removebot \"Name\"</code>")

# --- DASHBOARD COMMAND ---
@Client.on_message(filters.command("dashboard") & filters.private)
async def get_dashboard(client, message):
    user_id = message.from_user.id
    url = get_dash_url(user_id)
    await message.reply(f"📊 <b>Your Dashboard:</b>\n<code>{url}</code>")