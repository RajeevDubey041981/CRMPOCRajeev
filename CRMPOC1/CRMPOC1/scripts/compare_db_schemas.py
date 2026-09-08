"""Compare local vs production MySQL schemas.

Outputs:
  scripts/.e2e-tmp/schema-local.json
  scripts/.e2e-tmp/schema-prod.json
  scripts/.e2e-tmp/schema-diff.json          (full diff)
  scripts/.e2e-tmp/schema-diff-actionable.json
  scripts/.e2e-tmp/schema-diff-report.md     (human-readable, actionable only)
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import paramiko

HOST = "97.74.83.211"
USER = "indcooladmin"
PASSWORD = "JAdJh@yg4SFDP#!nGH"
OUT_DIR = Path(__file__).resolve().parents[1] / "scripts" / ".e2e-tmp"
OUT_DIR.mkdir(parents=True, exist_ok=True)

TEXT_TYPES = {"text", "tinytext", "mediumtext", "longtext"}
INT_TYPES = {"int", "integer", "bigint", "smallint", "mediumint"}
FLOAT_TYPES = {"float", "double", "decimal", "numeric"}


def dump_local_schema() -> dict:
    py = r"""
import json
from sqlalchemy import create_engine, text
from app.config import settings

engine = create_engine(settings.get_database_url())
q = text('''
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION
''')
with engine.connect() as conn:
    rows = conn.execute(q).fetchall()
    version = conn.execute(text('SELECT version_num FROM alembic_version')).scalar()

schema = {}
for table, col, col_type, nullable, default, extra in rows:
    schema.setdefault(table, {})[col] = {
        "type": col_type,
        "nullable": nullable,
        "default": str(default) if default is not None else None,
        "extra": extra or "",
    }
print(json.dumps({"alembic_version": version, "tables": schema}))
"""
    proc = subprocess.run(
        ["docker", "exec", "crmpoc1-api-1", "python", "-c", py],
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(proc.stdout.strip())


def dump_prod_schema() -> dict:
    remote_py = r"""
import json, os, sys
from pathlib import Path
from sqlalchemy import create_engine, text

api_dir = Path('/var/www/indcool/api')
sys.path.insert(0, str(api_dir))
for line in (api_dir / '.env').read_text(encoding='utf-8').splitlines():
    line = line.strip()
    if not line or line.startswith('#') or '=' not in line:
        continue
    k, v = line.split('=', 1)
    os.environ[k.strip()] = v.strip()

from app.config import Settings
settings = Settings()
engine = create_engine(settings.get_database_url())
q = text('''
SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA
FROM information_schema.COLUMNS
WHERE TABLE_SCHEMA = DATABASE()
ORDER BY TABLE_NAME, ORDINAL_POSITION
''')
with engine.connect() as conn:
    rows = conn.execute(q).fetchall()
    version = conn.execute(text('SELECT version_num FROM alembic_version')).scalar()

schema = {}
for table, col, col_type, nullable, default, extra in rows:
    schema.setdefault(table, {})[col] = {
        "type": col_type,
        "nullable": nullable,
        "default": str(default) if default is not None else None,
        "extra": extra or "",
    }
print(json.dumps({"alembic_version": version, "tables": schema}))
"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()
    remote_path = "/tmp/schema_dump_prod.py"
    with sftp.file(remote_path, "w") as f:
        f.write(remote_py)
    sftp.close()
    _, stdout, stderr = client.exec_command(
        "sudo -u www-data env PYTHONPATH=/var/www/indcool/api "
        "/var/www/indcool/api/venv/bin/python /tmp/schema_dump_prod.py",
        get_pty=True,
    )
    out = stdout.read().decode("utf-8", "replace")
    err = stderr.read().decode("utf-8", "replace")
    client.close()
    if err.strip():
        print(err, file=sys.stderr)
    start = out.find("{")
    if start < 0:
        raise RuntimeError(f"No JSON from prod dump:\n{out}")
    return json.loads(out[start:])


def parse_column_type(col_type: str) -> tuple[str, int | None, int | None]:
    """Return (family, size_or_precision, scale) for a MySQL COLUMN_TYPE string."""
    raw = col_type.strip().lower()
    if raw.startswith("enum(") or raw.startswith("set("):
        return "enum", None, None

    match = re.match(r"^([a-z]+)(?:\(([^)]+)\))?$", raw)
    if not match:
        return raw, None, None

    family, args = match.group(1), match.group(2)
    if family == "varchar" and args:
        return "varchar", int(args.split(",")[0].strip()), None
    if family in {"char"} and args:
        return "char", int(args.split(",")[0].strip()), None
    if family in {"decimal", "numeric"} and args:
        parts = [p.strip() for p in args.split(",")]
        return family, int(parts[0]), int(parts[1]) if len(parts) > 1 else None
    if family == "datetime" and args:
        return "datetime", int(args), None
    if family == "timestamp" and args:
        return "timestamp", int(args), None
    if family == "int" and args:
        return "int", int(args), None
    if family == "tinyint" and args:
        return "tinyint", int(args), None
    return family, None, None


def normalize_default(default: str | None) -> str | None:
    if default is None:
        return None
    value = default.strip().lower()
    value = value.replace("current_timestamp(6)", "current_timestamp")
    value = re.sub(r"\s+", " ", value)
    return value or None


def normalize_extra(extra: str) -> str:
    value = (extra or "").strip().lower()
    value = value.replace("default_generated", "").strip()
    value = re.sub(r"\s+", " ", value)
    return value


def types_compatible(local_type: str, prod_type: str) -> bool:
    local_family, local_size, local_scale = parse_column_type(local_type)
    prod_family, prod_size, prod_scale = parse_column_type(prod_type)

    if local_family == prod_family == "datetime":
        return True
    if local_family == prod_family == "timestamp":
        return True
    if local_family in TEXT_TYPES and prod_family in TEXT_TYPES:
        return True
    if local_family in INT_TYPES and prod_family in INT_TYPES:
        return True
    if local_family in FLOAT_TYPES and prod_family in FLOAT_TYPES:
        if local_family != prod_family:
            return False
        return local_size == prod_size and local_scale == prod_scale
    if local_family == "varchar" and prod_family == "varchar":
        if local_size is None or prod_size is None:
            return True
        return prod_size >= local_size
    if local_family == "char" and prod_family == "char":
        if local_size is None or prod_size is None:
            return True
        return prod_size >= local_size
    if local_family == "tinyint" and prod_family == "tinyint":
        return True
    if local_family == "json" and prod_family == "json":
        return True
    if local_family == "blob" and prod_family in {"blob", "mediumblob", "longblob", "tinyblob"}:
        return True
    if local_family in {"blob", "mediumblob", "longblob"} and prod_family in {"blob", "mediumblob", "longblob", "tinyblob"}:
        return True

    return local_type.lower() == prod_type.lower()


def classify_column_diff(local_col: dict, prod_col: dict) -> str:
    """Return: 'ok', 'cosmetic', 'review', or 'actionable'."""
    if not types_compatible(local_col["type"], prod_col["type"]):
        local_family, _, _ = parse_column_type(local_col["type"])
        prod_family, _, _ = parse_column_type(prod_col["type"])
        # Column exists but storage family changed (e.g. json vs text) — review, not blocking.
        if {local_family, prod_family} <= (TEXT_TYPES | {"json"}):
            return "review"
        return "actionable"

    if local_col["nullable"] != prod_col["nullable"]:
        return "review"

    local_default = normalize_default(local_col["default"])
    prod_default = normalize_default(prod_col["default"])
    if local_default != prod_default:
        timestamp_defaults = {None, "current_timestamp", "now()"}
        if local_default in timestamp_defaults and prod_default in timestamp_defaults:
            return "cosmetic"
        return "review"

    if normalize_extra(local_col["extra"]) != normalize_extra(prod_col["extra"]):
        return "cosmetic"

    return "cosmetic"


def compare(local: dict, prod: dict) -> dict:
    local_tables = set(local["tables"])
    prod_tables = set(prod["tables"])
    missing_tables = sorted(local_tables - prod_tables)
    extra_tables = sorted(prod_tables - local_tables)

    missing_columns: list[dict] = []
    extra_columns: list[dict] = []
    cosmetic_mismatches: list[dict] = []
    review_mismatches: list[dict] = []
    actionable_mismatches: list[dict] = []

    for table in sorted(local_tables & prod_tables):
        local_cols = local["tables"][table]
        prod_cols = prod["tables"][table]
        for col in sorted(set(local_cols) - set(prod_cols)):
            missing_columns.append({"table": table, "column": col, "local": local_cols[col]})
        for col in sorted(set(prod_cols) - set(local_cols)):
            extra_columns.append({"table": table, "column": col, "prod": prod_cols[col]})
        for col in sorted(set(local_cols) & set(prod_cols)):
            local_col = local_cols[col]
            prod_col = prod_cols[col]
            if local_col == prod_col:
                continue
            item = {
                "table": table,
                "column": col,
                "local": local_col,
                "prod": prod_col,
            }
            bucket = classify_column_diff(local_col, prod_col)
            if bucket == "actionable":
                actionable_mismatches.append(item)
            elif bucket == "review":
                review_mismatches.append(item)
            else:
                cosmetic_mismatches.append(item)

    alembic_ok = local["alembic_version"] == prod["alembic_version"]
    needs_migration = bool(missing_tables or missing_columns or actionable_mismatches or not alembic_ok)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "local_alembic": local["alembic_version"],
        "prod_alembic": prod["alembic_version"],
        "alembic_in_sync": alembic_ok,
        "summary": {
            "missing_tables": len(missing_tables),
            "extra_tables": len(extra_tables),
            "missing_columns": len(missing_columns),
            "extra_columns": len(extra_columns),
            "cosmetic_mismatches": len(cosmetic_mismatches),
            "review_mismatches": len(review_mismatches),
            "actionable_mismatches": len(actionable_mismatches),
            "needs_migration": needs_migration,
        },
        "missing_tables": missing_tables,
        "extra_tables": extra_tables,
        "missing_columns": missing_columns,
        "extra_columns": extra_columns,
        "cosmetic_mismatches": cosmetic_mismatches,
        "review_mismatches": review_mismatches,
        "actionable_mismatches": actionable_mismatches,
    }


def write_report(diff: dict) -> None:
    lines = [
        "# DB Schema Comparison (Actionable)",
        "",
        f"Generated: {diff['generated_at']}",
        "",
        "## Summary",
        "",
        f"| Check | Local | Production |",
        f"|-------|-------|------------|",
        f"| Alembic | `{diff['local_alembic']}` | `{diff['prod_alembic']}` |",
        f"| Tables missing on prod | {diff['summary']['missing_tables']} | |",
        f"| Columns missing on prod | {diff['summary']['missing_columns']} | |",
        f"| Actionable type issues | {diff['summary']['actionable_mismatches']} | |",
        f"| Review-only drift (defaults/nullable) | {diff['summary']['review_mismatches']} | |",
        f"| Cosmetic differences (ignored) | {diff['summary']['cosmetic_mismatches']} | |",
        f"| **Needs migration** | **{'YES' if diff['summary']['needs_migration'] else 'NO'}** | |",
        "",
    ]

    if not diff["summary"]["needs_migration"]:
        lines.extend([
            "## Result",
            "",
            "Production schema is aligned with local for tables/columns. No column migration required.",
            "",
            "Cosmetic differences (datetime precision, text vs longtext, wider varchar on prod) were ignored.",
            "",
        ])
        if diff["review_mismatches"]:
            lines.extend([
                "## Review-only drift (no migration required)",
                "",
                "These are legacy default/nullable differences. The application sets values in code.",
                "",
            ])
            for item in diff["review_mismatches"][:15]:
                lines.append(
                    f"- `{item['table']}.{item['column']}`: "
                    f"local `{item['local']['type']}` / prod `{item['prod']['type']}`"
                )
            if len(diff["review_mismatches"]) > 15:
                lines.append(f"- ... and {len(diff['review_mismatches']) - 15} more (see schema-diff.json)")
            lines.append("")
    else:
        lines.append("## Action required\n")
        if diff["local_alembic"] != diff["prod_alembic"]:
            lines.append(
                f"- Alembic out of sync: local `{diff['local_alembic']}` vs prod `{diff['prod_alembic']}`. "
                "Run `alembic upgrade head` on production."
            )
        if diff["missing_tables"]:
            lines.append(f"- Missing tables on prod: {', '.join(diff['missing_tables'])}")
        if diff["missing_columns"]:
            lines.append("- Missing columns on prod:")
            for item in diff["missing_columns"]:
                lines.append(f"  - `{item['table']}.{item['column']}` ({item['local']['type']})")
        if diff["actionable_mismatches"]:
            lines.append("- Actionable column type differences:")
            for item in diff["actionable_mismatches"]:
                lines.append(
                    f"  - `{item['table']}.{item['column']}`: "
                    f"local `{item['local']['type']}` vs prod `{item['prod']['type']}`"
                )

    (OUT_DIR / "schema-diff-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    print("Dumping local schema...")
    local = dump_local_schema()
    (OUT_DIR / "schema-local.json").write_text(json.dumps(local, indent=2), encoding="utf-8")

    print("Dumping production schema...")
    prod = dump_prod_schema()
    (OUT_DIR / "schema-prod.json").write_text(json.dumps(prod, indent=2), encoding="utf-8")

    diff = compare(local, prod)
    (OUT_DIR / "schema-diff.json").write_text(json.dumps(diff, indent=2), encoding="utf-8")

    actionable = {
        k: diff[k]
        for k in (
            "generated_at",
            "local_alembic",
            "prod_alembic",
            "alembic_in_sync",
            "summary",
            "missing_tables",
            "missing_columns",
            "actionable_mismatches",
            "review_mismatches",
        )
    }
    (OUT_DIR / "schema-diff-actionable.json").write_text(
        json.dumps(actionable, indent=2),
        encoding="utf-8",
    )
    write_report(diff)

    s = diff["summary"]
    print("\n=== ACTIONABLE SCHEMA CHECK ===")
    print(f"Local alembic:           {diff['local_alembic']}")
    print(f"Prod alembic:            {diff['prod_alembic']}")
    print(f"Missing tables on prod:  {s['missing_tables']}")
    print(f"Missing columns on prod: {s['missing_columns']}")
    print(f"Actionable mismatches:   {s['actionable_mismatches']}")
    print(f"Review-only drift:       {s['review_mismatches']}")
    print(f"Cosmetic (ignored):      {s['cosmetic_mismatches']}")
    print(f"Needs migration:         {'YES' if s['needs_migration'] else 'NO'}")
    print(f"\nReport: {OUT_DIR / 'schema-diff-report.md'}")

    if diff["missing_tables"]:
        print("\nMissing tables:", ", ".join(diff["missing_tables"]))
    if diff["missing_columns"]:
        print("\nMissing columns:")
        for item in diff["missing_columns"]:
            print(f"  - {item['table']}.{item['column']} ({item['local']['type']})")
    if diff["actionable_mismatches"]:
        print("\nActionable mismatches:")
        for item in diff["actionable_mismatches"]:
            print(
                f"  - {item['table']}.{item['column']}: "
                f"local {item['local']['type']} vs prod {item['prod']['type']}"
            )

    return 1 if s["needs_migration"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
