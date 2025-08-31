import logging
import os
import logging.handlers


def setup_logging():
    """Configura o sistema de logging"""

    # Garante a existência da pasta logs
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Define os formatos padrões dos logs
    log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
    date_format = '%d-%m-%Y %H:%M:%S'
    formatter = logging.Formatter(log_format,date_format)

    # Obtem o logger raiz
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Handler para o arquivo
    # Com RotatingFileHandler é criado um novo arquivo com base no máximo de bytes dele
    file_handler = logging.handlers.RotatingFileHandler(
        filename='logs/app.log',
        maxBytes=5*1024*1024,
        backupCount=2,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # Cria o Handler para o console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
