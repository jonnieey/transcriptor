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
            clients: tuple of (name, email)

        Returns:
            id of changed row or None
        """
        return self.execute_sql_with_args(
            "INSERT INTO clients (id, name, email) VALUES (NULL, :name, :email)",
            clients,
        )

    def add_rates(self, rates: tuple) -> Optional[int]:
        """
        Add rates to database

        Arguments:
            rates: tuple of (normal, expedite, interpreted)

        Returns:
            id of changed row or None
        """
        return self.execute_sql_with_args(
            "INSERT INTO rates (id, normal, expedite, interpreted, client_id) VALUES (NULL, :normal, :expedite, :interpreted, :client_id)",
            rates,
        )

    # TODO Rename this here and in `add_clients` and `add_rates`
    def execute_sql_with_args(self, arg0, arg1):
        stmt = arg0
        self.cursor.execute(stmt, arg1)
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
        placeholders = ", ".join(f":{column}" for column in jobs[0].keys())
        stmt = f"INSERT INTO jobs (id, {columns}) VALUES (NULL, {placeholders})"
        self.cursor.executemany(stmt, jobs)
        self.conn.commit()

    def get_clients(self, conditions: list[str] = None) -> list:
        """
        Get clients from database

        Arguments:
            conditions: search conditions

        Returns:
            list of dicts
        """
        if conditions is None:
            conditions = []
        stmt = """
            SELECT c.id AS client_id, c.name, c.email, r.normal, r.expedite, r.interpreted
            FROM clients AS c
            JOIN rates AS r ON c.id = r.client_id 
            """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]))
            stmt += f" WHERE {searchstrs}"
        return self.cursor.execute(stmt).fetchall()

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
        FROM rates AS r JOIN clients AS c ON c.id = r.client_id
        """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]))
            stmt += f" WHERE {searchstrs}"

        return self.cursor.execute(stmt).fetchall()

    def get_jobs(self, conditions: str = None, other_conditions: str = "") -> list:
        """
        Get jobs from database

        Arguments:
            conditions: search conditions

        Returns:
            list of dicts
        """
        if conditions is None:
            conditions = []
        stmt = """
         SELECT  j.client_id,  j.date_received, j.id AS job_id, j.job_number, j.job_type,
         j.status, j.date_due, j.total_quantity, j.quantity, j.job_rate,
         j.date_submitted, j.amount, j.amount_paid, j.note, j.job_path
         FROM JOBS AS j
        """
        if conditions:
            searchstrs = " and ".join(qv(conditions[0]))
            stmt += f" WHERE {searchstrs}"

        if other_conditions:
            stmt += other_conditions[0]
        return self.cursor.execute(stmt).fetchall()

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
        stmt += f" WHERE {searchstrs}"

        if other_conditions:
            stmt += other_conditions[0]

        self.cursor.execute(stmt)
        self.conn.commit()
        return self.cursor

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
        stmt += f" WHERE {searchstrs}"

        self.cursor.execute(stmt)
        self.conn.commit()
        return self.cursor.lastrowid
