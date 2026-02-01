import logging
import os
from pathlib import Path
import logging.handlers


def setup_logging():
    """Configura o sistema de logging"""

    # Garante a existência da pasta logs
    root_dir = Path(__file__).resolve().parent.parent.parent

    # Define a pasta de logs na RAIZ (ou onde você preferir)
    log_dir = root_dir / 'logs'

    # Cria a pasta se não existir (na raiz correta)
    if not log_dir.exists():
        log_dir.mkdir(parents=True, exist_ok=True)

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
        filename=f'{log_dir}/app.log',
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
