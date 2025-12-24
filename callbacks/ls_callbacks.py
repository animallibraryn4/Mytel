import asyncio
from pyrogram.errors import FloodWait
from handlers.ls_handler import user_ls_state, get_messages_between, sequence_messages
from handlers.ls_handler import check_bot_admin
from database import Database

def register_ls_callbacks(app):
    @app.on_callback_query()
    async def ls_callback_handler(client, query):
        data = query.data
        user_id = query.from_user.id
        
        if data.startswith("ls_chat_"):
            await handle_ls_chat_callback(client, query, data, user_id)
        elif data.startswith("ls_channel_"):
            await handle_ls_channel_callback(client, query, data, user_id)
        elif data.startswith("ls_close_"):
            await handle_ls_close_callback(client, query, data, user_id)

async def handle_ls_chat_callback(client, query, data, user_id):
    target_user_id = int(data.split("_")[2])
    
    if user_id != target_user_id:
        await query.answer("This button is not for you!", show_alert=True)
        return
    
    if target_user_id not in user_ls_state:
        await query.answer("Session expired. Please start again with /ls", show_alert=True)
        await query.message.delete()
        return
    
    ls_data = user_ls_state[target_user_id]
    
    await query.message.edit_text("<blockquote>⏳ Fetching files from channel... Please wait.</blockquote>")
    
    try:
        chat_id = ls_data["first_chat"]
        start_msg_id = ls_data["first_msg_id"]
        end_msg_id = ls_data["second_msg_id"]
        
        messages = await get_messages_between(client, chat_id, start_msg_id, end_msg_id)
        
        if not messages:
            await query.message.edit_text("<blockquote>❌ No files found between the specified links.</blockquote>")
            return
        
        sorted_files = await sequence_messages(client, messages, ls_data.get("mode", "per_ep"))
        
        if not sorted_files:
            await query.message.edit_text("<blockquote>❌ No valid files found to sequence.</blockquote>")
            return
        
        await query.message.edit_text(f"<blockquote>📤 Sending {len(sorted_files)} files to chat... Please wait.</blockquote>")
        
        for file in sorted_files:
            try:
                await client.copy_message(user_id, from_chat_id=file["chat_id"], message_id=file["msg_id"])
                await asyncio.sleep(0.8)
            except Exception:
                continue
        
        Database.update_user_stats(user_id, len(sorted_files), query.from_user.first_name)
        
        await query.message.edit_text(f"<blockquote><b>✅ Successfully sent {len(sorted_files)} files to your chat!</b></blockquote>")
        
    except Exception as e:
        print(f"LS Chat error: {e}")
        await query.message.edit_text("<blockquote>❌ An error occurred while processing files. Please try again.</blockquote>")
    
    if target_user_id in user_ls_state:
        del user_ls_state[target_user_id]

async def handle_ls_channel_callback(client, query, data, user_id):
    target_user_id = int(data.split("_")[2])
    
    if user_id != target_user_id:
        await query.answer("This button is not for you!", show_alert=True)
        return
    
    if target_user_id not in user_ls_state:
        await query.answer("Session expired. Please start again with /ls", show_alert=True)
        await query.message.delete()
        return
    
    ls_data = user_ls_state[target_user_id]
    
    await query.message.edit_text("<blockquote>⏳ Checking bot permissions in channel... Please wait.</blockquote>")
    
    try:
        chat_id = ls_data["first_chat"]
        
        try:
            chat = await client.get_chat(chat_id)
            await query.message.edit_text(f"<blockquote>Checking channel: {chat.title}</blockquote>")
        except Exception as e:
            await query.message.edit_text(f"<blockquote>Error getting channel info: {e}</blockquote>")
            return
        
        is_admin = await check_bot_admin(client, chat_id)
        
        if not is_admin:
            try:
                bot_member = await client.get_chat_member(chat_id, "me")
                status_info = f"Bot status: {bot_member.status}"
                
                await query.message.edit_text(
                    f"<blockquote><b>❌ Bot admin check failed!</b></blockquote>\n\n"
                    f"<blockquote>Chat ID: {chat_id}\n"
                    f"Chat Title: {chat.title}\n"
                    f"Status: {status_info}\n\n"
                    f"To send files back to the channel, the bot must be added as an administrator "
                    f"with permission to post messages.</blockquote>"
                )
            except Exception as e:
                await query.message.edit_text(
                    f"<blockquote><b>❌ Bot is not admin in this channel!</b></blockquote>\n\n"
                    f"<blockquote>Error checking status: {e}\n\n"
                    f"To send files back to the channel, the bot must be added as an administrator "
                    f"with permission to post messages.</blockquote>"
                )
            return
        
        await query.message.edit_text("<blockquote>✅ Bot is admin! Fetching files from channel... Please wait.</blockquote>")
        
        start_msg_id = ls_data["first_msg_id"]
        end_msg_id = ls_data["second_msg_id"]
        
        messages = await get_messages_between(client, chat_id, start_msg_id, end_msg_id)
        
        if not messages:
            await query.message.edit_text("<blockquote>❌ No files found between the specified links.</blockquote>")
            return
        
        sorted_files = await sequence_messages(client, messages, ls_data.get("mode", "per_ep"))
        
        if not sorted_files:
            await query.message.edit_text("<blockquote>❌ No valid files found to sequence.</blockquote>")
            return
        
        await query.message.edit_text(f"<blockquote>📤 Sending {len(sorted_files)} files to channel... Please wait.</blockquote>")
        
        success_count = 0
        for file in sorted_files:
            try:
                await client.copy_message(chat_id, from_chat_id=file["chat_id"], message_id=file["msg_id"])
                await asyncio.sleep(2)
            except FloodWait as e:
                print(f"FloodWait triggered. Sleeping for {e.value} seconds.")
                await asyncio.sleep(e.value)
            except Exception:
                continue
            else:
                success_count += 1
        
        Database.update_user_stats(user_id, success_count, query.from_user.first_name)
        
        await query.message.edit_text(
            f"<blockquote><b>✅ Successfully sent {success_count} files back to the channel!</b></blockquote>\n"
            f"<blockquote>Total files found: {len(sorted_files)}\n"
            f"Successfully sent: {success_count}</blockquote>"
        )
        
    except Exception as e:
        print(f"LS Channel error: {e}")
        await query.message.edit_text(f"<blockquote>❌ An error occurred: {str(e)[:200]}...</blockquote>")
    
    if target_user_id in user_ls_state:
        del user_ls_state[target_user_id]

async def handle_ls_close_callback(client, query, data, user_id):
    target_user_id = int(data.split("_")[2])
    
    if user_id != target_user_id:
        await query.answer("This button is not for you!", show_alert=True)
        return
    
    await query.message.delete()
    
    if target_user_id in user_ls_state:
        del user_ls_state[target_user_id]
