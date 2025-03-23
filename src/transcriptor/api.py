from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from sqlalchemy import and_
from sqlalchemy import delete as sql_delete
from sqlalchemy import select, text
from sqlalchemy import update as sql_update
from sqlalchemy.engine.row import RowMapping
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql.dml import Delete, Update
from sqlalchemy.sql.elements import TextClause
from sqlalchemy.sql.selectable import Select

from transcriptor.database import Database
from transcriptor.models import Client, Job, Rate

DB_FILE_NAME = "transcriptor5.db"


class API:
    def __init__(self, base_dir: Path | str) -> None:
        """Initializes the API with a base directory and sets up the database connection.
        Args:
            base_dir (str): The base directory where data will be stored.
        """
        base_dir = Path(base_dir)
        base_dir.mkdir(parents=True, exist_ok=True)

        self.base_dir = base_dir
        self.db = Database(db_file=f"{base_dir}/{DB_FILE_NAME}")
        self.session = sessionmaker(self.db.engine, expire_on_commit=False)
        self.db.init_db()

    def add(self, table: object, data: dict) -> int:
        """Adds a new record to the specified table.

        Args:
            table (sqlalchemy.ext.declarative.api.DeclarativeMeta): The SQLAlchemy table class to add the record to.
            data (dict): A dictionary containing the data for the new record.  Keys should correspond to column names in the table.

        Returns:
            int: The ID of the newly created record.
        """
        obj = table(**data)  # type: ignore
        with self.session() as session:
            session.add(obj)
            session.commit()
        return obj.id

    def add_client(self, client_dict: dict) -> int:
        """Adds a new client to the database.

        Args:
            client_dict (dict): A dictionary containing the client's information.

        Returns:
            int: The ID of the newly created client record.

        """
        return self.add(Client, client_dict)

    def add_rates(self, rates_dict: dict) -> int:
        """Adds rates to the database.

        Args:
            rates_dict (dict): A dictionary where keys are rate identifiers and values
                are dictionaries containing rate information

        Returns:
            int: The ID of the newly created rates record.
        """
        return self.add(Rate, rates_dict)

    def add_job(self, job_dict: dict) -> int:
        """Adds a single job to the database.

        Args:
            job_dict (dict): A dictionary containing the job details.

        Returns:
            int: The ID of the newly added job.
        """
        return self.add(Job, job_dict)

    def add_jobs(self, jobs: list[dict]) -> None:
        """Adds multiple jobs to the database in a single session.

        Args:
            jobs (list[dict]): A list of dictionaries, where each dictionary
                represents a job and contains the job details.

        Returns:
            None
        """
        job_objects = [Job(**job_dict) for job_dict in jobs]
        with self.session() as session:
            session.add_all(job_objects)
            session.commit()

    def _build_statement_with_conditions(
        self,
        table: Union[Type[Rate], Type[Job], Type[Client]],
        conditions: Optional[
            Dict[
                str,
                Union[
                    List[
                        Union[
                            Tuple[str, str], Tuple[str, int], Tuple[str, date]
                        ]
                    ],
                    List[Tuple[str, int]],
                    List[Tuple[str, str]],
                    List[Union[Tuple[str, str], Tuple[str, int]]],
                ],
            ]
        ] = None,
        stmt_type: str = "select",
    ) -> Union[Select, Update, Delete, bool]:
        """Builds a SQL statement with conditions.

        Args:
            table (sqlalchemy.Table): The SQLAlchemy table object to build
              the statement for.
            conditions (dict[str, list[tuple[str, typing.Any]]]): A dictionary
            where keys are column names and values are lists of tuples.
              Each tuple in the list represents a condition for that column,
              with the first element being the comparison operator and the
              second element being the value to compare against.
                Example: `{"column_name": [("=", "value"), (">", 10)]}`
            stmt_type (str, optional): The type of SQL statement to build.
              Must be one of "select", "update", or "delete". Defaults to "select".

        Returns:
            sqlalchemy.sql.expression.Select or sqlalchemy.sql.expression.Update
              or sqlalchemy.sql.expression.Delete or False:

        Raises:
            ValueError: If `stmt_type` is not one of "select", "update", or "delete".
            ValueError: If an invalid comparison operator is used in the `conditions`.

        Example:
            To build a SELECT statement:
            ```python
            conditions = {"age": [(">=", 18), ("<", 65)], "city": [("=", "New York")]}
            statement = _build_statement_with_conditions(table, conditions)
            # statement will be a SQLAlchemy select object equivalent to:
            # SELECT * FROM my_table WHERE age >= 18 AND age < 65 AND city = "New York"
            ```

            To build an UPDATE statement:
            ```python
            table = my_table  # SQLAlchemy table object
            conditions = {"age": [(">=", 18), ("<", 65)], "city": [("=", "New York")]}
            statement = _build_statement_with_conditions(table, conditions, stmt_type="update")
            # statement will be a SQLAlchemy update object equivalent to:
            # UPDATE my_table SET ... WHERE age >= 18 AND age < 65 AND city = "New York"
            ```

            To build a DELETE statement:
            ```python
            table = my_table  # SQLAlchemy table object
            conditions = {"age": [(">=", 18), ("<", 65)], "city": [("=", "New York")]}
            statement = _build_statement_with_conditions(table, conditions, stmt_type="delete")
            # statement will be a SQLAlchemy delete object equivalent to:
            # DELETE FROM my_table WHERE age >= 18 AND age < 65 AND city = "New York"
            ```
        """
        if not conditions:
            return False

        if stmt_type == "select":
            stmt = select(table)
        elif stmt_type == "update":
            stmt = sql_update(table)  # type: ignore
        elif stmt_type == "delete":
            stmt = sql_delete(table)  # type: ignore
        else:
            raise ValueError(
                "Invalid stmt_type.  Must be select, update, or delete"
            )

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
            # self.session.rollback()
            print(f"Error during {stmt_type}: {e}")
            return False

    def get(
        self,
        table: Union[Type[Rate], Type[Job], Type[Client]],
        conditions: Optional[
            Union[
                Dict[str, List[Tuple[str, str]]],
                Dict[
                    str,
                    List[
                        Union[
                            Tuple[str, str], Tuple[str, int], Tuple[str, date]
                        ]
                    ],
                ],
                Dict[str, List[Tuple[str, int]]],
                Dict[str, List[Union[Tuple[str, str], Tuple[str, int]]]],
            ]
        ] = None,
        raw_sql_stmt: Optional[str] = None,
    ) -> Union[Select, TextClause]:
        if raw_sql_stmt is not None:
            raw_stmt = text(raw_sql_stmt)
            return raw_stmt

        if conditions is None:
            stmt = select(table)
            return stmt

        # type: ignore
        return self._build_statement_with_conditions(
            table, conditions, "select"
        )

    def get_clients(
        self,
        conditions: Optional[Dict[str, List[Tuple[str, int]]]] = None,
        raw_sql_stmt: Optional[str] = None,
    ) -> Union[List[Dict[str, Any]], Sequence[RowMapping]]:
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
                {col: getattr(client, col) for col in ordination}
                for client in scalars
            ]

            return client_mappings

    def get_rates(
        self, conditions: Optional[Dict[str, List[Tuple[str, int]]]] = None
    ) -> List[Dict[str, Union[int, float]]]:
        ordination = ["id", "client_id", "normal", "expedite", "interpreted"]
        stmt = self.get(Rate, conditions)
        with self.session() as session:
            scalars = session.scalars(stmt).all()
            rate_mappings = [
                {
                    col: getattr(rate, col)
                    for col in ordination
                    if hasattr(rate, col)
                }
                for rate in scalars
            ]
            return rate_mappings

    def get_jobs(
        self,
        conditions: Optional[
            Dict[
                str,
                Union[
                    List[
                        Union[
                            Tuple[str, str], Tuple[str, int], Tuple[str, date]
                        ]
                    ],
                    List[Tuple[str, str]],
                    List[Union[Tuple[str, str], Tuple[str, int]]],
                ],
            ]
        ] = None,
        raw_sql_stmt: None = None,
    ) -> List[
        Union[
            Dict[str, Optional[Union[int, str, Client, float]]],
            Dict[str, Union[int, str, Client, float]],
            Any,
        ]
    ]:
        ordination = [
            "id",
            "job_number",
            "client",
            "client_id",
            "date_received",
            "date_due",
            "job_type",
            "status",
            "date_submitted",
            "total_quantity",
            "quantity",
            "job_rate",
            "amount",
            "amount_paid",
            "note",
            "job_path",
        ]
        columns = ", ".join(
            ["jobs." + col for col in ordination if col != "client"]
        )

        if raw_sql_stmt is not None:
            raw_sql_stmt = f"""
            SELECT
                jobs.id as job_id, {columns},
                clients.id AS client_id, clients.name AS client_name, clients.email AS client_email
            FROM
                jobs
            JOIN
                clients ON jobs.client_id = clients.id
            {raw_sql_stmt}
            """
            stmt = self.get(table=Job, raw_sql_stmt=raw_sql_stmt)
            with self.session() as session:
                jobs = []
                rows = session.execute(stmt).mappings().all()
                for row in rows:
                    job = {
                        col: row[col] for col in ordination if col != "client"
                    }
                    client = Client(
                        id=row["client_id"],
                        name=row["client_name"],
                        email=row["client_email"],
                    )
                    job["client"] = client
                    jobs.append(job)

                return jobs

        stmt = self.get(Job, conditions)  # type: ignore
        with self.session() as session:
            scalars = session.scalars(stmt).all()
            job_mappings = [
                {
                    col: getattr(job, col)
                    for col in ordination
                    if hasattr(job, col)
                }
                for job in scalars
            ]
            return job_mappings

    def update(
        self,
        table: Union[Type[Rate], Type[Job], Type[Client]],
        conditions: Optional[Dict[str, List[Tuple[str, int]]]] = None,
        values: Optional[Dict[str, str]] = None,
        raw_sql_stmt: None = None,
    ) -> Union[Select[Any], Update, Delete, bool]:
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(
                f"UPDATE {table.__tablename__} {raw_sql_stmt}"
            )
            return raw_sql_stmt

        if not all([conditions, values]):
            return False

        stmt = self._build_statement_with_conditions(
            table, conditions, "update"
        )  # type: ignore
        if stmt is None:
            return False
        try:
            stmt = stmt.values(**values)  # type: ignore
            return stmt

        except Exception as e:
            # self.session.rollback()
            print(f"Error during update: {e}")
            return False

    def update_clients(
        self,
        conditions: Optional[Dict[str, List[Tuple[str, int]]]] = None,
        values: Optional[Dict[str, str]] = None,
        raw_sql_stmt: None = None,
    ) -> bool:
        stmt = self.update(
            Client,
            conditions=conditions,
            values=values,
            raw_sql_stmt=raw_sql_stmt,
        )
        with self.session() as session:
            session.execute(stmt)  # type: ignore
            session.commit()
            return True

    def update_rates(
        self,
        conditions: Optional[Dict[str, List[Tuple[str, int]]]] = None,
        values: Optional[Dict[str, str]] = None,
        raw_sql_stmt: None = None,
    ):
        stmt = self.update(
            Rate,
            conditions=conditions,
            values=values,
            raw_sql_stmt=raw_sql_stmt,
        )
        with self.session() as session:
            session.execute(stmt)  # type: ignore
            session.commit()
            return True

    def update_jobs(
        self,
        conditions: Optional[Dict[str, List[Tuple[str, int]]]] = None,
        values: Optional[Dict[str, str]] = None,
        raw_sql_stmt: None = None,
    ):
        stmt = self.update(
            Job,
            conditions=conditions,
            values=values,
            raw_sql_stmt=raw_sql_stmt,
        )
        with self.session() as session:
            session.execute(stmt)  # type: ignore
            session.commit()
            return True

    def delete(
        self,
        table: Type[Client],
        conditions: Optional[Dict[str, List[Tuple[str, str]]]],
        raw_sql_stmt: None = None,
    ) -> Delete | bool:
        if raw_sql_stmt is not None:
            raw_sql_stmt = text(
                f"DELETE FROM {table.__tablename__} {raw_sql_stmt}"
            )
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
            # self.session.rollback()
            print(f"Error during delete: {e}")
            return False

    def delete_clients(
        self,
        conditions: Optional[Dict[str, List[Tuple[str, str]]]] = None,
        raw_sql_stmt: None = None,
    ) -> Sequence[RowMapping]:
        stmt = self.delete(
            Client, conditions=conditions, raw_sql_stmt=raw_sql_stmt
        )
        stmt = stmt.returning(Client.id, Client.name)  # type: ignore
        with self.session() as session:
            clients = session.execute(stmt).mappings().all()  # type: ignore
            session.commit()
            return clients

    def delete_jobs(self, conditions=None, raw_sql_stmt=None):
        stmt = self.delete(
            Job, conditions=conditions, raw_sql_stmt=raw_sql_stmt
        )
        stmt = stmt.returning(Job.job_path)
        with self.session() as session:
            jobs = session.execute(stmt).mappings().all()
            session.commit()
            return jobs


# if __name__ == "__main__":
#     api = API(base_dir=Path(__file__).parent)
#     print(
#         len(
#             api.get_clients(
#                 conditions={
#                     "name": [("~", "%vic%")],
#                     "id": [(">", 1), ("<", 5)],
#                 }
#             )
#         )
#     )
