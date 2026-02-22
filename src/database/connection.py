from pymongo import AsyncMongoClient
import logging
from src.utils.helpers import download_direct_cert
from src.app.config import DATABASE_NAME, MONGO_URI, CLIENT_PEM_URL

logger = logging.getLogger(__name__)

async def connect_to_database():
    """
    Cria e retorna uma conexão com o banco de dados MongoDB usando o AsyncMongoClient
    """
    try:
        logger.info("Autenticando com credenciais e certificados seguros (mTLS)...")

        #  Cria o arquivo temporário para o certifacado
        pem_path = await download_direct_cert(CLIENT_PEM_URL, ".pem")

        if not pem_path:
            logger.warning("Links dos certificados não configurados nas variáveis de ambiente!")

        mongo_uri = MONGO_URI
        host = mongo_uri.split("@")[-1].split("/")[0]
        if mongo_uri:

            # Configura a conexão base
            connection_kwargs = {
                "host": MONGO_URI,
                "serverSelectionTimeoutMS": 5000
            }

            # diciona a segurança apenas se encontrou as variáveis
            if pem_path:
                logger.info("Certificados gerados na memória. Aplicando segurança.")
                connection_kwargs.update({
                    "tls": True,
                    "tlsCAFile": pem_path,
                    "tlsCertificateKeyFile": pem_path,
                    "tlsAllowInvalidCertificates": True,
                    "tlsAllowInvalidHostnames": True
                })
            else:
                logger.warning("Variáveis de certificado não encontradas. Tentando sem mTLS...")

            client = AsyncMongoClient(**connection_kwargs)

            await client.admin.command('ping')
            logger.info(f'Conectado com sucesso ao host {host}!')

            db = client.get_database(DATABASE_NAME)
            return db
        else:
            logger.warning(f'Falha ao conectar ao host: {host}')
            return None
    except Exception as e:
        logger.error(f'Ocorreu um erro na criação do cleinet: {e}')
        raise
