import sys
import os

# Add current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
from pyrogram import Client
from config import API_HASH, API_ID, BOT_TOKEN

print("🤖 Starting Sequence Bot...")

app = Client(
    "sequence_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=BOT_TOKEN,
    workdir="/content"
)

# We'll import and register handlers directly here
from handlers.start_handler import register_start_handlers
from handlers.sequence_handler import register_sequence_handlers
from handlers.ls_handler import register_ls_handlers
from handlers.admin_handler import register_admin_handlers
from callbacks.main_callbacks import register_main_callbacks
from callbacks.ls_callbacks import register_ls_callbacks

# Register all handlers
register_start_handlers(app)
register_sequence_handlers(app)
register_ls_handlers(app)
register_admin_handlers(app)
register_main_callbacks(app)
register_ls_callbacks(app)

print("✅ All handlers registered successfully!")

if __name__ == "__main__":
    app.run()
