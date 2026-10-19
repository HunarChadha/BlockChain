from rocksdict import Rdict, Options, AccessType

DB_PATH = "ledger_db"

# open read-only so this script can't change anything by accident
db = Rdict(DB_PATH, options=Options(), access_type=AccessType.read_only())

print(f"=== Contents of {DB_PATH} ===\n")

counts = {}
for key, value in db.items():
    prefix = key.split(":", 1)[0] if isinstance(key, str) else "other"
    counts[prefix] = counts.get(prefix, 0) + 1
    print(f"{key}\n    -> {value}")

print("\n=== Summary ===")
for prefix, n in sorted(counts.items()):
    print(f"{prefix}: {n} entries")
print(f"total: {sum(counts.values())} entries")

db.close()