import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB  = os.getenv("MONGO_DB", "kart_db1")
FULL_DROP = os.getenv("FULL_DROP", "0") == "1"   # se "1", derruba o DB inteiro

def main():
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI não definido no ambiente.")

    # Conexão
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=6000)
    client.admin.command("ping")  # valida conectividade

    if FULL_DROP:
        # Derruba o banco inteiro (mais simples e garantia de limpeza total)
        client.drop_database(MONGO_DB)
        print(f"MongoDB (DB1): banco '{MONGO_DB}' removido por completo.")
        return

    # Modo padrão: remove todas as coleções existentes (ignorando as de sistema)
    db = client[MONGO_DB]
    cols = [c for c in db.list_collection_names() if not c.startswith("system.")]
    removed = 0
    for col in cols:
        db[col].drop()
        removed += 1

    print(f"MongoDB (DB1): {removed} coleção(ões) removida(s) em '{MONGO_DB}'.")
    if removed == 0:
        print("Nada para remover (já estava vazio ou só tinha coleções de sistema).")

if __name__ == "__main__":
    main()
