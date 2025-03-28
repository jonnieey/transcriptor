#!/bin/bash
OLD_DB="$1"
NEW_DB="$2"

if [[ ! -f "$OLD_DB" ]]; then
  echo "old db not found"
  exit 1
fi
if [[ ! -f "$NEW_DB" ]]; then
  mkdir -p "$(dirname "$NEW_DB")"
  touch "$NEW_DB"
fi

sqlite3 "$NEW_DB" <<EOF
DROP TABLE IF EXISTS Clients;
DROP TABLE IF EXISTS Rates;
DROP TABLE IF EXISTS Jobs;
EOF

sqlite3 "$NEW_DB" < createdb.sql

sqlite3 -header -csv "$OLD_DB" <<EOF
.output rates.csv
SELECT r.id, r.normal, r.expedite, r.interpreted, c.rates_id FROM rates AS r JOIN clients AS c WHERE r.id = c.rates_id;
.output clients.csv
SELECT id, name, email FROM clients;
.output jobs.csv
SELECT * from jobs;
EOF

sqlite3 -csv "$NEW_DB" <<EOF
.import clients.csv clients
.import rates.csv rates
.import jobs.csv jobs
EOF

rm {jobs,clients,rates}.csv
