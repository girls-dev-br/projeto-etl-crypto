import os
import glob
import re
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine

# 1. Conexão com o DW Neon
load_dotenv()

USUARIO = os.getenv("DB_USER")
SENHA = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")
PORTA = os.getenv("DB_PORT", "5432")
BANCO = os.getenv("DB_NAME")

URL_CONEXAO = f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}"
engine = create_engine(URL_CONEXAO)

DIR_LOGS = os.getenv("LOG_DIR", "logs")

def enviar_logs_para_nuvem():
    # Pega todos os arquivos .log gerados pelo logger.py dentro da pasta logs/
    arquivos_log = glob.glob(os.path.join(DIR_LOGS, "*.log"))
    
    # Se existir o meu_pipeline.log antigo na raiz, inclui também
    if os.path.exists("meu_pipeline.log"):
        arquivos_log.append("meu_pipeline.log")

    if not arquivos_log:
        print("⚠️ Nenhum arquivo de log encontrado para envio.")
        return

    print(f"📤 Lendo {len(arquivos_log)} arquivo(s) de log...")

    # Padrão gerado pelo seu logger.py:
    # 2026-08-30 19:15:00 [INFO] [RUN_ID: uuid] - Mensagem
    padrao = r"^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+\[(\w+)\]\s+\[RUN_ID:\s*([^\]]+)\]\s+-\s+(.*)$"

    linhas_processadas = []

    for arq in arquivos_log:
        with open(arq, "r", encoding="utf-8") as f:
            for linha in f:
                linha_limpa = linha.strip()
                if not linha_limpa:
                    continue

                match = re.match(padrao, linha_limpa)
                if match:
                    data_str, nivel, run_id, msg = match.groups()
                    linhas_processadas.append({
                        "timestamp_log": pd.to_datetime(data_str),
                        "modulo": "PIPELINE",
                        "run_id": run_id,
                        "nivel_log": nivel,
                        "mensagem": msg
                    })
                else:
                    # Captura linhas gerais ou traces
                    linhas_processadas.append({
                        "timestamp_log": pd.Timestamp.now(),
                        "modulo": "GERAL",
                        "run_id": "SEM_ID",
                        "nivel_log": "INFO",
                        "mensagem": linha_limpa
                    })

    if linhas_processadas:
        df_logs = pd.DataFrame(linhas_processadas)
        df_logs.to_sql("pipeline_logs_detalhado", con=engine, if_exists="append", index=False)
        print(f"✨ {len(df_logs)} registros de log enviados para o Neon PostgreSQL com sucesso!")
    else:
        print("Nenhum registro formatado para upload.")

if __name__ == "__main__":
    enviar_logs_para_nuvem()