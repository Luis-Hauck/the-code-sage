import os
from dotenv import load_dotenv


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
MONGO_URI = os.getenv('MONGO_URI')
DATABASE_NAME = os.getenv('DATABASE_NAME')
MISSION_CHANNEL_ID = int(os.getenv('MISSION_CHANNEL_ID'))