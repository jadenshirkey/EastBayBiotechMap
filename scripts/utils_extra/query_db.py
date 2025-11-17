#!/usr/bin/env python3
"""
Interactive database query tool for Bay Area Biotech database
Usage: python query_db.py
"""

import sqlite3
import pandas as pd
import sys
from pathlib import Path

DB_PATH = "data/bayarea_biotech_sources.db"

def execute_query(query):
    """Execute a SQL query and return results as a DataFrame"""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df
    except Exception as e:
        print(f"Error: {e}")
        return None

def show_tables():
    """Show all tables in the database"""
    query = "SELECT name FROM sqlite_master WHERE type='table';"
    df = execute_query(query)
    if df is not None:
        print("\nAvailable tables:")
        for table in df['name']:
            count_query = f"SELECT COUNT(*) as count FROM {table}"
            count_df = execute_query(count_query)
            print(f"  - {table}: {count_df['count'].iloc[0]} rows")

def show_schema(table_name):
    """Show schema for a specific table"""
    query = f"PRAGMA table_info({table_name})"
    df = execute_query(query)
    if df is not None:
        print(f"\nSchema for {table_name}:")
        for _, row in df.iterrows():
            pk = " (PK)" if row['pk'] == 1 else ""
            nullable = " NOT NULL" if row['notnull'] == 1 else ""
            print(f"  {row['name']}: {row['type']}{pk}{nullable}")

# Example queries
EXAMPLE_QUERIES = {
    "1": ("Top 10 companies by clinical trials", """
        SELECT c.company_name, COUNT(ct.trial_id) as trial_count
        FROM companies c
        JOIN clinical_trials ct ON c.company_id = ct.company_id
        GROUP BY c.company_id, c.company_name
        ORDER BY trial_count DESC
        LIMIT 10
    """),

    "2": ("Public companies with websites", """
        SELECT c.company_name, c.website, cc.company_stage
        FROM companies c
        JOIN company_classifications cc ON c.company_id = cc.company_id
        WHERE cc.company_stage = 'Public' AND cc.is_current = 1
        AND c.website IS NOT NULL
        ORDER BY c.company_name
        LIMIT 20
    """),

    "3": ("Companies by city", """
        SELECT city, COUNT(*) as company_count
        FROM companies
        WHERE city IS NOT NULL
        GROUP BY city
        ORDER BY company_count DESC
        LIMIT 15
    """),

    "4": ("Clinical stage companies with active trials", """
        SELECT DISTINCT c.company_name, c.city, ct.trial_status, ct.phase
        FROM companies c
        JOIN clinical_trials ct ON c.company_id = ct.company_id
        JOIN company_classifications cc ON c.company_id = cc.company_id
        WHERE cc.company_stage = 'Clinical Stage'
        AND cc.is_current = 1
        AND ct.trial_status LIKE '%ACTIVE%'
        ORDER BY c.company_name
        LIMIT 20
    """),

    "5": ("Company stage distribution", """
        SELECT company_stage, COUNT(DISTINCT company_id) as count
        FROM company_classifications
        WHERE is_current = 1
        GROUP BY company_stage
        ORDER BY count DESC
    """),
}

def main():
    print("=" * 60)
    print("Bay Area Biotech Database Query Tool")
    print("=" * 60)

    while True:
        print("\nOptions:")
        print("1. Show all tables")
        print("2. Show table schema")
        print("3. Run example query")
        print("4. Run custom SQL query")
        print("5. Export query to CSV")
        print("q. Quit")

        choice = input("\nEnter choice: ").strip().lower()

        if choice == 'q':
            break
        elif choice == '1':
            show_tables()
        elif choice == '2':
            table = input("Enter table name: ").strip()
            show_schema(table)
        elif choice == '3':
            print("\nExample queries:")
            for key, (desc, _) in EXAMPLE_QUERIES.items():
                print(f"  {key}. {desc}")
            query_choice = input("Choose query: ").strip()
            if query_choice in EXAMPLE_QUERIES:
                desc, query = EXAMPLE_QUERIES[query_choice]
                print(f"\nRunning: {desc}")
                df = execute_query(query)
                if df is not None:
                    print(df.to_string())
        elif choice == '4':
            print("Enter SQL query (end with ';'):")
            lines = []
            while True:
                line = input()
                lines.append(line)
                if line.strip().endswith(';'):
                    break
            query = ' '.join(lines)
            df = execute_query(query)
            if df is not None:
                print(df.to_string())
        elif choice == '5':
            query = input("Enter SQL query: ").strip()
            filename = input("Enter output filename (without .csv): ").strip()
            df = execute_query(query)
            if df is not None:
                df.to_csv(f"{filename}.csv", index=False)
                print(f"Saved to {filename}.csv")

if __name__ == "__main__":
    main()