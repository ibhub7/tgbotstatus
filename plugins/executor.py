import asyncio
import logging
from pyrogram import Client, filters, enums
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated, PeerIdInvalid
from database import worker_bots, broadcast_users
from config import Config

logger = logging.getLogger("MonitorBot")

@Client.on_callback_query(filters.regex(r"exec_(.*)_(.*)"))
async def start_worker_cast(client, callback_query):
    # Extracting Bot Username and Message ID from the callback data
    bot_user, msg_id = callback_query.data.split("_")[1:]
    
    # 1. Fetch the selected Worker Bot's Token from MongoDB
    worker = await worker_bots.find_one({"username": bot_user})
    if not worker:
        return await callback_query.answer("❌ ʙᴏᴛ ɴᴏᴛ ꜰᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀꜱᴇ!", show_alert=True)

    await callback_query.message.edit(f"⏳ ɪɴɪᴛɪᴀʟɪᴢɪɴɢ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴠɪᴀ @{bot_user}...")
    
    # 2. Start the temporary Worker Client session
    async with Client(
        name=f"run_{bot_user}", 
        api_id=Config.API_ID, 
        api_hash=Config.API_HASH, 
        bot_token=worker['token'],
        in_memory=True
    ) as worker_bot:
        
        count = 0
        blocked = 0
        failed = 0
        
        # 3. Stream users assigned specifically to THIS bot
        async for user in broadcast_users.find({"source": f"@{bot_user}"}):
            try:
                # Copy message from the Master Bot's chat to the target User ID
                await worker_bot.copy_message(
                    chat_id=user['user_id'], 
                    from_chat_id=callback_query.message.chat.id, 
                    message_id=int(msg_id)
                )
                count += 1
                
                # Update status message every 20 successful sends
                if count % 20 == 0: 
                    await callback_query.message.edit(
                        f"📡 <b>@{bot_user} ɪꜱ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...</b>\n\n"
                        f"✅ ꜱᴇɴᴛ: <code>{count}</code>\n"
                        f"🚫 ʙʟᴏᴄᴋᴇᴅ: <code>{blocked}</code>"
                    )
                
                # Small delay to keep the bot under the Telegram spam radar
                await asyncio.sleep(0.05) 

            except FloodWait as e:
                # Wait exactly as long as Telegram requires if rate-limited
                await asyncio.sleep(e.value)
                # Retry after sleep
                await worker_bot.copy_message(chat_id=user['user_id'], from_chat_id=callback_query.message.chat.id, message_id=int(msg_id))
                count += 1

            except (UserIsBlocked, InputUserDeactivated):
                # Clean the database: Remove users who blocked the bot or deleted accounts
                await broadcast_users.delete_one({"user_id": user['user_id']})
                blocked += 1

            except (PeerIdInvalid, Exception) as e:
                # Log any other unexpected errors
                failed += 1
                continue

    # 4. Final Summary Update
    final_text = (
        f"🏁 <b>ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!</b>\n\n"
        f"🤖 ᴇxᴇᴄᴜᴛᴏʀ: @{bot_user}\n"
        f"✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟ: <code>{count}</code>\n"
        f"🗑️ ᴘᴜʀɢᴇᴅ (ʙʟᴏᴄᴋᴇᴅ): <code>{blocked}</code>\n"
        f"❌ ꜰᴀɪʟᴇᴅ/ꜱᴋɪᴘᴘᴇᴅ: <code>{failed}</code>"
    )
    
    await callback_query.message.edit(final_text)
    logger.info(f"Broadcast finished via @{bot_user}. Total: {count}")