from pathlib import Path
from typing import Optional

from transcriptor.database import Database
from transcriptor.utils import mkdirp
from transcriptor.utils import quote_operands as qv


class API:
    # Create a new database if db not exists
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.db = Database(f"{base_dir}/transcriptor.db")
        mkdirp([self.base_dir])
        self.db.init_db()
        self.conn = self.db.conn
        self.cursor = self.db.conn.cursor()

    def add_clients(self, clients: tuple) -> Optional[int]:
        """
        Add clients to database

        Arguments:
            clients: tuple of (name, email, rates_id)

        Returns:
            id of changed row or None
        """
        stmt = "INSERT INTO clients (id, name, email, rates_id) VALUES (NULL, :name, :email, :rates_id)"
        self.cursor.execute(stmt, clients)
        self.conn.commit()
        return self.cursor.lastrowid

    def add_rates(self, rates: tuple) -> Optional[int]:
        """
        Add rates to database

        Arguments:
            rates: tuple of (normal, expedite, interpreted)

        Returns:
            id of changed row or None
        """
        stmt = "INSERT INTO rates (id, normal, expedite, interpreted) VALUES (NULL, :normal, :expedite, :interpreted)"
        self.cursor.execute(stmt, rates)
        self.conn.commit()
        return self.cursor.lastrowid

    def add_jobs(self, jobs: tuple) -> None:
        """
        Add jobs to database

        Arguments:
            jobs: tuple of (client_id, date_received, id, job_number,
                    job_type, status, date_due, total_quantity, quantity,
                    job_rate, date_submitted, amount, amount_paid, note)
        """
        columns = ", ".join(jobs[0].keys())
        placeholders = ", ".join(":" + column for column in jobs[0].keys())
        stmt = (
            "INSERT INTO jobs (id, " + columns + ") VALUES (NULL, " + placeholders + ")"
        )
        self.cursor.executemany(stmt, jobs)
        self.conn.commit()

    def get_clients(self, conditions: str = "") -> list:
        """
        Get clients from database

        Arguments:
            conditions: search conditions

        Returns:
            list of dicts
        """
        stmt = """
            SELECT c.id AS client_id, c.name, c.email, r.normal, r.expedite, r.interpreted
            FROM clients AS c
            JOIN rates AS r ON c.rates_id = r.id 
            """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]))
            stmt += " WHERE " + searchstrs
        clients = self.cursor.execute(stmt).fetchall()
        return clients

    def get_rates(self, conditions: str = "") -> list:
        """
        Get rates from database

        Arguments:
            conditions: search conditions

        Returns:
            list of dicts
        """
        stmt = """
        SELECT c.name, r.id, r.normal, r.expedite, r.interpreted 
        FROM rates AS r JOIN clients AS c ON c.rates_id = r.id
        """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]))
            stmt += " WHERE " + searchstrs

        rates = self.cursor.execute(stmt).fetchall()
        return rates

    def get_jobs(self, conditions: str = "") -> list:
        """
        Get jobs from database

        Arguments:
            conditions: search conditions

        Returns:
            list of dicts
        """
        stmt = """
         SELECT  j.client_id,  j.date_received, j.id AS job_id, j.job_number, j.job_type,
         j.status, j.date_due, j.total_quantity, j.quantity, j.job_rate,
         j.date_submitted, j.amount, j.amount_paid, j.note
         FROM JOBS AS j
        """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]))
            stmt += " WHERE " + searchstrs

        jobs = self.cursor.execute(stmt).fetchall()
        return jobs

    def update(
        self,
        table_name: str,
        set_conditions: list,
        search_conditions: list,
        other_conditions: str = "",
    ) -> Optional[int]:
        """
        Update table values

        Arguments:
            table_name: name of table
            set_conditions: list of conditions to set
            search_conditions: list of conditions to search
            other_conditions: other conditions

        Returns:
            id of changed row
        """
        setstr = ", ".join(qv(set_conditions[0]))
        stmt = f"UPDATE {table_name} SET {setstr} "

        searchstrs = " and ".join(qv(search_conditions[0]))
        stmt += " WHERE " + searchstrs

        if other_conditions:
            stmt += other_conditions[0]

        self.cursor.execute(stmt)
        self.conn.commit()
        return self.cursor.lastrowid

    def delete(
        self,
        table_name: str,
        search_conditions: list,
    ) -> Optional[int]:
        """
        Delete rows from table

        Arguments:
            table_name: name of table
            search_conditions: list of conditions

        Returns:
            number of deleted rows
        """
        stmt = f"DELETE FROM {table_name} "

        searchstrs = " and ".join(qv(search_conditions[0]))
        stmt += " WHERE " + searchstrs

        self.cursor.execute(stmt)
        self.conn.commit()
        return self.cursor.lastrowid
