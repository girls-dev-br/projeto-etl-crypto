import os
import logging
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

USUARIO = os.getenv("DB_USER")
SENHA = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")
PORTA = os.getenv("DB_PORT", "5432")
BANCO = os.getenv("DB_NAME")

URL_CONEXAO = f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}"
engine = create_engine(URL_CONEXAO)

def carregar_dados_dw(df_validos, df_rejeitados=None):
    """
    Função responsável exclusivamente pela etapa de Load (Carga) no Data Warehouse.
    """
    print("\n📦 [LOAD] Iniciando Carga no Data Warehouse...")
    
    # 1. Carregar Rejeitados (se houver)
    if df_rejeitados is not None and not df_rejeitados.empty:
        print(f"⚠️ Gravando {len(df_rejeitados)} registros na tabela rejected_stage_cotacoes...")
        df_rejeitados.to_sql('rejected_stage_cotacoes', con=engine, if_exists='append', index=False)
        logging.warning(f"{len(df_rejeitados)} registros rejeitados foram gravados.")

    # 2. Carregar Válidos nas Dimensões e Tabela Fato
    if df_validos is not None and not df_validos.empty:
        with engine.begin() as conexao:
            # A. Povoar dim_fiat
            print(" -> Atualizando dim_fiat...")
            conexao.execute(text("""
                INSERT INTO dim_fiat (fiat_id, nome, simbolo_monetario)
                VALUES ('usd', 'Dólar Americano', '$'), ('brl', 'Real Brasileiro', 'R$')
                ON CONFLICT (fiat_id) DO NOTHING;
            """))

            # B. Povoar dim_moeda
            print(" -> Atualizando dim_moeda...")
            for moeda in df_validos['moeda_id'].unique():
                simb = "BTC" if moeda == "bitcoin" else ("ETH" if moeda == "ethereum" else moeda.upper()[:5])
                conexao.execute(text("""
                    INSERT INTO dim_moeda (moeda_id, simbolo, nome)
                    VALUES (:id, :simbolo, :nome)
                    ON CONFLICT (moeda_id) DO NOTHING;
                """), {"id": moeda, "simbolo": simb, "nome": moeda.capitalize()})

            # C. Povoar dim_tempo
            print(" -> Atualizando dim_tempo...")
            datas_unicas = df_validos['data_id'].drop_duplicates()
            
            meses_pt = {
                1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
                5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
                9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
            }
            dias_pt = {
                0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
                3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
            }

            for d in datas_unicas:
                ano = d.year
                mes = d.month
                nome_mes = meses_pt[mes]
                dia = d.day
                dia_semana = dias_pt[d.weekday()]
                trimestre = (mes - 1) // 3 + 1

                conexao.execute(text("""
                    INSERT INTO dim_tempo (data_id, ano, mes, nome_mes, dia, dia_semana, trimestre)
                    VALUES (:data_id, :ano, :mes, :nome_mes, :dia, :dia_semana, :trimestre)
                    ON CONFLICT (data_id) DO NOTHING;
                """), {
                    "data_id": d,
                    "ano": ano,
                    "mes": mes,
                    "nome_mes": nome_mes,
                    "dia": dia,
                    "dia_semana": dia_semana,
                    "trimestre": trimestre
                })

            # D. Povoar fato_cotacoes
            print(" -> Inserindo registros na fato_cotacoes...")
            for _, row in df_validos.iterrows():
                conexao.execute(text("""
                    INSERT INTO fato_cotacoes (data_id, moeda_id, fiat_id, preco, market_cap, volume_total)
                    VALUES (:data_id, :moeda_id, :fiat_id, :preco, :market_cap, :volume_total)
                    ON CONFLICT (data_id, moeda_id, fiat_id) DO NOTHING;
                """), {
                    "data_id": row['data_id'],
                    "moeda_id": row['moeda_id'],
                    "fiat_id": row['fiat_id'],
                    "preco": row['preco'],
                    "market_cap": row['market_cap'],
                    "volume_total": row['volume_total']
                })

        print("✨ [LOAD] Dimensões e Fato carregadas com sucesso!")
        logging.info("Carga no DW concluída com sucesso.")