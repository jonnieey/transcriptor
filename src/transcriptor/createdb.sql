-- Create tables for transcriptor app
CREATE TABLE IF NOT EXISTS "Rates"  (
	id INTEGER PRIMARY KEY, 
	normal FLOAT NOT NULL, 
	expedite FLOAT NOT NULL, 
	interpreted FLOAT NOT NULL
);

CREATE TABLE IF NOT EXISTS "Clients"  (
	id INTEGER PRIMARY KEY, 
	name VARCHAR NOT NULL UNIQUE, 
	email VARCHAR NOT NULL, 
	rates_id INTEGER NOT NULL, 
	FOREIGN KEY(rates_id) REFERENCES "Rates" (id)
);
--
CREATE TABLE IF NOT EXISTS "Jobs"  (
	id INTEGER PRIMARY KEY, 
	client_id INTEGER, 
	date_received date NOT NULL, 
	job_number VARCHAR NOT NULL, 
	job_type VARCHAR NOT NULL, 
	status VARCHAR NOT NULL DEFAULT "Pending", 
	date_due date NOT NULL, 
	total_quantity FLOAT NOT NULL, 
	quantity FLOAT NOT NULL, 
	job_rate FLOAT NOT NULL, 
	date_submitted date, 
	amount FLOAT NOT NULL, 
	amount_paid FLOAT NOT NULL DEFAULT 0.0, 
	job_path VARCHAR(100) NOT NULL, 
	note VARCHAR NOT NULL DEFAULT "", 
	FOREIGN KEY(client_id) REFERENCES "Clients" (id)
);
