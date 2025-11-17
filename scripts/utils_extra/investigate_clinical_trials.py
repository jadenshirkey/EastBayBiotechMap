#!/usr/bin/env python3
"""
Investigate clinical trials data structure to understand:
1. Are trials active/ongoing or historical?
2. What's the distribution of trial statuses?
3. How should we define "Clinical Stage"?
"""

import sqlite3
import pandas as pd
from datetime import datetime

DB_PATH = "data/bayarea_biotech_sources.db"

conn = sqlite3.connect(DB_PATH)

print("=" * 70)
print("CLINICAL TRIALS DATA INVESTIGATION")
print("=" * 70)

# 1. Check table schema
print("\n1. Clinical Trials Table Schema:")
schema_query = "PRAGMA table_info(clinical_trials)"
schema_df = pd.read_sql_query(schema_query, conn)
print(schema_df[['name', 'type']].to_string())

# 2. Check trial status distribution
print("\n2. Trial Status Distribution:")
status_query = """
SELECT trial_status, COUNT(*) as count
FROM clinical_trials
WHERE trial_status IS NOT NULL
GROUP BY trial_status
ORDER BY count DESC
LIMIT 20
"""
status_df = pd.read_sql_query(status_query, conn)
print(status_df.to_string())

# 3. Check active vs completed trials
print("\n3. Active vs Completed Trials:")
active_query = """
SELECT
    CASE
        WHEN trial_status LIKE '%RECRUIT%' THEN 'Recruiting'
        WHEN trial_status LIKE '%ACTIVE%' THEN 'Active'
        WHEN trial_status LIKE '%ENROLL%' THEN 'Enrolling'
        WHEN trial_status LIKE '%COMPLET%' THEN 'Completed'
        WHEN trial_status LIKE '%TERMINAT%' THEN 'Terminated'
        WHEN trial_status LIKE '%WITHDRAW%' THEN 'Withdrawn'
        WHEN trial_status LIKE '%SUSPEND%' THEN 'Suspended'
        ELSE 'Other'
    END as status_category,
    COUNT(*) as count
FROM clinical_trials
GROUP BY status_category
ORDER BY count DESC
"""
active_df = pd.read_sql_query(active_query, conn)
print(active_df.to_string())

# 4. Check completion dates
print("\n4. Trial Completion Date Analysis:")
date_query = """
SELECT
    COUNT(*) as total_trials,
    COUNT(completion_date) as has_completion_date,
    COUNT(CASE WHEN completion_date > date('now') THEN 1 END) as future_completion,
    COUNT(CASE WHEN completion_date <= date('now') AND completion_date > date('now', '-1 year') THEN 1 END) as completed_last_year,
    COUNT(CASE WHEN completion_date <= date('now', '-1 year') AND completion_date > date('now', '-2 years') THEN 1 END) as completed_1_2_years,
    COUNT(CASE WHEN completion_date <= date('now', '-2 years') THEN 1 END) as completed_over_2_years
FROM clinical_trials
"""
date_df = pd.read_sql_query(date_query, conn)
print(date_df.T.to_string())

# 5. Check companies by trial recency
print("\n5. Companies by Trial Recency:")
recency_query = """
SELECT
    CASE
        WHEN MAX(CASE WHEN trial_status LIKE '%RECRUIT%' OR trial_status LIKE '%ACTIVE%' OR trial_status LIKE '%ENROLL%' THEN 1 ELSE 0 END) = 1 THEN 'Has Active Trials'
        WHEN MAX(CASE WHEN completion_date > date('now', '-2 years') THEN 1 ELSE 0 END) = 1 THEN 'Recent Trials (< 2 years)'
        WHEN COUNT(*) > 0 THEN 'Old Trials (> 2 years)'
        ELSE 'No Trials'
    END as trial_category,
    COUNT(DISTINCT company_id) as company_count
FROM clinical_trials
GROUP BY company_id
"""

# Wrap in a subquery to group by category
recency_summary_query = """
WITH company_categories AS (
    SELECT
        company_id,
        CASE
            WHEN MAX(CASE WHEN trial_status LIKE '%RECRUIT%' OR trial_status LIKE '%ACTIVE%' OR trial_status LIKE '%ENROLL%' THEN 1 ELSE 0 END) = 1 THEN 'Has Active Trials'
            WHEN MAX(CASE WHEN completion_date > date('now', '-2 years') THEN 1 ELSE 0 END) = 1 THEN 'Recent Trials (< 2 years)'
            WHEN COUNT(*) > 0 THEN 'Old Trials (> 2 years)'
            ELSE 'No Trials'
        END as trial_category
    FROM clinical_trials
    GROUP BY company_id
)
SELECT trial_category, COUNT(*) as company_count
FROM company_categories
GROUP BY trial_category
ORDER BY company_count DESC
"""
recency_df = pd.read_sql_query(recency_summary_query, conn)
print(recency_df.to_string())

# 6. Sample of clinical stage companies with their trials
print("\n6. Sample Clinical Stage Companies with Trial Details:")
sample_query = """
SELECT
    c.company_name,
    ct.trial_status,
    ct.phase,
    ct.start_date,
    ct.completion_date,
    CASE
        WHEN ct.completion_date > date('now') THEN 'Future'
        WHEN ct.completion_date > date('now', '-2 years') THEN 'Recent'
        ELSE 'Old'
    END as recency
FROM companies c
JOIN clinical_trials ct ON c.company_id = ct.company_id
JOIN company_classifications cc ON c.company_id = cc.company_id
WHERE cc.company_stage = 'Clinical Stage'
    AND cc.is_current = 1
ORDER BY ct.completion_date DESC
LIMIT 15
"""
sample_df = pd.read_sql_query(sample_query, conn)
print(sample_df.to_string())

conn.close()

print("\n" + "=" * 70)
print("RECOMMENDATIONS:")
print("=" * 70)
print("""
Based on the data:
1. We have both active/ongoing AND historical trials in the database
2. "Clinical Stage" should mean:
   - Companies with ACTIVE trials (Recruiting, Active, Enrolling)
   - OR companies with RECENT trials (completed within 2 years)
3. Companies with only OLD trials (>2 years) should be "Late Stage" or "Private"
4. This approach ensures we don't mislabel inactive companies as "Clinical Stage"
""")