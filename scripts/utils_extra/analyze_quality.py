#!/usr/bin/env python3
"""Analyze current data quality metrics for biotech dataset."""

import pandas as pd
import numpy as np

# Load the data
df = pd.read_csv("data/final/companies.csv")

print("=== CURRENT DATA QUALITY METRICS ===")
print(f"Total companies: {len(df)}")

# Check critical fields
print(f"\nCritical fields completeness:")
print(f"  Company Name: {df['Company Name'].notna().sum()} ({df['Company Name'].notna().mean()*100:.1f}%)")
print(f"  Address: {df['Address'].notna().sum()} ({df['Address'].notna().mean()*100:.1f}%)")
print(f"  Website: {df['Website'].notna().sum()} ({df['Website'].notna().mean()*100:.1f}%)")
print(f"  Latitude: {df['Latitude'].notna().sum()} ({df['Latitude'].notna().mean()*100:.1f}%)")
print(f"  Longitude: {df['Longitude'].notna().sum()} ({df['Longitude'].notna().mean()*100:.1f}%)")

# Check validation status
validated = df['Latitude'].notna() & df['Longitude'].notna()
print(f"\nValidation Status:")
print(f"  Validated (has lat/long): {validated.sum()} ({validated.mean()*100:.1f}%)")
print(f"  Not validated: {(~validated).sum()} ({(~validated).mean()*100:.1f}%)")

# Check confidence scores
if "Confidence_Score" in df.columns:
    print(f"\nConfidence Score Distribution:")
    print(f"  High (>=0.9): {(df['Confidence_Score'] >= 0.9).sum()} companies")
    print(f"  Medium (0.7-0.9): {((df['Confidence_Score'] >= 0.7) & (df['Confidence_Score'] < 0.9)).sum()} companies")
    print(f"  Low (<0.7): {(df['Confidence_Score'] < 0.7).sum()} companies")
    print(f"  Missing: {df['Confidence_Score'].isna().sum()} companies")

# Company stages for visualization
print(f"\nCompany Stage Distribution:")
print(df["Company_Stage_Classified"].value_counts().head(10))

# Cities with most companies
print(f"\nTop 10 Cities:")
print(df['City'].value_counts().head(10))

# Companies missing critical data
missing_address = df[df['Address'].isna()]
print(f"\n=== COMPANIES NEEDING ATTENTION ===")
print(f"Companies without addresses: {len(missing_address)}")
if len(missing_address) > 0:
    print("First 5 companies missing addresses:")
    for idx, row in missing_address.head().iterrows():
        print(f"  - {row['Company Name']} ({row['City'] if pd.notna(row['City']) else 'No city'})")

# Companies with low confidence
if "Confidence_Score" in df.columns:
    low_confidence = df[df['Confidence_Score'] < 0.7]
    print(f"\nCompanies with low confidence scores: {len(low_confidence)}")
    if len(low_confidence) > 0:
        print("First 5 low confidence companies:")
        for idx, row in low_confidence.head().iterrows():
            print(f"  - {row['Company Name']}: {row['Confidence_Score']}")