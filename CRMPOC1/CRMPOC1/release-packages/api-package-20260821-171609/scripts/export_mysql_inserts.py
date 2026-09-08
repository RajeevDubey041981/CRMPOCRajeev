from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.database import Base, SessionLocal
import app.models  # noqa: F401
import app.models.project  # noqa: F401


OUTPUT_PATH = Path(__file__).resolve().parents[1] / "sql" / "mysql_inserts.sql"


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
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace("'", "''")
    return f"'{text}'"


def table_insert_sql(table, rows: list[dict[str, Any]]) -> list[str]:
    lines = [f"-- Table: {table.name}"]
    if not rows:
        lines.append(f"-- No data in `{table.name}`")
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
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with SessionLocal() as session:
        script_lines = [
            "-- MySQL-compatible data export generated from the current application database",
            "SET FOREIGN_KEY_CHECKS=0;",
            "",
        ]

        for table in Base.metadata.sorted_tables:
            result = session.execute(select(table)).mappings().all()
            rows = [dict(row) for row in result]
            script_lines.extend(table_insert_sql(table, rows))

        script_lines.append("SET FOREIGN_KEY_CHECKS=1;")
        script_lines.append("")

    output_path.write_text("\n".join(script_lines), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = export_mysql_inserts()
    print(path)
