import os
import logging
from datetime import datetime
from dotenv import load_dotenv

# Carrega variáveis do arquivo .env
load_dotenv()

LOG_DIR = os.getenv("LOG_DIR", "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Define nome do arquivo de log baseado na data do dia
log_filename = os.path.join(LOG_DIR, f"ingestion_{datetime.now().strftime('%Y-%m-%d')}.log")

def get_logger(run_id: str):
    """
    Retorna uma instância configurada do logger registrando mensagens
    no arquivo .log com o ID de execução (run_id).
    """
    logger = logging.getLogger(f"PipelineLogger_{run_id}")
    logger.setLevel(logging.INFO)

    # Evita duplicar handlers se a função for chamada mais de uma vez
    if not logger.handlers:
        file_handler = logging.FileHandler(log_filename, encoding="utf-8")
        formatter = logging.Formatter(
            fmt=f"%(asctime)s [%(levelname)s] [RUN_ID: {run_id}] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger