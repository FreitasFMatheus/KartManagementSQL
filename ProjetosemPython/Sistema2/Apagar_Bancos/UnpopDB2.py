import os
from neo4j import GraphDatabase

NEO4J_URI  = os.getenv("NEO4J_URI")
NEO4J_AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
NEO4J_DB   = os.getenv("NEO4J_DATABASE", "neo4j")


def neo4j_session():
    if not NEO4J_URI or not NEO4J_AUTH[0] or not NEO4J_AUTH[1]:
        raise RuntimeError("Variáveis NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD não configuradas.")
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    return driver.session(database=NEO4J_DB)


def main():
    print("== Neo4j (DB2): limpando dados do projeto ==")

    with neo4j_session() as s:
        # Ordem não importa muito por causa do DETACH DELETE
        queries = [
            "MATCH (n:Position)  DETACH DELETE n",
            "MATCH (n:Runner)    DETACH DELETE n",
            "MATCH (n:Race)      DETACH DELETE n",
            "MATCH (n:Character) DETACH DELETE n",
            "MATCH (n:Kart)      DETACH DELETE n",
            "MATCH (n:Wheel)     DETACH DELETE n",
            "MATCH (n:Glider)    DETACH DELETE n",
            "MATCH (n:Track)     DETACH DELETE n",
        ]

        for q in queries:
            s.run(q).consume()

    print("🧹 Neo4j (DB2): nós e relações do projeto removidos com sucesso.")


if __name__ == "__main__":
    main()
