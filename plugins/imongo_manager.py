import time
from pyrogram import Client, filters
from motor.motor_asyncio import AsyncIOMotorClient
from database import db

@Client.on_message(filters.command("icheckmongo") & filters.private)
async def check_mongo(client, message):
    start = time.perf_counter()
    try:
        # Ping check
        await db.command("ping")
        end = time.perf_counter()
        await message.reply(f"✅ **MongoDB is Alive!**\n⏱ **Latency:** `{(end - start) * 1000:.2f}ms`")
    except Exception as e:
        await message.reply(f"❌ **MongoDB Error:**\n`{e}`")

@Client.on_message(filters.command("ishowmongo") & filters.private)
async def show_mongo(client, message):
    cols = await db.list_collection_names()
    if not cols:
        return await message.reply("📂 **No collections found.**")
    
    text = "📂 **Current Collections:**\n\n"
    for i, col in enumerate(cols, 1):
        count = await db[col].count_documents({})
        text += f"{i}. `{col}` (Documents: {count})\n"
    await message.reply(text)

@Client.on_message(filters.command("iclearmongo") & filters.private)
async def clear_mongo(client, message):
    cols = await db.list_collection_names()
    for col in cols:
        await db[col].drop()
    await message.reply("🗑 **All collections have been deleted successfully!**")

@Client.on_message(filters.command("idelmongocol") & filters.private)
async def del_col(client, message):
    if len(message.command) < 2:
        return await message.reply("❌ **Usage:** `/delmongocol collection_name`")
    
    col_name = message.command[1]
    await db[col_name].drop()
    await message.reply(f"🗑 Collection `{col_name}` deleted.")

@Client.on_message(filters.command("iclonemongo") & filters.private)
async def clone_mongo(client, message):
    # Usage: /clonemongo mongodb_url_here
    if len(message.command) < 2:
        return await message.reply("❌ **Usage:** `/clonemongo NEW_MONGO_URL`")
    
    new_url = message.command[1]
    await message.reply("⏳ **Cloning started... Please wait.**")
    
    try:
        new_client = AsyncIOMotorClient(new_url)
        new_db = new_client.get_default_database()
        
        cols = await db.list_collection_names()
        for col_name in cols:
            docs = await db[col_name].find().to_list(length=None)
            if docs:
                await new_db[col_name].insert_many(docs)
        
        await message.reply("✅ **Cloning Complete!** All data moved to new DB.")
    except Exception as e:
        await message.reply(f"❌ **Clone Failed:** `{e}`")