from pymongo import AsyncMongoClient
import logging
from src.app.config import MONGO_URI, DATABASE_NAME

logger = logging.getLogger('__name__')

async def connect_to_database():
    """
    Cria e retorna uma conexão com o banco de dados MongoDB usando o AsyncMongoClient
    """
    try:
        client = AsyncMongoClient(MONGO_URI)
        await client.admin.command('ping')
        logger.info('Cliente criado!')

        # Seleciona e e retorna o abnco de dados diretamente
        db = client.get_database(DATABASE_NAME)
        return db

    except Exception as e:
        logger.warning(f'Ocorreu um erro na criação do cleinet: {e}')
        raise
