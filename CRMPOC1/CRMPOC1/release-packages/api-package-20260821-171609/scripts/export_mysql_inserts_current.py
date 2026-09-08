from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import MetaData, func, inspect, select

from app.database import engine

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "sql" / "mysql_inserts.sql"
FULL_TABLES = {"item_masters"}
SAMPLE_LIMIT = 5


def sql_literal(value: Any) -> str:
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, Decimal):
        return format(value, "f")
    if isinstance(value, datetime):
        return f"'{value.strftime('%Y-%m-%d %H:%M:%S')}'"
    if isinstance(value, date):
        return f"'{value.isoformat()}'"
    if isinstance(value, time):
        return f"'{value.strftime('%H:%M:%S')}'"
    if isinstance(value, (bytes, bytearray)):
        return "0x" + bytes(value).hex()
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{text}'"


def table_insert_sql(table, rows: list[dict[str, Any]], total_count: int) -> list[str]:
    lines = [f"-- Table: {table.name}"]
    if table.name in FULL_TABLES:
        lines.append(f"-- Export mode: full data ({total_count} row(s))")
    else:
        lines.append(f"-- Export mode: sample data ({len(rows)} of {total_count} row(s))")
    if not rows:
        lines.append(f"-- No live sample data in `{table.name}`")
        lines.append("")
        return lines

    column_names = [column.name for column in table.columns]
    column_sql = ", ".join(f"`{name}`" for name in column_names)
    lines.append(f"DELETE FROM `{table.name}`;")
    for row in rows:
        values_sql = ", ".join(sql_literal(row.get(column)) for column in column_names)
        lines.append(f"INSERT INTO `{table.name}` ({column_sql}) VALUES ({values_sql});")
    lines.append("")
    return lines


def export_mysql_inserts(output_path: Path = OUTPUT_PATH) -> Path:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    inspector = inspect(engine)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    script_lines = [
        "-- MySQL-compatible insert data generated from live local MySQL database",
        f"-- Database: {engine.url.database}",
        f"-- Date: {date.today().isoformat()}",
        f"-- Rule: full data for {', '.join(sorted(FULL_TABLES))}; sample up to {SAMPLE_LIMIT} row(s) for other tables",
        "",
        "SET FOREIGN_KEY_CHECKS=0;",
        "START TRANSACTION;",
        "",
    ]

    with engine.connect() as conn:
        for table in metadata.sorted_tables:
            pk_names = inspector.get_pk_constraint(table.name).get("constrained_columns", [])
            pk_cols = [table.c[name] for name in pk_names if name in table.c]
            stmt = select(table)
            if pk_cols:
                stmt = stmt.order_by(*pk_cols)
            total_count = conn.execute(select(func.count()).select_from(table)).scalar_one()
            if table.name not in FULL_TABLES:
                stmt = stmt.limit(SAMPLE_LIMIT)
            rows = [dict(row) for row in conn.execute(stmt).mappings().all()]
            script_lines.extend(table_insert_sql(table, rows, int(total_count)))

    script_lines.extend(["COMMIT;", "SET FOREIGN_KEY_CHECKS=1;", ""])
    output_path.write_text("\n".join(script_lines), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = export_mysql_inserts()
    print(path)
