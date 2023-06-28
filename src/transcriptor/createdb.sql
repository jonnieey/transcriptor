-- sqlite
-- Create tables for transcriptor app
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS "Rates"  (
	id INTEGER PRIMARY KEY, 
	normal FLOAT NOT NULL, 
	expedite FLOAT NOT NULL, 
	interpreted FLOAT NOT NULL,
	client_id INTEGER,
	FOREIGN KEY (client_id) REFERENCES "Clients" (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "Clients"  (
	id INTEGER PRIMARY KEY, 
	name VARCHAR NOT NULL UNIQUE, 
	email VARCHAR NOT NULL 
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
	FOREIGN KEY(client_id) REFERENCES "Clients" (id) ON DELETE CASCADE
);

CREATE TRIGGER IF NOT EXISTS update_amount
	AFTER UPDATE OF job_rate, quantity ON Jobs
BEGIN
	UPDATE Jobs
	SET amount = ROUND(NEW.quantity * NEW.job_rate, 2)
	WHERE id = NEW.id;
END;
--


CREATE TRIGGER IF NOT EXISTS update_date
	AFTER UPDATE OF status ON Jobs
BEGIN
	UPDATE Jobs
	SET 
		date_submitted = CASE
			WHEN NEW.status = 'Pending' THEN NULL
			WHEN NEW.status = 'Done' AND NEW.date_submitted IS NULL THEN DATE("NOW", 'localtime')
			ELSE date_submitted
		END
		WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_status
	AFTER UPDATE OF date_submitted ON Jobs
BEGIN
	UPDATE Jobs
	SET 
		status = CASE
			WHEN NEW.date_submitted IS NULL THEN 'Pending'
			WHEN NEW.date_submitted IS '' THEN 'Pending'
			WHEN DATE(NEW.date_submitted) IS NOT NULL THEN 'Done'
			ELSE status
		END
		WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS limit_amounts_paid
	AFTER UPDATE OF amount_paid ON Jobs
BEGIN
	UPDATE Jobs
	SET
		amount_paid = (
			CASE 
				WHEN NEW.amount_paid > Jobs.amount THEN Jobs.amount
				ELSE NEW.amount_paid
			END
		)
		WHERE Jobs.id = New.id;
END;

CREATE TRIGGER IF NOT EXISTS update_job_rates
	AFTER UPDATE OF client_id ON Jobs
BEGIN
	UPDATE Jobs
		SET job_rate = CASE
			WHEN LOWER(job_type) = 'normal' THEN (SELECT normal FROM Rates WHERE Rates.id = New.client_id)
			WHEN LOWER(job_type) = 'expedite' THEN (SELECT expedite FROM Rates WHERE Rates.id = New.client_id)
			WHEN LOWER(job_type) = 'interpreted' THEN (SELECT interpreted FROM Rates WHERE Rates.id = New.client_id)
			ELSE job_rate
		END
	WHERE id = NEW.id;
END;
