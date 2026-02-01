import os
from dotenv import load_dotenv


load_dotenv()

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
MONGO_HOST = os.getenv('MONGO_HOST')
MONGO_PASSWORD= os.getenv('MONGO_PASSWORD')
MONGO_USER= os.getenv('MONGO_USER')
DATABASE_NAME = os.getenv('DATABASE_NAME')
MISSION_CHANNEL_ID = int(os.getenv('MISSION_CHANNEL_ID'))
MOD_LOG_CHANNEL_ID = int(os.getenv('MOD_LOG_CHANNEL_ID'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')