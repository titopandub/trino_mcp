#!/bin/bash

# Wait for Trino to be ready
echo "Waiting for Trino to be ready..."
sleep 30

echo "Creating schema in memory catalog..."
docker exec -it trino_mcp_trino_1 trino --execute "CREATE SCHEMA IF NOT EXISTS memory.bullshit"

echo "Creating table with sample data..."
docker exec -it trino_mcp_trino_1 trino --execute "
CREATE TABLE memory.bullshit.bullshit_data AS
SELECT * FROM (
  VALUES
    (1, 'Sample 1', 10.5, 'A', TIMESTAMP '2023-01-01 12:00:00'),
    (2, 'Sample 2', 20.7, 'B', TIMESTAMP '2023-01-02 13:00:00'),
    (3, 'Sample 3', 15.2, 'A', TIMESTAMP '2023-01-03 14:00:00'),
    (4, 'Sample 4', 30.1, 'C', TIMESTAMP '2023-01-04 15:00:00'),
    (5, 'Sample 5', 25.8, 'B', TIMESTAMP '2023-01-05 16:00:00')
) AS t(id, name, value, category, created_at)
"

echo "Querying data from table..."
docker exec -it trino_mcp_trino_1 trino --execute "SELECT * FROM memory.bullshit.bullshit_data"

echo "Creating summary view..."
docker exec -it trino_mcp_trino_1 trino --execute "
CREATE OR REPLACE VIEW memory.bullshit.bullshit_summary AS
SELECT
  category,
  COUNT(*) as count,
  AVG(value) as avg_value,
  MIN(value) as min_value,
  MAX(value) as max_value
FROM
  memory.bullshit.bullshit_data
GROUP BY
  category
"

echo "Querying summary view..."
docker exec -it trino_mcp_trino_1 trino --execute "SELECT * FROM memory.bullshit.bullshit_summary ORDER BY count DESC"

echo "Setup complete." 