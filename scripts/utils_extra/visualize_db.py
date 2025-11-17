#!/usr/bin/env python3
"""
Database visualization tool for Bay Area Biotech database
Creates various charts and visualizations from the data
Usage: python visualize_db.py
"""

import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import folium
import json

# Set style for better looking plots
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

DB_PATH = "data/bayarea_biotech_sources.db"

def get_data(query):
    """Execute query and return DataFrame"""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def plot_company_stages():
    """Pie chart of company stages"""
    query = """
        SELECT company_stage, COUNT(DISTINCT company_id) as count
        FROM company_classifications
        WHERE is_current = 1
        GROUP BY company_stage
        ORDER BY count DESC
    """
    df = get_data(query)

    plt.figure(figsize=(10, 8))
    colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD']
    plt.pie(df['count'], labels=df['company_stage'], autopct='%1.1f%%', colors=colors)
    plt.title('Bay Area Biotech Companies by Stage', fontsize=16, fontweight='bold')
    plt.savefig('visualizations/company_stages_pie.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: visualizations/company_stages_pie.png")

def plot_cities_bar():
    """Bar chart of companies by city"""
    query = """
        SELECT city, COUNT(*) as company_count
        FROM companies
        WHERE city IS NOT NULL
        GROUP BY city
        ORDER BY company_count DESC
        LIMIT 15
    """
    df = get_data(query)

    plt.figure(figsize=(14, 8))
    bars = plt.bar(df['city'], df['company_count'], color='steelblue')
    plt.xlabel('City', fontsize=12)
    plt.ylabel('Number of Companies', fontsize=12)
    plt.title('Top 15 Cities by Biotech Company Count', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')

    # Add value labels on bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('visualizations/companies_by_city.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: visualizations/companies_by_city.png")

def plot_clinical_trials_timeline():
    """Timeline of clinical trials"""
    query = """
        SELECT phase, COUNT(*) as count
        FROM clinical_trials
        WHERE phase IS NOT NULL
        GROUP BY phase
        ORDER BY
            CASE
                WHEN phase LIKE '%PHASE1%' THEN 1
                WHEN phase LIKE '%PHASE2%' THEN 2
                WHEN phase LIKE '%PHASE3%' THEN 3
                WHEN phase LIKE '%PHASE4%' THEN 4
                ELSE 5
            END
    """
    df = get_data(query)

    plt.figure(figsize=(12, 6))
    bars = plt.bar(df['phase'], df['count'], color='coral')
    plt.xlabel('Trial Phase', fontsize=12)
    plt.ylabel('Number of Trials', fontsize=12)
    plt.title('Clinical Trials by Phase', fontsize=16, fontweight='bold')
    plt.xticks(rotation=45, ha='right')

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('visualizations/trials_by_phase.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: visualizations/trials_by_phase.png")

def plot_enrichment_coverage():
    """Stacked bar chart showing enrichment coverage"""
    query = """
        WITH company_enrichment AS (
            SELECT
                c.company_id,
                CASE WHEN s.company_id IS NOT NULL THEN 1 ELSE 0 END as has_sec,
                CASE WHEN ct.company_id IS NOT NULL THEN 1 ELSE 0 END as has_trials
            FROM companies c
            LEFT JOIN (SELECT DISTINCT company_id FROM sec_edgar_data) s ON c.company_id = s.company_id
            LEFT JOIN (SELECT DISTINCT company_id FROM clinical_trials) ct ON c.company_id = ct.company_id
        )
        SELECT
            CASE
                WHEN has_sec = 1 AND has_trials = 1 THEN 'Both SEC & Trials'
                WHEN has_sec = 1 AND has_trials = 0 THEN 'SEC Only'
                WHEN has_sec = 0 AND has_trials = 1 THEN 'Trials Only'
                ELSE 'No Enrichment'
            END as enrichment_type,
            COUNT(*) as count
        FROM company_enrichment
        GROUP BY enrichment_type
    """
    df = get_data(query)

    plt.figure(figsize=(10, 6))
    colors = ['#2ecc71', '#3498db', '#e74c3c', '#95a5a6']
    bars = plt.bar(df['enrichment_type'], df['count'], color=colors)
    plt.xlabel('Enrichment Type', fontsize=12)
    plt.ylabel('Number of Companies', fontsize=12)
    plt.title('Data Enrichment Coverage', fontsize=16, fontweight='bold')

    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom')

    plt.tight_layout()
    plt.savefig('visualizations/enrichment_coverage.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: visualizations/enrichment_coverage.png")

def create_company_map():
    """Create an interactive map of companies with lat/lon data"""
    query = """
        SELECT c.company_name, c.city, c.latitude, c.longitude,
               c.website, cc.company_stage
        FROM companies c
        LEFT JOIN company_classifications cc ON c.company_id = cc.company_id
        WHERE c.latitude IS NOT NULL
        AND c.longitude IS NOT NULL
        AND cc.is_current = 1
    """
    df = get_data(query)

    # Create base map centered on Bay Area
    m = folium.Map(location=[37.5, -122.2], zoom_start=9)

    # Color mapping for company stages
    color_map = {
        'Public': 'green',
        'Private': 'blue',
        'Clinical Stage': 'orange',
        'Private with SEC Filings': 'purple',
        'Defunct': 'red',
        'Unknown': 'gray'
    }

    # Add markers for each company
    for _, row in df.iterrows():
        color = color_map.get(row['company_stage'], 'gray')
        popup_text = f"""
        <b>{row['company_name']}</b><br>
        City: {row['city']}<br>
        Stage: {row['company_stage']}<br>
        Website: {row['website'] if row['website'] else 'N/A'}
        """
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=folium.Popup(popup_text, max_width=300),
            icon=folium.Icon(color=color, icon='info-sign')
        ).add_to(m)

    # Add legend
    legend_html = '''
    <div style="position: fixed;
                bottom: 50px; left: 50px; width: 200px; height: auto;
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; border-radius: 5px; padding: 10px">
        <p style="font-weight: bold;">Company Stages</p>
        <p><span style="color: green;">●</span> Public</p>
        <p><span style="color: blue;">●</span> Private</p>
        <p><span style="color: orange;">●</span> Clinical Stage</p>
        <p><span style="color: purple;">●</span> Private with SEC Filings</p>
        <p><span style="color: red;">●</span> Defunct</p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))

    m.save('visualizations/company_map.html')
    print("Saved: visualizations/company_map.html")
    return len(df)

def plot_top_companies_trials():
    """Horizontal bar chart of top companies by trial count"""
    query = """
        SELECT c.company_name, COUNT(ct.trial_id) as trial_count
        FROM companies c
        JOIN clinical_trials ct ON c.company_id = ct.company_id
        GROUP BY c.company_id, c.company_name
        ORDER BY trial_count DESC
        LIMIT 20
    """
    df = get_data(query)

    plt.figure(figsize=(10, 10))
    plt.barh(df['company_name'], df['trial_count'], color='teal')
    plt.xlabel('Number of Clinical Trials', fontsize=12)
    plt.title('Top 20 Companies by Clinical Trial Count', fontsize=16, fontweight='bold')

    # Add value labels
    for i, v in enumerate(df['trial_count']):
        plt.text(v + 0.5, i, str(v), va='center')

    plt.tight_layout()
    plt.savefig('visualizations/top_companies_trials.png', dpi=150, bbox_inches='tight')
    plt.show()
    print("Saved: visualizations/top_companies_trials.png")

def main():
    """Run all visualizations"""
    print("=" * 60)
    print("Bay Area Biotech Database Visualization Tool")
    print("=" * 60)

    # Create visualizations directory if it doesn't exist
    Path("visualizations").mkdir(exist_ok=True)

    print("\nGenerating visualizations...")
    print("-" * 40)

    try:
        print("\n1. Company Stages Distribution")
        plot_company_stages()
    except Exception as e:
        print(f"   Error: {e}")

    try:
        print("\n2. Companies by City")
        plot_cities_bar()
    except Exception as e:
        print(f"   Error: {e}")

    try:
        print("\n3. Clinical Trials by Phase")
        plot_clinical_trials_timeline()
    except Exception as e:
        print(f"   Error: {e}")

    try:
        print("\n4. Data Enrichment Coverage")
        plot_enrichment_coverage()
    except Exception as e:
        print(f"   Error: {e}")

    try:
        print("\n5. Top Companies by Trial Count")
        plot_top_companies_trials()
    except Exception as e:
        print(f"   Error: {e}")

    try:
        print("\n6. Interactive Company Map")
        count = create_company_map()
        print(f"   Mapped {count} companies with location data")
    except Exception as e:
        print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("All visualizations saved in 'visualizations/' directory")
    print("Open company_map.html in a browser to view the interactive map")

if __name__ == "__main__":
    main()