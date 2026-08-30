import os
import pandas as pd
from datetime import timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Carregar configurações do banco
load_dotenv()

USUARIO = os.getenv("DB_USER")
SENHA = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")
PORTA = os.getenv("DB_PORT", "5432")
BANCO = os.getenv("DB_NAME")

URL_CONEXAO = f"postgresql://{USUARIO}:{SENHA}@{HOST}:{PORTA}/{BANCO}"
engine = create_engine(URL_CONEXAO)

print("Etapa 1: Conexão estabelecida com sucesso!")

# 2. Ler histórico da fato_cotacoes
query = "SELECT data_id, moeda_id, fiat_id, preco FROM fato_cotacoes ORDER BY data_id ASC;"
df = pd.read_sql(query, con=engine)
df['data_id'] = pd.to_datetime(df['data_id'])

print(f"Etapa 2: Total de registros lidos da fato_cotacoes: {len(df)}")

# 3. Calcular a projeção de 5 dias
print("Etapa 3: Calculando valores projetados...")
lista_projecoes = []

for (moeda, fiat), grupo in df.groupby(['moeda_id', 'fiat_id']):
    grupo = grupo.sort_values('data_id')
    
    # Variação média dos últimos 30 dias
    grupo['variacao'] = grupo['preco'].pct_change()
    taxa_media = grupo['variacao'].tail(30).mean()
    
    ultima_data = grupo.iloc[-1]['data_id']
    ultimo_preco = float(grupo.iloc[-1]['preco'])
    
    preco_acumulado = ultimo_preco
    for i in range(1, 6):
        data_futura = ultima_data + timedelta(days=i)
        preco_acumulado = preco_acumulado * (1 + taxa_media)
        
        lista_projecoes.append({
            "data_projecao": data_futura.date(),
            "moeda_id": moeda,
            "fiat_id": fiat,
            "preco_projetado": round(preco_acumulado, 4)
        })

df_proj = pd.DataFrame(lista_projecoes)
print("\n--- PRÉVIA DAS PROJEÇÕES GERADAS ---")
print(df_proj)
# 4. Gravar no Banco de Dados
print("\nEtapa 4: Gravando datas na dim_tempo e projeções na fato_projecoes...")

meses_pt = {
    1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril',
    5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto',
    9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
}
dias_pt = {
    0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira',
    3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
}

with engine.begin() as conexao:
    # 4.1 Garantir que as datas futuras existam na dim_tempo
    for _, linha in df_proj.iterrows():
        d = linha['data_projecao']
        conexao.execute(text("""
            INSERT INTO dim_tempo (data_id, ano, mes, nome_mes, dia, dia_semana, trimestre)
            VALUES (:data_id, :ano, :mes, :nome_mes, :dia, :dia_semana, :trimestre)
            ON CONFLICT (data_id) DO NOTHING;
        """), {
            "data_id": d,
            "ano": d.year,
            "mes": d.month,
            "nome_mes": meses_pt[d.month],
            "dia": d.day,
            "dia_semana": dias_pt[d.weekday()],
            "trimestre": (d.month - 1) // 3 + 1
        })
    
    # 4.2 Limpar dados antigos de projeção e inserir os novos
    conexao.execute(text("DELETE FROM fato_projecoes;"))
    
    for _, linha in df_proj.iterrows():
        conexao.execute(text("""
            INSERT INTO fato_projecoes (data_projecao, moeda_id, fiat_id, preco_projetado)
            VALUES (:data_projecao, :moeda_id, :fiat_id, :preco_projetado);
        """), {
            "data_projecao": linha['data_projecao'],
            "moeda_id": linha['moeda_id'],
            "fiat_id": linha['fiat_id'],
            "preco_projetado": linha['preco_projetado']
        })

print(f"\n✨ Sucesso! {len(df_proj)} projeções gravadas com êxito na tabela fato_projecoes.")