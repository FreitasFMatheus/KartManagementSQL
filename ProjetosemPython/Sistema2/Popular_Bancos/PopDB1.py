import os
from pymongo import MongoClient

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB  = os.getenv("MONGO_DB", "kart_db1")

DATA = {
  "characters": [
    {"name":"Mario","weight":"medium"},
    {"name":"Luigi","weight":"medium"},
    {"name":"Peach","weight":"light"},
    {"name":"Bowser","weight":"heavy"},
    {"name":"Yoshi","weight":"light"},
    {"name":"Toad","weight":"light"},
    {"name":"Donkey Kong","weight":"heavy"},
    {"name":"Wario","weight":"heavy"},
  ],
  "karts": [
    {"name":"Standard Kart","weight":2,"speed":3,"accel":3},
    {"name":"Pipe Frame","weight":1,"speed":2,"accel":4},
    {"name":"Mach 8","weight":2,"speed":4,"accel":2},
    {"name":"Steel Driver","weight":3,"speed":3,"accel":1},
    {"name":"Cat Cruiser","weight":2,"speed":3,"accel":3},
    {"name":"Circuit Special","weight":3,"speed":4,"accel":1},
    {"name":"Prancer","weight":2,"speed":3,"accel":2},
    {"name":"Biddybuggy","weight":1,"speed":1,"accel":5}
  ],
  "wheels": [
    {"name":"Standard","weight":1,"speed":2,"accel":2},
    {"name":"Slick","weight":2,"speed":3,"accel":1},
    {"name":"Roller","weight":0,"speed":1,"accel":4},
    {"name":"Azure Roller","weight":0,"speed":1,"accel":4},
    {"name":"Monster","weight":3,"speed":2,"accel":1},
    {"name":"Cyber Slick","weight":2,"speed":3,"accel":1},
    {"name":"Off-Road","weight":2,"speed":2,"accel":2},
    {"name":"Gold Tires","weight":3,"speed":3,"accel":1}
  ],
  "gliders": [
    {"name":"Super Glider","weight":1,"speed":2,"accel":2},
    {"name":"Paraglider","weight":1,"speed":2,"accel":2},
    {"name":"Wario Wing","weight":2,"speed":3,"accel":1},
    {"name":"Cloud Glider","weight":1,"speed":1,"accel":3},
    {"name":"Peach Parasol","weight":1,"speed":2,"accel":2},
    {"name":"Bowser Kite","weight":2,"speed":3,"accel":1},
    {"name":"Parachute","weight":1,"speed":1,"accel":3},
    {"name":"Plane Glider","weight":1,"speed":2,"accel":2}
  ],
  "tracks": [
    {"name":"Mario Kart Stadium"},
    {"name":"Water Park"},
    {"name":"Sweet Sweet Canyon"},
    {"name":"Thwomp Ruins"},
    {"name":"Mario Circuit"},
    {"name":"Toad Harbor"},
    {"name":"Twisted Mansion"},
    {"name":"Shy Guy Falls"}
  ]
}

def main():
    if not MONGO_URI: raise RuntimeError("MONGO_URI não definido")
    cli = MongoClient(MONGO_URI)
    db = cli[MONGO_DB]
    for col, items in DATA.items():
        c = db[col]
        c.create_index("name", unique=True)
        for it in items:
            c.update_one({"name": it["name"]}, {"$setOnInsert": it}, upsert=True)
    print(f"Mongo: populado/atualizado em '{MONGO_DB}' com 8 itens por coleção.")
if __name__ == "__main__":
    main()
