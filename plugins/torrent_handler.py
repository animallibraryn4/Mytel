import libtorrent as lt
import time
import logging
from typing import Optional, Dict
from pyrogram.types import Message

logger = logging.getLogger(__name__)

class TorrentHandler:
    def __init__(self):
        self.session = lt.session()
        self.session.listen_on(6881, 6891)
        self.session.start_dht()
    
    def download(self, magnet_link: str, status_message: Message = None) -> Optional[Dict]:
        """
        Download a torrent from magnet link
        
        Args:
            magnet_link: Magnet URI
            status_message: Pyrogram message to update with progress
            
        Returns:
            Dict containing file path and name, or None if failed
        """
        try:
            logger.info(f"Starting download: {magnet_link[:50]}...")
            
            # Add torrent to session
            params = {'save_path': './downloads'}
            handle = lt.add_magnet_uri(self.session, magnet_link, params)
            
            # Wait for metadata
            start_time = time.time()
            while not handle.has_metadata():
                time.sleep(1)
                if time.time() - start_time > 60:  # Timeout after 60 seconds
                    logger.error("Timeout waiting for metadata")
                    return None
            
            logger.info(f"Downloading: {handle.name()}")
            
            # Download loop
            while handle.status().state != lt.torrent_status.seeding:
                status = handle.status()
                state_str = [
                    'queued', 'checking', 'downloading metadata',
                    'downloading', 'finished', 'seeding', 'allocating'
                ]
                
                progress_text = (
                    f"{status.progress * 100:.1f}% complete | "
                    f"↓ {status.download_rate / 1000:.1f} kB/s | "
                    f"↑ {status.upload_rate / 1000:.1f} kB/s | "
                    f"Peers: {status.num_peers} | "
                    f"{state_str[status.state]}"
                )
                
                logger.info(progress_text)
                
                # Update status message if provided
                if status_message:
                    try:
                        status_message.edit_text(progress_text)
                    except:
                        pass
                
                time.sleep(5)
            
            # Download completed
            end_time = time.time()
            elapsed = end_time - start_time
            logger.info(
                f"Download completed: {handle.name()} | "
                f"Time: {int(elapsed // 60)}m {int(elapsed % 60)}s"
            )
            
            if status_message:
                status_message.edit_text("✅ Download completed, now uploading...")
            
            return {
                "file": f"./downloads/{handle.name()}",
                "name": handle.name()
            }
            
        except Exception as e:
            logger.error(f"Torrent download error: {e}")
            if status_message:
                status_message.edit_text(f"❌ Download failed: {e}")
            return None
    
    def cleanup(self):
        """Clean up torrent session"""
        try:
            self.session.pause()
            logger.info("Torrent session cleaned up")
        except Exception as e:
            logger.error(f"Error cleaning up torrent session: {e}")
