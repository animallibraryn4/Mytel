import requests
from lxml import etree
from typing import Optional, Dict, List
from config import config
import logging

logger = logging.getLogger(__name__)

class WebScraper:
    def __init__(self):
        self.rss_url = config.RSS_URL
    
    def get_latest_anime(self, last_hash: Optional[str] = None, limit: int = 10) -> Optional[Dict]:
        """
        Get latest anime from RSS feed
        
        Args:
            last_hash: Last processed hash to start from
            limit: Maximum number of items to fetch
            
        Returns:
            Dictionary with anime array and latest hash
        """
        try:
            response = requests.get(self.rss_url, timeout=10)
            if response.status_code != 200:
                logger.error(f"Failed to fetch RSS: {response.status_code}")
                return None
            
            # Parse XML
            root = etree.fromstring(response.content)
            items = root.xpath('//item')
            
            if not items:
                logger.warning("No items found in RSS feed")
                return None
            
            # Process items
            anime_array = []
            latest_hash = None
            
            for i, item in enumerate(items[:limit]):
                item_hash = item.findtext('guid')
                
                # Stop if we reached the last processed hash
                if last_hash and item_hash == last_hash:
                    break
                
                # Extract anime information
                category = item.findtext('category', '').split("-")
                if len(category) < 2:
                    continue
                
                anime_name = category[0].strip()
                quality = category[-1].strip() if len(category) > 1 else "Unknown"
                
                # Group by anime name
                if anime_array and anime_array[-1]['name'] == anime_name:
                    # Add to existing anime entry
                    anime_array[-1]['magnet'].append(item.findtext('link'))
                    anime_array[-1]['hash'].append(item_hash)
                    anime_array[-1]['quality'].append(quality)
                    anime_array[-1]['title'].append(item.findtext('title'))
                else:
                    # Create new anime entry
                    anime_array.append({
                        'name': anime_name,
                        'magnet': [item.findtext('link')],
                        'hash': [item_hash],
                        'quality': [quality],
                        'title': [item.findtext('title')]
                    })
                
                # Update latest hash
                if i == 0:
                    latest_hash = item_hash
            
            if not anime_array:
                return None
            
            return {
                'array': anime_array,
                'hash': latest_hash
            }
            
        except Exception as e:
            logger.error(f"Error fetching anime: {e}")
            return None
    
    def test_connection(self) -> bool:
        """Test RSS feed connection"""
        try:
            response = requests.get(self.rss_url, timeout=5)
            return response.status_code == 200
        except:
            return False
