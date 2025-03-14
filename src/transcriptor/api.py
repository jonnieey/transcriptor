from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, text
from sqlalchemy import update as sql_update
from sqlalchemy import delete as sql_delete

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

    def get(self, table, conditions=None, raw_sql_stmt=None):
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(raw_sql_stmt)
            return self.session.execute(raw_sql_stmt).mappings().all()

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

    def get_clients(self, conditions=None, raw_sql_stmt=None) -> list:
        if raw_sql_stmt is not None:
            raw_sql_stmt = f"""
                SELECT c.id AS client_id, c.name, c.email, r.normal, r.expedite, r.interpreted
                FROM clients AS c
                JOIN rates AS r ON c.id = r.client_id {raw_sql_stmt}"""
            return self.session.execute(text(raw_sql_stmt)).mappings().all()

        elif conditions is None:
            stmt = select(
                Client.id.label("client_id"),
                Client.name,
                Client.email,
                Rate.normal,
                Rate.expedite,
                Rate.interpreted,
            ).join(Rate, Client.id == Rate.client_id)

            return self.session.execute(stmt).mappings().all()

        return self.get(Client, conditions, raw_sql_stmt)

    def get_rates(self, conditions=None):
        return self.get(Rate, conditions)

    def get_jobs(self, conditions=None, raw_sql_stmt=None):
        if raw_sql_stmt is not None:
            raw_sql_stmt = f"""
             SELECT  j.client_id,  j.date_received, j.id AS job_id, j.job_number, j.job_type,
             j.status, j.date_due, j.total_quantity, j.quantity, j.job_rate,
             j.date_submitted, j.amount, j.amount_paid, j.note, j.job_path
             FROM JOBS AS j {raw_sql_stmt}
            """
            return self.session.execute(text(raw_sql_stmt)).mappings().all()

        return self.get(Job, conditions)

    def update(self, table, conditions=None, values=None, raw_sql_stmt=None):
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(raw_sql_stmt)
            self.session.execute(raw_sql_stmt)
            self.session.commit()
            return True

        if not all([conditions, values]):
            return False

        stmt = sql_update(table)
        try:
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
                        raise ValueError(
                            f"Invalid comparison operator: {comparison_op}"
                        )
                stmt = stmt.where(and_(*filters))
            stmt = stmt.values(**values)
            self.session.execute(stmt)
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            print(f"Error during update: {e}")
            return False

    def update_clients(self, conditions=None, values=None, raw_sql_stmt=None):
        return self.update(
            Client, conditions=conditions, values=values, raw_sql_stmt=raw_sql_stmt
        )

    def update_rates(self, conditions=None, values=None, raw_sql_stmt=None):
        return self.update(
            Rate, conditions=conditions, values=values, raw_sql_stmt=raw_sql_stmt
        )

    def update_jobs(self, conditions=None, values=None, raw_sql_stmt=None):
        return self.update(
            Job, conditions=conditions, values=values, raw_sql_stmt=raw_sql_stmt
        )

    def delete(self, table, conditions, raw_sql_stmt=None):
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(raw_sql_stmt)
            self.session.execute(raw_sql_stmt)
            self.session.commit()
            return True

        if not conditions:
            return False

        stmt = sql_delete(table)
        try:
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
                        raise ValueError(
                            f"Invalid comparison operator: {comparison_op}"
                        )
                stmt = stmt.where(and_(*filters))
            self.session.execute(stmt)
            self.session.commit()
            return True

        except Exception as e:
            self.session.rollback()
            print(f"Error during delete: {e}")
            return False

    def delete_clients(self, conditions=None, raw_sql_stmt=None):
        return self.delete(Client, conditions=conditions, raw_sql_stmt=raw_sql_stmt)

    def delete_jobs(self, conditions=None, raw_sql_stmt=None):
        return self.delete(Job, conditions=conditions, raw_sql_stmt=raw_sql_stmt)


if __name__ == "__main__":
    api = API(base_dir=Path(__file__).parent)
    print(
        len(
            api.get_clients(
                conditions={"name": [("~", "%vic%")], "id": [(">", 1), ("<", 5)]}
            )
        )
    )
