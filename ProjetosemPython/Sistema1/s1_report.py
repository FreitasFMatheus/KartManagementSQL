import os
import requests

API_BASE = os.getenv("S2_API", "http://localhost:8000")

def send_race_to_s2(mode: str, track_name: str, players: list[dict]) -> str | None:
    """
    Envia o resultado da corrida para o S2 (/race/finish), que grava no Neo4j.

    players: lista de dicts como:
      {
        "id": "uuid-ou-bot-1",
        "name": "Matheus ou Bot 1",
        "character": {"name": "Mario"},
        "kart": {"name": "Pipe Frame"},
        "wheel": {"name": "Standard"},
        "glider": {"name": "Super Glider"},
        "position": 1,
        "stats": {"peso_total": 6, "velocidade": 7, "aceleracao": 0}
      }
    """
    payload = {
        "mode": mode,
        "track": {"name": track_name},
        "players": players
    }
    try:
        r = requests.post(f"{API_BASE}/race/finish", json=payload, timeout=10)
        if r.ok:
            data = r.json()
            rid = data.get("race_id")
            print(f"[S1] Neo4j OK: race_id={rid}")
            return rid
        else:
            print(f"[S1] Falha ao salvar no Neo4j: {r.status_code} {r.text}")
    except Exception as e:
        print(f"[S1] Erro ao contatar S2: {e}")
    return None
def report_race_to_neo4j(mode: str, track_name: str, results: list[dict]) -> str | None:
    players = []
    for r in results:
        players.append({
            "id": r.get("id") or r.get("user_id") or r.get("name"),
            "name": r.get("name"),
            "character": {"name": (r.get("character") or {}).get("name") if isinstance(r.get("character"), dict) else r.get("character")},
            "kart": {"name": (r.get("kart") or {}).get("name") if isinstance(r.get("kart"), dict) else r.get("kart")},
            "wheel": {"name": (r.get("wheel") or {}).get("name") if isinstance(r.get("wheel"), dict) else r.get("wheel")},
            "glider": {"name": (r.get("glider") or {}).get("name") if isinstance(r.get("glider"), dict) else r.get("glider")},
            "position": int(r.get("position", 0)),
            "stats": {
                "peso_total": int(((r.get("stats") or {}).get("peso_total", 0))),
                "velocidade": int(((r.get("stats") or {}).get("velocidade", 0))),
                "aceleracao": int(((r.get("stats") or {}).get("aceleracao", 0))),
            },
        })
    from s1_report import send_race_to_s2
    return send_race_to_s2(mode=mode, track_name=track_name, players=players)
