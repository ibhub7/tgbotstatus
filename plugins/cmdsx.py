from pyrogram import Client, filters
from pyrogram.types import BotCommand
from config import Config

async def set_commands(bot):
    commands = [
        BotCommand("start", "sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"),
        BotCommand("addbot", "ᴀᴅᴅ ʙᴏᴛ ᴛᴏ ʟɪsᴛ"),
        BotCommand("removebot", "ʀᴇᴍᴏᴠᴇ ᴀ ʙᴏᴛ"),
        BotCommand("list", "sʜᴏᴡ ᴀʟʟ ʏᴏᴜʀ ʙᴏᴛs"),
        BotCommand("set_interval", "sᴇᴛ 𝟸/𝟻 ᴍɪɴ ᴄʜᴇᴄᴋs"),
        BotCommand("dashboard", "ɢᴇᴛ ʏᴏᴜʀ ᴡᴇʙ ʟɪɴᴋ"),
        BotCommand("logs", "ᴠɪᴇᴡ sʏsᴛᴇᴍ ʟᴏɢs"),
        BotCommand("status", "ɢᴇᴛ ʙᴏᴛ sᴛᴀᴛs"),
    ]
    await bot.set_bot_commands(commands)

@Client.on_message(filters.command("addcmds") & filters.user(Config.OWNER_ID))
async def add_cmds_handler(client, message):
    try:
        await set_commands(client)
        await message.reply("✅ Bot commands set successfully!")
    except Exception as e:
        await message.reply(f"❌ Error: {e}")