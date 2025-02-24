from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete

from transcriptor.database import Database
from transcriptor.models import Client, Rate, Job


DB_FILE_NAME = "transcriptor_sqlalchemy.db"


class API:
    def __init__(self, base_dir: Path):
        base_dir = Path(base_dir)
        if not base_dir.exists():
            base_dir.mkdir(parents=True)

        self.base_dir = base_dir
        self.db = Database(db_file=f"{base_dir}/{DB_FILE_NAME}")
        self.db.init_db()
        self.session = Session(self.db.engine)

    def add(self, table, data):
        obj = table(**data)
        self.session.add(obj)
        self.session.commit()
        return obj.id

    def add_client(self, client) -> None:
        return self.add(Client, client)

    def add_rates(self, rates) -> None:
        return self.add(Rate, rates)

    def add_job(self, job) -> None:
        return self.add(Job, job)

    def get(self, table, conditions=None):
        stmt = select(table)
        return self.session.scalars(stmt).all()

    def get_clients(self) -> list:
        return self.get(Client)

    def get_rates(self):
        return self.get(Rate)

    def get_jobs(self):
        return self.get(Job)

    def update(self, table, conditions, values):
        try:
            table_obj = table.__table__
            where_clauses = []

            for key, value in conditions.items():
                column = getattr(table, key)
                where_clauses.append(column == value)

            stmt = update(table_obj).where(*where_clauses).values(values)
            self.session.execute(stmt)
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            print(f"Error during update: {e}")
            return False

    def delete(self, table, conditions):
        try:
            table_obj = table.__table__
            where_clauses = []

            for key, value in conditions.items():
                column = getattr(table, key)
                where_clauses.append(column == value)

            stmt = delete(table_obj).where(*where_clauses)
            result = self.session.execute(stmt)

            if result.rowcount > 0:
                self.session.commit()
                return True
            else:
                print("Warning: No records matched the delete conditions.")
                return False

        except Exception as e:
            self.session.rollback()
            print(f"Error during delete: {e}")
            return False
