import os
from dotenv import load_dotenv
import urllib.parse
import logging

load_dotenv()

logger = logging.getLogger('__name__')

def get_mongo_uri():
    """
    Função que decide como montar a URI.
    Prioridade 1: URI completa já definida (ex: Local ou Atlas).
    Prioridade 2: Montagem manual para Cosmos DB (tratando a senha).
    """
    # 1. Tenta pegar a URI pronta
    uri_env = os.getenv("MONGO_URI")
    if uri_env:
        return uri_env

    # Se não tem URI, montamos
    user = os.getenv("MONGO_USER")
    password = os.getenv("MONGO_PASSWORD")
    host = os.getenv("MONGO_HOST")

    if user and password and host:

        user_safe = urllib.parse.quote_plus(user)
        pass_safe = urllib.parse.quote_plus(password)

        # Monta a string específica do Cosmos DB
        return (
            f"mongodb://{user_safe}:{pass_safe}@{host}:10255/?"
            "ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000"
            f"&appName=@{user_safe}@"
        )


    return None

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
DATABASE_NAME = os.getenv('DATABASE_NAME')
MONGO_URI = get_mongo_uri()
MISSION_CHANNEL_ID = int(os.getenv('MISSION_CHANNEL_ID'))
MOD_LOG_CHANNEL_ID = int(os.getenv('MOD_LOG_CHANNEL_ID'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')