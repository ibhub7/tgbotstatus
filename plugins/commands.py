import re
from pyrogram import Client, filters
from database import add_bot, remove_bot

def register_commands(bot: Client):
    @bot.on_message(filters.command("addbot") & filters.private)
    async def on_add(client, message):
        # Format: /addbot @username https://url.com
        args = message.text.split()
        if len(args) < 3:
            return await message.reply("❌ **Usage:** `/addbot @BotUsername https://your-link.com`")

        username = args[1].replace("@", "")
        url = args[2]

        try:
            # Telegram se Bot ka asli naam fetch karna
            target_bot = await client.get_users(username)
            full_name = target_bot.first_name
            
            # Database mein save karna (Username bhi save karenge link ke liye)
            await add_bot(full_name, url, username) 
            await message.reply(f"✅ **Monitoring started!**\n🤖 Bot: [{full_name}](telegram.me/{username})\n🔗 URL: `{url}`")
        
        except Exception as e:
            await message.reply(f"❌ **Error:** Username invalid hai ya bot nahi mila.\n`{e}`")

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