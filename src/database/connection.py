from pymongo import AsyncMongoClient
import logging
from src.app.config import MONGO_URI

logger = logging.getLogger('__name__')

async def connect_to_database():
    """
    Cria e retorna uma conexão com o banco de dados MongoDB usando o AsyncMongoClient
    """
    try:
        client = AsyncMongoClient(MONGO_URI)
        db = client.the_code_sage_db
        logger.info('Conexão com MongoDB estabelecida.')
        return db

    except Exception as e:
        logger.warning(f'Ocorreu um erro na conexão: {e}')
        raise
