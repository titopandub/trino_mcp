-- Setup Tables in Trino with Hive Metastore
-- This script creates necessary schemas and tables, then loads the Parquet data

-- Create a schema for our data
CREATE SCHEMA IF NOT EXISTS bullshit.raw;

-- Create a table for our parquet data
CREATE TABLE IF NOT EXISTS bullshit.raw.bullshit_data (
    id BIGINT,
    name VARCHAR,
    value DOUBLE,
    category VARCHAR,
    created_at TIMESTAMP
)
WITH (
    external_location = 'file:///opt/trino/data',
    format = 'PARQUET'
);

-- Show tables in our schema
SELECT * FROM bullshit.raw.bullshit_data LIMIT 10;

-- Create a view for convenience
CREATE OR REPLACE VIEW bullshit.raw.bullshit_summary AS
SELECT 
    category,
    COUNT(*) as count,
    AVG(value) as avg_value,
    MIN(value) as min_value,
    MAX(value) as max_value
FROM bullshit.raw.bullshit_data
GROUP BY category;

-- Query the view
SELECT * FROM bullshit.raw.bullshit_summary ORDER BY count DESC; 