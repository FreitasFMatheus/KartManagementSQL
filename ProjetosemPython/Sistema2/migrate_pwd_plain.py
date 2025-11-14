import os, psycopg

PG_DSN = os.getenv("PG_DSN")
assert PG_DSN, "PG_DSN não definido"

SQL = """
-- 1) cria tabela se não existir (com coluna senha)
CREATE TABLE IF NOT EXISTS usuarios (
  id UUID PRIMARY KEY,
  nome TEXT NOT NULL,
  email TEXT NOT NULL,
  senha TEXT,
  criado_em TIMESTAMP DEFAULT NOW()
);

-- 2) se existir senha_hash e NÃO existir senha, renomeia
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='usuarios' AND column_name='senha_hash'
  ) AND NOT EXISTS (
    SELECT 1 FROM information_schema.columns
    WHERE table_name='usuarios' AND column_name='senha'
  ) THEN
    EXECUTE 'ALTER TABLE usuarios RENAME COLUMN senha_hash TO senha';
  END IF;
END$$;

-- 3) garante que a coluna senha existe (se não existir ainda)
ALTER TABLE usuarios ADD COLUMN IF NOT EXISTS senha TEXT;

-- 4) garante índice único em email (nome de índice padronizado)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_indexes
    WHERE schemaname='public' AND indexname='usuarios_email_key'
  ) THEN
    CREATE UNIQUE INDEX usuarios_email_key ON usuarios(email);
  END IF;
END$$;

-- 5) preenche senha vazia com uma default (apenas para evitar NOT NULL falhar)
UPDATE usuarios SET senha = '123456' WHERE senha IS NULL;

-- 6) agora aplica NOT NULL em senha
ALTER TABLE usuarios ALTER COLUMN senha SET NOT NULL;
"""

with psycopg.connect(PG_DSN) as conn, conn.cursor() as cur:
    cur.execute(SQL)
    conn.commit()

with psycopg.connect(PG_DSN) as conn, conn.cursor() as cur:
    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name='usuarios'
        ORDER BY ordinal_position
    """)
    cols = cur.fetchall()
    print("Colunas 'usuarios':")
    for c in cols:
        print("  ", c)
print("OK: Migração aplicada. 'usuarios' usa apenas 'senha' (plaintext).")
