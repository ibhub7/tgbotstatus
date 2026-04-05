import asyncio
import io
import logging
from pyrogram import Client, filters, enums
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from motor.motor_asyncio import AsyncIOMotorClient
from database import worker_bots, broadcast_users
from config import Config

logger = logging.getLogger("MonitorBot")

# --- ᴄᴏɴɴᴇᴄᴛ ᴡᴏʀᴋᴇʀ ʙᴏᴛ ---
@Client.on_message(filters.command("connectbot") & filters.user(Config.OWNER_ID))
async def connect_worker(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ ᴜꜱᴀɢᴇ: <code>/connectbot TOKEN</code>")
    
    token = message.command[1]
    status = await message.reply("📡 ᴠᴇʀɪꜰʏɪɴɢ ʙᴏᴛ ᴛᴏᴋᴇɴ...")
    
    try:
        # Using a temporary client to verify the bot identity
        async with Client("temp_session", bot_token=token, api_id=Config.API_ID, api_hash=Config.API_HASH, in_memory=True) as b:
            me = await b.get_me()
            await worker_bots.update_one(
                {"username": me.username}, 
                {"$set": {"token": token, "name": me.first_name, "username": me.username}}, 
                upsert=True
            )
        await status.edit(f"✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ: <b>{me.first_name}</b> (@{me.username})")
    except Exception as e:
        await status.edit(f"❌ ɪɴᴠᴀʟɪᴅ ᴛᴏᴋᴇɴ ᴏʀ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ᴇʀʀᴏʀ:\n<code>{e}</code>")

# --- ᴅɪꜱᴄᴏɴɴᴇᴄᴛ ᴡᴏʀᴋᴇʀ ʙᴏᴛ ---
@Client.on_message(filters.command("disconnect") & filters.user(Config.OWNER_ID))
async def disconnect_bot(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ ᴜꜱᴀɢᴇ: <code>/disconnect @username</code>")
    
    target = message.command[1].replace("@", "")
    # Remove bot from the worker list
    await worker_bots.delete_one({"username": target})
    # Purge users associated with this bot from the broadcast dict
    deleted = await broadcast_users.delete_many({"source": f"@{target}"})
    
    await message.reply(
        f"🗑️ <b>@{target} ʀᴇᴍᴏᴠᴇᴅ!</b>\n"
        f"<blockquote>ᴘᴜʀɢᴇᴅ <code>{deleted.deleted_count}</code> ᴜꜱᴇʀꜱ ꜰʀᴏᴍ ᴛʜᴇ ʙʀᴏᴀᴅᴄᴀꜱᴛ ʟɪꜱᴛ.</blockquote>"
    )

# --- ʟɪɢʜᴛᴡᴇɪɢʜᴛ ᴅʙ ᴄʟᴏɴᴇʀ (ɪᴅ ᴏɴʟʏ) ---
@Client.on_message(filters.command("cloneuserdb") & filters.user(Config.OWNER_ID))
async def clone_db(client, message):
    if len(message.command) < 3:
        return await message.reply("❌ ᴜꜱᴀɢᴇ: <code>/cloneuserdb URL @target_bot</code>")
    
    url, bot_tag = message.command[1], message.command[2]
    if not bot_tag.startswith("@"): bot_tag = f"@{bot_tag}"
    
    status = await message.reply("📡 ꜱᴄᴀɴɴɪɴɢ ᴇxᴛᴇʀɴᴀʟ ᴍᴏɴɢᴏᴅʙ...")
    
    try:
        ext_client = AsyncIOMotorClient(url)
        db_names = await ext_client.list_database_names()
        new, dupe = 0, 0
        
        for db_n in db_names:
            if db_n in ["admin", "local", "config"]: continue
            ext_db = ext_client[db_n]
            cols = await ext_db.list_collection_names()
            
            # Common user collection names
            for c_n in ["users", "user", "tgusers", "registered", "bot_users"]:
                if c_n in cols:
                    # Fetch ONLY User IDs to save RAM and time
                    cursor = ext_db[c_n].find({}, {"user_id": 1, "_id": 1, "id": 1, "chat_id": 1})
                    async for doc in cursor:
                        # Extract ID from various common naming formats
                        raw_id = doc.get("user_id") or doc.get("_id") or doc.get("id") or doc.get("chat_id")
                        
                        if isinstance(raw_id, int):
                            res = await broadcast_users.update_one(
                                {"user_id": raw_id}, 
                                {"$set": {"source": bot_tag}}, 
                                upsert=True
                            )
                            if res.upserted_id: new += 1
                            else: dupe += 1
                        
                        # Live update every 100 users
                        if (new + dupe) % 100 == 0:
                            await status.edit(f"⏳ ᴄʟᴏɴɪɴɢ ꜰᴏʀ {bot_tag}...\n📥 ɴᴇᴡ ɪᴅꜱ: <code>{new}</code>\n🔄 ᴅᴜᴘʟɪᴄᴀᴛᴇꜱ: <code>{dupe}</code>")
        
        await status.edit(f"✅ <b>ᴄʟᴏɴᴇ ᴄᴏᴍᴘʟᴇᴛᴇ!</b>\n🎯 ᴛᴀʀɢᴇᴛ: {bot_tag}\n✨ ɴᴇᴡ ᴜꜱᴇʀꜱ: <code>{new}</code>\n♻️ ᴇxɪꜱᴛɪɴɢ: <code>{dupe}</code>")
    except Exception as e:
        await status.edit(f"❌ ᴇʀʀᴏʀ ᴅᴜʀɪɴɢ ᴄʟᴏɴᴇ: <code>{e}</code>")

# --- ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜱᴇʟᴇᴄᴛɪᴏɴ ᴍᴇɴᴜ ---
@Client.on_message(filters.command("botcast") & filters.reply & filters.user(Config.OWNER_ID))
async def botscast_menu(client, message):
    workers = await worker_bots.find({}).to_list(length=100)
    if not workers:
        return await message.reply("❌ ɴᴏ ᴡᴏʀᴋᴇʀ ʙᴏᴛꜱ ᴄᴏɴɴᴇᴄᴛᴇᴅ.")
    
    btns = []
    for w in workers:
        count = await broadcast_users.count_documents({"source": f"@{w['username']}"})
        btns.append([
            InlineKeyboardButton(
                f"🤖 {w['name']} | 👥 {count}", 
                callback_data=f"exec_{w['username']}_{message.reply_to_message.id}"
            )
        ])
    
    await message.reply(
        "📢 <b>ᴍᴜʟᴛɪ-ʙᴏᴛ ʙʀᴏᴀᴅᴄᴀꜱᴛ</b>\n\nꜱᴇʟᴇᴄᴛ ᴀ ᴡᴏʀᴋᴇʀ ʙᴏᴛ ᴛᴏ ᴅᴇʟɪᴠᴇʀ ᴛʜɪꜱ ᴍᴇꜱꜱᴀɢᴇ:",
        reply_markup=InlineKeyboardMarkup(btns)
    )

@Client.on_message(filters.command("purgedict") & filters.user(Config.OWNER_ID))
async def purge_bot_dict(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ ᴜꜱᴀɢᴇ: <code>/purgedict @username</code>")
    
    target = message.command[1].replace("@", "")
    res = await broadcast_users.delete_many({"source": f"@{target}"})
    await message.reply(f"🗑️ ᴘᴜʀɢᴇᴅ <code>{res.deleted_count}</code> ᴜꜱᴇʀꜱ ꜰʀᴏᴍ @{target} ᴅɪᴄᴛɪᴏɴᴀʀʏ.")

# --- ʟɪꜱᴛ ᴀʟʟ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴡᴏʀᴋᴇʀꜱ ---
@Client.on_message(filters.command("mybots") & filters.user(Config.OWNER_ID))
async def list_my_workers(client, message):
    cursor = worker_bots.find({})
    workers = await cursor.to_list(length=100)
    
    if not workers:
        return await message.reply("❌ ɴᴏ ᴡᴏʀᴋᴇʀ ʙᴏᴛꜱ ᴄᴏɴɴᴇᴄᴛᴇᴅ.")
    
    text = "🤖 <b>ᴀᴄᴛɪᴠᴇ ᴡᴏʀᴋᴇʀ ɴᴇᴛᴡᴏʀᴋ</b>\n\n"
    for i, w in enumerate(workers, 1):
        count = await broadcast_users.count_documents({"source": f"@{w['username']}"})
        text += f"{i}. {w['name']} (@{w['username']})\n   └ 👥 ꜱᴀᴠᴇᴅ ɪᴅꜱ: <code>{count}</code>\n\n"
    
    await message.reply(text)

# --- ᴠɪᴇᴡ & ᴇxᴘᴏʀᴛ ᴜꜱᴇʀ ɪᴅꜱ ---
# --- ꜱᴇʟᴇᴄᴛ ʙᴏᴛ ᴛᴏ ᴠɪᴇᴡ ɪᴅꜱ (ᴡɪᴛʜ ʟɪᴠᴇ ᴄᴏᴜɴᴛꜱ) ---
@Client.on_message(filters.command("botusers") & filters.user(Config.OWNER_ID))
async def view_bot_users_menu(client, message):
    workers = await worker_bots.find({}).to_list(length=100)
    if not workers:
        return await message.reply("❌ ɴᴏ ᴡᴏʀᴋᴇʀ ʙᴏᴛꜱ ꜰᴏᴜɴᴅ.")

    buttons = []
    for w in workers:
        # Har bot ke liye database se count nikaalein
        bot_tag = f"@{w['username']}"
        count = await broadcast_users.count_documents({"source": bot_tag})
        
        # Button label mein Name aur Count dono dikhayenge
        buttons.append([
            InlineKeyboardButton(
                f"🤖 {w['name']} | 👥 {count}", 
                callback_data=f"viewusers:{w['username']}"
            )
        ])

    await message.reply(
        "📂 <b>ʙᴏᴛ ᴜꜱᴇʀ ᴅɪᴄᴛɪᴏɴᴀʀʏ</b>\n\nꜱᴇʟᴇᴄᴛ ᴀ ʙᴏᴛ ᴛᴏ ᴇxᴘᴏʀᴛ ɪᴛꜱ ᴜꜱᴇʀ ʟɪꜱᴛ:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

# --- ʜᴀɴᴅʟᴇ ɪᴅ ᴇxᴘᴏʀᴛ ᴄᴀʟʟʙᴀᴄᴋ ---

@Client.on_callback_query(filters.regex(r"viewusers:(.*)"))
async def show_specific_bot_users(client, callback_query):
    # Colon (:) use karne se underscore (_) wale usernames safely nikal aayenge
    bot_user = callback_query.data.split(":")[1]
    bot_tag = f"@{bot_user}"
    
    await callback_query.answer(f"🔍 ꜰᴇᴛᴄʜɪɴɢ ɪᴅꜱ ꜰᴏʀ {bot_tag}...")
    
    # Database se IDs uthayein
    cursor = broadcast_users.find({"source": bot_tag}, {"user_id": 1})
    user_list = await cursor.to_list(length=10000)

    if not user_list:
        return await callback_query.message.edit(
            f"❌ ɴᴏ ᴜꜱᴇʀꜱ ꜰᴏᴜɴᴅ ꜰᴏʀ <b>{bot_tag}</b>\n\n"
            f"<i>💡 Try starting @{bot_user} or cloning IDs to this tag.</i>"
        )

    total = len(user_list)
    id_text = f"📋 <b>ᴜꜱᴇʀ ꜱᴀᴍᴘʟᴇ ꜰᴏʀ {bot_tag}</b>\n\n"
    
    # Pehle 30 IDs message mein sample ke liye
    for user in user_list[:30]:
        id_text += f"• <code>{user['user_id']}</code>\n"

    if total > 30:
        id_text += f"\n<i>...ᴀɴᴅ {total - 30} ᴍᴏʀᴇ ɪᴅꜱ ɪɴ ꜰɪʟᴇ.</i>"
        
        # Pura list .txt file mein
        full_list = "\n".join([str(u['user_id']) for u in user_list])
        file = io.BytesIO(full_list.encode())
        file.name = f"{bot_user}_ids.txt"
        
        await callback_query.message.reply_document(
            document=file, 
            caption=f"📄 <b>ꜰᴜʟʟ ɪᴅ ʟɪꜱᴛ:</b> {bot_tag}\n👥 ᴛᴏᴛᴀʟ: <code>{total}</code>"
        )

    await callback_query.message.edit(id_text)

@Client.on_message(filters.command("network") & filters.user(Config.OWNER_ID))
async def network_stats(client, message):
    total_bots = await worker_bots.count_documents({})
    total_users = await broadcast_users.count_documents({})
    unique_ids = len(await broadcast_users.distinct("user_id"))
    
    stats = (
        "🌐 <b>ɢʟᴏʙᴀʟ ɴᴇᴛᴡᴏʀᴋ ꜱᴛᴀᴛꜱ</b>\n\n"
        f"🤖 ᴛᴏᴛᴀʟ ᴡᴏʀᴋᴇʀꜱ: <code>{total_bots}</code>\n"
        f"👥 ᴛᴏᴛᴀʟ ꜱᴀᴠᴇᴅ ɪᴅꜱ: <code>{total_users}</code>\n"
        f"✨ ᴜɴɪQᴜᴇ ʀᴇᴀᴄʜ: <code>{unique_ids}</code>\n"
    )
    await message.reply(stats)