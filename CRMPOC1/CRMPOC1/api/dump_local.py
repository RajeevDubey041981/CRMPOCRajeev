import json
from sqlalchemy import text
from app.database import engine
with engine.connect() as conn:
    q = "SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = DATABASE() ORDER BY TABLE_NAME, ORDINAL_POSITION"
    rows = conn.execute(text(q)).fetchall()
schema = {}
for r in rows:
    schema.setdefault(r[0], {})[r[1]] = {"type": r[2], "nullable": r[3], "default": str(r[4]) if r[4] is not None else None, "extra": r[5] or ""}
with open("/tmp/local_schema_full.json", "w") as f:
    json.dump(schema, f)
print(len(schema))
