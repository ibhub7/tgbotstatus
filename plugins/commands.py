import re
from pyrogram import Client, filters
from database import add_bot, remove_bot

def register_commands(bot: Client):
    @bot.on_message(filters.command("addbot") & filters.private)
    async def on_add(client, message):
        match = re.search(r'"([^"]+)"\s+(https?://\S+)', message.text)
        if match:
            name, url = match.group(1).strip(), match.group(2).strip()
            await add_bot(name, url)
            await message.reply(f"✅ Monitoring started for: **{name}**")
        else:
            await message.reply("Usage: `/addbot \"Bot Name\" URL`")

    @bot.on_message(filters.command("removebot") & filters.private)
    async def on_remove(client, message):
        match = re.search(r'"([^"]+)"', message.text)
        if match:
            name = match.group(1).strip()
            await remove_bot(name)
            await message.reply(f"🗑 Removed **{name}**.")
        else:
            await message.reply("Usage: `/removebot \"Bot Name\"`")