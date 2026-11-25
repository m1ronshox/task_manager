import argparse
from pathlib import Path

from sqlalchemy import create_engine, func, select, text

from database import Base, engine
from models import Task, User


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("backup", type=Path, help="Path to a consistent SQLite backup")
    args = parser.parse_args()

    if engine.dialect.name != "postgresql":
        parser.error("Set DATABASE_URL to the destination PostgreSQL database.")
    if not args.backup.is_file():
        parser.error("SQLite backup file does not exist.")

    sqlite = create_engine(f"sqlite:///{args.backup.resolve().as_uri()}?mode=ro&uri=true")
    with sqlite.connect() as source, engine.begin() as destination:
        Base.metadata.create_all(destination)
        destination.execute(text("LOCK TABLE users, tasks IN EXCLUSIVE MODE"))
        tables = (User.__table__, Task.__table__)
        if any(destination.scalar(select(func.count()).select_from(table)) for table in tables):
            parser.error("The destination users and tasks tables must be empty.")

        counts = {}
        for table in tables:
            rows = source.execute(select(table)).mappings().all()
            if rows:
                destination.execute(table.insert(), rows)
                next_id = max(row["id"] for row in rows) + 1
                destination.execute(text(f"ALTER SEQUENCE {table.name}_id_seq RESTART WITH {next_id}"))
            counts[table.name] = len(rows)

    print(f"Imported {counts['users']} users and {counts['tasks']} tasks.")


if __name__ == "__main__":
    main()
