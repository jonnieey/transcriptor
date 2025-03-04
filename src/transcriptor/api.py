from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select, update, delete, and_

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

    def add_client(self, client_dict) -> None:
        return self.add(Client, client_dict)

    def add_rates(self, rates) -> None:
        return self.add(Rate, rates)

    def add_job(self, job) -> None:
        return self.add(Job, job)

    def add_jobs(self, jobs):
        job_objects = [Job(**job_dict) for job_dict in jobs]
        self.session.add_all(job_objects)
        self.session.commit()

    def get(self, table, conditions=None):
        stmt = select(table)
        if conditions is None:
            return self.session.scalars(stmt).all()

        for column, conditions_list in conditions.items():
            column_attribute = getattr(table, column)
            op_map = {
                "<=": column_attribute.__le__,
                ">=": column_attribute.__ge__,
                "!=": column_attribute.__ne__,
                "<": column_attribute.__lt__,
                ">": column_attribute.__gt__,
                "=": column_attribute.__eq__,
                "==": column_attribute.__eq__,
                "~": column_attribute.ilike,
            }
            filters = []
            for comparison_op, comp_value in conditions_list:
                try:
                    filters.append(op_map[comparison_op](comp_value))
                except KeyError:
                    raise ValueError(f"Invalid comparison operator: {comparison_op}")
            stmt = stmt.filter(and_(*filters))

        return self.session.scalars(stmt).all()

    def get_clients(self, conditions=None) -> list:
        return self.get(Client, conditions)

    def get_rates(self, conditions=None):
        return self.get(Rate, conditions)

    def get_jobs(self, conditions=None):
        return self.get(Job, conditions)

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


if __name__ == "__main__":
    api = API(base_dir=Path(__file__).parent)
    print(
        len(
            api.get_clients(
                conditions={"name": [("~", "%vic%")], "id": [(">", 1), ("<", 5)]}
            )
        )
    )
