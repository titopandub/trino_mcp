#!/usr/bin/env python3
"""
Quick script to load our bullshit data directly into Trino using the memory connector
instead of relying on the Hive metastore which seems to be having issues.
"""
import pandas as pd
import trino
import time
import sys

# Configure Trino connection
TRINO_HOST = "localhost"
TRINO_PORT = 9095
TRINO_USER = "trino"
TRINO_CATALOG = "memory"

def main():
    print("🚀 Loading bullshit data into Trino...")
    
    # Load the parquet data
    try:
        print("Reading the bullshit data...")
        df = pd.read_parquet('data/bullshit_data.parquet')
        print(f"Loaded {len(df)} rows of bullshit data")
    except Exception as e:
        print(f"❌ Failed to load parquet data: {e}")
        sys.exit(1)

    # Connect to Trino
    print(f"Connecting to Trino at {TRINO_HOST}:{TRINO_PORT}...")
    
    # Try to connect with retries
    max_attempts = 10
    for attempt in range(1, max_attempts + 1):
        try:
            conn = trino.dbapi.connect(
                host=TRINO_HOST,
                port=TRINO_PORT,
                user=TRINO_USER,
                catalog=TRINO_CATALOG
            )
            print("✅ Connected to Trino")
            break
        except Exception as e:
            print(f"Attempt {attempt}/{max_attempts} - Failed to connect: {e}")
            if attempt == max_attempts:
                print("❌ Could not connect to Trino after multiple attempts")
                sys.exit(1)
            time.sleep(2)

    # Create cursor
    cursor = conn.cursor()
    
    try:
        # Create a schema
        print("Creating bullshit schema...")
        cursor.execute("CREATE SCHEMA IF NOT EXISTS memory.bullshit")
        
        # Drop tables if they exist (memory connector doesn't support CREATE OR REPLACE)
        print("Dropping existing tables if they exist...")
        try:
            cursor.execute("DROP TABLE IF EXISTS memory.bullshit.bullshit_data")
            cursor.execute("DROP TABLE IF EXISTS memory.bullshit.real_bullshit_data")
            cursor.execute("DROP VIEW IF EXISTS memory.bullshit.bullshit_summary")
        except Exception as e:
            print(f"Warning during table drops: {e}")
        
        # Create a sample table for our bullshit data
        print("Creating sample bullshit_data table...")
        cursor.execute("""
        CREATE TABLE memory.bullshit.bullshit_data (
            id BIGINT,
            job_title VARCHAR,
            name VARCHAR,
            salary BIGINT,
            bullshit_factor INTEGER,
            boolean_flag BOOLEAN,
            enum_field VARCHAR
        )
        """)
        
        # Insert sample data
        print("Inserting sample data...")
        cursor.execute("""
        INSERT INTO memory.bullshit.bullshit_data VALUES
        (1, 'CEO', 'Sample Data', 250000, 10, TRUE, 'Option A'),
        (2, 'CTO', 'More Examples', 225000, 8, TRUE, 'Option B'),
        (3, 'Developer', 'Testing Data', 120000, 5, FALSE, 'Option C')
        """)
        
        # Now we'll load real data from our dataframe
        # For memory connector, we need to create a new table with the data
        print("Creating real_bullshit_data table with our generated data...")
        
        # Take a subset of columns for simplicity
        cols = ['id', 'name', 'job_title', 'salary', 'bullshit_factor', 'bullshit_statement', 'company']
        df_subset = df[cols].head(100)  # Take just 100 rows to keep it manageable
        
        # Handle NULL values - replace with empty strings for strings and 0 for numbers
        df_subset = df_subset.fillna({
            'name': 'Anonymous', 
            'job_title': 'Unknown', 
            'bullshit_statement': 'No statement',
            'company': 'Unknown Co'
        })
        df_subset = df_subset.fillna(0)
        
        # Create the table structure
        cursor.execute("""
        CREATE TABLE memory.bullshit.real_bullshit_data (
            id BIGINT,
            job_title VARCHAR,
            name VARCHAR,
            salary DOUBLE,
            bullshit_factor DOUBLE,
            bullshit_statement VARCHAR,
            company VARCHAR
        )
        """)
        
        # Insert data in batches to avoid overly long SQL statements
        batch_size = 10
        total_batches = (len(df_subset) + batch_size - 1) // batch_size  # Ceiling division
        
        print(f"Inserting {len(df_subset)} rows in {total_batches} batches...")
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min(start_idx + batch_size, len(df_subset))
            batch = df_subset.iloc[start_idx:end_idx]
            
            # Create VALUES part of SQL statement for this batch
            values_list = []
            for _, row in batch.iterrows():
                # Clean string values to prevent SQL injection/syntax errors
                job_title = str(row['job_title']).replace("'", "''")
                name = str(row['name']).replace("'", "''")
                statement = str(row['bullshit_statement']).replace("'", "''")
                company = str(row['company']).replace("'", "''")
                
                values_str = f"({row['id']}, '{job_title}', '{name}', {row['salary']}, {row['bullshit_factor']}, '{statement}', '{company}')"
                values_list.append(values_str)
            
            values_sql = ", ".join(values_list)
            
            # Insert batch
            insert_sql = f"""
            INSERT INTO memory.bullshit.real_bullshit_data VALUES
            {values_sql}
            """
            cursor.execute(insert_sql)
            
            print(f"Batch {batch_num+1}/{total_batches} inserted.")
        
        # Create a summary view
        print("Creating summary view...")
        cursor.execute("""
        CREATE VIEW memory.bullshit.bullshit_summary AS
        SELECT
          job_title,
          COUNT(*) as count,
          AVG(salary) as avg_salary,
          AVG(bullshit_factor) as avg_bs_factor
        FROM
          memory.bullshit.real_bullshit_data
        GROUP BY
          job_title
        """)
        
        # Query to verify
        print("\nVerifying data with a query:")
        cursor.execute("SELECT * FROM memory.bullshit.bullshit_summary ORDER BY count DESC")
        
        # Print results
        columns = [desc[0] for desc in cursor.description]
        print("\n" + " | ".join(columns))
        print("-" * 80)
        
        rows = cursor.fetchall()
        for row in rows:
            print(" | ".join(str(cell) for cell in row))
        
        print(f"\n✅ Successfully loaded {len(df_subset)} rows of bullshit data into Trino!")
        print("You can now query it with: SELECT * FROM memory.bullshit.real_bullshit_data")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        cursor.close()
        conn.close()
        print("Connection closed")

if __name__ == "__main__":
    main() 