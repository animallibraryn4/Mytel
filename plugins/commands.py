

from pyrogram import filters, Client
from pyrogram.types import Message
from config import config
from database import db
import logging

logger = logging.getLogger(__name__)

# Convert owner IDs to integers for comparison
OWNER_IDS = [int(uid) for uid in config.OWNER_IDS]

def setup_commands(bot: Client):
    """Setup command handlers"""
    
    @bot.on_message(filters.command("alive") & filters.user(OWNER_IDS))
    async def alive_command(client: Client, message: Message):
        """Check if bot is alive"""
        await message.reply_text("✅ I am alive and running!")
        logger.info(f"Alive command executed by {message.from_user.id}")
    
    @bot.on_message(filters.command("start") & filters.private)
    async def start_command(client: Client, message: Message):
        """Handle start command"""
        try:
            # Extract hash from command
            args = message.text.split()
            if len(args) > 1:
                file_hash = args[1].split("_")[-1]
                doc = db.get_file_by_hash(file_hash)
                
                if not doc:
                    await message.reply_text("❌ Invalid hash or file not found.")
                    return
                
                # Forward the file
                await client.forward_messages(
                    chat_id=message.chat.id,
                    from_chat_id=config.FILES_CHANNEL,
                    message_ids=doc['message_id'],
                    protect_content=True
                )
                logger.info(f"File sent to {message.from_user.id}")
            else:
                # Show help message
                await message.reply_text(
                    "👋 Hello! I'm AutoAnimeBot\n\n"
                    "I can send anime files based on their hash.\n"
                    "Use the provided links to get files."
                )
        
        except Exception as e:
            logger.error(f"Error in start command: {e}")
            await message.reply_text("❌ An error occurred. Please try again.")
    
    @bot.on_message(filters.command("logs") & filters.user(OWNER_IDS))
    async def logs_command(client: Client, message: Message):
        """Send log file to owner"""
        try:
            # Send logs via document
            await client.send_document(
                chat_id=message.from_user.id,
                document=config.LOG_FILE,
                caption="📊 Current session logs"
            )
            await message.reply_text("✅ Logs sent to your PM")
            logger.info(f"Logs sent to {message.from_user.id}")
        
        except Exception as e:
            logger.error(f"Error sending logs: {e}")
            await message.reply_text(f"❌ Error: {e}")
    
    @bot.on_message(filters.command("status") & filters.user(OWNER_IDS))
    async def status_command(client: Client, message: Message):
        """Show bot status"""
        try:
            # Get database info
            remaining = db.get_remaining_anime()
            is_working = db.is_worker_busy()
            
            status_text = (
                "🤖 **Bot Status**\n"
                "──────────────\n"
                f"• **Worker Status:** {'🟢 Working' if is_working else '🟡 Idle'}\n"
                f"• **Queue Length:** {len(remaining)} anime\n"
                f"• **Database:** {'🟢 Connected' if db.test_connection() else '🔴 Disconnected'}\n"
                "──────────────\n"
                "Use /logs to get detailed logs."
            )
            
            await message.reply_text(status_text)
        
        except Exception as e:
            logger.error(f"Error in status command: {e}")
            await message.reply_text(f"❌ Error: {e}")
