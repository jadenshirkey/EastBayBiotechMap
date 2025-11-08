#!/usr/bin/env python3
import pandas as pd
from datetime import datetime

# Read the original CSV
df = pd.read_csv('east_bay_biotech_combined_notes.csv')

# Create a copy
df_with_addresses = df.copy()

# Get column names and find the index of 'City'
cols = df_with_addresses.columns.tolist()
city_index = cols.index('City')

# Insert 'Address' column right after 'City'
cols.insert(city_index + 1, 'Address')

# Reorder the dataframe with the new column order
df_with_addresses['Address'] = ''  # Initialize empty
df_with_addresses = df_with_addresses[cols]

# List to store addresses as we find them
addresses = {
    # Will be populated as we search
}

# Apply known addresses if available
for company, address in addresses.items():
    mask = df_with_addresses['Company Name'] == company
    df_with_addresses.loc[mask, 'Address'] = address

# Save the new CSV
df_with_addresses.to_csv('east_bay_biotech_with_addresses.csv', index=False)
print(f"Created east_bay_biotech_with_addresses.csv with {len(df_with_addresses)} companies")
print(f"Address column added after City column")
print(f"Columns: {', '.join(df_with_addresses.columns)}")