"""
Handlers package for Sequence Bot
"""

from .start_handler import register_start_handlers
from .sequence_handler import register_sequence_handlers
from .ls_handler import register_ls_handlers
from .admin_handler import register_admin_handlers

def register_handlers(app):
    """
    Register all command handlers with the Pyrogram client
    """
    print("📝 Registering handlers...")
    register_start_handlers(app)
    register_sequence_handlers(app)
    register_ls_handlers(app)
    register_admin_handlers(app)
    print("✅ All handlers registered!")
