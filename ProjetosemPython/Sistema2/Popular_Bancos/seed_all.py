import subprocess, sys

CMDS = [
    ["python", "PopRDB.py"],
    ["python", "PopDB1.py"],
    ["python", "PopDB2.py"],
]

def run(cmd):
    print("\n$"," ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        print(f"ERRO ao executar: {' '.join(cmd)}")
        sys.exit(r.returncode)

def main():
    print("== SEED ALL ==")
    for c in CMDS:
        run(c)
    print("\n✅ Seed completo.")

if __name__ == "__main__":
    main()
