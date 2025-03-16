from pathlib import Path
from sqlalchemy import select, and_, text
from sqlalchemy import update as sql_update
from sqlalchemy import delete as sql_delete

from transcriptor.database import Database
from transcriptor.models import Client, Rate, Job
from sqlalchemy.orm import sessionmaker


DB_FILE_NAME = "transcriptor_sqlalchemy.db"


class API:
    def __init__(self, base_dir):
        base_dir = Path(base_dir)
        if not base_dir.exists():
            base_dir.mkdir(parents=True)

        self.base_dir = base_dir
        self.db = Database(db_file=f"{base_dir}/{DB_FILE_NAME}")
        self.session = sessionmaker(self.db.engine, expire_on_commit=False)
        self.db.init_db()

    def add(self, table, data):
        obj = table(**data)
        with self.session() as session:
            session.add(obj)
            session.commit()
        return obj.id

    def add_client(self, client_dict):
        return self.add(Client, client_dict)

    def add_rates(self, rates):
        return self.add(Rate, rates)

    def add_job(self, job):
        return self.add(Job, job)

    def add_jobs(self, jobs):
        job_objects = [Job(**job_dict) for job_dict in jobs]
        with self.session() as session:
            session.add_all(job_objects)
            session.commit()

    def _build_statement_with_conditions(self, table, conditions, stmt_type="select"):
        """Builds a SQL statement with conditions."""
        if not conditions:
            return False

        if stmt_type == "select":
            stmt = select(table)
        elif stmt_type == "update":
            stmt = sql_update(table)
        elif stmt_type == "delete":
            stmt = sql_delete(table)
        else:
            raise ValueError("Invalid stmt_type.  Must be select, update, or delete")

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
                if stmt_type == "select":
                    stmt = stmt.filter(and_(*filters))
                else:
                    stmt = stmt.where(and_(*filters))
            return stmt
        except Exception as e:
            self.session.rollback()
            print(f"Error during {stmt_type}: {e}")
            return False

    def get(self, table, conditions=None, raw_sql_stmt=None):
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(raw_sql_stmt)
            return raw_sql_stmt

        if conditions is None:
            stmt = select(table)
            return stmt

        return self._build_statement_with_conditions(table, conditions, "select")

    def get_clients(self, conditions=None, raw_sql_stmt=None) -> list:
        if raw_sql_stmt is not None:
            raw_sql_stmt = f"""
                SELECT id, name, email
                FROM clients {raw_sql_stmt}"""
            stmt = self.get(table=Client, raw_sql_stmt=raw_sql_stmt)
            with self.session() as session:
                return session.execute(stmt).mappings().all()

        if conditions is None:
            stmt = select(
                Client.id,
                Client.name,
                Client.email,
            )
            with self.session() as session:
                return session.execute(stmt).mappings().all()

        stmt = self.get(Client, conditions, raw_sql_stmt)
        with self.session() as session:
            scalars = session.scalars(stmt).all()
            ordination = {"id", "name", "email"}
            client_mappings = [
                {col: getattr(client, col) for col in ordination} for client in scalars
            ]

            return client_mappings

    def get_rates(self, conditions=None):
        ordination = ["id", "client_id", "normal", "expedite", "interpreted"]
        stmt = self.get(Rate, conditions)
        with self.session() as session:
            scalars = session.scalars(stmt).all()
            rate_mappings = [
                {col: getattr(rate, col) for col in ordination if hasattr(rate, col)}
                for rate in scalars
            ]
            return rate_mappings

    def get_jobs(self, conditions=None, raw_sql_stmt=None):
        ordination = [
            "id",
            "date_received",
            "client",
            "client_id",
            "job_number",
            "job_type",
            "status",
            "date_due",
            "total_quantity",
            "quantity",
            "job_rate",
            "date_submitted",
            "amount",
            "amount_paid",
            "note",
            "job_path",
        ]
        if raw_sql_stmt is not None:
            raw_sql_stmt = f"""
             SELECT {', '.join(ordination)} FROM JOBS {raw_sql_stmt}
            """
            stmt = self.get(table=Job, raw_sql_stmt=raw_sql_stmt)
            with self.session() as session:
                return session.execute(stmt).mappings().all()

        stmt = self.get(Job, conditions)
        with self.session() as session:
            scalars = session.scalars(stmt).all()
            job_mappings = [
                {col: getattr(job, col) for col in ordination if hasattr(job, col)}
                for job in scalars
            ]
            return job_mappings

    def update(self, table, conditions=None, values=None, raw_sql_stmt=None):
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(f"UPDATE {table.__tablename__} {raw_sql_stmt}")
            return raw_sql_stmt

        if not all([conditions, values]):
            return False

        stmt = self._build_statement_with_conditions(table, conditions, "update")
        if stmt is None:
            return False
        try:
            stmt = stmt.values(**values)
            return stmt

        except Exception as e:
            self.session.rollback()
            print(f"Error during update: {e}")
            return False

    def update_clients(self, conditions=None, values=None, raw_sql_stmt=None):
        stmt = self.update(
            Client, conditions=conditions, values=values, raw_sql_stmt=raw_sql_stmt
        )
        with self.session() as session:
            session.execute(stmt)
            session.commit()
            return True

    def update_rates(self, conditions=None, values=None, raw_sql_stmt=None):
        stmt = self.update(
            Rate, conditions=conditions, values=values, raw_sql_stmt=raw_sql_stmt
        )
        with self.session() as session:
            session.execute(stmt)
            session.commit()
            return True

    def update_jobs(self, conditions=None, values=None, raw_sql_stmt=None):
        stmt = self.update(
            Job, conditions=conditions, values=values, raw_sql_stmt=raw_sql_stmt
        )
        with self.session() as session:
            session.execute(stmt)
            session.commit()
            return True

    def delete(self, table, conditions, raw_sql_stmt=None):
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(f"DELETE FROM {table.__tablename__} {raw_sql_stmt}")
            return raw_sql_stmt

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
            return stmt

        except Exception as e:
            self.session.rollback()
            print(f"Error during delete: {e}")
            return False

    def delete_clients(self, conditions=None, raw_sql_stmt=None):
        stmt = self.delete(Client, conditions=conditions, raw_sql_stmt=raw_sql_stmt)
        stmt = stmt.returning(Client.id, Client.name)
        with self.session() as session:
            clients = session.execute(stmt).mappings().all()
            session.commit()
            return clients

    def delete_jobs(self, conditions=None, raw_sql_stmt=None):
        stmt = self.delete(Job, conditions=conditions, raw_sql_stmt=raw_sql_stmt)
        with self.session() as session:
            jobs = session.execute(stmt).mappings().all()
            session.commit()
            return jobs


if __name__ == "__main__":
    api = API(base_dir=Path(__file__).parent)
    print(
        len(
            api.get_clients(
                conditions={"name": [("~", "%vic%")], "id": [(">", 1), ("<", 5)]}
            )
        )
    )
