from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant, FloodWait
from config import START_PIC, START_MSG, COMMAND_TXT, HELP_TXT, FSUB_CHANNEL, FSUB_CHANNEL_2, FSUB_CHANNEL_3
from handlers.sequence_handler import send_sequence_files, user_sequences, user_settings
from database import Database

async def safe_edit(message, text, reply_markup=None):
    try:
        await message.edit_text(text=text, reply_markup=reply_markup)
    except Exception as e:
        if "MESSAGE_NOT_MODIFIED" not in str(e):
            raise e

def register_main_callbacks(app):
    @app.on_callback_query()
    async def cb_handler(client, query):
        data = query.data
        user_id = query.from_user.id
        
        # FSUB callback
        if data == "check_fsub":
            channels = []
            if FSUB_CHANNEL and FSUB_CHANNEL != 0:
                channels.append(FSUB_CHANNEL)
            if FSUB_CHANNEL_2 and FSUB_CHANNEL_2 != 0:
                channels.append(FSUB_CHANNEL_2)
            if FSUB_CHANNEL_3 and FSUB_CHANNEL_3 != 0:
                channels.append(FSUB_CHANNEL_3)

            unjoined_channels = []
            channel_info_list = []

            for channel_id in channels:
                try:
                    user = await client.get_chat_member(channel_id, user_id)
                    if user.status == "kicked":
                        await query.answer("You are banned from using this bot!", show_alert=True)
                        return
                except UserNotParticipant:
                    try:
                        chat = await client.get_chat(channel_id)
                        url = chat.invite_link if chat.invite_link else f"https://t.me/{chat.username}"
                        unjoined_channels.append({"title": chat.title, "url": url})
                        channel_info_list.append(f"• {chat.title}")
                    except:
                        continue

            if unjoined_channels:
                buttons = []
                for i, ch in enumerate(unjoined_channels, 1):
                    buttons.append([InlineKeyboardButton(f"Join Channel {i} 📢", url=ch["url"])])
                buttons.append([InlineKeyboardButton("Try Again 🔄", callback_data="check_fsub")])
                
                channels_list = "\n".join(channel_info_list)
                
                await safe_edit(
                    query.message,
                    f"<b>⚠️ Still Not Subscribed!</b>\n\n"
                    f"<blockquote>You need to join all these channels:\n\n"
                    f"{channels_list}\n\n"
                    f"Please join and try again.</blockquote>",
                    InlineKeyboardMarkup(buttons)
                )
            else:
                await query.message.delete()
                await client.send_photo(
                    user_id,
                    START_PIC,
                    START_MSG,
                    reply_markup=InlineKeyboardMarkup([
                        [InlineKeyboardButton("ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs", callback_data="all_cmds")],
                        [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/BOTSKINGDOMS")],
                        [
                            InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"),
                            InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="help")
                        ]
                    ])
                )
            return
        
        # My all commands
        elif data == "all_cmds":
            updated_command_txt = COMMAND_TXT + "\n<blockquote>• /ls - Sequence files from channel links (range selection)</blockquote>"
            
            await safe_edit(
                query.message,
                updated_command_txt,
                InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_start"),
                        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close")
                    ]
                ])
            )
        
        # Back to start
        elif data == "back_start":
            await safe_edit(
                query.message,
                START_MSG,
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("ᴍʏ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs", callback_data="all_cmds")],
                    [InlineKeyboardButton("ᴜᴘᴅᴀᴛᴇs", url="https://t.me/BOTSKINGDOMS")],
                    [
                        InlineKeyboardButton("ᴄʟᴏsᴇ", callback_data="close"),
                        InlineKeyboardButton("ᴀʙᴏᴜᴛ", callback_data="help")
                    ]
                ])
            )
        
        # About/Help
        elif data == "help":
            await safe_edit(
                query.message,
                HELP_TXT,
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("ʙᴀᴄᴋ", callback_data="back_start")]
                ])
            )
        
        # Sequence modes
        elif data == "set_mode_group":
            user_settings[user_id] = "group"
            await query.message.edit_text("<blockquote><b>✅ MODE SET: QUALITY FLOW</b></blockquote>")

        elif data == "set_mode_per_ep":
            user_settings[user_id] = "per_ep"
            await query.message.edit_text("<blockquote><b>✅ MODE SET: EPISODE FLOW</b></blockquote>")

        elif data == "send_sequence":
            if user_id in user_sequences:
                await send_sequence_files(client, query.message, user_id)

        elif data == "cancel_sequence":
            user_sequences.pop(user_id, None)
            await query.message.edit_text("<blockquote>Sequence cancelled.</blockquote>")

        # Close
        elif data == "close":
            await query.message.delete()

        # Broadcast callback
        elif data in ["confirm_broadcast", "cancel_broadcast"]:
            await handle_broadcast_callback(client, query, data)

async def handle_broadcast_callback(client, query, data):
    user_id = query.from_user.id
    
    if data == "confirm_broadcast":
        from config import OWNER_ID
        if user_id != OWNER_ID:
            await query.answer("Only owner can broadcast!", show_alert=True)
            return
        
        await query.message.edit_text("<blockquote>📤 Starting broadcast... Please wait.</blockquote>")
        
        all_users = Database.get_all_users()
        total_users = len(all_users)
        
        success = 0
        failed = 0
        blocked = 0
        
        progress_msg = await query.message.edit_text(
            f"<blockquote>📤 Broadcasting...\n"
            f"Progress: 0/{total_users}\n"
            f"✅ Success: 0 | ❌ Failed: 0</blockquote>"
        )
        
        for index, user in enumerate(all_users, 1):
            user_id = user.get("user_id")
            
            try:
                await query.message.reply_to_message.copy(user_id)
                success += 1
                
                if index % 20 == 0 or index == total_users:
                    try:
                        await progress_msg.edit_text(
                            f"<blockquote>📤 Broadcasting...\n"
                            f"Progress: {index}/{total_users}\n"
                            f"✅ Success: {success} | ❌ Failed: {failed}</blockquote>"
                        )
                    except:
                        pass
                
                await asyncio.sleep(0.1)
                
            except FloodWait as e:
                await asyncio.sleep(e.value + 1)
                try:
                    await query.message.reply_to_message.copy(user_id)
                    success += 1
                except:
                    failed += 1
                    
            except Exception as e:
                if "USER_IS_BLOCKED" in str(e) or "user is deactivated" in str(e):
                    blocked += 1
                else:
                    failed += 1
        
        from datetime import datetime
        stats = {
            "total": total_users,
            "success": success,
            "failed": failed,
            "blocked": blocked,
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        Database.save_broadcast_stats(stats)
        
        stats_text = (
            f"<b>📊 Broadcast Completed!</b>\n\n"
            f"<blockquote>👥 Total Users: {total_users}\n"
            f"✅ Successful: {success}\n"
            f"❌ Failed: {failed}\n"
            f"🚫 Blocked/Deleted: {blocked}</blockquote>"
        )
        
        await progress_msg.edit_text(stats_text)
    
    elif data == "cancel_broadcast":
        await query.message.edit_text("<blockquote>❌ Broadcast cancelled.</blockquote>")
