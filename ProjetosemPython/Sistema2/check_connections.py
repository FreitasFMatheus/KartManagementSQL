import os, sys

def check_postgres():
    import psycopg
    dsn = os.getenv("PG_DSN")
    if not dsn:
        return "PG ERRO: variável PG_DSN não definida."
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("select version();")
                v = cur.fetchone()[0]
        return f"PG OK: {v}"
    except Exception as e:
        return f"PG ERRO: {e}"

def check_mongo():
    from pymongo import MongoClient
    uri = os.getenv("MONGO_URI")
    dbn = os.getenv("MONGO_DB", "kart_db1")
    if not uri:
        return "Mongo ERRO: variável MONGO_URI não definida."
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=6000, uuidRepresentation="standard")
        client.admin.command("ping")
        _ = client[dbn]
        return f"Mongo OK: ping ok. DB={dbn}"
    except Exception as e:
        return f"Mongo ERRO: {e}"

def check_neo4j():
    from neo4j import GraphDatabase
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER") or os.getenv("NEO4J_USERNAME")
    pwd  = os.getenv("NEO4J_PASSWORD")
    db   = os.getenv("NEO4J_DATABASE", "neo4j")
    if not (uri and user and pwd):
        return "Neo4j ERRO: faltam NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD."
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pwd))
        driver.verify_connectivity()
        with driver.session(database=db) as s:
            n = s.run("RETURN 1 AS ok").single()["ok"]
        return f"Neo4j OK: retorno={n} (db={db})"
    except Exception as e:
        return f"Neo4j ERRO: {e}"

if __name__ == "__main__":
    results = [check_postgres(), check_mongo(), check_neo4j()]
    print("\n".join(results))
    if any("ERRO" in r for r in results):
        sys.exit(1)
