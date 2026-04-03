import asyncio
import io

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from motor.motor_asyncio import AsyncIOMotorClient

from database import worker_bots, broadcast_users
from config import Config


# --- ᴄᴏɴɴᴇᴄᴛ ᴡᴏʀᴋᴇʀ ʙᴏᴛ ---
@Client.on_message(filters.command("connectbot") & filters.user(Config.OWNER_ID))
async def connect_worker(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ ᴜꜱᴀɢᴇ: <code>/connectbot TOKEN</code>")
    token = message.command[1]
    status = await message.reply("📡 ᴠᴇʀɪꜰʏɪɴɢ...")
    try:
        async with Client("temp", bot_token=token, api_id=Config.API_ID, api_hash=Config.API_HASH) as b:
            me = await b.get_me()
            await worker_bots.update_one({"username": me.username}, {"$set": {"token": token, "name": me.first_name}}, upsert=True)
        await status.edit(f"✅ ᴄᴏɴɴᴇᴄᴛᴇᴅ: {me.first_name} (@{me.username})")
    except: await status.edit("❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ!")

# --- ᴅɪꜱᴄᴏɴɴᴇᴄᴛ ᴡᴏʀᴋᴇʀ ʙᴏᴛ ---
@Client.on_message(filters.command("disconnect") & filters.user(Config.OWNER_ID))
async def disconnect_bot(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ ᴜꜱᴀɢᴇ: <code>/disconnect @username</code>")
    target = message.command[1].replace("@", "")
    await worker_bots.delete_one({"username": target})
    deleted = await broadcast_users.delete_many({"source": f"@{target}"})
    await message.reply(f"✅ @{target} ʀᴇᴍᴏᴠᴇᴅ! 🗑️ ᴘᴜʀɢᴇᴅ {deleted.deleted_count} ᴜꜱᴇʀꜱ.")

# --- ʟɪɢʜᴛᴡᴇɪɢʜᴛ ᴅʙ ᴄʟᴏɴᴇʀ (ɪᴅ ᴏɴʟʏ) ---
@Client.on_message(filters.command("cloneuserdb") & filters.user(Config.OWNER_ID))
async def clone_db(client, message):
    if len(message.command) < 3:
        return await message.reply("❌ ᴜꜱᴀɢᴇ: <code>/cloneuserdb URL @target_bot</code>")
    url, bot_tag = message.command[1], message.command[2]
    status = await message.reply("📡 ꜱᴄᴀɴɴɪɴɢ ᴇxᴛᴇʀɴᴀʟ ᴍᴏɴɢᴏ...")
    try:
        ext_client = AsyncIOMotorClient(url)
        db_names = await ext_client.list_database_names()
        new, dupe = 0, 0
        for db_n in db_names:
            if db_n in ["admin", "local", "config"]: continue
            ext_db = ext_client[db_n]
            cols = await ext_db.list_collection_names()
            for c_n in ["users", "user", "tgusers", "registered"]:
                if c_n in cols:
                    cursor = ext_db[c_n].find({}, {"user_id": 1, "_id": 1})
                    async for doc in cursor:
                        raw_id = doc.get("user_id") or doc.get("_id")
                        if isinstance(raw_id, int):
                            res = await broadcast_users.update_one({"user_id": raw_id}, {"$set": {"source": bot_tag}}, upsert=True)
                            if res.upserted_id: new += 1
                            else: dupe += 1
                        if (new + dupe) % 100 == 0:
                            await status.edit(f"⏳ ᴄʟᴏɴɪɴɢ {bot_tag}...\n📥 ɴᴇᴡ: {new} | 🔄 ᴅᴜᴘᴇꜱ: {dupe}")
        await status.edit(f"✅ <b>ᴄʟᴏɴᴇ ᴅᴏɴᴇ!</b>\n✨ ɴᴇᴡ: {new}\n♻️ ᴇxɪꜱᴛɪɴɢ: {dupe}")
    except Exception as e: await status.edit(f"❌ ᴇʀʀᴏʀ: {e}")

# --- ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴍᴇɴᴜ ---
@Client.on_message(filters.command("botscast") & filters.reply & filters.user(Config.OWNER_ID))
async def botscast_menu(client, message):
    workers = await worker_bots.find({}).to_list(length=100)
    if not workers: return await message.reply("❌ ɴᴏ ᴡᴏʀᴋᴇʀꜱ.")
    btns = []
    for w in workers:
        count = await broadcast_users.count_documents({"source": f"@{w['username']}"})
        btns.append([InlineKeyboardButton(f"🤖 {w['name']} | 👥 {count}", callback_data=f"exec_{w['username']}_{message.reply_to_message.id}")])
    await message.reply("📢 ꜱᴇʟᴇᴄᴛ ᴡᴏʀᴋᴇʀ ʙᴏᴛ:", reply_markup=InlineKeyboardMarkup(btns))



# --- ꜱᴇʟᴇᴄᴛ ʙᴏᴛ ᴛᴏ ᴠɪᴇᴡ ɪᴅꜱ ---
@Client.on_message(filters.command("botusers") & filters.user(Config.OWNER_ID))
async def view_bot_users_menu(client, message):
    workers = await worker_bots.find({}).to_list(length=100)
    if not workers:
        return await message.reply("❌ ɴᴏ ᴡᴏʀᴋᴇʀ ʙᴏᴛꜱ ꜰᴏᴜɴᴅ.")

    buttons = []
    for w in workers:
        # Count users for the button label
        count = await broadcast_users.count_documents({"source": f"@{w['username']}"})
        buttons.append([
            InlineKeyboardButton(
                f"🤖 {w['name']} ({count})", 
                callback_data=f"viewusers_{w['username']}"
            )
        ])

    await message.reply(
        "📂 <b>ʙᴏᴛ ᴜꜱᴇʀ ᴅɪᴄᴛɪᴏɴᴀʀʏ</b>\n\nꜱᴇʟᴇᴄᴛ ᴀ ʙᴏᴛ ᴛᴏ ᴠɪᴇᴡ ᴛʜᴇ ꜱᴀᴠᴇᴅ ᴜꜱᴇʀ ɪᴅꜱ:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- ʜᴀɴᴅʟᴇ ᴛʜᴇ ꜱᴇʟᴇᴄᴛɪᴏɴ ---
@Client.on_callback_query(filters.regex(r"viewusers_(.*)"))
async def show_specific_bot_users(client, callback_query):
    bot_user = callback_query.data.split("_")[1]
    bot_tag = f"@{bot_user}"
    
    await callback_query.answer("🔍 ꜰᴇᴛᴄʜɪɴɢ ɪᴅꜱ...")
    
    # Fetch all IDs for this bot
    cursor = broadcast_users.find({"source": bot_tag}, {"user_id": 1})
    user_list = await cursor.to_list(length=5000) # Limit to 5k for safety

    if not user_list:
        return await callback_query.message.edit(f"❌ ɴᴏ ᴜꜱᴇʀꜱ ꜰᴏᴜɴᴅ ꜰᴏʀ {bot_tag}")

    # Format the IDs into a string
    id_text = f"📋 <b>ᴜꜱᴇʀ ɪᴅꜱ ꜰᴏʀ {bot_tag}</b>\n\n"
    for user in user_list[:50]: # Only show first 50 in message to avoid length limit
        id_text += f"• <code>{user['user_id']}</code>\n"

    total = await broadcast_users.count_documents({"source": bot_tag})
    
    if total > 50:
        id_text += f"\n<i>...ᴀɴᴅ {total - 50} ᴍᴏʀᴇ ɪᴅꜱ.</i>"
        
        # --- ᴘʀᴏ ꜰᴇᴀᴛᴜʀᴇ: ꜱᴇɴᴅ ᴀꜱ ꜰɪʟᴇ ɪꜰ ᴛᴏᴏ ᴍᴀɴʏ ---
        full_list = "\n".join([str(u['user_id']) for u in user_list])
        file = io.BytesIO(full_list.encode())
        file.name = f"{bot_user}_users.txt"
        
        await callback_query.message.reply_document(
            document=file,
            caption=f"📄 <b>ꜰᴜʟʟ ᴜꜱᴇʀ ʟɪꜱᴛ:</b> {bot_tag}\n👥 ᴛᴏᴛᴀʟ: <code>{total}</code>"
        )

    await callback_query.message.edit(id_text, parse_mode=enums.ParseMode.HTML)