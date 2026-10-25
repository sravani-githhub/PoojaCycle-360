"""Read-only, section-by-section viewer for the local SQLite prototype."""
import json
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("poojacycle360.db")
SECTIONS = {
    "Collection and pickup": ["waste_sources", "waste_types", "waste_reports", "collection_assignments"],
    "Batch processing and impact": ["waste_batches", "processing_records", "impact_records"],
    "ArtisanConnect": ["artisans", "artisan_material_requests"],
    "Eco Store": ["products", "product_batches"],
    "Orders": ["orders", "order_items"],
    "Users": ["users"],
    "Database migrations": ["alembic_version"],
}


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Run the backend once, then run this viewer again.")
        return

    print(f"SQLite database: {DB_PATH}\n")
    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        existing = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        for section, tables in SECTIONS.items():
            present = [table for table in tables if table in existing]
            if not present:
                continue
            print(f"{'=' * 12} {section} {'=' * 12}")
            for table in present:
                quoted = '"' + table.replace('"', '""') + '"'
                rows = connection.execute(f"SELECT * FROM {quoted} ORDER BY 1 LIMIT 50").fetchall()
                total = connection.execute(f"SELECT COUNT(*) FROM {quoted}").fetchone()[0]
                print(f"\n{table.replace('_', ' ').title()} — {total} record(s)")
                if not rows:
                    print("  No records saved yet.")
                    continue
                for row in rows:
                    values = dict(row)
                    record_id = values.pop("id", None)
                    values.pop("password_hash", None)
                    print(f"  Record #{record_id}" if record_id is not None else "  Record")
                    shown = False
                    for key, value in values.items():
                        if value is None:
                            continue
                        shown = True
                        if isinstance(value, (int, float)):
                            formatted = str(value)
                        else:
                            try:
                                formatted = json.dumps(value, ensure_ascii=False, default=str)
                            except TypeError:
                                formatted = str(value)
                        print(f"    {key.replace('_', ' ').title()}: {formatted}")
                    if not shown:
                        print("    (No optional values set)")
            print()


if __name__ == "__main__":
    main()
