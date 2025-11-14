from s1_report import send_race_to_s2
import requests, sys, random, textwrap, time

API = "http://localhost:8000"

# ==============================
# Helpers básicos de I/O
# ==============================

def prompt(msg):
    try:
        return input(msg)
    except EOFError:
        return ""

def print_title(t):
    print("\n" + "="*len(t))
    print(t)
    print("="*len(t))

def pretty_row(idx, name, extra=""):
    return f"{idx}. {name}{(' ' + extra) if extra else ''}"

# ==============================
# AUTH
# ==============================

def signup():
    print("\n== Cadastro ==")
    nome = prompt("Nome: ").strip()
    email = prompt("E-mail: ").strip()
    senha = prompt("Senha: ").strip()
    try:
        r = requests.post(f"{API}/auth/signup",
                          json={"name": nome, "email": email, "password": senha},
                          timeout=10)
        r.raise_for_status()
        data = r.json()
        print("Cadastro OK!")
        return data  # { user_id, name, email, ... }
    except Exception as e:
        try:
            print("Erro:", r.text)
        except:
            print("Erro:", e)
        return None

def login():
    print("\n== Login ==")
    email = prompt("E-mail: ").strip()
    senha = prompt("Senha: ").strip()
    try:
        r = requests.post(f"{API}/auth/login",
                          json={"email": email, "password": senha},
                          timeout=10)
        r.raise_for_status()
        data = r.json()
        print("Login OK!")
        return data  # { user_id, name, email, ... }
    except Exception as e:
        try:
            print("Falhou:", r.text)
        except:
            print("Falhou:", e)
        return None

# ==============================
# DB1 CATALOG
# ==============================

def get_catalog():
    r = requests.get(f"{API}/db1/catalog", timeout=10)
    r.raise_for_status()
    return r.json()  # {"characters":[...], "karts":[...], "wheels":[...], "gliders":[...], "tracks":[...]}

def choose_from_list(title, items, render_extra):
    print_title(title)
    for i, it in enumerate(items, 1):
        extra = render_extra(it)
        print(pretty_row(i, it.get("name") or it.get("Nome") or "?", extra))
    while True:
        s = prompt("Escolha (número): ").strip()
        if not s.isdigit():
            print("Digite um número válido.")
            continue
        idx = int(s)
        if 1 <= idx <= len(items):
            return items[idx-1]
        print("Opção inválida.")

# ==============================
# Normalização de atributos (PT/EN)
# ==============================

WEIGHT_MAP = {"light": 1, "medium": 2, "heavy": 3}

# Se no seu DB1 os personagens já trazem "Peso": "light/medium/heavy",
# este mapa não é obrigatório, mas ajuda a garantir fallback.
WEIGHT_BY_CHARACTER = {
    "Mario": "medium", "Luigi": "medium", "Peach": "light", "Bowser": "heavy",
    "Yoshi": "light", "Toad": "light", "Donkey Kong": "heavy", "Wario": "heavy"
}

def _to_int(x, default=0):
    try:
        return int(x)
    except Exception:
        return default

def normalize_weight(val):
    """Aceita 'light/medium/heavy' ou número."""
    if isinstance(val, str):
        m = val.strip().lower()
        if m in WEIGHT_MAP:
            return WEIGHT_MAP[m]
        # pode ser número em string
        return _to_int(m, 0)
    return _to_int(val, 0)

def get_field(d: dict, *keys, default=None):
    """Busca primeira chave existente (case-sensitive) em PT/EN."""
    for k in keys:
        if d.get(k) is not None:
            return d.get(k)
    return default

def render_part_extra(part):
    # tenta pegar Peso em PT/EN
    w_raw = get_field(part, "Peso", "peso", "weight", default=None)
    v_raw = get_field(part, "Velocidade", "velocidade", "speed", default=None)
    a_raw = get_field(part, "Aceleração", "aceleracao", "acceleration", default=None)

    wv = normalize_weight(w_raw) if w_raw is not None else None
    bits = []
    if w_raw is not None:
        if isinstance(w_raw, str) and w_raw.lower() in WEIGHT_MAP:
            bits.append(f"Peso={w_raw}({wv})")
        else:
            bits.append(f"Peso={wv}")
    if v_raw is not None:
        bits.append(f"Velocidade={_to_int(v_raw)}")
    if a_raw is not None:
        bits.append(f"Aceleração={_to_int(a_raw)}")
    return "[" + ", ".join(bits) + "]" if bits else ""

def resumo_stats(escolhas):
    """Somatória do peso/vel/acc (char + kart + roda + glider), aceitando PT/EN."""
    pes, vel, acc = 0, 0, 0

    # personagem: pode ser "Peso": "light/medium/heavy" OU "weight"
    ch = escolhas["character"]
    ch_weight_label = get_field(ch, "Peso", "peso", "weight", default=None)
    if ch_weight_label is None:
        # fallback por nome do personagem
        label = WEIGHT_BY_CHARACTER.get(ch.get("name") or ch.get("Nome") or "", "medium")
        pes += WEIGHT_MAP.get(label, 0)
    else:
        pes += normalize_weight(ch_weight_label)

    # demais peças (preferimos PT, caindo em EN)
    for key in ("kart", "wheel", "glider"):
        part = escolhas[key]
        pes += normalize_weight(get_field(part, "Peso", "peso", "weight", default=0))
        vel += _to_int(get_field(part, "Velocidade", "velocidade", "speed", default=0))
        acc += _to_int(get_field(part, "Aceleração", "aceleracao", "acceleration", default=0))
    return pes, vel, acc

# ==============================
# Construção de escolhas do usuário
# ==============================

def montar_kart_user(catalog):
    ch = choose_from_list("Selecione seu Personagem:", catalog["characters"], render_part_extra)
    ka = choose_from_list("Selecione seu Kart:", catalog["karts"], render_part_extra)
    wh = choose_from_list("Selecione a Roda:", catalog["wheels"], render_part_extra)
    gl = choose_from_list("Selecione o Glider:", catalog["gliders"], render_part_extra)
    return {"character": ch, "kart": ka, "wheel": wh, "glider": gl}

def escolha_pista_aleatoria(catalog):
    tracks = catalog.get("tracks") or []
    if not tracks:
        return {"name": "Pista Desconhecida"}
    return random.choice(tracks)

def nome_de(item):
    return item.get("name") or item.get("Nome") or "?"

def print_resumo_corrida(titulo, pista, jogadores):
    print_title(titulo)
    print(f"Pista: {nome_de(pista)}")
    print("-"*60)
    for idx, j in enumerate(jogadores, 1):
        ch, ka, wh, gl = j["character"], j["kart"], j["wheel"], j["glider"]
        pes, vel, acc = resumo_stats(j)
        print(textwrap.dedent(f"""
        {idx}. {j['name']}
           Personagem: {nome_de(ch)}
           Kart/Roda/Glider: {nome_de(ka)} / {nome_de(wh)} / {nome_de(gl)}
           Peso total: {pes}  |  Velocidade: {vel}  |  Aceleração: {acc}
        """).strip())
        print("-"*60)

# ==============================
# GRID / RACE
# ==============================

def pick_random_build(catalog):
    return {
        "character": random.choice(catalog["characters"]),
        "kart":      random.choice(catalog["karts"]),
        "wheel":     random.choice(catalog["wheels"]),
        "glider":    random.choice(catalog["gliders"]),
    }

def lista_users_rdb(exclude_id=None, limit=7):
    params = {"limit": limit}
    if exclude_id:
        params["exclude_id"] = exclude_id
    r = requests.get(f"{API}/rdb/users", params=params, timeout=10)
    r.raise_for_status()
    return r.json()

# Contagem + simulação

def run_countdown():
    for n in ["1", "2", "3"]:
        print(n)
        time.sleep(1)
    print("VAI!!!")

def simulate_race(players):
    """Ordem aleatória como resultado (posição 1..N)."""
    results = players[:]  # shallow copy
    random.shuffle(results)
    return results

def _player_stats_dict(p):
    # gera dict {"peso_total":..., "velocidade":..., "aceleracao":...} para payload
    pes, vel, acc = resumo_stats(p)
    return {"peso_total": pes, "velocidade": vel, "aceleracao": acc}

def _payload_from_results(mode: str, track, results):
    players_payload = []
    for pos, pl in enumerate(results, start=1):
        ch, ka, wh, gl = pl["character"], pl["kart"], pl["wheel"], pl["glider"]
        stats = _player_stats_dict(pl)
        players_payload.append({
            "id": pl.get("id") or pl.get("user_id") or f"bot-{pos}",
            "name": pl.get("name") or pl.get("nome") or f"Bot {pos}",
            "character": {"name": nome_de(ch)},
            "kart": {"name": nome_de(ka)},
            "wheel": {"name": nome_de(wh)},
            "glider": {"name": nome_de(gl)},
            "position": pos,
            "stats": stats
        })
    return {
        "mode": mode,
        "track_name": nome_de(track),
        "players": players_payload
    }

def print_race_results(track, results):
    print_title("RESULTADO FINAL")
    print(f"Pista: {nome_de(track)}\n" + "-"*60)
    for pos, j in enumerate(results, 1):
        ch, ka, wh, gl = j["character"], j["kart"], j["wheel"], j["glider"]
        pes, vel, acc = resumo_stats(j)
        print(textwrap.dedent(f"""
        #{pos} - {j['name']}
           Personagem: {nome_de(ch)}
           Kart:       {nome_de(ka)}
           Roda:       {nome_de(wh)}
           Glider:     {nome_de(gl)}
           Peso total: {pes}  |  Velocidade: {vel}  |  Aceleração: {acc}
        """).strip())
        print("-"*60)

def run_race_flow(players, track, titulo_inicio, mode_str: str):
    # grid já foi impresso antes
    print_title(titulo_inicio)
    run_countdown()
    print("\nCorrida em andamento...", end="", flush=True)
    for _ in range(5):
        time.sleep(1)
        print(".", end="", flush=True)
    print("\n")

    # resultado
    results = simulate_race(players)
    print_race_results(track, results)

    # envia para S2/Neo4j
    payload = _payload_from_results(mode=mode_str, track=track, results=results)
    rid = send_race_to_s2(mode=payload["mode"],
                          track_name=payload["track_name"],
                          players=payload["players"])
    if rid:
        print(f"\n[S1] Corrida registrada no Neo4j. race_id={rid}")
    else:
        print("\n[S1] Falha ao registrar a corrida no Neo4j.")

    _ = prompt("\nPressione ENTER para voltar ao menu...")

# ==============================
# MENUS
# ==============================

def menu_principal():
    while True:
        print("\nOlá, seja bem-vindo ao Nintendo Switch\n")
        print("1. Login")
        print("2. SignUp (Cadastro)")
        print("3. Desligar Switch")
        op = prompt("Escolha: ").strip()
        if op == "1":
            data = login()
            if data: menu_usuario(data)
        elif op == "2":
            data = signup()
            if data: menu_usuario(data)
        elif op == "3":
            print("Desligando...")
            sys.exit(0)
        else:
            print("Opção inválida.")

def menu_usuario(user):
    uid = user.get("user_id") or user.get("id")
    uname = user.get("name") or user.get("nome") or "Player"
    while True:
        print(f"\nOlá, {uname}!")
        print("1. Jogar Mario Kart (Online)")
        print("2. Jogar Mario Kart (Local)")
        print("3. Voltar ao menu")
        op = prompt("Escolha: ").strip()
        if op == "1":
            jogar_online(uid, uname)
        elif op == "2":
            jogar_local(uname)
        elif op == "3":
            return
        else:
            print("Opção inválida.")

def jogar_local(uname):
    catalog = get_catalog()
    minhas_escolhas = montar_kart_user(catalog)
    pista = escolha_pista_aleatoria(catalog)

    players = [{
        "id": "you",
        "name": uname,
        **minhas_escolhas,
    }]
    for i in range(7):
        build = pick_random_build(catalog)
        players.append({
            "id": f"bot-{i+1}",
            "name": f"Bot {i+1}",
            **build
        })

    print_resumo_corrida("Mario Kart (Local) — Grid de Largada", pista, players)
    run_race_flow(players, pista, "Preparar...", mode_str="local")

def jogar_online(uid, uname):
    catalog = get_catalog()
    minhas_escolhas = montar_kart_user(catalog)
    pista = escolha_pista_aleatoria(catalog)

    adversarios = []
    try:
        raw_users = lista_users_rdb(exclude_id=uid, limit=7)
        random.shuffle(raw_users)
        for u in raw_users[:7]:
            build = pick_random_build(catalog)
            adversarios.append({
                "id": u["id"],
                "name": u["name"],
                **build
            })
    except Exception as e:
        print("(Aviso) Falha ao buscar usuários no RDB, completando com bots:", e)

    while len(adversarios) < 7:
        build = pick_random_build(catalog)
        adversarios.append({
            "id": f"bot-{len(adversarios)+1}",
            "name": f"Bot {len(adversarios)+1}",
            **build
        })

    players = [{
        "id": uid or "you",
        "name": uname,
        **minhas_escolhas,
    }] + adversarios[:7]

    print_resumo_corrida("Mario Kart (Online) — Grid de Largada", pista, players)
    run_race_flow(players, pista, "Preparar...", mode_str="online")

# ==============================
# MAIN
# ==============================

if __name__ == "__main__":
    menu_principal()
