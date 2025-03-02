#!/usr/bin/env python3
"""
Create a bullshit parquet file full of random silly data for Trino to query.
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string

# Make this shit reproducible
random.seed(42069)
np.random.seed(42069)

def random_company_name():
    """Generate a ridiculous startup name."""
    prefixes = ["Block", "Hash", "Crypto", "Data", "Quantum", "Neural", "Cloud", "Cyber", "Meta", "Digital", 
                "AI", "ML", "Algo", "Bit", "Logic", "Hyper", "Ultra", "Deep", "Sync", "Tech"]
    suffixes = ["Chain", "Flow", "Mind", "Logic", "Base", "Scale", "Cube", "Stream", "Grid", "Verse", 
                "Net", "Ware", "Hub", "Pulse", "Sense", "Node", "Edge", "Core", "Link", "Matrix"]
    
    return f"{random.choice(prefixes)}{random.choice(suffixes)}"

def random_bullshit_job_title():
    """Generate a bullshit job title."""
    prefix = ["Chief", "Senior", "Lead", "Global", "Dynamic", "Principal", "Executive", "Head of", 
              "Director of", "VP of", "Distinguished", "Advanced", "Master", "Innovation", "Transformation"]
    middle = ["Digital", "Data", "Blockchain", "AI", "Experience", "Product", "Solutions", "Technical", 
              "Strategic", "Cloud", "Enterprise", "Creative", "Platform", "Innovation", "Disruption"]
    suffix = ["Officer", "Architect", "Evangelist", "Guru", "Ninja", "Rockstar", "Wizard", "Jedi", 
              "Explorer", "Catalyst", "Visionary", "Storyteller", "Hacker", "Champion", "Designer"]
    
    return f"{random.choice(prefix)} {random.choice(middle)} {random.choice(suffix)}"

def random_email(name):
    """Generate a random email based on a name."""
    domains = ["gmail.com", "hotmail.com", "yahoo.com", "outlook.com", "icloud.com", 
               "protonmail.com", "example.com", "bullshit.io", "fakeaf.dev", "notreal.net"]
    
    name_part = name.lower().replace(" ", "")
    return f"{name_part}{random.randint(1, 999)}@{random.choice(domains)}"

def random_ip():
    """Generate a random IP address."""
    return f"{random.randint(1, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"

def random_name():
    """Generate a random person name."""
    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer", "Michael", "Linda", 
                   "William", "Elizabeth", "David", "Susan", "Richard", "Jessica", "Joseph", "Sarah", 
                   "Thomas", "Karen", "Charles", "Nancy", "Skyler", "Jesse", "Walter", "Saul", "Mike"]
    
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", 
                  "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson", 
                  "White", "Goodman", "Pinkman", "Fring", "Ehrmantraut", "Schrader", "Wexler"]
    
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def random_sentence():
    """Generate a random bullshit sentence."""
    subjects = ["Our company", "The team", "This product", "The algorithm", "Our platform", "The API", 
                "Our solution", "The dashboard", "Our methodology", "The framework", "This breakthrough"]
    
    verbs = ["leverages", "utilizes", "implements", "optimizes", "integrates", "streamlines", "facilitates", 
             "enables", "empowers", "revolutionizes", "disrupts", "transforms", "synergizes with"]
    
    adjectives = ["cutting-edge", "next-generation", "state-of-the-art", "innovative", "advanced", 
                  "robust", "scalable", "agile", "dynamic", "intuitive", "seamless", "bleeding-edge"]
    
    nouns = ["blockchain", "AI", "machine learning", "cloud computing", "big data", "IoT", "microservices", 
             "neural networks", "quantum computing", "edge computing", "digital transformation", "DevOps"]
    
    benefits = ["increasing efficiency", "maximizing ROI", "driving growth", "boosting productivity", 
                "enhancing performance", "reducing overhead", "optimizing workflows", "minimizing downtime", 
                "accelerating innovation", "enabling scalability", "facilitating collaboration"]
    
    return f"{random.choice(subjects)} {random.choice(verbs)} {random.choice(adjectives)} {random.choice(nouns)} for {random.choice(benefits)}."

def generate_bullshit_data(num_rows=1000):
    """Generate a DataFrame of complete bullshit data."""
    print(f"Generating {num_rows} rows of absolute bullshit...")
    
    # Generate random data
    data = {
        "id": list(range(1, num_rows + 1)),
        "name": [random_name() for _ in range(num_rows)],
        "email": [],  # Will fill after generating names
        "company": [random_company_name() for _ in range(num_rows)],
        "job_title": [random_bullshit_job_title() for _ in range(num_rows)],
        "salary": np.random.normal(150000, 50000, num_rows).astype(int),  # Ridiculously high tech salaries
        "bullshit_factor": np.random.randint(1, 11, num_rows),  # On a scale of 1-10
        "ip_address": [random_ip() for _ in range(num_rows)],
        "created_at": [(datetime.now() - timedelta(days=random.randint(0, 365 * 3))).strftime('%Y-%m-%d %H:%M:%S') for _ in range(num_rows)],
        "last_active": [(datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d %H:%M:%S') for _ in range(num_rows)],
        "account_status": np.random.choice(['active', 'inactive', 'suspended', 'pending'], num_rows, p=[0.7, 0.1, 0.1, 0.1]),
        "login_count": np.random.randint(1, 1000, num_rows),
        "buzzword_quota": np.random.randint(5, 100, num_rows),
        "bullshit_statement": [random_sentence() for _ in range(num_rows)],
        "favorite_framework": np.random.choice(['React', 'Angular', 'Vue', 'Svelte', 'Django', 'Flask', 'Spring', 'Rails'], num_rows),
        "preferred_language": np.random.choice(['Python', 'JavaScript', 'Java', 'C#', 'Go', 'Rust', 'TypeScript', 'Ruby'], num_rows),
        "coffee_consumption": np.random.randint(1, 10, num_rows),  # Cups per day
        "meeting_hours": np.random.randint(0, 40, num_rows),  # Hours per week
        "actual_work_hours": np.random.randint(0, 40, num_rows),  # Hours per week
        "bugs_created": np.random.randint(0, 100, num_rows),
        "bugs_fixed": [], # Will calculate after bugs_created
        "productivity_score": np.random.rand(num_rows) * 100,
        "gitlab_commits": np.random.negative_binomial(5, 0.5, num_rows), # Most people commit very little
        "stackoverflow_reputation": np.random.exponential(1000, num_rows).astype(int),
        "random_float": np.random.rand(num_rows) * 100,
        "boolean_flag": np.random.choice([True, False], num_rows),
        "enum_field": np.random.choice(['Option A', 'Option B', 'Option C', 'Option D'], num_rows),
        "null_percentage": np.random.rand(num_rows) * 100,
    }
    
    # Generate dependent fields
    for i in range(num_rows):
        # Email based on name
        data["email"].append(random_email(data["name"][i]))
        
        # Bugs fixed is some percentage of bugs created
        fix_rate = random.uniform(0.5, 1.2)  # Sometimes they fix more bugs than they create!
        data["bugs_fixed"].append(int(data["bugs_created"][i] * fix_rate))
    
    # Create DataFrame
    df = pd.DataFrame(data)
    
    # Add some NULL values for realism
    for col in df.columns:
        if col != 'id':  # Keep id intact
            null_mask = np.random.random(num_rows) < 0.05  # 5% chance of NULL
            df.loc[null_mask, col] = None
    
    return df

def main():
    """Main function to create and save the bullshit data."""
    # Create data directory if it doesn't exist
    data_dir = "data"
    os.makedirs(data_dir, exist_ok=True)
    
    # Generate bullshit data
    df = generate_bullshit_data(num_rows=10000)  # 10,000 rows of pure nonsense
    
    # Save as parquet
    parquet_path = os.path.join(data_dir, "bullshit_data.parquet")
    df.to_parquet(parquet_path, index=False)
    print(f"Saved bullshit data to {parquet_path}")
    
    # Print some sample data
    print("\nSample of the bullshit data:")
    print(df.head())
    
    # Print column info
    print("\nColumn data types:")
    print(df.dtypes)
    
    # Print basic stats
    print("\nBasic statistics:")
    print(df.describe())
    
    # Also save as CSV for easy inspection
    csv_path = os.path.join(data_dir, "bullshit_data.csv")
    df.to_csv(csv_path, index=False)
    print(f"Also saved as CSV to {csv_path} for easy inspection")

if __name__ == "__main__":
    main() 