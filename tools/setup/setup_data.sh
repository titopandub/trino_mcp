#!/bin/bash
set -e

echo "Waiting for Trino to become available..."
max_attempts=20
attempt=0
while [ $attempt -lt $max_attempts ]; do
    if curl -s "http://localhost:9095/v1/info" > /dev/null; then
        echo "Trino is available!"
        break
    else
        attempt=$((attempt + 1))
        echo "Attempt $attempt/$max_attempts: Trino not yet available. Waiting 5 seconds..."
        sleep 5
    fi
done

if [ $attempt -eq $max_attempts ]; then
    echo "Failed to connect to Trino after multiple attempts"
    exit 1
fi

echo -e "\n=== Creating schema and table ==="
# Create a schema and table that points to our Parquet files
trino_query="
-- Create schema if it doesn't exist
CREATE SCHEMA IF NOT EXISTS bullshit.datasets
WITH (location = 'file:///opt/trino/data');

-- Create table pointing to our Parquet file
CREATE TABLE IF NOT EXISTS bullshit.datasets.employees
WITH (
  external_location = 'file:///opt/trino/data/bullshit_data.parquet',
  format = 'PARQUET'
)
AS SELECT * FROM parquet 'file:///opt/trino/data/bullshit_data.parquet';
"

# Execute the queries
echo "$trino_query" | curl -s -X POST -H "X-Trino-User: trino" --data-binary @- http://localhost:9095/v1/statement | jq

echo -e "\n=== Verifying data ==="
# Run a simple query to verify the table
curl -s -X POST -H "X-Trino-User: trino" --data "SELECT COUNT(*) FROM bullshit.datasets.employees" http://localhost:9095/v1/statement | jq
curl -s -X POST -H "X-Trino-User: trino" --data "SELECT * FROM bullshit.datasets.employees LIMIT 3" http://localhost:9095/v1/statement | jq

echo -e "\nSetup complete!" 