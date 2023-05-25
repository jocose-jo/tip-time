from dotenv import load_dotenv
import os

# load all environment variables here
load_dotenv()

MODE = os.environ["MODE"]
DISCORD_TOKEN = os.environ["DISCORD_TOKEN"]
MONGO_CONNECTION_URL = os.environ["MONGO_CONNECTION_URL"]
