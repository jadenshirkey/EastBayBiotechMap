#!/usr/bin/env python3
"""Check database for source of data quality issues"""

import sqlite3
import pandas as pd

# Connect to database
conn = sqlite3.connect("data/bayarea_biotech_sources.db")

# Check the problematic companies
query = """
SELECT
    company_id,
    company_name,
    google_address,
    address,
    city
FROM companies
WHERE company_name IN ('Intuitive Surgical', 'GE HealthCare', 'Curebase')
ORDER BY company_name
"""

df = pd.read_sql_query(query, conn)
print("Source data for problematic companies:")
print("=" * 80)
for _, row in df.iterrows():
    print(f"\nCompany: {row['company_name']}")
    print(f"  Company ID: {row['company_id']}")
    print(f"  Google Address: {row['google_address']}")
    print(f"  Address: {row['address']}")
    print(f"  City: {row['city']}")

conn.close()