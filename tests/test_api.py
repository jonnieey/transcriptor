import shutil
import tempfile
import unittest

from transcriptor.api import API


class TestAPI(unittest.TestCase):
    def setup_class(self):
        self.temp_dir = tempfile.mkdtemp()
        self.api = API(self.temp_dir)

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_add_client(self):
        client_dict = {"name": "test_name", "email": "test_email"}
        self.api.add_clients(client_dict)
        clients = (
            self.api.conn.cursor().execute("SELECT * FROM clients").fetchall()
        )
        self.assertEqual(len(clients), 1)

    def test_add_rates(self):
        rates_dict = {
            "normal": 0.50,
            "expedite": 0.70,
            "interpreted": 0.40,
            "client_id": 1,
        }
        self.api.add_rates(rates_dict)
        rates = (
            self.api.conn.cursor().execute("SELECT * FROM rates").fetchall()
        )
        self.assertEqual(len(rates), 1)

    #
    def test_add_job(self):
        jobs_dict = (
            {
                "client_id": 1,
                "date_received": "2023-06-01",
                "job_number": "JOB001",
                "job_type": "Translation",
                "date_due": "2023-06-15",
                "total_quantity": 1000.0,
                "quantity": 500.0,
                "job_rate": 0.50,
                "job_path": "/path/to/job1",
                "status": "Pending",
                "amount": 50.0,
                "note": "Cannot be late",
            },
        )
        self.api.add_jobs(jobs_dict)
        jobs = self.api.conn.cursor().execute("SELECT * FROM jobs").fetchall()
        self.assertEqual(len(jobs), 1)

    def test_get_clients(self):
        clients = self.api.get_clients()
        self.assertEqual(len(clients), 1)
        self.assertIsInstance(clients[0], dict)

    def test_get_rates(self):
        rates = self.api.get_rates()
        self.assertEqual(len(rates), 1)
        self.assertIsInstance(rates[0], dict)

    def test_get_jobs(self):
        jobs = self.api.get_jobs()
        self.assertEqual(len(jobs), 1)
        self.assertIsInstance(jobs[0], dict)

    def test_update_client(self):
        self.api.update("Clients", ["name=tester"], ["id=1"])
        clients = (
            self.api.conn.cursor().execute("SELECT * FROM clients").fetchall()
        )
        self.assertEqual(len(clients), 1)
        self.assertEqual(clients[0]["name"], "tester")
        self.assertEqual(clients[0]["email"], "test_email")

    def delete_client(self):
        self.api.delete("Clients", {"id": 1})
        clients = (
            self.api.conn.cursor().execute("SELECT * FROM clients").fetchall()
        )
        self.assertEqual(len(clients), 0)
