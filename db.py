import pymongo
from pymongo import MongoClient
from env import MONGO_CONNECTION_URL


cluster = MongoClient(MONGO_CONNECTION_URL)
db = cluster["TipTimeTest"]
runtime_collection = db["RunTimes"]
user_collection = db["Users"]
rdw_game_collection = db["RDWGames"]


def save_new_user(user):
    user_query = {"_id": user.id}
    if user_collection.count_documents(user_query) == 0:
        post = {"_id": user.id, "name": "Jojo Bot"}
        user_collection.insert_one(post)
        return True
    return False


def add_new_rdw_game(game_name):
    game_query = {"lowerName": game_name.lower()}
    if rdw_game_collection.count_documents(game_query) == 0:
        post = {"name": game_name, "lowerName": game_name.lower()}
        rdw_game_collection.insert_one(post)
        return True
    return False


def destroy_rdw_game(game_name):
    game_query = {"lowerName": game_name.lower()}
    if rdw_game_collection.count_documents(game_query) > 0:
        rdw_game_collection.delete_one(game_query)
        return True
    return False


def fetch_rdw_games():
    results = [result["name"] for result in rdw_game_collection.find({}, ["name"])]
    return results
