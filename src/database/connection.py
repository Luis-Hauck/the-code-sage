from pymongo import AsyncMongoClient
import logging
import urllib.parse
from src.app.config import MONGO_USER, MONGO_HOST, MONGO_PASSWORD, DATABASE_NAME

logger = logging.getLogger('__name__')

async def connect_to_database():
    """
    Cria e retorna uma conexão com o banco de dados MongoDB usando o AsyncMongoClient
    """
    try:
        # Verificação de Segurança
        if not MONGO_PASSWORD or not MONGO_HOST:
            raise ValueError("As variáveis MONGO_PASSWORD ou MONGO_HOST estão vazias!")

        # Tratamento de Caracteres Especiais (A Correção do ==)
        # O quote_plus transforma "==" em "%3D%3D" e arruma o "@"
        user_safe = urllib.parse.quote_plus(MONGO_USER)
        pass_safe = urllib.parse.quote_plus(MONGO_PASSWORD)

        # 3. Montagem da URL (Padrão Cosmos DB com porta 10255)
        mongo_uri = (
            f"mongodb://{user_safe}:{pass_safe}@{MONGO_HOST}:10255/?"
            "ssl=true&replicaSet=globaldb&retrywrites=false&maxIdleTimeMS=120000"
            f"&appName=@{MONGO_USER}@"
        )


        client = AsyncMongoClient(mongo_uri)

        await client.admin.command('ping')
        logger.info(f'Conectado com sucesso ao Host: {MONGO_HOST}')

        db = client.get_database(DATABASE_NAME)
        return db
    except Exception as e:
        logger.warning(f'Ocorreu um erro na criação do cleinet: {e}')
        raise
