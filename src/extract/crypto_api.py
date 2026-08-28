#EXTRAÇÃO BRUTA DOS DADOS NO STAGE

import os
import uuid
import time
import logging
import requests
import pandas as pd
import urllib.parse
from datetime import datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# ==========================================
# 1. CARREGA AS VARIÁVEIS DE AMBIENTE (.env)
# ==========================================
load_dotenv()

USUARIO_BANCO = os.getenv("DB_USER")
SENHA_BANCO = os.getenv("DB_PASSWORD")
HOST_BANCO = os.getenv("DB_HOST", "localhost")
PORTA_BANCO = os.getenv("DB_PORT", "5432")
NOME_BANCO = os.getenv("DB_NAME")

# ==========================================
# 2. LOGS SIMPLES
# ==========================================
RUN_ID = str(uuid.uuid4())

logging.basicConfig(
    filename="meu_pipeline.log",
    level=logging.INFO,
    format=f"%(asctime)s - [RUN_ID: {RUN_ID}] - %(message)s"
)

logging.info("Iniciando verificação de carga incremental...")
print("🚀 Iniciando verificação de carga incremental...")

# ==========================================
# 3. CONEXÃO COM O POSTGRESQL
# ==========================================
SENHA_ENCODED = urllib.parse.quote_plus(SENHA_BANCO) if SENHA_BANCO else ""
USUARIO_ENCODED = urllib.parse.quote_plus(USUARIO_BANCO) if USUARIO_BANCO else ""

URL_CONEXAO = f"postgresql://{USUARIO_ENCODED}:{SENHA_ENCODED}@{HOST_BANCO}:{PORTA_BANCO}/{NOME_BANCO}?client_encoding=utf8"

engine = create_engine(
    URL_CONEXAO,
    connect_args={"client_encoding": "utf8"}
)

# ==========================================
# 4. BUSCA ÚLTIMA DATA GRAVADA NO BANCO
# ==========================================
ultima_data_str = None

try:
    with engine.connect() as conexao:
        conexao.execute(text("CREATE SCHEMA IF NOT EXISTS stage;"))
        conexao.commit()
        
        # Tenta buscar a data máxima gravada na stage
        query = text("SELECT MAX(data_referencia) FROM stage.stg_cotacoes;")
        resultado = conexao.execute(query).scalar()
        if resultado:
            ultima_data_str = str(resultado).split()[0]  # Mantém formato YYYY-MM-DD
except Exception as e:
    logging.warning(f"Não foi possível consultar a última data na stage: {e}")

if ultima_data_str:
    print(f"📅 ÚLTIMA DATA ENCONTRADA NO BANCO: {ultima_data_str}")
    logging.info(f"Última data encontrada na stage: {ultima_data_str}")
    
    # Define os dias a buscar com base na diferença até hoje
    data_max = datetime.strptime(ultima_data_str, "%Y-%m-%d")
    dias_diferenca = (datetime.now() - data_max).days
    
    # Se a base já está atualizada para o dia de hoje, busca apenas o último dia por segurança
    dias_busca = str(max(dias_diferenca + 1, 2))
else:
    print("⚠️ NENHUM DADO ANTERIOR ENCONTRADO. REALIZANDO CARGA COMPLETA (365 DIAS).")
    logging.info("Carga inicial de 365 dias acionada.")
    dias_busca = "365"

# ==========================================
# 5. EXTRAÇÃO INCREMENTAL DA API
# ==========================================
MOEDAS = ["bitcoin", "ethereum"]
TODOS_OS_DADOS = []

for moeda in MOEDAS:
    print(f"Buscando cotações recentes da moeda: {moeda} (janela: {dias_busca} dias)...")
    logging.info(f"Buscando cotações para {moeda} (janela: {dias_busca} dias)")
    
    url = f"https://api.coingecko.com/api/v3/coins/{moeda}/market_chart"
    parametros = {
        "vs_currency": "usd",
        "days": dias_busca,
        "interval": "daily"
    }
    
    try:
        resposta = requests.get(url, params=parametros, timeout=15)
        resposta.raise_for_status()
        dados_json = resposta.json()
        
        precos = dados_json.get("prices", [])
        mcaps = dados_json.get("market_caps", [])
        volumes = dados_json.get("total_volumes", [])
        
        for i in range(len(precos)):
            timestamp_ms = precos[i][0]
            preco_valor = precos[i][1]
            mcap_valor = mcaps[i][1] if i < len(mcaps) else None
            vol_valor = volumes[i][1] if i < len(volumes) else None
            
            data_texto = datetime.fromtimestamp(timestamp_ms / 1000.0).strftime('%Y-%m-%d')
            
            # FILTRO INCREMENTAL: Descarta datas que já existem no banco
            if ultima_data_str and data_texto <= ultima_data_str:
                continue

            TODOS_OS_DADOS.append({
                "moeda": moeda,
                "moeda_fiat": "usd",
                "timestamp_ms": str(timestamp_ms),
                "data_referencia": str(data_texto),
                "preco": str(preco_valor),
                "market_cap": str(mcap_valor),
                "volume_total": str(vol_valor)
            })
            
    except Exception as erro:
        logging.error(f"Erro ao buscar dados de {moeda}: {erro}")
        print(f"❌ Erro na moeda {moeda}: {erro}")
    
    time.sleep(2)

# ==========================================
# 6. CARGA DOS NOVOS REGISTROS NA STAGE
# ==========================================
if TODOS_OS_DADOS:
    df = pd.DataFrame(TODOS_OS_DADOS)

    df['_ingestion_at'] = datetime.now()
    df['_run_id'] = RUN_ID
    df['_source_endpoint'] = "https://api.coingecko.com/api/v3/coins"

    try:
        df.to_sql(
            name='stg_cotacoes',
            schema='stage',
            con=engine,
            if_exists='append',
            index=False
        )
        
        mensagem_sucesso = f"✅ SUCESSO! {len(df)} novos registros inseridos na stage.stg_cotacoes!"
        print(mensagem_sucesso)
        logging.info(mensagem_sucesso)

    except Exception as erro:
        mensagem_erro = f"❌ ERRO ao salvar no banco: {erro}"
        print(mensagem_erro)
        logging.error(mensagem_erro)
else:
    mensagem_sem_dados = "ℹ️ Nenhum dado novo para inserir. A base já está atualizada com as datas mais recentes!"
    print(mensagem_sem_dados)
    logging.info(mensagem_sem_dados)