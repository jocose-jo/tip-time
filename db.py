import pymongo
from pymongo import MongoClient
from env import MONGO_CONNECTION_URL


cluster = MongoClient(MONGO_CONNECTION_URL)
db = cluster["TipTimeTest"]
runtime_collection = db["RunTimes"]
user_collection = db["Users"]


def save_new_user(user):
    post = {"_id": user.id, "name": "Jojo Bot"}
    user_collection.insert_one(post)
