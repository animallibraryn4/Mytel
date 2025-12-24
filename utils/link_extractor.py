def extract_message_info(link):
    try:
        link = link.strip()
        
        if "/c/" in link:
            parts = link.split("/")
            chat_id_str = parts[4]
            
            if chat_id_str.startswith("-100"):
                chat_id = int(chat_id_str)
            elif chat_id_str.startswith("100"):
                chat_id = int("-" + chat_id_str)
            else:
                chat_id = int("-100" + chat_id_str)
            
            message_id = int(parts[5])
            return chat_id, message_id
            
        elif "t.me/" in link:
            parts = link.split("/")
            username = parts[3]
            message_id = int(parts[4])
            return username, message_id
            
    except Exception:
        pass
        
    return None, None
