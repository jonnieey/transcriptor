import shutil
import tempfile
from pathlib import Path

from sqlalchemy import Row, inspect, select

from transcriptor.controller import API
from transcriptor.models import ClientModel, JobModel, RatesModel


class TestAPI:
    def setup_class(self):
        self.temp_dir = tempfile.mkdtemp()
        self.api = API(self.temp_dir)

    def teardown_class(self):
        shutil.rmtree(self.temp_dir)

    def test_API_init(self):
        # with TemporaryDirectory() as temp_dir:
        # api = API(base_dir=base_dir)
        assert Path(self.temp_dir).exists()
        assert Path(self.temp_dir).joinpath("transcriptor.db").exists()

        inspector = inspect(self.api.db.engine)
        assert "Rates" in inspector.get_table_names()
        assert "Clients" in inspector.get_table_names()
        assert "Jobs" in inspector.get_table_names()

    def test_client(self):

        stmt = select(ClientModel)
        assert self.api.session.execute(stmt).all() == []

        # Create a new client
        client = self.api.create_client(name="Alice", email="alice@example.com")

        # Save the client
        self.api.save_client(client)

        assert self.api.session.execute(stmt).all() != []

        # List all clients
        clients = self.api.list_clients()
        assert isinstance(clients, list)
        assert len(clients) == 1
        assert type(clients[0]) == Row
        assert clients[0]._mapping["ClientModel"].name == "Alice"

        # get a client
        client = self.api.list_clients(client_id=1)
        assert isinstance(client, list)

        # Edit the client's name and email
        self.api.edit_client(
            client_id=1,
            name="Alice Smith",
            email="alice.smith@example.com",
        )

        stmt = select(ClientModel).where(ClientModel.id == 1)
        updated_client = self.api.session.execute(stmt).scalar_one()

        # Check that the client's name and email have been updated
        assert updated_client.name == "Alice Smith"
        assert updated_client.email == "alice.smith@example.com"

        # Edit the client's rates
        self.api.edit_client(
            client_id=1,
            rates={"normal": 0.50, "expedite": 0.70, "interpreted": 0.40},
        )

        # Check that the client's rates have been updated
        stmt = select(RatesModel).filter_by(client=updated_client)
        updated_rates = self.api.session.execute(stmt).scalar_one()

        assert updated_rates.normal == 0.50
        assert updated_rates.expedite == 0.70
        assert updated_rates.interpreted == 0.40

        # delete the client
        self.api.delete_client(client_id=1)
        stmt = select(ClientModel)
        assert self.api.session.execute(stmt).all() == []

    def test_job(self):

        client = self.api.create_client(name="Alice", email="alice@example.com")

        # Save the client
        self.api.save_client(client)

        stmt = select(JobModel)
        assert self.api.session.execute(stmt).all() == []

        # Create a new job
        job = self.api.create_job(
            client_id=1,
            date_received="2020-01-01",
            job_number="123456",
            job_type="normal",
            total_quantity=10,
            job_rate=0.4,
            quantity=5,
            date_due="2020-01-02",
            job_path=f"path/to/clients/clientname/year/month/jobdir",
            note="note",
        )
        assert isinstance(job, JobModel)

        # Save the job
        self.api.save_job(job)

        assert self.api.session.execute(stmt).all() != []

        # List all jobs
        jobs = self.api.list_jobs()

        assert isinstance(jobs, list)
        assert len(jobs) == 1
        assert type(jobs[0]) == Row
        assert jobs[0]._mapping["JobModel"].note == "note"
        assert jobs[0]._mapping["JobModel"].amount == 2.0

        # Edit the job (update quantity)
        self.api.edit_job(job_id=1, quantity="15", note="Note2")

        # Retrieve the job from the database to verify that it was updated correctly
        stmt = select(JobModel).where(JobModel.id == 1)
        updated_job_model = self.api.session.execute(stmt).scalar_one()

        assert updated_job_model.job_type == "normal"
        assert updated_job_model.quantity == 15
        assert updated_job_model.job_rate == 0.4
        # amount is updated  if quantity or rate is updated
        assert updated_job_model.amount == 6.0
        assert updated_job_model.client_id == 1
        assert updated_job_model.note == "Note2"

        # Edit the job (update rate)
        self.api.edit_job(job_id=1, job_rate=0.55, note="Note2")
        updated_job_model = self.api.session.execute(stmt).scalar_one()
        assert updated_job_model.job_rate == 0.55
        assert updated_job_model.amount == 8.25

        # delete the job
        self.api.delete_job(job_id=1)
        stmt = select(JobModel)
        assert self.api.session.execute(stmt).all() == []
