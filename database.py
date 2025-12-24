from pymongo import MongoClient
from config import MONGO_URI

mongo_client = MongoClient(MONGO_URI)
db = mongo_client["sequence_bot"]
users_collection = db["users_sequence"]
broadcast_stats_collection = db["broadcast_stats"]

class Database:
    @staticmethod
    def update_user_stats(user_id, files_count, username):
        users_collection.update_one(
            {"user_id": user_id}, 
            {"$inc": {"files_sequenced": files_count}, "$set": {"username": username}}, 
            upsert=True
        )
    
    @staticmethod
    def get_top_users(limit=5):
        return users_collection.find().sort("files_sequenced", -1).limit(limit)
    
    @staticmethod
    def get_total_users():
        return users_collection.count_documents({})
    
    @staticmethod
    def get_all_users():
        return list(users_collection.find({}))
    
    @staticmethod
    def save_broadcast_stats(stats):
        broadcast_stats_collection.update_one(
            {"_id": "latest"},
            {"$set": stats},
            upsert=True
        )
