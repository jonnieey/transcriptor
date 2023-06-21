from pathlib import Path

from transcriptor.database import Database
from transcriptor.utils import mkdirp
from transcriptor.utils import quote_values as qv


class API:
    # Create a new database if db not exists
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.db = Database(f"{base_dir}/transcriptor.db")
        mkdirp([self.base_dir])
        self.db.init_db()
        self.conn = self.db.conn
        self.cursor = self.db.conn.cursor()

    def add_clients(self, clients: tuple):
        stmt = "INSERT INTO clients (id, name, email, rates_id) VALUES (NULL, :name, :email, :rates_id)"
        self.cursor.execute(stmt, clients)
        self.conn.commit()
        return self.cursor.lastrowid

    def add_rates(self, rates: tuple):
        stmt = "INSERT INTO rates (id, normal, expedite, interpreted) VALUES (NULL, :normal, :expedite, :interpreted)"
        self.cursor.execute(stmt, rates)
        self.conn.commit()
        return self.cursor.lastrowid

    def add_jobs(self, jobs: tuple):
        columns = ", ".join(jobs[0].keys())
        placeholders = ", ".join(":" + column for column in jobs[0].keys())
        stmt = (
            "INSERT INTO jobs (id, " + columns + ") VALUES (NULL, " + placeholders + ")"
        )
        self.cursor.executemany(stmt, jobs)
        self.conn.commit()

    def get_clients(self, conditions=""):
        stmt = """
            SELECT c.id AS client_id, c.name, c.email, r.normal, r.expedite, r.interpreted
            FROM clients AS c
            JOIN rates AS r ON c.rates_id = r.id 
            """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]).split(" "))
            stmt += " WHERE " + searchstrs
        # if where:
        #     searchstrs = " and ".join(f"{pk}=:{pk}" for pk in where.keys())
        #     stmt += " WHERE " + searchstrs
        #     args += where.values()
        clients = self.cursor.execute(stmt).fetchall()
        return clients

    def get_rates(self):
        stmt = "SELECT * FROM rates"
        rates = self.cursor.execute(stmt).fetchall()
        return rates

    def get_jobs(self, conditions=""):
        # stmt = """
        # SELECT  c.id AS client_id,  j.date_received, j.id AS job_id, j.job_number, j.job_type,
        # j.status, j.date_due, j.total_quantity, j.quantity, j.job_rate,
        # j.date_submitted, j.amount, j.amount_paid, j.note
        # FROM jobs AS j
        # JOIN clients AS c ON j.client_id = c.id
        # UNION ALL
        # SELECT '', '', '', '', '', '', '', '', '', '', '', ROUND(SUM(amount), 2), ROUND(SUM(amount_paid), 2), ''
        # FROM jobs
        # ORDER BY j.id ASC
        # """
        stmt = """
         SELECT  j.client_id,  j.date_received, j.id AS job_id, j.job_number, j.job_type,
         j.status, j.date_due, j.total_quantity, j.quantity, j.job_rate,
         j.date_submitted, j.amount, j.amount_paid, j.note
         FROM JOBS AS j
        """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]).split(" "))
            stmt += " WHERE " + searchstrs

        jobs = self.cursor.execute(stmt).fetchall()
        return jobs

    # WITH ROLLUP;

    def update(
        self,
        table_name: str,
        set_conditions: str,
        search_conditions: str,
        other_conditions: str = "",
    ):
        # args = list(data.values())
        # set_clause = ", ".join(f"{column} = :{column}" for column in data.keys())
        setstr = ", ".join(qv(set_conditions[0]).split(" "))
        stmt = f"UPDATE {table_name} SET {setstr} "

        searchstrs = " and ".join(qv(search_conditions[0]).split(" "))
        stmt += " WHERE " + searchstrs

        if other_conditions:
            stmt += qv(other_conditions[0])

        # if where:
        #     searchstrs = " and ".join(f"{pk}=:{pk}" for pk in where.keys())
        #     stmt += " WHERE " + searchstrs
        #     args += where.values()

        self.cursor.execute(stmt)
        self.conn.commit()
        return self.cursor.lastrowid

    def delete(self, table_name: str, where: dict):
        stmt = f"DELETE FROM {table_name} WHERE {where}"
        self.cursor.execute(stmt)
        self.conn.commit()
