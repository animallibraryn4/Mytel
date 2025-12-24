from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import UserNotParticipant
from config import FSUB_CHANNEL, FSUB_CHANNEL_2, FSUB_CHANNEL_3

async def is_subscribed(client, message):
    channels = []
    if FSUB_CHANNEL and FSUB_CHANNEL != 0:
        channels.append(FSUB_CHANNEL)
    if FSUB_CHANNEL_2 and FSUB_CHANNEL_2 != 0:
        channels.append(FSUB_CHANNEL_2)
    if FSUB_CHANNEL_3 and FSUB_CHANNEL_3 != 0:
        channels.append(FSUB_CHANNEL_3)
    
    if not channels:
        return True
    
    unjoined_channels = []
    channel_info_list = []
    
    for channel_id in channels:
        try:
            user = await client.get_chat_member(channel_id, message.from_user.id)
            if user.status == "kicked":
                await message.reply_text("<blockquote><b>❌ You are banned from using this bot.</b></blockquote>")
                return False
        except UserNotParticipant:
            try:
                chat = await client.get_chat(channel_id)
                channel_url = chat.invite_link if chat.invite_link else f"https://t.me/{chat.username}"
                unjoined_channels.append({
                    "id": channel_id,
                    "title": chat.title,
                    "url": channel_url
                })
                channel_info_list.append(f"• {chat.title}")
            except Exception:
                continue
        except Exception:
            continue
    
    if unjoined_channels:
        buttons = []
        for idx, channel in enumerate(unjoined_channels, 1):
            buttons.append([InlineKeyboardButton(f"Join Channel {idx} 📢", url=channel["url"])])
        
        buttons.append([InlineKeyboardButton("Try Again 🔄", callback_data="check_fsub")])
        
        channels_list = "\n".join(channel_info_list)
        await message.reply_text(
            f"<blockquote><b>⚠️ Force Subscribe Required!</b></blockquote>\n\n"
            f"<blockquote>Please join all these channels to use the bot:\n\n"
            f"{channels_list}\n\n"
            f"After joining, click 'Try Again'</blockquote>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return False
            
    return True
