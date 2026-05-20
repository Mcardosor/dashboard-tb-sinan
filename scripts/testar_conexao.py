import psycopg2

modos = ["disable", "allow", "prefer", "require"]
for modo in modos:
    try:
        conn = psycopg2.connect(
            host="10.20.10.107",
            port=5432,
            dbname="cenarios_ai",
            user="matheus",
            password="@Matheus_Cardoso",
            sslmode=modo,
            connect_timeout=5,
        )
        print(f"[OK] sslmode={modo}")
        conn.close()
        break
    except Exception as e:
        print(f"[FALHA] sslmode={modo} -> {e}")
