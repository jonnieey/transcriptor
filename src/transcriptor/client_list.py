from dataclasses import dataclass

from transcriptor.client import Client
from transcriptor.job import Job


@dataclass
class ClientList:
    jobs_list: list
    client: dict

    def __post_init__(self):
        self.jobs_list = [Job.from_json(j) for j in self.jobs_list]
        self.client = Client(**self.client)
        self.length = len(self.jobs_list)

    def all_jobs(self):
        return self.jobs_list

    def jobs(self):
        return [j for j in self.jobs_list if j.amount_paid < j.amount]

    def finished_jobs(self):
        return [j for j in self.jobs_list if j.amount_paid >= j.amount]

    def headers(self):
        return [t for t in self.jobs_list[0].to_dict()]

    def __len__(self):
        return len(self.jobs_list)

    def __iter__(self):
        self.current = 0
        return self

    def __next__(self):
        if self.current >= self.length:
            raise StopIteration
        to_return = self.jobs_list[self.current]
        self.current += 1
        return to_return


@dataclass
class ClientLists:
    clients_jobs: list[ClientList]

    def __post_init__(self):
        self.length = len(self.clients_jobs)

    def all_jobs(self):
        jobs = []
        [jobs.extend(j.jobs_list) for j in self.clients_jobs]
        return jobs

    def jobs(self):
        jobs = [
            job for j in self.clients_jobs for job in j if job.amount_paid < job.amount
        ]
        return jobs

    def finished_jobs(self):
        finished_jobs  = [
            job for j in self.clients_jobs for job in j if job.amount_paid >= job.amount
        ]
        return finished_jobs

    def clients(self):
        return [j.client for j in self.clients_jobs]

    def headers(self):
        return [t.headers() for t in self.clients_jobs][0]

    def __len__(self):
        return len(self.clients_jobs)

    def __iter__(self):
        self.current = 0
        return self

    def __next__(self):
        if self.current >= self.length:
            raise StopIteration
        to_return = self.clients_jobs[self.current]
        self.current += 1
        return to_return
