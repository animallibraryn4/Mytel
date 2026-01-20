import os
import re
import time
import shutil
import asyncio
import logging
from datetime import datetime
from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InputMediaDocument, Message
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
from plugins.antinsfw import check_anti_nsfw
from helper.utils import progress_for_pyrogram, humanbytes, convert
from helper.database import n4bots
from config import Config
from plugins import is_user_verified, send_verification
from plugins.auto_rename import info_mode_users
from plugins.sequence import user_sequences
from plugins.admin_panel import check_ban_status

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== IMPROVED QUEUE SYSTEM =====
class UserQueueManager:
    """Manages separate queues and workers for each user"""
    
    def __init__(self):
        self.user_queues = {}  # user_id -> asyncio.Queue
        self.user_workers = {}  # user_id -> task
        self.user_sequence_counters = {}  # user_id -> sequence counter
        self.max_concurrent_per_user = 1  # Process 1 file at a time per user
        self.user_semaphores = {}  # user_id -> semaphore
        self.client = None  # Will be set when bot starts
        self.processing_messages = {}  # user_id -> set of message IDs being processed
        
    def set_client(self, client):
        """Set the client instance for processing"""
        self.client = client
        
    async def add_to_queue(self, user_id, message):
        """Add a message to user's queue and ensure worker is running"""
        # Initialize message tracking for user
        if user_id not in self.processing_messages:
            self.processing_messages[user_id] = set()
        
        # Check if message is already being processed
        if message.id in self.processing_messages[user_id]:
            logger.warning(f"Message {message.id} for user {user_id} is already in queue, skipping")
            return
            
        # Mark message as being processed
        self.processing_messages[user_id].add(message.id)
        
        # Create queue for user if not exists
        if user_id not in self.user_queues:
            self.user_queues[user_id] = asyncio.Queue()
            self.user_semaphores[user_id] = asyncio.Semaphore(self.max_concurrent_per_user)
            
            # Initialize sequence counter
            self.user_sequence_counters[user_id] = 0
            
            # Start worker for this user
            self.user_workers[user_id] = asyncio.create_task(
                self.user_worker(user_id, self.client)
            )
            logger.info(f"Started worker for user {user_id}")
        
        # Increment sequence counter and add message to queue
        self.user_sequence_counters[user_id] += 1
        sequence_num = self.user_sequence_counters[user_id]
        
        await self.user_queues[user_id].put((sequence_num, message))
        logger.info(f"Added message to queue for user {user_id}, position: {sequence_num}")
        
    async def user_worker(self, user_id, client):
        """Worker that processes files for a specific user"""
        queue = self.user_queues.get(user_id)
        if not queue:
            return
            
        # Dictionary to maintain order of messages
        pending_messages = {}
        next_expected_sequence = 1
        
        while True:
            try:
                # Wait for next message with timeout
                sequence_num, message = await asyncio.wait_for(queue.get(), timeout=300)
                
                # Store message in pending dict
                pending_messages[sequence_num] = message
                
                # Process messages in order
                while next_expected_sequence in pending_messages:
                    message_to_process = pending_messages.pop(next_expected_sequence)
                    
                    # Process with user's semaphore (ensures only 1 file at a time per user)
                    async with self.user_semaphores[user_id]:
                        # Use the actual processing function with client
                        await process_rename(client, message_to_process)
                    
                    # Remove message from tracking after processing
                    if user_id in self.processing_messages and message_to_process.id in self.processing_messages[user_id]:
                        self.processing_messages[user_id].remove(message_to_process.id)
                    
                    queue.task_done()
                    next_expected_sequence += 1
                    
            except asyncio.TimeoutError:
                # Cleanup if no activity for 5 minutes
                logger.info(f"Worker timeout for user {user_id}, cleaning up...")
                await self.cleanup_user(user_id)
                break
                
            except Exception as e:
                logger.error(f"Error in worker for user {user_id}: {e}")
                try:
                    queue.task_done()
                except:
                    pass
                
                # Remove message from tracking on error
                if user_id in self.processing_messages and message.id in self.processing_messages[user_id]:
                    self.processing_messages[user_id].remove(message.id)
                    
                # Don't break on individual errors, continue processing
                continue
    
    async def cleanup_user(self, user_id):
        """Clean up user's queue and worker"""
        if user_id in self.user_queues:
            try:
                # Cancel worker
                if user_id in self.user_workers:
                    self.user_workers[user_id].cancel()
                    try:
                        await self.user_workers[user_id]
                    except asyncio.CancelledError:
                        pass
                
                # Clear all data
                del self.user_queues[user_id]
                del self.user_workers[user_id]
                del self.user_semaphores[user_id]
                if user_id in self.user_sequence_counters:
                    del self.user_sequence_counters[user_id]
                if user_id in self.processing_messages:
                    del self.processing_messages[user_id]
                    
                logger.info(f"Cleaned up user {user_id}")
            except Exception as e:
                logger.error(f"Error cleaning up user {user_id}: {e}")
    
    def get_active_users(self):
        """Get list of users with active queues"""
        return list(self.user_queues.keys())

# Global queue manager
queue_manager = UserQueueManager()

# ===== PATTERNS =====
pattern_caption_season_verbose = re.compile(
    r'(?:season|saison|sezon|сезон|temporada|сезона|temporada)\s*[:=-]?\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_episode_verbose = re.compile(
    r'(?:episode|ep|eps|эпизод|cap[íi]tulo|серия|episodio)\s*[:=-]?\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_season_episode_combined = re.compile(
    r'(?:season|s)\s*[:=-]?\s*(\d+)\s*(?:episode|ep)\s*[:=-]?\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_simple = re.compile(
    r'(?:season|s)\s*(\d+)\s*(?:episode|ep)\s*(\d+)', 
    re.IGNORECASE
)
pattern_caption_number_pair = re.compile(r'(\d+)\s*(?:[-~]|and|&|,)\s*(\d+)', re.IGNORECASE)
pattern1 = re.compile(r'S(\d+)(?:E|EP)(\d+)')
pattern2 = re.compile(r'S(\d+)\s*(?:E|EP|-\s*EP)(\d+)')
pattern3 = re.compile(r'(?:[([<{]?\s*(?:E|EP)\s*(\d+)\s*[)\]>}]?)')
pattern3_2 = re.compile(r'(?:\s*-\s*(\d+)\s*)')
pattern4 = re.compile(r'S(\d+)[^\d]*(\d+)', re.IGNORECASE)
patternX = re.compile(r'(\d+)')
pattern5 = re.compile(r'\b(?:.*?(\d{3,4}[^\dp]*p).*?|.*?(\d{3,4}p))\b', re.IGNORECASE)
pattern6 = re.compile(r'[([<{]?\s*4k\s*[)\]>}]?', re.IGNORECASE)
pattern7 = re.compile(r'[([<{]?\s*2k\s*[)\]>}]?', re.IGNORECASE)
pattern8 = re.compile(r'[([<{]?\s*HdRip\s*[)\]>}]?|\bHdRip\b', re.IGNORECASE)
pattern9 = re.compile(r'[([<{]?\s*4kX264\s*[)\]>}]?', re.IGNORECASE)
pattern10 = re.compile(r'[([<{]?\s*4kx265\s*[)]>}]?', re.IGNORECASE)
pattern11 = re.compile(r'Vol(\d+)\s*-\s*Ch(\d+)', re.IGNORECASE)

# ===== HELPER FUNCTIONS =====
def standardize_quality_name(quality):
    """Standardize quality names for consistent storage"""
    if not quality or quality == "Unknown":
        return "Unknown"
        
    q = quality.lower().strip()
    if any(x in q for x in ['4k', '2160', 'uhd']): return '2160p'
    if any(x in q for x in ['2k', '1440', 'qhd']): return '1440p'
    if '1080' in q: return '1080p'
    if '720' in q: return '720p'
    if '480' in q: return '480p'
    if '360' in q: return '360p'
    if any(x in q for x in ['hdrip', 'hd', 'web-dl']): return 'HDrip'
    if '4kx264' in q: return '4kX264'
    if '4kx265' in q: return '4kx265'
    
    match = re.search(r'(\d{3,4}p)', q)
    if match: return match.group(1)
    
    return quality.capitalize()

async def convert_ass_subtitles(input_path, output_path):
    """Convert ASS subtitles to mov_text format for MP4 compatibility"""
    ffmpeg_cmd = shutil.which('ffmpeg')
    if ffmpeg_cmd is None:
        raise Exception("FFmpeg not found")
    
    command = [
        ffmpeg_cmd,
        '-i', input_path,
        '-c:v', 'copy',
        '-c:a', 'copy',
        '-c:s', 'mov_text',
        '-map', '0',
        '-loglevel', 'error',
        '-y',
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_message = stderr.decode()
        raise Exception(f"Subtitle conversion failed: {error_message}")

async def convert_to_mkv(input_path, output_path):
    """Convert any video file to MKV format without re-encoding"""
    ffmpeg_cmd = shutil.which('ffmpeg')
    if ffmpeg_cmd is None:
        raise Exception("FFmpeg not found")
    
    command = [
        ffmpeg_cmd,
        '-i', input_path,
        '-map', '0',
        '-c', 'copy',
        '-loglevel', 'error',
        '-y',
        output_path
    ]
    
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    
    if process.returncode != 0:
        error_message = stderr.decode()
        raise Exception(f"MKV conversion failed: {error_message}")

def extract_quality(text):
    """Extract quality from text with enhanced caption support"""
    caption_quality_patterns = [
        (re.compile(r'(?:quality|resolution|res|qualit[ée])\s*[:=-]?\s*(\d{3,4}[^\dp]*p)', re.IGNORECASE), 
         lambda m: m.group(1)),
        (re.compile(r'(?:quality|resolution|res|qualit[ée])\s*[:=-]?\s*(\d{3,4}p)', re.IGNORECASE), 
         lambda m: m.group(1)),
        (re.compile(r'\b(?:HD|Full HD|FHD|UHD|4K|2K|HDR|HDRip)\b', re.IGNORECASE),
         lambda m: m.group(0)),
    ]
    
    for pattern, quality in caption_quality_patterns:
        match = re.search(pattern, text)
        if match:
            return quality(match) if callable(quality) else quality
    
    for pattern, quality in [(pattern5, lambda m: m.group(1) or m.group(2)), 
                            (pattern6, "4k"), 
                            (pattern7, "2k"), 
                            (pattern8, "HdRip"), 
                            (pattern9, "4kX264"), 
                            (pattern10, "4kx265")]:
        match = re.search(pattern, text)
        if match: 
            return quality(match) if callable(quality) else quality
    return "Unknown"

def extract_season_number(text, is_caption_mode=False):
    """Extract season number from text with enhanced caption support"""
    if not text:
        return None
    
    if is_caption_mode:
        clean_text = re.sub(r'\s+', ' ', text.strip())
        
        match = pattern_caption_season_verbose.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_season_episode_combined.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_simple.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_number_pair.search(clean_text)
        if match:
            if any(keyword in clean_text.lower() for keyword in ['season', 'episode', 'ep', 's', 'e']):
                return match.group(1)
    
    for pattern in [pattern1, pattern4]:
        match = pattern.search(text)
        if match: 
            return match.group(1)
    
    return None

def extract_episode_number(text, is_caption_mode=False):
    """Extract episode number from text with enhanced caption support"""
    if not text:
        return None
    
    if is_caption_mode:
        clean_text = re.sub(r'\s+', ' ', text.strip())
        
        match = pattern_caption_episode_verbose.search(clean_text)
        if match:
            return match.group(1)
        
        match = pattern_caption_season_episode_combined.search(clean_text)
        if match:
            return match.group(2)
        
        match = pattern_caption_simple.search(clean_text)
        if match:
            return match.group(2)
        
        match = pattern_caption_number_pair.search(clean_text)
        if match:
            if any(keyword in clean_text.lower() for keyword in ['season', 'episode', 'ep', 's', 'e']):
                return match.group(2)
    
    for pattern in [pattern1, pattern2, pattern3, pattern3_2, pattern4, patternX]:
        match = pattern.search(text)
        if match: 
            if pattern in [pattern1, pattern2, pattern4]:
                return match.group(2) 
            else:
                return match.group(1)
    
    return None

def extract_volume_chapter(filename):
    match = re.search(pattern11, filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

async def forward_to_dump_channel(client, path, media_type, ph_path, file_name, renamed_file_name, user_info):
    if not Config.DUMP_CHANNEL: 
        return
    try:
        dump_caption = (
            f"➜ **File Renamed**\n\n"
            f"» **User:** {user_info['mention']}\n"
            f"» **User ID:** `{user_info['id']}`\n"
            f"» **Username:** @{user_info['username']}\n\n"
            f"➲ **Original Name:** `{file_name}`\n"
            f"➲ **Renamed To:** `{renamed_file_name}`"
        )
        
        send_func = {
            "document": client.send_document, 
            "video": client.send_video, 
            "audio": client.send_audio,
            "image": client.send_document  # Images sent as documents
        }.get(media_type, client.send_document)
        
        await send_func(
            Config.DUMP_CHANNEL,
            **{media_type if media_type != "image" else "document": path},
            file_name=renamed_file_name,
            caption=dump_caption,
            thumb=ph_path if ph_path else None,
        )
    except Exception as e:
        logger.error(f"[DUMP ERROR] {e}")

async def extract_info_from_source(message, user_mode):
    """Extract season, episode, quality from source based on mode"""
    user_id = message.from_user.id
    is_caption_mode = user_mode == "caption_mode"
    
    if user_mode == "file_mode":
        if message.document:
            source_text = message.document.file_name
        elif message.video:
            source_text = message.video.file_name or ""
        elif message.audio:
            source_text = message.audio.file_name or ""
        elif message.photo:
            # For photos, use caption if available, otherwise no text
            source_text = message.caption or ""
        elif message.animation:
            # For animations/GIFs
            source_text = message.animation.file_name or (message.caption or "")
        elif message.sticker:
            # Stickers don't have filenames
            source_text = message.caption or ""
        else:
            return None, None, None, None, None
    else:
        source_text = message.caption or ""
    
    if source_text:
        source_text = re.sub(r'\s+', ' ', source_text.strip())
    
    season_number = extract_season_number(source_text, is_caption_mode)
    episode_number = extract_episode_number(source_text, is_caption_mode)
    
    if is_caption_mode and not episode_number and season_number:
        episode_patterns = [
            r'episode\s*[:=-]?\s*(\d+)',
            r'ep\s*[:=-]?\s*(\d+)',
            r'eps?\s*(\d+)',
            r'e\s*(\d+)',
        ]
        
        for ep_pattern in episode_patterns:
            match = re.search(ep_pattern, source_text, re.IGNORECASE)
            if match:
                episode_number = match.group(1)
                break
    
    extracted_quality = extract_quality(source_text)
    standard_quality = standardize_quality_name(extracted_quality) if extracted_quality != "Unknown" else None
    
    volume_number, chapter_number = extract_volume_chapter(source_text)
    
    return season_number, episode_number, standard_quality, volume_number, chapter_number

# ===== IMAGE SUPPORT =====
def is_image_file(file_name):
    """Check if file is an image based on extension"""
    if not file_name:
        return False
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif', '.ico', '.jfif']
    return any(file_name.lower().endswith(ext) for ext in image_extensions)

def get_image_extension(file_name, mime_type=None):
    """Get appropriate extension for image file"""
    if mime_type:
        if 'jpeg' in mime_type or 'jpg' in mime_type:
            return '.jpg'
        elif 'png' in mime_type:
            return '.png'
        elif 'gif' in mime_type:
            return '.gif'
        elif 'webp' in mime_type:
            return '.webp'
        elif 'bmp' in mime_type:
            return '.bmp'
        elif 'tiff' in mime_type:
            return '.tiff'
    
    # Fallback to original extension
    if file_name:
        ext = os.path.splitext(file_name)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.tif']:
            return ext
    
    # Default to .jpg
    return '.jpg'

# ===== MAIN PROCESSING FUNCTION =====
async def process_rename(client: Client, message: Message):
    ph_path = None
    
    user_id = message.from_user.id
    if not await is_user_verified(user_id): 
        return

    user_mode = await n4bots.get_mode(user_id)
    format_template = await n4bots.get_format_template(user_id)
    media_preference = await n4bots.get_media_preference(user_id)
    
    if not format_template:
        return await message.reply_text("Please Set An Auto Rename Format First Using /autorename")

    # Determine file type and get file information
    is_image = False
    is_gif = False
    is_sticker = False
    is_pdf = False
    
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
        file_size = message.document.file_size
        mime_type = message.document.mime_type or ""
        
        # Check if it's an image document
        if mime_type.startswith('image/'):
            is_image = True
            media_type = "image"
        elif mime_type == "application/pdf":
            is_pdf = True
            media_type = media_preference or "document"
        else:
            media_type = media_preference or "document"
            is_pdf = False
            
    elif message.video:
        file_id = message.video.file_id
        file_name = f"{message.video.file_name}.mp4" if message.video.file_name else "video.mp4"
        file_size = message.video.file_size
        media_type = media_preference or "video"
        is_pdf = False
        
    elif message.audio:
        file_id = message.audio.file_id
        file_name = f"{message.audio.file_name}.mp3" if message.audio.file_name else "audio.mp3"
        file_size = message.audio.file_size
        media_type = media_preference or "audio"
        is_pdf = False
        
    elif message.photo:
        # Handle photos (compressed images sent as photo)
        file_id = message.photo.file_id
        file_name = f"photo_{message.id}.jpg"
        file_size = message.photo.file_size
        media_type = "image"
        is_image = True
        is_pdf = False
        
    elif message.animation:
        # Handle GIFs/animations
        file_id = message.animation.file_id
        file_name = message.animation.file_name or f"animation_{message.id}.gif"
        file_size = message.animation.file_size
        media_type = "image"
        is_image = True
        is_gif = True
        is_pdf = False
        
    elif message.sticker:
        # Handle stickers
        file_id = message.sticker.file_id
        file_name = f"sticker_{message.id}.webp"
        file_size = message.sticker.file_size
        media_type = "image"
        is_image = True
        is_sticker = True
        is_pdf = False
        
    else:
        return await message.reply_text("Unsupported File Type")

    # Also check by filename if it wasn't already identified as image
    if not is_image and file_name:
        is_image = is_image_file(file_name)

    if user_mode == "file_mode":
        check_text = file_name
    else:
        check_text = message.caption or ""
    
    if await check_anti_nsfw(check_text, message):
        return await message.reply_text("NSFW content detected. File upload rejected.")

    season_number, episode_number, standard_quality, volume_number, chapter_number = await extract_info_from_source(message, user_mode)
    
    logger.info(f"User {user_id} Mode: {user_mode}")
    logger.info(f"Source Text: {message.caption if user_mode == 'caption_mode' else file_name}")
    logger.info(f"Extracted - Season: {season_number}, Episode: {episode_number}, Quality: {standard_quality}")
    logger.info(f"File Type: Image={is_image}, GIF={is_gif}, Sticker={is_sticker}")

    if episode_number:
        format_template = format_template.replace("[EP.NUM]", str(episode_number)).replace("{episode}", str(episode_number))
    else:
        format_template = format_template.replace("[EP.NUM]", "").replace("{episode}", "")

    if season_number:
        format_template = format_template.replace("[SE.NUM]", str(season_number)).replace("{season}", str(season_number))
    else:
        format_template = format_template.replace("[SE.NUM]", "").replace("{season}", "")

    if volume_number and chapter_number:
        format_template = format_template.replace("[Vol{volume}]", f"Vol{volume_number}").replace("[Ch{chapter}]", f"Ch{chapter_number}")
    else:
        format_template = format_template.replace("[Vol{volume}]", "").replace("[Ch{chapter}]", "")

    # For images, don't add quality tags
    if is_image:
        format_template = format_template.replace("[QUALITY]", "").replace("{quality}", "")
    elif not is_pdf and standard_quality:
        format_template = format_template.replace("[QUALITY]", standard_quality).replace("{quality}", standard_quality)
    else:
        format_template = format_template.replace("[QUALITY]", "").replace("{quality}", "")

    format_template = re.sub(r'\s+', ' ', format_template).strip()
    format_template = format_template.replace("_", " ")
    format_template = re.sub(r'\[\s*\]', '', format_template)

    # Get file extension
    _, original_extension = os.path.splitext(file_name)
    
    # For images, use appropriate extension
    if is_image:
        if is_gif:
            file_extension = '.gif'
        elif is_sticker:
            file_extension = '.webp'
        elif message.document and message.document.mime_type:
            file_extension = get_image_extension(file_name, message.document.mime_type)
        elif message.photo:
            file_extension = '.jpg'
        else:
            file_extension = original_extension if original_extension else '.jpg'
    else:
        file_extension = original_extension
    
    renamed_file_name = f"{format_template}{file_extension}"
    
    download_path = f"downloads/{message.id}_{renamed_file_name}"
    metadata_path = f"Metadata/{message.id}_{renamed_file_name}"
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("Metadata", exist_ok=True)

    download_msg = await message.reply_text("**__Downloading...__**")
    
    try:
        path = await client.download_media(
            message,
            file_name=download_path,
            progress=progress_for_pyrogram,
            progress_args=("Download Started...", download_msg, time.time()),
        )
    except Exception as e:
        return await download_msg.edit(f"**Download Error:** {e}")

    await download_msg.edit("**__Processing File...__**")

    try:
        # For images, skip metadata and MKV conversion
        if is_image:
            # Simply copy the image file without processing
            import shutil
            shutil.copy2(path, metadata_path)
            path = metadata_path
            
            # Update renamed file name with correct extension
            if not renamed_file_name.lower().endswith(file_extension.lower()):
                renamed_file_name = f"{format_template}{file_extension}"
                metadata_path = f"Metadata/{message.id}_{renamed_file_name}"
                
        else:
            # Original processing for non-image files
            need_mkv_conversion = False
            if media_type == "document":
                need_mkv_conversion = True
            elif media_type == "video" and path.lower().endswith('.mp4'):
                need_mkv_conversion = True

            if need_mkv_conversion and not path.lower().endswith('.mkv'):
                temp_mkv_path = f"{path}.temp.mkv"
                try:
                    await convert_to_mkv(path, temp_mkv_path)
                    os.remove(path)
                    os.rename(temp_mkv_path, path)
                    renamed_file_name = f"{format_template}.mkv"
                    metadata_path = f"Metadata/{message.id}_{renamed_file_name}"
                except Exception as e:
                    await download_msg.edit(f"**MKV Conversion Error:** {e}")
                    return

            file_title = await n4bots.get_title(user_id)
            artist = await n4bots.get_artist(user_id)
            author = await n4bots.get_author(user_id)
            video_title = await n4bots.get_video(user_id)
            audio_title = await n4bots.get_audio(user_id)
            subtitle_title = await n4bots.get_subtitle(user_id)

            metadata_command = [
                'ffmpeg',
                '-i', path,
                '-metadata', f'title={file_title}',
                '-metadata', f'artist={artist}',
                '-metadata', f'author={author}',
                '-metadata:s:v', f'title={video_title}',
                '-metadata:s:a', f'title={audio_title}',
                '-metadata:s:s', f'title={subtitle_title}',
                '-map', '0',
                '-c', 'copy',
                '-loglevel', 'error',
                '-y',
                metadata_path
            ]

            process = await asyncio.create_subprocess_exec(
                *metadata_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode != 0:
                error_message = stderr.decode()
                await download_msg.edit(f"**Metadata Error:**\n{error_message}")
                return

            path = metadata_path

        upload_msg = await download_msg.edit("**__Uploading...__**")

        c_caption = await n4bots.get_caption(message.chat.id)
        c_thumb = None
        is_global_enabled = await n4bots.is_global_thumb_enabled(user_id)

        if is_global_enabled:
            c_thumb = await n4bots.get_global_thumb(user_id)
        else:
            if standard_quality:
                c_thumb = await n4bots.get_quality_thumbnail(user_id, standard_quality)
            
            if not c_thumb:
                c_thumb = await n4bots.get_thumbnail(user_id)

        if not c_thumb and media_type == "video" and message.video.thumbs:
            c_thumb = message.video.thumbs[0].file_id

        caption = (
            c_caption.format(
                filename=renamed_file_name,
                filesize=humanbytes(file_size),
                duration=convert(0),
            )
            if c_caption
            else f"**{renamed_file_name}**"
        )

        if c_thumb:
            ph_path = await client.download_media(c_thumb)
            if ph_path and os.path.exists(ph_path):
                try:
                    img = Image.open(ph_path).convert("RGB")
                    
                    if media_type == "document" or is_image:
                        width, height = img.size
                        min_dim = min(width, height)
                        left, top = (width - min_dim) // 2, (height - min_dim) // 2
                        right, bottom = (width + min_dim) // 2, (height + min_dim) // 2
                        img = img.crop((left, top, right, bottom)).resize((320, 320), Image.LANCZOS)
                    else:
                        img.thumbnail((320, 320), Image.LANCZOS)
                    
                    img.save(ph_path, "JPEG", quality=95)
                except Exception as e:
                    logger.error(f"Thumbnail processing error: {e}")
                    ph_path = None

        user_info = {
            'mention': message.from_user.mention, 
            'id': message.from_user.id, 
            'username': message.from_user.username or "No Username"
        }
        asyncio.create_task(forward_to_dump_channel(client, path, media_type, ph_path, file_name, renamed_file_name, user_info))

        try:
            if is_image:
                # Send images as documents with proper file names
                await client.send_document(
                    message.chat.id,
                    document=path,
                    file_name=renamed_file_name,
                    caption=caption,
                    thumb=ph_path,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started...", upload_msg, time.time()),
                )
            elif media_type == "document":
                await client.send_document(
                    message.chat.id,
                    document=path,
                    file_name=renamed_file_name,
                    thumb=ph_path,
                    caption=caption,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started...", upload_msg, time.time()),
                )
            elif media_type == "video":
                await client.send_video(
                    message.chat.id,
                    video=path,
                    file_name=renamed_file_name,
                    caption=caption,
                    thumb=ph_path,
                    duration=0,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started...", upload_msg, time.time()),
                )
            elif media_type == "audio":
                await client.send_audio(
                    message.chat.id,
                    audio=path,
                    file_name=renamed_file_name,
                    caption=caption,
                    thumb=ph_path,
                    duration=0,
                    progress=progress_for_pyrogram,
                    progress_args=("Upload Started...", upload_msg, time.time()),
                )
        except Exception as e:
            os.remove(path)
            if ph_path and os.path.exists(ph_path):
                os.remove(ph_path)
            return await upload_msg.edit(f"Error: {e}")

        await upload_msg.delete()

    except Exception as e:
        logger.error(f"Process Error: {e}")
        await download_msg.edit(f"Error: {e}")
    finally:
        for file_path in [download_path, metadata_path, path, ph_path]:
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    logger.warning(f"Error removing file {file_path}: {e}")
        
        temp_files = [f"{download_path}.temp.mkv"]
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except:
                    pass

# ===== IMPROVED MESSAGE HANDLER WITH DUPLICATE PREVENTION =====
async def auto_rename_files(client, message):
    user_id = message.from_user.id

    # ✅ Check if user is banned
    if await check_ban_status(user_id):
        return
    
    # ✅ Check if user is in info mode
    if user_id in info_mode_users:
        return
    
    # ✅ Check if user is in sequence mode
    from plugins.sequence import user_sequences
    if user_id in user_sequences:
        return
    
    # ✅ Check verification
    if not await is_user_verified(user_id):
        await send_verification(client, message)
        return
    
    # ✅ IMPORTANT: Check if message is already being processed
    # Track processed message IDs to prevent duplicates
    if not hasattr(auto_rename_files, "processed_messages"):
        auto_rename_files.processed_messages = set()
    
    message_id = f"{user_id}_{message.id}"
    if message_id in auto_rename_files.processed_messages:
        logger.info(f"Message {message.id} from user {user_id} already being processed, skipping")
        return
    
    # Mark message as being processed
    auto_rename_files.processed_messages.add(message_id)
    
    # ✅ Clean up old processed messages to prevent memory leak
    # Keep only last 1000 processed messages
    if len(auto_rename_files.processed_messages) > 1000:
        # Convert to list, remove oldest
        msg_list = list(auto_rename_files.processed_messages)
        auto_rename_files.processed_messages = set(msg_list[-500:])
    
    # ✅ Ensure queue manager has client
    queue_manager.set_client(client)
    
    # ✅ Add message to user's queue
    await queue_manager.add_to_queue(user_id, message)
    
    logger.info(f"File from user {user_id} added to queue. Active users: {queue_manager.get_active_users()}")
