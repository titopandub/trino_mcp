#!/usr/bin/env python3
"""
Set up the bullshit schema and table in Trino
"""
import os
import time
import trino
import pandas as pd
from trino.exceptions import TrinoExternalError

# Connect to Trino
def connect_to_trino():
    print("Waiting for Trino to become available...")
    max_attempts = 20
    attempt = 0
    while attempt < max_attempts:
        try:
            conn = trino.dbapi.connect(
                host="localhost",
                port=9095,
                user="trino",
                catalog="bullshit",
                schema="datasets",
            )
            
            # Test the connection
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            
            print("Trino is available!")
            return conn
        except Exception as e:
            attempt += 1
            print(f"Attempt {attempt}/{max_attempts}: Trino not yet available. Waiting 5 seconds... ({str(e)})")
            time.sleep(5)
    
    raise Exception("Failed to connect to Trino after multiple attempts")

# Create schema if it doesn't exist
def create_schema(conn):
    print("Creating schema if it doesn't exist...")
    with conn.cursor() as cursor:
        try:
            # Try to list tables in the schema to see if it exists
            try:
                cursor.execute("SHOW TABLES FROM bullshit.datasets")
                rows = cursor.fetchall()
                print(f"Schema already exists with {len(rows)} tables")
                return
            except Exception as e:
                pass  # Schema probably doesn't exist, continue to create it
                
            # Create schema
            cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS bullshit.datasets
            WITH (location = 'file:///bullshit-data')
            """)
            print("Schema created successfully")
        except Exception as e:
            print(f"Error creating schema: {e}")
            # Continue anyway, the error might be that the schema already exists

# Get table schema from parquet file
def get_parquet_schema():
    print("Reading parquet file to determine schema...")
    try:
        df = pd.read_parquet('data/bullshit_data.parquet')
        
        # Map pandas dtypes to Trino types
        type_mapping = {
            'int64': 'INTEGER',
            'int32': 'INTEGER',
            'float64': 'DOUBLE',
            'float32': 'DOUBLE',
            'object': 'VARCHAR',
            'bool': 'BOOLEAN',
            'datetime64[ns]': 'TIMESTAMP',
        }
        
        columns = []
        for col_name, dtype in df.dtypes.items():
            trino_type = type_mapping.get(str(dtype), 'VARCHAR')
            columns.append(f'"{col_name}" {trino_type}')
        
        return columns
    except Exception as e:
        print(f"Error reading parquet file: {e}")
        return None

# Create the table
def create_table(conn, columns):
    print("Creating table...")
    columns_str = ",\n        ".join(columns)
    sql = f"""
    CREATE TABLE IF NOT EXISTS bullshit.datasets.employees (
        {columns_str}
    )
    WITH (
        external_location = 'file:///bullshit-data/bullshit_data.parquet',
        format = 'PARQUET'
    )
    """
    print("SQL:", sql)
    
    with conn.cursor() as cursor:
        try:
            cursor.execute(sql)
            print("Table created successfully")
        except Exception as e:
            print(f"Error creating table: {e}")

# Verify table was created by running a query
def verify_table(conn):
    print("Verifying table creation...")
    with conn.cursor() as cursor:
        try:
            cursor.execute("SELECT * FROM bullshit.datasets.employees LIMIT 5")
            rows = cursor.fetchall()
            print(f"Successfully queried table with {len(rows)} rows")
            
            if rows:
                print("First row:")
                for row in rows:
                    print(row)
                    break
        except Exception as e:
            print(f"Error verifying table: {e}")

def main():
    try:
        conn = connect_to_trino()
        print("Connecting to Trino...")
        
        create_schema(conn)
        
        columns = get_parquet_schema()
        if columns:
            create_table(conn, columns)
            verify_table(conn)
        else:
            print("Failed to get table schema from parquet file")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main() 