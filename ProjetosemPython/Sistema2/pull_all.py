import subprocess, sys

CMDS = [
    ["python", "PullRDB.py"],
    ["python", "PullDB1.py"],
    ["python", "PullDB2.py"],
]

def run(cmd):
    print("\n$"," ".join(cmd))
    r = subprocess.run(cmd)
    if r.returncode != 0:
        sys.exit(r.returncode)

if __name__ == "__main__":
    print("== PULL ALL ==")
    for c in CMDS:
        run(c)
    print("\n✅ Pull completo.")
