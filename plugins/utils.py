"""
Utility functions for AutoAnimeBot
Licensed under GNU General Public License v3.0
"""

import re
import random
import string
import requests
import subprocess
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# AniList GraphQL query
ANIME_QUERY = '''
query ($search: String) { 
    Media (type: ANIME, search: $search) { 
        title {
            english
            romaji
        }
        status
        coverImage {
            extraLarge
        }
    }
}
'''

def extract_anime_info(title: str) -> Optional[Dict]:
    """
    Extract information from anime title
    
    Args:
        title: Anime title string
        
    Returns:
        Dictionary with extracted info or None
    """
    # Pattern for [SubsPlease] Anime Name - Episode (Quality) [Release Info]
    pattern = r"\[SubsPlease\] (.+?)(?: S(\d+))? - (\d+)(?: \((\d+p)\) \[.+?\])?"
    
    match = re.match(pattern, title)
    if not match:
        logger.warning(f"Could not parse title: {title}")
        return None
    
    # Extract groups
    anime_name = match.group(1)
    season = match.group(2)
    episode = match.group(3)
    quality = match.group(4)
    
    # Build display name
    if season:
        display_name = f"{anime_name} Season {season}"
        search_query = f"{anime_name} Season {season}"
    else:
        display_name = anime_name
        search_query = anime_name
    
    return {
        "display_name": display_name,
        "search_query": search_query,
        "episode": episode,
        "season": season,
        "quality": quality,
        "original_title": title
    }

def get_anime_details(anime_name: str) -> Dict:
    """
    Get anime details from AniList API
    
    Args:
        anime_name: Name of anime to search
        
    Returns:
        Dictionary with anime details
    """
    try:
        variables = {'search': anime_name}
        response = requests.post(
            'https://graphql.anilist.co',
            json={'query': ANIME_QUERY, 'variables': variables}
        )
        
        if response.status_code == 200:
            data = response.json()
            media = data.get('data', {}).get('Media', {})
            
            return {
                "name": media.get('title', {}).get('english') or 
                       media.get('title', {}).get('romaji') or anime_name,
                "status": media.get('status', 'Unknown'),
                "image": media.get('coverImage', {}).get('extraLarge')
            }
        else:
            logger.error(f"AniList API error: {response.status_code}")
    
    except Exception as e:
        logger.error(f"Error fetching anime details: {e}")
    
    # Return default values on error
    return {
        "name": anime_name,
        "status": "Unknown",
        "image": None
    }

def generate_random_hash(length: int = 20) -> str:
    """
    Generate a random hash string
    
    Args:
        length: Length of hash
        
    Returns:
        Random hash string
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def encode_video_file(input_path: str) -> Optional[str]:
    """
    Encode video file to compressed format
    
    Args:
        input_path: Path to input video file
        
    Returns:
        Path to encoded file or None if failed
    """
    try:
        # Extract filename without extension
        base_name = os.path.splitext(os.path.basename(input_path))[0]
        output_path = f"./downloads/{base_name}_encoded.mp4"
        
        # Extract subtitles
        subprocess.run([
            "ffmpeg", "-i", input_path,
            "-c:s", "srt", "subtitles.srt"
        ], capture_output=True)
        
        # Encode video
        command = [
            "ffmpeg", "-i", input_path,
            "-i", "subtitles.srt" if os.path.exists("subtitles.srt") else None,
            "-c:v", "libx264",
            "-b:v", "700k",
            "-c:a", "aac",
            "-c:s", "mov_text",
            output_path
        ]
        
        # Remove None values
        command = [c for c in command if c is not None]
        
        result = subprocess.run(command, capture_output=True)
        
        # Clean up subtitle file
        if os.path.exists("subtitles.srt"):
            os.remove("subtitles.srt")
        
        if result.returncode == 0:
            logger.info(f"Video encoded successfully: {output_path}")
            return output_path
        else:
            logger.error(f"Encoding failed: {result.stderr}")
            return None
    
    except Exception as e:
        logger.error(f"Error encoding video: {e}")
        return None

def progress_callback(current: int, total: int):
    """
    Progress callback for uploads/downloads
    
    Args:
        current: Current bytes transferred
        total: Total bytes to transfer
    """
    percentage = (current / total) * 100
    logger.debug(f"Progress: {percentage:.1f}%")
