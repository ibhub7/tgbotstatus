from pyrogram import Client, filters
from pyrogram.types import BotCommand
from config import Config

async def set_commands(bot):
    commands = [
        # --- User Commands ---
        BotCommand("start", "🚀 sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"),
        BotCommand("help", "❓ ɢᴇᴛ ʜᴇʟᴘ ɪɴsᴛʀᴜᴄᴛɪᴏɴs"),
        BotCommand("addbot", "➕ ᴀᴅᴅ ʙᴏᴛ ᴛᴏ ᴍᴏɴɪᴛᴏʀ"),
        BotCommand("removebot", "➖ ʀᴇᴍᴏᴠᴇ ᴀ ʙᴏᴛ"),
        BotCommand("list", "📑 sʜᴏᴡ ᴀʟʟ ʏᴏᴜʀ ʙᴏᴛs"),
        BotCommand("set_interval", "⏲️ sᴇᴛ 𝟸/𝟻 ᴍɪɴ ᴄʜᴇᴄᴋs"),
        BotCommand("set_link", "🔗 sᴇᴛ ʟɪᴠᴇ sᴛᴀᴛᴜs ʟɪɴᴋ"),
        BotCommand("get_link", "🔍 ᴠɪᴇᴡ ᴀᴄᴛɪᴠᴇ sᴛᴀᴛᴜs ʟɪɴᴋ"),
        BotCommand("settings", "⚙️ ᴍᴀɴᴀɢᴇ ʙᴏᴛ sᴇᴛᴛɪɴɢs"),
        BotCommand("reset_settings", "🔄 ʀᴇsᴇᴛ ᴛᴏ ᴅᴇғᴀᴜʟᴛs"),
        BotCommand("deleteall", "💥 ᴘᴜʀɢᴇ ᴀʟʟ ʙᴏᴛs"),
        BotCommand("dashboard", "🌐 ɢᴇᴛ ʏᴏᴜʀ ᴡᴇʙ ʟɪɴᴋ"),
        BotCommand("status", "📊 ɢᴇᴛ ʙᴏᴛ sᴛᴀᴛs"),
        BotCommand("id", "🆔 ɢᴇᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ɪᴅ"),
        BotCommand("info", "📋 ɢᴇᴛ ᴜsᴇʀ ɪɴғᴏʀᴍᴀᴛɪᴏɴ"),
        BotCommand("finfo", "✉️ ɢᴇᴛ ғᴏʀᴡᴀʀᴅ sᴏᴜʀᴄᴇ ɪᴅ"),
        BotCommand("broadcast", "📢 sᴇɴᴅ ᴀʟᴇʀᴛ ᴛᴏ ᴀʟʟ ᴜsᴇʀs"),
        BotCommand("logs", "📄 ᴠɪᴇᴡ sʏsᴛᴇᴍ ʟᴏɢs"),
        BotCommand("send", "✉️ sᴇɴᴅ ᴘʀɪᴠᴀᴛᴇ ᴍsɢ ᴛᴏ ᴜsᴇʀ"),
        BotCommand("stats", "📈 ᴠɪᴇᴡ ɢʟᴏʙᴀʟ ɴᴇᴛᴡᴏʀᴋ sᴛᴀᴛs"),
        BotCommand("restart", "🔄 ʀᴇsᴛᴀʀᴛ ᴛʜᴇ sʏsᴛᴇᴍ")
    ]
    ]
    await bot.set_bot_commands(commands)

@Client.on_message(filters.command("addcmds") & filters.user(Config.OWNER_ID))
async def add_cmds_handler(client, message):
    try:
        await set_commands(client)
        await message.reply("✅ **ʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅs ᴜᴘᴅᴀᴛᴇᴅ!**\n\n<blockquote>ᴀʟʟ {len(commands)} ᴄᴏᴍᴍᴀɴᴅs ʜᴀᴠᴇ ʙᴇᴇɴ ʀᴇɢɪsᴛᴇʀᴇᴅ. ɪғ ᴛʜᴇʏ ᴅᴏɴ'ᴛ ᴀᴘᴘᴇᴀʀ, ʀᴇsᴛᴀʀᴛ ʏᴏᴜʀ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴘᴘ.</blockquote>")
    except Exception as e:
        await message.reply(f"❌ **ᴇʀʀᴏʀ:** <code>{e}</code>")