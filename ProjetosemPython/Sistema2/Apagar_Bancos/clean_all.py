import subprocess, sys

CMDS = [
    ["python", "UnpopDB2.py"],
    ["python", "UnpopDB1.py"],
    ["python", "UnpopRDB.py"],
]

def run(cmd):
    print("\n$"," ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(r.returncode)

if __name__ == "__main__":
    print("== CLEAN ALL ==")
    for c in CMDS:
        run(c)
    print("\n🧹 Limpeza completa.")
