import os
import uuid
from neo4j import GraphDatabase

# Mesmo esquema do api.py
NEO4J_URI  = os.getenv("NEO4J_URI")
NEO4J_AUTH = (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
NEO4J_DB   = os.getenv("NEO4J_DATABASE", "neo4j")


def neo4j_session():
    if not NEO4J_URI or not NEO4J_AUTH[0] or not NEO4J_AUTH[1]:
        raise RuntimeError("Variáveis NEO4J_URI/NEO4J_USER/NEO4J_PASSWORD não configuradas.")
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    # igual ao api.py: retorna direto a session, que é context manager
    return driver.session(database=NEO4J_DB)


# Seeds de exemplo: 2 corridas, uma para cada usuário do PopRDB.py
RACE_SEEDS = [
    {
        "user_id": "02ff17b3-c158-45b7-b148-b39a6fa40a2d",  # ArchLinux
        "selection": {
            "character": "Mario",
            "kart":      "Standard Kart",
            "wheel":     "Standard",
            "glider":    "Super Glider",
            "track":     "Mario Kart Stadium",
        },
        "place": 1,
    },
    {
        "user_id": "265c0ed7-58d0-4c9a-8be6-7caec1f7df94",  # Ximbica
        "selection": {
            "character": "Luigi",
            "kart":      "Pipe Frame",
            "wheel":     "Slim",
            "glider":    "Cloud Glider",
            "track":     "Water Park",
        },
        "place": 1,
    },
]


def main():
    print("== Neo4j (DB2): populando corridas de exemplo ==")

    with neo4j_session() as s:
        # Mesmos constraints usados em /race/start
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Runner)   REQUIRE n.runner_id IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Race)     REQUIRE n.race_id IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Character) REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Kart)      REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Wheel)     REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Glider)    REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Track)     REQUIRE n.name IS UNIQUE").consume()

        for seed in RACE_SEEDS:
            sel = seed["selection"]

            # Garante catálogo (idempotente) – exatamente como no /race/start
            for lbl, val in [
                ("Character", sel["character"]),
                ("Kart",      sel["kart"]),
                ("Wheel",     sel["wheel"]),
                ("Glider",    sel["glider"]),
                ("Track",     sel["track"]),
            ]:
                s.run(
                    f"MERGE (n:{lbl} {{name:$name}})",
                    name=val,
                ).consume()

            runner_id = str(uuid.uuid4())
            race_id   = str(uuid.uuid4())

            # Cria runner e vínculos com Character/Kart/Wheel/Glider
            s.run(
                """
MERGE (u:Runner {runner_id:$runner_id})
  ON CREATE SET u.user_id=$user_id
  ON MATCH SET  u.user_id=$user_id
WITH u
MATCH (c:Character {name:$character})
MATCH (k:Kart      {name:$kart})
MATCH (w:Wheel     {name:$wheel})
MATCH (g:Glider    {name:$glider})
MERGE (u)-[:CHOSE_CHARACTER]->(c)
MERGE (u)-[:CHOSE_KART]->(k)
MERGE (u)-[:CHOSE_WHEEL]->(w)
MERGE (u)-[:CHOSE_GLIDER]->(g)
""",
                runner_id=runner_id,
                user_id=seed["user_id"],
                character=sel["character"],
                kart=sel["kart"],
                wheel=sel["wheel"],
                glider=sel["glider"],
            ).consume()

            # Cria corrida e vincula com Track
            s.run(
                """
MERGE (r:Race {race_id:$race_id})
WITH r
MATCH (t:Track {name:$track})
MERGE (r)-[:ON_TRACK]->(t)
""",
                race_id=race_id,
                track=sel["track"],
            ).consume()

            # Cria posição (Position) e liga Runner + Race
            s.run(
                """
MATCH (u:Runner {runner_id:$runner_id})
MATCH (r:Race {race_id:$race_id})
MERGE (pos:Position {race_id:$race_id, runner_id:$runner_id})
  ON CREATE SET pos.place = $place
MERGE (pos)-[:OF_RUNNER]->(u)
MERGE (pos)-[:IN_RACE]->(r)
MERGE (u)-[:PARTICIPATED_IN]->(r)
""",
                runner_id=runner_id,
                race_id=race_id,
                place=seed.get("place", 1),
            ).consume()

            print(f"  -> Corrida criada: race_id={race_id}, runner_id={runner_id}")

    print("✅ Neo4j (DB2): seeds de corridas criados com sucesso.")


if __name__ == "__main__":
    main()
