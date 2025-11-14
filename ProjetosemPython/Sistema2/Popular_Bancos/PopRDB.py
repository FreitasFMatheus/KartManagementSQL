import os, psycopg
from typing import cast

PG_DSN = cast(str, os.getenv("PG_DSN"))  # garante para o type checker

def main():
    with psycopg.connect(PG_DSN) as conn, conn.cursor() as cur:
        # tabela com senha (plaintext)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id UUID PRIMARY KEY,
                nome TEXT NOT NULL,
                email TEXT NOT NULL,
                senha TEXT NOT NULL,
                criado_em TIMESTAMP DEFAULT NOW()
            );
        """)
        # índice único em email
        cur.execute("""
            DO $$
            BEGIN
              IF NOT EXISTS (
                SELECT 1 FROM pg_indexes
                WHERE schemaname='public' AND indexname='usuarios_email_key'
              ) THEN
                CREATE UNIQUE INDEX usuarios_email_key ON usuarios(email);
              END IF;
            END$$;
        """)

        # seeds idempotentes (senha texto puro)
        cur.execute("""
            INSERT INTO usuarios (id, nome, email, senha)
            VALUES ('02ff17b3-c158-45b7-b148-b39a6fa40a2d','ArchLinux','ArchLinux@example.com','123456')
            ON CONFLICT (id) DO NOTHING;
        """)
        cur.execute("""
            INSERT INTO usuarios (id, nome, email, senha)
            VALUES ('265c0ed7-58d0-4c9a-8be6-7caec1f7df94','Ximbica','Ximbicao@example.com','123456')
            ON CONFLICT (id) DO NOTHING;
        """)

        conn.commit()
    print("Postgres (RDB): schema + seeds ok (senha em plaintext).")

if __name__ == "__main__":
    main()
