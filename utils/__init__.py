from .main_callbacks import register_main_callbacks
from .ls_callbacks import register_ls_callbacks

def register_callbacks(app):
    register_main_callbacks(app)
    register_ls_callbacks(app)
