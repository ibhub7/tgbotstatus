import re, asyncio, logging, os, sys
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery
from database import (
    add_bot, remove_bot, get_user_bots, update_user_settings, 
    get_user_config, add_user, get_all_users, delete_all_user_bots,
    reset_user_intervals
) 
from config import Config
from datetime import datetime

logger = logging.getLogger("MonitorBot")

async def refresh_monitor(user_id):
    try:
        from bot import active_tasks, monitor_user_task
        if user_id in active_tasks: active_tasks[user_id].cancel()
        cfg = await get_user_config(user_id)
        p = cfg.get('ping_interval', Config.DEFAULT_PING) if cfg else Config.DEFAULT_PING
        m = cfg.get('msg_interval', Config.DEFAULT_MSG) if cfg else Config.DEFAULT_MSG
        lnk = cfg.get('post_link') if cfg else None
        active_tasks[user_id] = asyncio.create_task(monitor_user_task(user_id, p, m, lnk))
    except Exception as e: logger.error(f"ʀᴇꜰʀᴇꜱʜ ᴇʀʀᴏʀ: {e}")

# --- ꜱᴇᴛᴛɪɴɢꜱ ᴍᴇɴᴜ ---
# This handler now listens for both commands and callback triggers
@Client.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client, message):
    # Use message.from_user whether it's a Message or CallbackQuery
    user_id = message.from_user.id
    cfg = await get_user_config(user_id)
    p = (cfg.get('ping_interval', Config.DEFAULT_PING) if cfg else Config.DEFAULT_PING) // 60
    m = (cfg.get('msg_interval', Config.DEFAULT_MSG) if cfg else Config.DEFAULT_MSG) // 60

    text = (
        "⚙️ <b>ᴍᴏɴɪᴛᴏʀ ᴄᴏɴꜰɪɢᴜʀᴀᴛɪᴏɴ</b>\n\n"
        f"🛰 <b>ᴘɪɴɢ ɪɴᴛᴇʀᴠᴀʟ:</b> <code>{p}ᴍ</code>\n"
        f"🔄 <b>ᴜᴘᴅᴀᴛᴇ ɪɴᴛᴇʀᴠᴀʟ:</b> <code>{m}ᴍ</code>\n\n"
        "ᴄʜᴏᴏꜱᴇ ᴀɴ ᴏᴘᴛɪᴏɴ ʙᴇʟᴏᴡ ᴛᴏ ᴍᴏᴅɪꜰʏ:"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛰 ꜱᴇᴛ ᴘɪɴɢ ɪɴᴛᴇʀᴠᴀʟ", callback_data="set_p_inv")],
        [InlineKeyboardButton("🔄 ꜱᴇᴛ ᴍꜱɢ ɪɴᴛᴇʀᴠᴀʟ", callback_data="set_m_inv")],
        [InlineKeyboardButton("♻️ ʀᴇꜱᴇᴛ ᴛᴏ ᴅᴇꜰᴀᴜʟᴛ", callback_data="confirm_reset")]
    ])
    
    # FIXED: Check against the CallbackQuery class
    if isinstance(message, CallbackQuery):
        await message.edit_message_text(text, reply_markup=buttons)
    else:
        await message.reply(text, reply_markup=buttons)

@Client.on_callback_query(filters.regex(r"set_(p|m)_inv"))
async def choose_interval_val(client, callback_query):
    type_inv = callback_query.data.split("_")[1]
    vals = [2, 5, 10, 15, 20, 25, 30, 45, 60, 90, 120] if type_inv == "p" else [10, 15, 20, 30, 40, 45, 50, 60]
    
    if type_inv == "p":
        text = "🛰 <b>ꜱᴇᴛ ᴘɪɴɢ ɪɴᴛᴇʀᴠᴀʟ (ᴍɪɴᴜᴛᴇꜱ)</b>"
    else:
        text = "🔄 <b>ꜱᴇᴛ ᴍꜱɢ ᴜᴘᴅᴀᴛᴇ ɪɴᴛᴇʀᴠᴀʟ (ᴍɪɴᴜᴛᴇꜱ)</b>"

    btns = []
    row = []
    for v in vals:
        row.append(InlineKeyboardButton(f"{v}ᴍ", callback_data=f"save_{type_inv}_{v}"))
        if len(row) == 4:
            btns.append(row); row = []
    if row: btns.append(row)
    btns.append([InlineKeyboardButton("⬅️ ʙᴀᴄᴋ", callback_data="back_settings")])
    await callback_query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(btns))

@Client.on_callback_query(filters.regex(r"save_(p|m)_(\d+)"))
async def save_interval_val(client, callback_query):
    _, type_inv, val = callback_query.data.split("_")
    user_id = callback_query.from_user.id
    val_sec = int(val) * 60
    
    if type_inv == "p": await update_user_settings(user_id, ping_interval=val_sec)
    else: await update_user_settings(user_id, msg_interval=val_sec)
    
    await refresh_monitor(user_id)
    await callback_query.answer(f"✅ ꜱᴀᴠᴇᴅ {val} ᴍɪɴᴜᴛᴇꜱ", show_alert=True)
    await settings_cmd(client, callback_query)

@Client.on_callback_query(filters.regex("confirm_reset"))
async def reset_callback(client, callback_query):
    user_id = callback_query.from_user.id
    await reset_user_intervals(user_id)
    await refresh_monitor(user_id)
    await callback_query.answer("ꜱᴇᴛᴛɪɴɢꜱ ʀᴇꜱᴇᴛ!", show_alert=True)
    await settings_cmd(client, callback_query)

@Client.on_callback_query(filters.regex("back_settings"))
async def back_settings(client, callback_query):
    await settings_cmd(client, callback_query)