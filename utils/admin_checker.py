from pyrogram.errors import ChatAdminRequired, ChannelPrivate

async def check_bot_admin(client, chat_id):
    try:
        if isinstance(chat_id, str):
            try:
                chat = await client.get_chat(chat_id)
                chat_id = chat.id
            except Exception:
                return False
        
        try:
            bot_member = await client.get_chat_member(chat_id, "me")
            status_str = str(bot_member.status).lower()
            
            admin_statuses = [
                "administrator", "creator", "admin",
                "chat_member_status_administrator", "chat_member_status_creator"
            ]
            
            for admin_status in admin_statuses:
                if admin_status.lower() in status_str:
                    return True
                    
            return False
            
        except (ChatAdminRequired, ChannelPrivate):
            return False
        except Exception:
            return False
            
    except Exception:
        return False
