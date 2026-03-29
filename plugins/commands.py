import re, asyncio
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from database import add_bot, remove_bot, get_user_bots, update_user_settings, get_user_config, add_user, get_all_users
from config import Config

async def refresh_monitor(user_id):
    from bot import active_tasks, monitor_user_task
    if user_id in active_tasks: active_tasks[user_id].cancel()
    cfg = await get_user_config(user_id)
    if cfg:
        inv, lnk = cfg.get('interval', 300), cfg.get('post_link')
        active_tasks[user_id] = asyncio.create_task(monitor_user_task(user_id, inv, lnk))

def get_dash_url(user_id):
    return f"https://infinity-monitor-bot-ug.koyeb.app/dashboard/{user_id}"

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    await add_user(user_id)
    dashboard_url = get_dash_url(user_id)
    text = f"👋 <b>Hello {message.from_user.mention}!</b>\n\nWelcome to <b>Bot Monitor Pro (SaaS)</b>."
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("🌐 My Dashboard", web_app=WebAppInfo(url=dashboard_url))]])
    await message.reply(text, reply_markup=reply_markup, parse_mode=enums.ParseMode.HTML)

@Client.on_message(filters.command("addbot") & filters.private)
async def on_add(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 3: return await message.reply("❌ Usage: /addbot @Username URL")
    username, url = args[1].replace("@", ""), args[2]
    try:
        target_bot = await client.get_users(username)
        await add_bot(user_id, target_bot.first_name, url, username) 
        await refresh_monitor(user_id)
        await message.reply(f"✅ <b>{target_bot.first_name}</b> added and monitor started!")
    except Exception as e: await message.reply(f"❌ Error: {e}")

@Client.on_message(filters.command("broadcast") & filters.user(Config.OWNER_ID))
async def broadcast_handler(client, message):
    if not message.reply_to_message: return await message.reply("Reply to a message to broadcast.")
    all_users = await get_all_users()
    count = 0
    async for user in all_users:
        try:
            await message.reply_to_message.copy(user['user_id'])
            count += 1
            await asyncio.sleep(0.3)
        except: pass
    await message.reply(f"✅ Sent to {count} users.")

@Client.on_message(filters.command("set_interval") & filters.private)
async def set_interval(client, message):
    user_id = message.from_user.id
    args = message.text.split()
    if len(args) < 2 or args[1] not in ["2", "5"]: return await message.reply("Use /set_interval 2 or 5")
    await update_user_settings(user_id, interval=int(args[1])*60)
    await refresh_monitor(user_id)
    await message.reply(f"✅ Interval set to {args[1]} min.")

@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    await message.reply("📖 <b>Help Menu</b>\n<blockquote>/addbot @user URL\n/set_interval 2\n/set_link POST_LINK\n/list\n/dashboard</blockquote>", parse_mode=enums.ParseMode.HTML)

# Baki commands (list, removebot, set_link) bhi same pattern mein user_id ke sath update kar lein.