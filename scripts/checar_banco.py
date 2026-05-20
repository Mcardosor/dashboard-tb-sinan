"""
checar_banco.py
---------------
Diagnóstico: testa acesso a public.sinan_tube e mostra colunas/anos disponíveis.
"""
import os
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, text

load_dotenv()

url = URL.create(
    drivername="postgresql+psycopg2",
    username=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOST"),
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.getenv("DB_NAME"),
)
engine = create_engine(url, pool_pre_ping=True)

# Cada teste usa conexão própria para evitar cascata de erros
def testar(sql, label):
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql)).fetchall()
        print(f"  OK  {label}")
        return result
    except Exception as e:
        print(f"  X   {label}  ->  {str(e).splitlines()[0][:100]}")
        return None

print(f"Conectado como: {os.getenv('DB_USER')}@{os.getenv('DB_HOST')}\n")

# 1. Conta total
rows = testar("SELECT COUNT(*) FROM public.sinan_tube", "public.sinan_tube COUNT")
if rows:
    print(f"      Total de linhas: {rows[0][0]:,}")

# 2. Anos disponíveis
rows = testar(
    "SELECT ano_notificacao, COUNT(*) as n FROM public.sinan_tube GROUP BY 1 ORDER BY 1",
    "anos disponíveis"
)
if rows:
    for r in rows:
        print(f"      {r[0]}: {r[1]:,} registros")

# 3. Primeiras colunas
rows = testar(
    """SELECT column_name, data_type
       FROM information_schema.columns
       WHERE table_schema = 'public' AND table_name = 'sinan_tube'
       ORDER BY ordinal_position LIMIT 20""",
    "colunas de public.sinan_tube"
)
if rows:
    for r in rows:
        print(f"      {r[0]:<40} {r[1]}")
