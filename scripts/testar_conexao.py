"""
testar_conexao.py
-----------------
Testa conectividade com o banco PostgreSQL via variáveis de ambiente (.env).

Uso:
    python scripts/testar_conexao.py
"""
import os
from pathlib import Path
from dotenv import load_dotenv
import psycopg2

load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

modos = ["disable", "allow", "prefer", "require"]
for modo in modos:
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=int(os.getenv("DB_PORT", "5432")),
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            sslmode=modo,
            connect_timeout=5,
        )
        print(f"[OK] sslmode={modo}")
        conn.close()
        break
    except Exception as e:
        print(f"[FALHA] sslmode={modo} -> {e}")
