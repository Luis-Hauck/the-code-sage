from pymongo import AsyncMongoClient
import logging
from src.app.config import DATABASE_NAME,get_mongo_uri

logger = logging.getLogger('__name__')

async def connect_to_database():
    """
    Cria e retorna uma conexão com o banco de dados MongoDB usando o AsyncMongoClient
    """
    try:
        mongo_uri = get_mongo_uri()

        if mongo_uri:

            client = AsyncMongoClient(mongo_uri)

            await client.admin.command('ping')
            logger.info(f'Conectado com sucesso em: {mongo_uri}')

            db = client.get_database(DATABASE_NAME)
            return db
        else:
            logger.warning(f'Falha ao conectar a uri: {mongo_uri}')
            return None
    except Exception as e:
        logger.error(f'Ocorreu um erro na criação do cleinet: {e}')
        raise
