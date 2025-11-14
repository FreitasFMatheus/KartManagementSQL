import psycopg, os
DSN = os.getenv("PG_DSN")

def main():
    if not DSN:
        raise RuntimeError("PG_DSN não definido no .env")
    with psycopg.connect(DSN) as conn, conn.cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS consoles CASCADE;")
        cur.execute("DROP TABLE IF EXISTS usuarios CASCADE;")
        conn.commit()
    print("Postgres (RDB): tudo removido.")

if __name__ == "__main__":
    main()
