#!/usr/bin/python3
import unittest
from datetime import date

from transcriptor.database import Database

today = date.today()

unittest.TestLoader.sortTestMethodsUsing = None


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = Database(":memory:")
        self.db.init_db()
        self.conn = self.db.conn

    def tearDown(self):
        self.db.conn.close()

    def test_init_db(self):
        # conn = self.db.init_db()
        cur = self.conn.cursor()
        # Check tables in database
        stmt = "SELECT name FROM sqlite_master WHERE type='table'"
        # cur = conn.cursor()
        cur.execute(stmt)
        tables = cur.fetchall()
        self.assertEqual(len(tables), 3)
        # self.assertIn(("Clients",), tables)
        # self.assertIn(("Rates",), tables)
        # self.assertIn(("Jobs",), tables)

    def test_insert_rates(self):
        #     # conn = self.db.init_db()
        cur = self.conn.cursor()
        clients_data = {"name": "Mike John", "email": "micke@example.com"}
        cur.execute(
            "INSERT INTO clients (id, name, email) VALUES (NULL, :name, :email)",
            clients_data,
        )
        client_id = cur.lastrowid
        self.conn.commit()

        # Dummy data for the Rates table
        rates_data = [
            {
                "normal": 0.50,
                "expedite": 0.70,
                "interpreted": 0.40,
                "client_id": client_id,
            },
            {
                "normal": 0.45,
                "expedite": 0.65,
                "interpreted": 0.35,
                "client_id": client_id,
            },
            {
                "normal": 0.55,
                "expedite": 0.75,
                "interpreted": 0.45,
                "client_id": client_id,
            },
        ]
        cur.executemany(
            "INSERT INTO rates (id, normal, expedite, interpreted, client_id) VALUES (NULL, :normal, :expedite, :interpreted, :client_id)",
            rates_data,
        )
        self.conn.commit()
        stmt = "SELECT * FROM rates"
        rates = cur.execute(stmt).fetchall()
        self.assertEqual(len(rates), 3)

    def test_insert_clients(self):
        # conn = self.db.init_db()
        cur = self.conn.cursor()

        clients_data = {
            "name": "John Doe",
            "email": "johndoe@example.com",
            "rates_id": 1,
        }
        cur.execute(
            "INSERT INTO clients (id, name, email) VALUES (NULL, :name, :email)",
            clients_data,
        )
        client_id = cur.lastrowid
        self.conn.commit()

        rates_data = {
            "normal": 0.50,
            "expedite": 0.70,
            "interpreted": 0.40,
            "client_id": client_id,
        }
        cur.execute(
            "INSERT INTO rates (id, normal, expedite, interpreted, client_id) VALUES (NULL, :normal, :expedite, :interpreted, :client_id)",
            rates_data,
        )
        stmt = "SELECT * FROM rates"
        rates = cur.execute(stmt).fetchall()
        self.conn.commit()

        stmt = "SELECT * FROM clients"
        clients = cur.execute(stmt).fetchall()
        self.assertEqual(len(clients), 1)

    def test_insert_jobs(self):
        # conn = self.db.init_db()
        # conn = init_db(":memory:")
        cur = self.conn.cursor()
        clients_data = {"name": "John Doe", "email": "johndoe@example.com"}
        cur.execute(
            "INSERT INTO clients (id, name, email) VALUES (NULL, :name, :email)",
            clients_data,
        )
        client_id = cur.lastrowid
        self.conn.commit()

        rates_data = {
            "normal": 0.50,
            "expedite": 0.70,
            "interpreted": 0.40,
            "client_id": client_id,
        }
        cur.execute(
            "INSERT INTO rates (id, normal, expedite, interpreted, client_id) VALUES (NULL, :normal, :expedite, :interpreted, :client_id)",
            rates_data,
        )
        self.conn.commit()

        # Dummy data for the Jobs table
        jobs_data = [
            {
                "client_id": client_id,
                "date_received": today,
                "job_number": "JOB001",
                "job_type": "Translation",
                "date_due": "2023-06-15",
                "total_quantity": 1000.0,
                "quantity": 500.0,
                "job_rate": 0.50,
                "job_path": "/path/to/job1",
                "status": "Pending",
                "amount": 50.0,
            },
            {
                "client_id": client_id,
                "date_received": "2023-06-02",
                "job_number": "JOB002",
                "job_type": "Interpretation",
                "date_due": "2023-06-20",
                "total_quantity": 2000.0,
                "quantity": 1000.0,
                "job_rate": 0.45,
                "job_path": "/path/to/job2",
                "status": "Pending",
                "amount": 60.7,
            },
            {
                "client_id": client_id,
                "date_received": "2023-06-03",
                "job_number": "JOB003",
                "job_type": "Translation",
                "date_due": "2023-06-25",
                "total_quantity": 3000.0,
                "quantity": 1500.0,
                "job_rate": 0.55,
                "job_path": "/path/to/job3",
                "status": "Pending",
                "amount": 20.7,
            },
        ]
        #
        cur.executemany(
            "INSERT INTO jobs (id, client_id, date_received, job_number, job_type, date_due, total_quantity, quantity, job_rate, job_path, status, amount) VALUES (NULL, :client_id, :date_received, :job_number, :job_type, :date_due, :total_quantity, :quantity, :job_rate, :job_path, :status, :amount)",
            jobs_data,
        )
        self.conn.commit()
        stmt = "SELECT * FROM jobs"
        jobs = cur.execute(stmt).fetchall()
        self.assertEqual(len(jobs), 3)
        self.assertIsInstance(jobs[0]["date_received"], date)

    def test_zelete_clients(self):
        cur = self.conn.cursor()
        clients_data = {"name": "John Doe", "email": "johndoe@example.com"}
        cur.execute(
            "INSERT INTO clients (id, name, email) VALUES (NULL, :name, :email)",
            clients_data,
        )
        client_id = cur.lastrowid
        rates_data = {
            "normal": 0.50,
            "expedite": 0.70,
            "interpreted": 0.40,
            "client_id": client_id,
        }
        cur.execute(
            "INSERT INTO rates (id, normal, expedite, interpreted, client_id) VALUES (NULL, :normal, :expedite, :interpreted, :client_id)",
            rates_data,
        )
        rates_id = cur.lastrowid

        self.db.conn.execute("DELETE FROM clients WHERE id=?", (client_id,))
        self.conn.commit()

        cur.execute("SELECT * FROM rates WHERE id = ?", (rates_id,))
        rates = cur.fetchone()
        self.assertIsNone(rates)

    def test_db_triggers(self):
        cur = self.conn.cursor()
        clients_data = {"name": "John Doe", "email": "johndoe@example.com"}
        cur.execute(
            "INSERT INTO clients (id, name, email) VALUES (NULL, :name, :email)",
            clients_data,
        )
        client_id = cur.lastrowid
        self.conn.commit()

        rates_data = {
            "normal": 0.50,
            "expedite": 0.70,
            "interpreted": 0.40,
            "client_id": client_id,
        }
        cur.execute(
            "INSERT INTO rates (id, normal, expedite, interpreted, client_id) VALUES (NULL, :normal, :expedite, :interpreted, :client_id)",
            rates_data,
        )
        self.conn.commit()

        # Dummy data for the Jobs table
        jobs_data = [
            {
                "client_id": client_id,
                "date_received": today,
                "job_number": "JOB001",
                "job_type": "Translation",
                "date_due": "2023-06-15",
                "total_quantity": 1000.0,
                "quantity": 500.0,
                "job_rate": 0.50,
                "job_path": "/path/to/job1",
                "status": "Pending",
                "amount": 50.0,
            },
        ]
        cur.executemany(
            "INSERT INTO jobs (id, client_id, date_received, job_number, job_type, date_due, total_quantity, quantity, job_rate, job_path, status, amount) VALUES (NULL, :client_id, :date_received, :job_number, :job_type, :date_due, :total_quantity, :quantity, :job_rate, :job_path, :status, :amount)",
            jobs_data,
        )
        # TRIGGER update_amount
        # amount = job_rate * quantity
        query = "UPDATE Jobs SET job_rate = 0.10 WHERE id = 1"
        cur.execute(query)
        query = "SELECT * FROM Jobs WHERE id = 1"
        job = cur.execute(query).fetchone()
        assert job["amount"] == 0.10 * 500
        assert job["job_rate"] == 0.10

        # TRIGGER update_date
        query = "UPDATE Jobs SET status='Done' WHERE id = 1"
        cur.execute(query)
        query = "SELECT * FROM Jobs WHERE id = 1"
        job = cur.execute(query).fetchone()
        # returns date object
        assert job["date_submitted"] == today
        assert job["status"] == "Done"

        # TRIGGER update date
        query = "UPDATE Jobs SET status='Pending' WHERE id = 1"
        cur.execute(query)
        query = "SELECT * FROM Jobs WHERE id = 1"
        job = cur.execute(query).fetchone()
        assert job["date_submitted"] == None
        assert job["status"] == "Pending"

        # TRIGGER update_status
        query = "UPDATE Jobs SET date_submitted='2023-04-11' WHERE id = 1"
        cur.execute(query)
        query = "SELECT * FROM Jobs WHERE id = 1"
        job = cur.execute(query).fetchone()
        # returns date object
        assert job["date_submitted"].strftime("%Y-%m-%d") == "2023-04-11"
        assert job["status"] == "Done"

        # TRIGGER limit_amount_paid
        query = "UPDATE Jobs SET amount_paid=2000 WHERE id = 1"
        cur.execute(query)
        query = "SELECT * FROM Jobs WHERE id = 1"
        job = cur.execute(query).fetchone()
        # returns date object
        assert job["amount"] == job["amount_paid"]
