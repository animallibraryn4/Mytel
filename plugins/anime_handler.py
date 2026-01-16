import os
import asyncio
import logging
from typing import List, Dict, Optional
from pyrogram import Client
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import config
from database import db
from plugins.web_scraper import WebScraper
from plugins.torrent_handler import TorrentHandler
from plugins.utils import (
    extract_anime_info,
    get_anime_details,
    generate_random_hash,
    encode_video_file
)

logger = logging.getLogger(__name__)

class AnimeHandler:
    def __init__(self, main_bot: Client, file_bot: Client):
        self.bot = main_bot
        self.file_client = file_bot
        self.bot_me = None
        self.scraper = WebScraper()
        self.torrent_handler = TorrentHandler()
    
    def check_new_anime(self):
        """Check for new anime from RSS feed"""
        try:
            logger.info("Checking for new anime...")
            
            last_hash = db.get_last_hash()
            new_anime = self.scraper.get_latest_anime(last_hash, limit=30)
            
            if not new_anime or not new_anime.get("array"):
                logger.info("No new anime found.")
                return
            
            # Add new anime to queue
            db.add_remaining_anime(new_anime["array"])
            
            # Update last hash
            if new_anime.get("hash"):
                db.update_last_hash(new_anime["hash"])
            
            # Log and notify
            count = len(new_anime["array"])
            logger.info(f"Added {count} new anime to queue")
            
            # Send notification (in a thread-safe way)
            asyncio.run_coroutine_threadsafe(
                self._send_notification(count),
                asyncio.get_event_loop()
            )
        
        except Exception as e:
            logger.error(f"Error checking new anime: {e}")
    
    async def _send_notification(self, count: int):
        """Send notification about new anime"""
        try:
            await self.bot.send_message(
                config.PRODUCTION_CHAT,
                f"📥 {count} new anime added to queue"
            )
        except Exception as e:
            logger.error(f"Error sending notification: {e}")
    
    def process_anime_queue(self):
        """Process anime from the queue"""
        if db.is_worker_busy():
            logger.info("Worker is already busy, skipping...")
            return
        
        try:
            db.set_worker_status(True)
            anime_list = db.get_remaining_anime()
            
            if not anime_list:
                logger.info("Anime queue is empty")
                return
            
            # Process each anime in the list
            for anime_item in anime_list:
                self._process_anime_item(anime_item)
                
                # Update remaining list
                updated_list = db.remove_first_anime_item(anime_list)
                db.update_remaining_anime(updated_list)
                
                # Break after processing one item to prevent overload
                break
        
        except Exception as e:
            logger.error(f"Error processing anime queue: {e}")
        finally:
            db.set_worker_status(False)
    
    def _process_anime_item(self, anime_item: Dict):
        """Process a single anime item"""
        try:
            # Extract info from first title
            title = anime_item["title"][0]
            info = extract_anime_info(title)
            
            if not info:
                logger.error(f"Could not extract info from title: {title}")
                return
            
            # Get anime details from AniList
            anime_details = get_anime_details(info["search_query"])
            
            # Create and send post
            post_message = self._create_post_message(info, anime_details)
            
            # This would need to be run in an async context
            asyncio.run_coroutine_threadsafe(
                self._upload_anime_files(anime_item, info, anime_details),
                asyncio.get_event_loop()
            )
        
        except Exception as e:
            logger.error(f"Error processing anime item: {e}")
    
    def _create_post_message(self, info: Dict, anime_details: Dict) -> str:
        """Create post message for anime"""
        return config.POST_TEMPLATE.format(
            info["display_name"],
            info.get("episode", "N/A"),
            anime_details.get("status", "Unknown")
        )
    
    async def _upload_anime_files(self, anime_item: Dict, info: Dict, anime_details: Dict):
        """Upload anime files to channel"""
        try:
            # Send initial post with uploading button
            message = await self.bot.send_photo(
                chat_id=config.MAIN_CHANNEL,
                photo=anime_details.get("image", config.THUMBNAIL_URL),
                caption=self._create_post_message(info, anime_details),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("⏳ Uploading...", callback_data="uploading")
                ]])
            )
            
            # Process each quality version
            for i in range(len(anime_item["hash"])):
                await self._process_quality(
                    anime_item, i, info, message, anime_details
                )
        
        except Exception as e:
            logger.error(f"Error uploading anime files: {e}")
    
    async def _process_quality(self, anime_item: Dict, index: int, info: Dict, 
                               message, anime_details: Dict):
        """Process a specific quality version"""
        quality = anime_item["quality"][index]
        is_720p = "720" in quality
        
        # Download torrent
        download_msg = await self.bot.send_message(
            config.PRODUCTION_CHAT,
            f"📥 Downloading {anime_item['name']} ({quality})..."
        )
        
        downloaded_file = self.torrent_handler.download(
            anime_item["magnet"][index],
            download_msg
        )
        
        if not downloaded_file:
            await download_msg.edit_text("❌ Download failed")
            return
        
        # Upload original file
        await download_msg.edit_text(f"📤 Uploading {anime_item['name']}...")
        
        file_msg = await self.file_client.send_document(
            chat_id=config.FILES_CHANNEL,
            document=downloaded_file["file"],
            file_name=info["display_name"],
            caption=anime_item["title"][index],
            force_document=True,
            thumb=config.THUMBNAIL_URL
        )
        
        # Add to database
        file_hash = generate_random_hash(20)
        db.add_file_record(
            anime_item["title"][index],
            file_hash,
            file_msg.id
        )
        
        # Update post with download button
        await self._update_post_buttons(
            message, quality, file_msg.id, file_hash
        )
        
        # Process encoding for 720p files
        if is_720p:
            await self._encode_and_upload(
                downloaded_file["file"], anime_item, info, index, message
            )
        
        # Clean up downloaded file
        os.remove(downloaded_file["file"])
    
    async def _update_post_buttons(self, message, quality: str, 
                                   msg_id: int, file_hash: str):
        """Update post with download buttons"""
        buttons = message.reply_markup.inline_keyboard if message.reply_markup else []
        
        # Remove uploading button if present
        buttons = [btn for btn in buttons if btn[0].callback_data != "uploading"]
        
        # Add new button
        buttons.append([InlineKeyboardButton(
            text=f"⬇️ {quality}",
            url=f"https://t.me/{self.bot_me.username}?start={msg_id}_{file_hash}"
        )])
        
        await message.edit_reply_markup(InlineKeyboardMarkup(buttons))
    
    async def _encode_and_upload(self, file_path: str, anime_item: Dict, 
                                 info: Dict, index: int, message):
        """Encode and upload encoded version"""
        try:
            # Encode file
            encode_msg = await self.bot.send_message(
                config.PRODUCTION_CHAT,
                f"🔧 Encoding {anime_item['name']}..."
            )
            
            encoded_file = encode_video_file(file_path)
            
            if not encoded_file:
                await encode_msg.edit_text("❌ Encoding failed")
                return
            
            await encode_msg.edit_text("📤 Uploading encoded version...")
            
            # Upload encoded file
            encoded_msg = await self.file_client.send_document(
                chat_id=config.FILES_CHANNEL,
                document=encoded_file,
                file_name=f"[ENCODED] {info['display_name']}",
                caption=f"[ENCODED] {anime_item['title'][index]}",
                force_document=True,
                thumb=config.THUMBNAIL_URL
            )
            
            # Add to database
            enc_hash = generate_random_hash(20)
            db.add_file_record(
                f"[ENCODED] {anime_item['title'][index]}",
                enc_hash,
                encoded_msg.id
            )
            
            # Update post with encoded button
            buttons = message.reply_markup.inline_keyboard if message.reply_markup else []
            buttons.append([InlineKeyboardButton(
                text="🎬 ENCODED",
                url=f"https://t.me/{self.bot_me.username}?start={encoded_msg.id}_{enc_hash}"
            )])
            
            await message.edit_reply_markup(InlineKeyboardMarkup(buttons))
            
            # Clean up encoded file
            os.remove(encoded_file)
            
        except Exception as e:
            logger.error(f"Error in encoding: {e}")
