import pymongo
from pymongo import MongoClient
from env import MONGO_CONNECTION_URL
from formatting import format_time_delta, calculate_in_game_time
from enum import Enum


cluster = MongoClient(MONGO_CONNECTION_URL)
db = cluster["TipTimeTest"]
runtime_collection = db["RunTimes"]
user_collection = db["Users"]
rdw_game_collection = db["RDWGames"]


class GameStatus(Enum):
    PENDING = 1
    IN_PROGRESS = 2
    COMPLETE = 3
    CANCELED = 4
    FAILED = 5


def fetch_all_users():
    all_user_ids = [result for result in user_collection.find({})]
    return all_user_ids


def save_new_user(user):
    user_query = {"_id": user.id}
    if user_collection.count_documents(user_query) == 0:
        post = {"_id": user.id, "name": user.name, "strikes": 0}
        response = user_collection.insert_one(post)
        return response.inserted_id
    return False


def fetch_user(user_id):
    user_query = {"_id": user_id}
    return user_collection.find_one(user_query)


def find_or_create_user(user):
    user_id = user.id
    user_query = {"_id": user_id}
    if user_collection.count_documents(user_query) == 0:
        user_id = save_new_user(user)
    user = fetch_user(user_id)
    return user


def update_user_strikes(user, plus_minus, quantity):
    user_id, current_strikes = user["_id"], user["strikes"]
    new_value = current_strikes + quantity if plus_minus == "plus" else max(current_strikes - quantity, 0)
    user_query = {"_id": user_id}
    response = user_collection.update_one(user_query, {'$set': {'strikes': new_value}})
    return response.acknowledged, new_value


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


def start_rdw_run(users, start_time):
    rdw_games = fetch_rdw_games()
    new_rdw_run = {
        "users": users,
        "status": "IN-PROGRESS",
        "start": start_time,
        "end": None,
        "total_time": None,
        "game_data": [{"name": game, "start": None, "end": None, "status": "PENDING"} for game in rdw_games]
    }
    response = runtime_collection.insert_one(new_rdw_run)
    new_rdw_run["_id"] = response.inserted_id
    return new_rdw_run


def fetch_rdw_run(run_id):
    run_query = {"_id": run_id}
    return runtime_collection.find_one(run_query)


def fetch_fastest_rdw_runs(amount=10):
    return runtime_collection.find({"status": "COMPLETE"}).sort("total_time", pymongo.ASCENDING).limit(amount)


def fetch_rdw_run_or_create(run_id, users, start_time):
    rdw_run = fetch_rdw_run(run_id)
    if not rdw_run:
        rdw_run = start_rdw_run(users, start_time)
    return rdw_run


def update_rdw_run(run_id, status, time, total_time):
    run_query = {"_id": run_id}
    if status == "COMPLETE":
        runtime_collection.update_one(run_query, {'$set': {"end": time, "status": status, "total_time": total_time[0], "in_game_time": total_time[1]}})
    elif status == "CANCELED":
        # do something else, maybe reset to pending?
        runtime_collection.update_one(run_query, {'$set': {"start": None, "status": status}})


def update_rdw_game(run_id, game_name, status, time):
    run_query = {"_id": run_id, "game_data.name": game_name}
    current_game = next(game for game in fetch_rdw_run(run_id)["game_data"] if game["name"] == game_name)
    updated = False  # variable returned to view, verifies if update condition went through

    if status == "IN-PROGRESS":
        if current_game["status"] in ["PENDING"]:
            runtime_collection.update_one(run_query, {'$set': {"game_data.$.start": time, "game_data.$.status": status}})
            updated = True
    elif status == "COMPLETE":
        if current_game["status"] in ["IN-PROGRESS"]:
            runtime_collection.update_one(run_query, {'$set': {"game_data.$.end": time, "game_data.$.status": status}})
            updated = True
    elif status == "CANCELED":
        # do something else, maybe reset to pending?
        if current_game["status"] in ["IN-PROGRESS"]:
            runtime_collection.update_one(run_query, {'$set': {"game_data.$.start": None, "game_data.$.status": "PENDING"}})
            updated = True
    return updated, current_game["status"]


def check_if_run_complete(run_id, time):
    run_attributes = fetch_rdw_run(run_id)
    is_complete = all([game["status"] == "COMPLETE" for game in run_attributes["game_data"]])
    already_complete = run_attributes["status"] == "COMPLETE"
    total_time_for_run = "IN-PROGRESS"
    if already_complete:
        return already_complete, run_attributes["end"]
    if is_complete:
        total_time_for_run = time - run_attributes["start"]
        total_in_game_time = calculate_in_game_time(run_attributes["game_data"])
        update_rdw_run(run_id, "COMPLETE", time, (format_time_delta(total_time_for_run), format_time_delta(total_in_game_time)))
    return is_complete, total_time_for_run
