from pymongo import MongoClient, server_api
from typing import Optional, List, Dict, Any
from config import config
import logging

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.client = MongoClient(
            config.DATABASE_URL,
            server_api=server_api.ServerApi('1') # Update this line
        )
        self.db = self.client[config.DATABASE_NAME]
        
        # Collections
        self.last_added = self.db['last_added']
        self.new_db = self.db['new_db']
        self.remain = self.db['remain']
        self.worker = self.db['worker']
        self.files = self.db['files']
        
        self._initialize_collections()
    
    def _initialize_collections(self):
        """Initialize collections with default documents if needed"""
        # Ensure worker collection has a document
        if not self.worker.find_one({"_id": 1}):
            self.worker.insert_one({"_id": 1, "working": False})
        
        # Ensure last_added collection has a document
        if not self.last_added.find_one({"_id": 1}):
            self.last_added.insert_one({"_id": 1, "hash": None})
    
    def get_last_hash(self) -> Optional[str]:
        """Get the last processed hash from RSS feed"""
        data = self.last_added.find_one({"_id": 1})
        return data.get("hash") if data else None
    
    def update_last_hash(self, hash_value: str) -> None:
        """Update the last processed hash"""
        self.last_added.update_one(
            {"_id": 1},
            {"$set": {"hash": hash_value}},
            upsert=True
        )
    
    def is_new_database(self) -> bool:
        """Check if this is a fresh database"""
        return self.new_db.find_one({"_id": 1}) is None
    
    def mark_database_initialized(self) -> None:
        """Mark database as initialized"""
        self.new_db.insert_one({"_id": 1})
    
    def add_remaining_anime(self, anime_list: List[Dict]) -> None:
        """Add anime to remaining queue"""
        current_data = self.remain.find_one({"_id": 1})
        
        if not current_data:
            self.remain.insert_one({"_id": 1, "list": anime_list})
        else:
            current_list = current_data["list"]
            current_list.extend(anime_list)
            self.remain.update_one(
                {"_id": 1},
                {"$set": {"list": current_list}},
                upsert=True
            )
    
    def get_remaining_anime(self) -> List[Dict]:
        """Get list of remaining anime to process"""
        data = self.remain.find_one({"_id": 1})
        return data.get("list", []) if data else []
    
    def update_remaining_anime(self, anime_list: List[Dict]) -> None:
        """Update the remaining anime list"""
        self.remain.update_one(
            {"_id": 1},
            {"$set": {"list": anime_list}},
            upsert=True
        )
    
    def is_worker_busy(self) -> bool:
        """Check if worker is currently processing"""
        data = self.worker.find_one({"_id": 1})
        return data.get("working", False) if data else False
    
    def set_worker_status(self, busy: bool) -> None:
        """Set worker status"""
        self.worker.update_one(
            {"_id": 1},
            {"$set": {"working": busy}},
            upsert=True
        )
    
    def add_file_record(self, name: str, file_hash: str, message_id: int) -> None:
        """Add file record to database"""
        self.files.insert_one({
            "name": name,
            "hash": file_hash,
            "message_id": message_id
        })
    
    def get_file_by_hash(self, file_hash: str) -> Optional[Dict]:
        """Get file record by hash"""
        return self.files.find_one({"hash": file_hash})
    
    def remove_first_anime_item(self, anime_list: List[Dict]) -> List[Dict]:
        """Remove the first item from anime list"""
        if not anime_list:
            return []
        
        first_item = anime_list[0]
        
        # If there are multiple qualities in the first item, remove the first quality
        if len(first_item.get("quality", [])) > 1:
            first_item["magnet"].pop(0)
            first_item["hash"].pop(0)
            first_item["quality"].pop(0)
            first_item["title"].pop(0)
            return anime_list
        else:
            # Remove the entire anime entry
            return anime_list[1:] if len(anime_list) > 1 else []
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            self.client.admin.command('ping')
            logger.info("Database connection successful")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

# Global database instance
db = Database()
