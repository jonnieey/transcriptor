from transcriptor.api import API

if __name__ == "__main__":
    name = "Client"
    email = "clientemail@gmail.com"
    rates = {"Normal": 0.4, "Expedite": 0.5, "Interpreted": 0.3}
    api = API()
    client = api.create_client(name, email, rates)
    api.save_client(client)
    # print(api.get_client_from_uuid(client.client_id))
    job = api.create_job(
        client_id=client.client_id,
        date_received="2022-05-05",
        job_number="56321",
        job_type="Normal",
        total_quantity="42.12630",
        job_rate="0.40",
        quantity="21.06315",
        date_due="2022-06-01",
        job_path="somerandompath",
    )
    api.save_job(job)
