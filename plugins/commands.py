import re
from pyrogram import Client, filters
from database import add_bot, remove_bot
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from config import Config

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
    async def start_cmd(client, message):
        # Aapka Dashboard URL (Koyeb/Render ka URL)
        dashboard_url = "https://your-app-name.koyeb.app" 

        text = (
            f"👋 **Hello {message.from_user.mention}!**\n\n"
            "Welcome to **Bot Monitor Pro**. I can track your bots' uptime "
            "and alert you if they go offline.\n\n"
            "📢 **Status Channel:** [Join Here](https://t.me/your_channel)\n"
            "📊 **Live Dashboard:** Click the button below!"
        )

        reply_markup = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🌐 Open Web Dashboard", 
                    web_app=WebAppInfo(url=dashboard_url)
                )
            ],
            [
                InlineKeyboardButton("📢 Channel", url="https://t.me/infinity_botzz"),
                InlineKeyboardButton("👨‍💻 Owner", user_id=Config.OWNER_ID)
            ]
        ])

        await message.reply(
            text, 
            reply_markup=reply_markup,
            disable_web_page_preview=True
        )