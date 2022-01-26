from dataclasses import dataclass

from transcriptor.job import Job


@dataclass
class ClientList:
    jobs_list: list
    client: dict

    def __post_init__(self):
        self.jobs_list = [Job.from_json(j) for j in self.jobs_list]

    def amount(self):
        return round(sum([d.amount for d in self.jobs_list]), 0)

    def amount_paid(self):
        return round(sum([d.amount_paid for d in self.jobs_list]), 0)

    def jobs(self):
        return self.jobs_list

    def headers(self):
        return [t for t in self.jobs_list[0].to_dict()]


@dataclass
class ClientLists:
    clients_jobs: list[ClientList]

    def __post_init__(self):
        self.length = len(self.clients_jobs)

    def amount(self):
        return round(sum([d.amount() for d in self.clients_jobs]), 0)

    def amount_paid(self):
        return round(sum([d.amount_paid() for d in self.clients_jobs]), 0)

    def jobs(self):
        jobs = []
        [jobs.extend(j.jobs_list) for j in self.clients_jobs]
        return jobs

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
