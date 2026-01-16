import os
from typing import List

class Config:
    # Bot Information
    AUTHOR = "Yash-Kun"
    LICENSED_UNDER = "GNU GPL V-3.0"
    
    # Telegram Configuration
    API_ID = 22299340
    API_HASH = ""  # Add your API hash
    MAIN_BOT_TOKEN = "7765824536:AAFxnM5qftx3LWjLjxKsnXeuLf3XMXo950o"  # Add your bot token
    CLIENT_BOT_TOKEN = "7906213903:AAEvUmwjmwTHC9NtayJ2NLbYsROQdaOeZR0"  # Add your client bot token
    
    # Chat IDs
    OWNER_IDS = ["5380609667"]  # Convert to list of ints if needed
    MAIN_CHANNEL = -1001896877147
    FILES_CHANNEL = -1001896877147
    PRODUCTION_CHAT = -1001925970923
    
    # Database
    DATABASE_URL = "mongodb+srv://mikota4432:jkJDQuZH6o8pxxZe@cluster0.2vngilq.mongodb.net/?retryWrites=true&w=majority"
    DATABASE_NAME = "AAB"
    
    # File Paths
    DOWNLOADS_DIR = "./downloads"
    THUMBNAIL_URL = "https://files.catbox.moe/50drro.jpg"
    LOG_FILE = "logging.txt"
    
    # RSS Feed
    RSS_URL = "http://subsplease.org/rss"
    
    # AniList API
    ANILIST_URL = "https://graphql.anilist.co"
    
    # Post Template
    POST_TEMPLATE = """
🔸 {}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Episode - {}
〰️➖〰️➖〰️➖〰️➖〰️➖
🔸 Status - {}
➖〰️➖〰️➖〰️➖〰️➖〰️
🔸 Quality - Sub
〰️➖〰️➖〰️➖〰️➖〰️➖
"""
    
    # Check Intervals (in seconds)
    ANIME_CHECK_INTERVAL = 300  # 5 minutes
    WORKER_CHECK_INTERVAL = 300  # 5 minutes

config = Config()

