#!/usr/bin/python3
import unittest
from datetime import date

from transcriptor.database import Database

today = date.today()


class TestDatabase(unittest.TestCase):
    def setup_class(self):
        self.db = Database(":memory:")

    def teardown_class(self):
        self.db.conn.close()

    def test_init_db(self):
        conn = self.db.init_db()
        # Check tables in database
        stmt = "SELECT name FROM sqlite_master WHERE type='table'"
        cur = conn.cursor()
        cur.execute(stmt)
        tables = cur.fetchall()
        self.assertEqual(len(tables), 3)
        # self.assertIn(("Clients",), tables)
        # self.assertIn(("Rates",), tables)
        # self.assertIn(("Jobs",), tables)

    def test_insert_dummy_rates(self):
        conn = self.db.init_db()
        cur = conn.cursor()

        # Dummy data for the Rates table
        rates_data = [
            {"normal": 0.50, "expedite": 0.70, "interpreted": 0.40},
            {"normal": 0.45, "expedite": 0.65, "interpreted": 0.35},
            {"normal": 0.55, "expedite": 0.75, "interpreted": 0.45},
        ]
        cur.executemany(
            "INSERT INTO rates (id, normal, expedite, interpreted) VALUES (NULL, :normal, :expedite, :interpreted)",
            rates_data,
        )
        conn.commit()
        stmt = "SELECT * FROM rates"
        rates = cur.execute(stmt).fetchall()
        self.assertEqual(len(rates), 3)

    def test_insert_dummy_clients(self):
        conn = self.db.init_db()
        # conn = init_db(":memory:")
        cur = conn.cursor()

        clients_data = [
            {"name": "John Doe", "email": "johndoe@example.com", "rates_id": 1},
            {"name": "Jane Smith", "email": "janesmith@example.com", "rates_id": 2},
            {
                "name": "Michael Johnson",
                "email": "michaeljohnson@example.com",
                "rates_id": 3,
            },
        ]
        cur.executemany(
            "INSERT INTO clients (id, name, email, rates_id) VALUES (NULL, :name, :email, :rates_id)",
            clients_data,
        )
        conn.commit()
        stmt = "SELECT * FROM clients"
        clients = cur.execute(stmt).fetchall()
        self.assertEqual(len(clients), 3)

    def test_insert_dummy_jobs(self):
        conn = self.db.init_db()
        # conn = init_db(":memory:")
        cur = conn.cursor()

        # Dummy data for the Jobs table
        jobs_data = [
            {
                "client_id": 1,
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
                "client_id": 2,
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
                "client_id": 3,
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
        conn.commit()
        stmt = "SELECT * FROM jobs"
        jobs = cur.execute(stmt).fetchall()
        self.assertEqual(len(jobs), 3)
        self.assertIsInstance(jobs[0]["date_received"], date)


#
# #
# # # Insert dummy data into the Jobs table
#
# #if __name__ == "__main__":
#
