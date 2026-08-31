import os
import sys
import uuid
import logging
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Permitir importação da pasta src.load
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.load.loader import carregar_dados_dw

# 1. AMBIENTE E LOG
load_dotenv()

USUARIO = os.getenv("DB_USER")
SENHA = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")
PORTA = os.getenv("DB_PORT", "5432")
BANCO = os.getenv("DB_NAME")

RUN_ID = str(uuid.uuid4())

logging.basicConfig(
    filename="meu_pipeline.log",
    level=logging.INFO,
    format=f"%(asctime)s - [TRANSFORM - RUN_ID: {RUN_ID}] - %(message)s"
)

print(f"🚀 Iniciando Leitura da Stage [RUN_ID: {RUN_ID}]...")
logging.info("Iniciando leitura dos dados brutos na stage.")

# 2. CONEXÃO E LEITURA (STAGE)
URL_CONEXAO = f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}"
engine = create_engine(URL_CONEXAO)

query = "SELECT * FROM stage.stg_cotacoes;"
df_bruto = pd.read_sql(query, con=engine)
print(f"Total de registros lidos da Stage: {len(df_bruto)}")

# 3. TRIAGEM E TRANSFORMAÇÃO
print("\n⚙️ Aplicando regras de transformação e validação...")

registros_validos = []
registros_rejeitados = []
TAXA_CAMBIO_BRL = 5.50

for idx, linha in df_bruto.iterrows():
    motivos_rejeicao = []

    # REGRA 1: Validar Moeda
    moeda_limpa = str(linha['moeda']).strip().lower() if pd.notnull(linha['moeda']) else ""
    if not moeda_limpa:
        motivos_rejeicao.append("Moeda vazia ou nula")

    # REGRA 2: Validar Moeda Fiat
    fiat_limpa = str(linha['moeda_fiat']).strip().lower() if pd.notnull(linha['moeda_fiat']) else ""
    if not fiat_limpa:
        motivos_rejeicao.append("Moeda fiat vazia ou nula")

    # REGRA 3: Validar Data
    data_convertida = None
    try:
        data_convertida = datetime.strptime(str(linha['data_referencia']), "%Y-%m-%d").date()
        if data_convertida > datetime.now().date():
            motivos_rejeicao.append("Data no futuro")
    except Exception:
        motivos_rejeicao.append("Formato de data inválido")

    # REGRA 4: Validar Preço
    preco_convertido = None
    try:
        preco_convertido = float(linha['preco'])
        if preco_convertido <= 0:
            motivos_rejeicao.append("Preço menor ou igual a zero")
    except Exception:
        motivos_rejeicao.append("Preço não numérico")

    # REGRA 5: Validar Market Cap e Volume
    market_cap_convertido = None
    if pd.notnull(linha['market_cap']) and str(linha['market_cap']).strip() != "None":
        try:
            market_cap_convertido = float(linha['market_cap'])
        except Exception:
            motivos_rejeicao.append("Market Cap inválido")

    volume_total_convertido = None
    if pd.notnull(linha['volume_total']) and str(linha['volume_total']).strip() != "None":
        try:
            volume_total_convertido = float(linha['volume_total'])
        except Exception:
            motivos_rejeicao.append("Volume total inválido")

    # SEPARAÇÃO
    if motivos_rejeicao:
        registros_rejeitados.append({
            "stage_id": idx,
            "_run_id": RUN_ID,
            "motivo_rejeicao": "; ".join(motivos_rejeicao),
            "moeda": str(linha['moeda']),
            "moeda_fiat": str(linha['moeda_fiat']),
            "timestamp_ms": str(linha['timestamp_ms']),
            "data_referencia": str(linha['data_referencia']),
            "preco": str(linha['preco']),
            "market_cap": str(linha['market_cap']),
            "volume_total": str(linha['volume_total'])
        })
    else:
        # USD
        registros_validos.append({
            "data_id": data_convertida,
            "moeda_id": moeda_limpa,
            "fiat_id": "usd",
            "preco": round(preco_convertido, 4),
            "market_cap": round(market_cap_convertido, 2) if market_cap_convertido else None,
            "volume_total": round(volume_total_convertido, 2) if volume_total_convertido else None
        })

        # BRL (Conversão)
        registros_validos.append({
            "data_id": data_convertida,
            "moeda_id": moeda_limpa,
            "fiat_id": "brl",
            "preco": round(preco_convertido * TAXA_CAMBIO_BRL, 4),
            "market_cap": round(market_cap_convertido * TAXA_CAMBIO_BRL, 2) if market_cap_convertido else None,
            "volume_total": round(volume_total_convertido * TAXA_CAMBIO_BRL, 2) if volume_total_convertido else None
        })

df_validos = pd.DataFrame(registros_validos)
df_rejeitados = pd.DataFrame(registros_rejeitados)

print(f"✅ Registros Aprovados: {len(df_validos)}")
print(f"❌ Registros Rejeitados: {len(df_rejeitados)}")

logging.info(f"Triagem concluída: {len(df_validos)} válidos, {len(df_rejeitados)} rejeitados.")

# 4. CHAMADA DO MÓDULO LOAD
carregar_dados_dw(df_validos, df_rejeitados)