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

    @bot.on_message(filters.command("start") & filters.private)
    async def on_start(client, message):
        # Professional greeting using the user's name
        user_name = message.from_user.first_name
        
        start_text = (
            f"👋 **Hello {user_name}!**\n\n"
            "I am your **Advanced Bot Status Monitor**. I keep an eye on your "
            "Koyeb and Render deployments to ensure they stay online.\n\n"
            "📌 **Main Features:**\n"
            "• Automatic 5-minute status checks.\n"
            "• Live message editing in your channel.\n"
            "• Support for multi-word bot names.\n"
            "• No bot token required for pings.\n\n"
            "🛠 **How to use me:**\n"
            "1. Use `/addbot` to start monitoring a new URL.\n"
            "2. Use `/list` to see your database.\n"
            "3. Use `/stats` for a health overview.\n\n"
            "💡 **Example:**\n"
            "`/addbot \"Pro Movie Search\" https://mybot.koyeb.app`"
        )
        
        await message.reply(start_text)