import logging

# Configuração básica
logging.basicConfig(
    filename=r'D:\Projects\the-code-sage\logs\app.log',
    filemode='a',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',  # Formato da mensagem de log
    datefmt='%Y-%m-%d %H:%M:%S'  # Formato da data e hora

)

logger = logging.getLogger(__name__)
