import os
import urllib.parse
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()

USUARIO = os.getenv("DB_USER")
SENHA = os.getenv("DB_PASSWORD")
HOST = os.getenv("DB_HOST", "localhost")
PORTA = os.getenv("DB_PORT", "5432")
BANCO = os.getenv("DB_NAME")

USUARIO_ENCODED = urllib.parse.quote_plus(USUARIO) if USUARIO else ""
SENHA_ENCODED = urllib.parse.quote_plus(SENHA) if SENHA else ""

URL_CONEXAO = (
    f"postgresql://{USUARIO_ENCODED}:{SENHA_ENCODED}@{HOST}:{PORTA}/{BANCO}"
    f"?client_encoding=utf8&sslmode=require&channel_binding=require"
)

engine = create_engine(URL_CONEXAO)

def aplicar_views():
    # Sobe de src/utils para a raiz do projeto (..) e entra em sql/views.sql
    diretorio_atual = os.path.dirname(os.path.abspath(__file__))
    raiz_projeto = os.path.abspath(os.path.join(diretorio_atual, "..", ".."))
    caminho_sql = os.path.join(raiz_projeto, "sql", "views.sql")

    # Fallback caso seja executado a partir da própria raiz
    if not os.path.exists(caminho_sql):
        caminho_sql = os.path.abspath("sql/views.sql")

    print(f"📄 Localizando arquivo em: {caminho_sql}")

    with open(caminho_sql, "r", encoding="utf-8") as f:
        conteudo_sql = f.read()

    # Separa os comandos por ponto e vírgula para executar individualmente
    comandos = [cmd.strip() for cmd in conteudo_sql.split(";") if cmd.strip()]

    print(f"⚙️ Aplicando {len(comandos)} views no banco de dados...")

    with engine.begin() as conexao:
        for i, comando in enumerate(comandos, start=1):
            conexao.execute(text(comando))
            print(f"  -> View {i}/{len(comandos)} aplicada com sucesso!")

    print("✅ Todas as views de sql/views.sql foram aplicadas com sucesso no banco!")

if __name__ == "__main__":
    aplicar_views()