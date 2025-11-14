from typing import Any, Dict, List, Optional
import os, uuid, hashlib
from datetime import datetime
from fastapi import FastAPI, APIRouter, HTTPException
from pydantic import BaseModel, EmailStr
import psycopg
from pymongo import MongoClient
from neo4j import GraphDatabase

app = FastAPI(title="MK S2 API", version="1.0")

# ---- Conexões (do .env) ----
PG_DSN    = os.getenv("PG_DSN")
MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB  = os.getenv("MONGO_DB","kart_db1")
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_AUTH= (os.getenv("NEO4J_USER"), os.getenv("NEO4J_PASSWORD"))
NEO4J_DB  = os.getenv("NEO4J_DATABASE","neo4j")

# ---- Helpers ----
def hash_pwd(p: str) -> str:
    return p

def pg_conn():
    return psycopg.connect(PG_DSN)

def mongo_db():
    return MongoClient(MONGO_URI)[MONGO_DB]

def neo4j_session():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH).session(database=NEO4J_DB)

# ---- Models ----
class SignUp(BaseModel):
    name: str
    email: EmailStr
    password: str

class Login(BaseModel):
    email: EmailStr
    password: str

class Selection(BaseModel):
    character: str
    kart: str
    wheel: str
    glider: str
    track: str

class StartRace(BaseModel):
    user_id: str
    selection: Selection

# ---- Endpoints ----
@app.get("/health")
def health():
    # PG
    try:
        with pg_conn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                pg_ok = True
    except Exception as e:
        pg_ok = False
    # Mongo
    try:
        mongo_db().command("ping")
        mg_ok = True
    except Exception:
        mg_ok = False
    # Neo4j
    try:
        with neo4j_session() as s:
            s.run("RETURN 1").consume()
            n4j_ok = True
    except Exception:
        n4j_ok = False
    return {"pg": pg_ok, "mongo": mg_ok, "neo4j": n4j_ok}

# --- Auth: SignUp ---
@app.post("/auth/signup")
def signup(p: SignUp):
    uid = str(uuid.uuid4())
    now = datetime.utcnow()
    try:
        with pg_conn() as conn, conn.cursor() as cur:
            cur.execute("""
                INSERT INTO usuarios (id, nome, email, senha, criado_em)
                VALUES (%s, %s, %s, %s, %s)
            """, (uid, p.name, p.email, hash_pwd(p.password), now))
            conn.commit()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(409, "E-mail já cadastrado")
    except Exception as e:
        raise HTTPException(500, f"Erro no cadastro: {e}")
    return {"ok": True, "user_id": uid, "name": p.name, "email": p.email}

# --- Auth: Login ---
@app.post("/auth/login")
def login(p: Login):
    with pg_conn() as conn, conn.cursor() as cur:
        cur.execute("SELECT id, nome, senha FROM usuarios WHERE email=%s", (p.email,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(401, "Usuário não encontrado")
        uid, name, stored = row
        if stored != hash_pwd(p.password):
            raise HTTPException(401, "Senha incorreta")
        return {"ok": True, "user_id": str(uid), "name": name, "email": p.email}

# --- Catálogo (DB1) ---
@app.get("/db1/catalog")
def catalog():
    db = mongo_db()
    out = {}
    for col in ["characters","karts","wheels","gliders","tracks"]:
        out[col] = list(db[col].find({}, {"_id":0}).limit(100))
    return out

# --- Iniciar corrida (DB2) ---
@app.post("/race/start")
def start_race(p: StartRace):
    # cria runner + corrida + posição=1 (demo single player)
    with neo4j_session() as s:
        # constraints básicos
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Runner)   REQUIRE n.runner_id IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Race)     REQUIRE n.race_id IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Character) REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Kart)      REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Wheel)     REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Glider)    REQUIRE n.name IS UNIQUE").consume()
        s.run("CREATE CONSTRAINT IF NOT EXISTS FOR (n:Track)     REQUIRE n.name IS UNIQUE").consume()

        # garante catálogo do nó (idempotente)
        for lbl, val in [("Character", p.selection.character),
                         ("Kart",      p.selection.kart),
                         ("Wheel",     p.selection.wheel),
                         ("Glider",    p.selection.glider),
                         ("Track",     p.selection.track)]:
            s.run(f"MERGE (n:{lbl} {{name:$name}})", name=val).consume()

        runner_id = str(uuid.uuid4())
        race_id   = str(uuid.uuid4())

        # cria runner e vínculos
        s.run("""
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
""", runner_id=runner_id, user_id=p.user_id,
     character=p.selection.character, kart=p.selection.kart,
     wheel=p.selection.wheel, glider=p.selection.glider).consume()

        # cria corrida e posição
        s.run("""
MERGE (r:Race {race_id:$race_id})
WITH r
MATCH (t:Track {name:$track})
MERGE (r)-[:ON_TRACK]->(t)
""", race_id=race_id, track=p.selection.track).consume()

        s.run("""
MATCH (u:Runner {runner_id:$runner_id})
MATCH (r:Race {race_id:$race_id})
MERGE (pos:Position {race_id:$race_id, runner_id:$runner_id})
  ON CREATE SET pos.place = 1
MERGE (pos)-[:OF_RUNNER]->(u)
MERGE (pos)-[:IN_RACE]->(r)
MERGE (u)-[:PARTICIPATED_IN]->(r)
""", runner_id=runner_id, race_id=race_id).consume()

    return {"ok": True, "race_id": race_id, "runner_id": runner_id}


from fastapi import APIRouter
rdb_router = APIRouter()

@rdb_router.get("/rdb/users")
def list_users():
    with psycopg.connect(PG_DSN) as conn, conn.cursor() as cur:
        cur.execute("""
            SELECT id::text, nome, email, to_char(criado_em,'YYYY-MM-DD HH24:MI')
            FROM usuarios
            ORDER BY criado_em DESC
            LIMIT 200
        """)
        rows = cur.fetchall()
    return [{"id": r[0], "name": r[1], "email": r[2], "created_at": r[3]} for r in rows]


# --- Rota direta no app para listar usuários do RDB ---
from typing import Optional
from fastapi import Query
import os, psycopg

@app.get("/rdb/users")
def list_users(
    exclude_id: Optional[str] = Query(default=None),
    limit: int = Query(default=200, ge=1, le=500),
):
    where = ""
    params = [limit]
    if exclude_id:
        where = "WHERE id::text <> %s"
        params = [exclude_id, limit]

    sql = f"""
        SELECT id::text, nome, email, to_char(criado_em,'YYYY-MM-DD HH24:MI')
        FROM usuarios
        {where}
        ORDER BY RANDOM()
        LIMIT %s
    """

    dsn = os.getenv("PG_DSN")
    with psycopg.connect(dsn) as conn, conn.cursor() as cur:
        cur.execute(sql, params)
        rows = cur.fetchall()

    return [
        {"id": r[0], "name": r[1], "email": r[2], "created_at": r[3]}
        for r in rows
    ]


# ==== MODELOS PARA /race/finish ====
class Part(BaseModel):
    name: str
    Peso: Optional[int] | Optional[str] = None
    Velocidade: Optional[int] = 0
    Aceleracao: Optional[int] | None = None
    # Aceita também keys minúsculas do Mongo
    peso: Optional[int] | Optional[str] = None
    speed: Optional[int] = None
    acceleration: Optional[int] = None

class RaceFinishPlayer(BaseModel):
    id: str
    name: str
    character: Dict[str, Any]
    kart: Dict[str, Any]
    wheel: Dict[str, Any]
    glider: Dict[str, Any]
    position: int
    stats: Dict[str, int]  # {peso_total, velocidade, aceleracao}

class RaceFinishPayload(BaseModel):
    mode: str  # "online" ou "local"
    track: Dict[str, Any]
    players: List[RaceFinishPlayer]


def _part_name(d: Dict[str, Any]) -> str:
    return d.get("name") or d.get("Nome") or "?"

def persist_race_to_neo4j(track: Dict[str, Any], players: list[dict], mode: str = "online") -> str:
    # Usa driver já configurado no arquivo (get_neo4j() que você já tem)
    from datetime import datetime
    from uuid import uuid4
    race_id = str(uuid4())
# ====== BLOCO LIMPO: modelos e salvamento de corrida no Neo4j ======
from pydantic import BaseModel  # já deve existir no topo; manter por segurança

class RaceFinishPlayer(BaseModel):
    id: str
    name: str
    character: dict
    kart: dict
    wheel: dict
    glider: dict
    position: int
    stats: dict = {}

class RaceFinishPayload(BaseModel):
    mode: str                 # "local" ou "online"
    track: dict               # {"name": "..."}
    players: list[RaceFinishPlayer]

def save_race_to_neo4j(payload: "RaceFinishPayload") -> str:
    import uuid, datetime
    driver, db = get_neo4j()  # definido anteriormente no arquivo
    race_id = str(uuid.uuid4())
    ts = datetime.datetime.utcnow().isoformat()

    def _tx(tx, race_id, payload_dict, ts):
        # Garante nós Race e Track
        tx.run(
            """
            MERGE (t:Track {name: $track})
            MERGE (r:Race {id: $race_id})
            ON CREATE SET r.mode = $mode, r.created_at = $ts, r.track = $track
            """,
            race_id=race_id,
            mode=payload_dict.get("mode"),
            track=(payload_dict.get("track") or {}).get("name"),
            ts=ts,
        )

        # Cria/atualiza resultados por jogador
        for pl in payload_dict.get("players", []):
            pid = pl.get("id")
            pname = pl.get("name")
            pos = pl.get("position")
            ch = (pl.get("character") or {}).get("name")
            kart = (pl.get("kart") or {}).get("name")
            wheel = (pl.get("wheel") or {}).get("name")
            glider = (pl.get("glider") or {}).get("name")
            stats = pl.get("stats") or {}
            peso_total = stats.get("peso_total")
            vel = stats.get("velocidade")
            acc = stats.get("aceleracao")

            tx.run(
                """
                MATCH (r:Race {id: $race_id})
                MERGE (p:Person {id: $pid})
                ON CREATE SET p.name = $pname
                MERGE (p)-[res:RACED_IN]->(r)
                SET res.position   = $pos,
                    res.character  = $ch,
                    res.kart       = $kart,
                    res.wheel      = $wheel,
                    res.glider     = $glider,
                    res.peso_total = $peso_total,
                    res.velocidade = $vel,
                    res.aceleracao = $acc
                """,
                race_id=race_id, pid=pid, pname=pname, pos=pos,
                ch=ch, kart=kart, wheel=wheel, glider=glider,
                peso_total=peso_total, vel=vel, acc=acc
            )

    # >>> sessão correta (sem parênteses extras)
    with driver.session(database=db) as s:
        s.execute_write(_tx, race_id, payload.model_dump(), ts)

    return race_id

@app.post("/race/finish")
def race_finish(payload: RaceFinishPayload):
    try:
        race_id = save_race_to_neo4j(payload)
        return {"ok": True, "race_id": race_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao salvar corrida no Neo4j: {e}")
# ====== FIM DO BLOCO LIMPO ======


def get_neo4j():
    """Retorna (driver, db) usando NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD e NEO4J_DB (padrão 'neo4j')."""
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pwd = os.getenv("NEO4J_PASSWORD")
    db = os.getenv("NEO4J_DB", "neo4j")
    if not uri or not user or not pwd:
        raise RuntimeError("Variáveis NEO4J_URI/USER/PASSWORD ausentes no ambiente do container.")
    driver = GraphDatabase.driver(uri, auth=(user, pwd))
    return driver, db
