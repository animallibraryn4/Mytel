import asyncio
from pyrogram import Client
from config import API_HASH, API_ID, BOT_TOKEN
import callbacks

app = Client(
    "sequence_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    workdir="/content"
)

# Register all handlers
handlers.register_handlers(app)
callbacks.register_callbacks(app)

if __name__ == "__main__":
    print("Bot starting...")
    app.run()
