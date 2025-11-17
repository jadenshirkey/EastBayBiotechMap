#!/usr/bin/env python3
"""
Enhanced CSV to SQLite Migration Script with Source Tracking
Imports raw data from BioPharmGuy and Wikipedia, then creates merged company records
Maintains complete data provenance through source mapping
"""

import sqlite3
import csv
import json
import logging
from pathlib import Path
from datetime import datetime
import shutil
import sys
import traceback
from typing import Dict, List, Optional, Tuple
import re

# Add path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from scripts.utils.url_standardizer import standardize_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/migration_with_sources.log'),
        logging.StreamHandler()
    ]
)

class EnhancedDatabaseMigrator:
    def __init__(self, db_path: str, schema_path: str):
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.conn = None
        self.cursor = None
        self.import_batch = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.stats = {
            'bpg_imported': 0,
            'wiki_imported': 0,
            'companies_created': 0,
            'mappings_created': 0,
            'duplicates_merged': 0,
            'errors': 0
        }

    def create_database(self):
        """Create SQLite database with enhanced schema"""
        try:
            # Connect to database (creates file if doesn't exist)
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()

            # Enable foreign keys
            self.cursor.execute("PRAGMA foreign_keys = ON")

            # Read and execute schema
            with open(self.schema_path, 'r') as f:
                schema_sql = f.read()

            # Execute the schema
            self.cursor.executescript(schema_sql)
            self.conn.commit()

            logging.info("Enhanced database schema created successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to create database schema: {e}")
            return False

    def import_biopharmguy_raw(self, bpg_csv_path: str):
        """Import raw BioPharmGuy data"""
        if not Path(bpg_csv_path).exists():
            logging.warning(f"BioPharmGuy file not found: {bpg_csv_path}")
            return

        logging.info(f"Importing BioPharmGuy data from: {bpg_csv_path}")

        with open(bpg_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Clean city field (remove trailing commas)
                    city = row.get('City', '').strip().rstrip(',')

                    # Insert into raw imports table
                    self.cursor.execute('''
                    INSERT OR IGNORE INTO biopharmguy_raw_imports (
                        company_name, website, city, state, focus_areas,
                        source_url, import_batch, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('Company Name', '').strip(),
                        row.get('Website', '').strip(),
                        city,
                        'CA',  # California companies
                        row.get('Focus Area', '').strip(),
                        row.get('Source URL', '').strip(),
                        self.import_batch,
                        json.dumps(row)  # Store complete raw data
                    ))

                    if self.cursor.rowcount > 0:
                        self.stats['bpg_imported'] += 1

                except Exception as e:
                    logging.error(f"Error importing BPG row: {e}")
                    self.stats['errors'] += 1

        self.conn.commit()
        logging.info(f"Imported {self.stats['bpg_imported']} BioPharmGuy companies")

    def import_wikipedia_raw(self, wiki_csv_path: str):
        """Import raw Wikipedia data"""
        if not Path(wiki_csv_path).exists():
            logging.warning(f"Wikipedia file not found: {wiki_csv_path}")
            return

        logging.info(f"Importing Wikipedia data from: {wiki_csv_path}")

        with open(wiki_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                try:
                    # Insert into raw imports table
                    self.cursor.execute('''
                    INSERT OR IGNORE INTO wikipedia_raw_imports (
                        company_name, wikipedia_url, website, headquarters_location,
                        description_text, import_batch, raw_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        row.get('Company Name', '').strip(),
                        row.get('Source URL', '').strip(),
                        standardize_url(row.get('Website', '').strip()) if row.get('Website', '').strip() else '',
                        row.get('City', '').strip(),
                        row.get('Description', '').strip(),
                        self.import_batch,
                        json.dumps(row)  # Store complete raw data
                    ))

                    if self.cursor.rowcount > 0:
                        self.stats['wiki_imported'] += 1

                except Exception as e:
                    logging.error(f"Error importing Wikipedia row: {e}")
                    self.stats['errors'] += 1

        self.conn.commit()
        logging.info(f"Imported {self.stats['wiki_imported']} Wikipedia companies")

    def normalize_company_name(self, name: str) -> str:
        """Normalize company name for matching"""
        if not name:
            return ""

        # Convert to uppercase
        name = name.upper()

        # Remove common suffixes
        suffixes = [
            r'\s+INC\.?$', r'\s+CORP\.?$', r'\s+CORPORATION$',
            r'\s+LLC\.?$', r'\s+LTD\.?$', r'\s+LIMITED$',
            r'\s+CO\.?$', r'\s+COMPANY$', r'\s+PLC\.?$',
            r'\s+LP\.?$', r'\s+L\.?P\.?$', r'\s+HOLDINGS?$'
        ]

        for suffix in suffixes:
            name = re.sub(suffix, '', name, flags=re.IGNORECASE)

        # Remove special characters
        name = re.sub(r'[^\w\s]', '', name)

        # Remove extra spaces
        name = ' '.join(name.split())

        return name.strip()

    def calculate_match_confidence(self, name1: str, name2: str,
                                  website1: str = None, website2: str = None) -> float:
        """Calculate confidence score for company match"""
        # Normalize names
        norm_name1 = self.normalize_company_name(name1)
        norm_name2 = self.normalize_company_name(name2)

        # Exact match after normalization
        if norm_name1 == norm_name2:
            return 0.95

        # Check website match if available
        if website1 and website2:
            # Extract domain from websites
            domain1 = re.sub(r'^https?://(www\.)?', '', website1.lower()).rstrip('/')
            domain2 = re.sub(r'^https?://(www\.)?', '', website2.lower()).rstrip('/')

            if domain1 == domain2:
                return 0.90

        # Fuzzy name matching
        if norm_name1 and norm_name2:
            # Calculate word overlap
            words1 = set(norm_name1.split())
            words2 = set(norm_name2.split())

            if words1 and words2:
                overlap = len(words1 & words2)
                total = len(words1 | words2)

                if total > 0:
                    score = overlap / total
                    if score > 0.7:
                        return score

        return 0.0

    def create_merged_companies(self):
        """Create merged company records from raw imports"""
        logging.info("Creating merged company records...")

        # Get all unique companies from both sources
        companies_processed = set()

        # Process BioPharmGuy companies
        self.cursor.execute('''
            SELECT bpg_id, company_name, website, city, state, focus_areas
            FROM biopharmguy_raw_imports
            WHERE import_batch = ?
        ''', (self.import_batch,))

        bpg_companies = self.cursor.fetchall()

        for bpg_id, company_name, website, city, state, focus_areas in bpg_companies:
            if not company_name:
                continue

            norm_name = self.normalize_company_name(company_name)
            if norm_name in companies_processed:
                continue

            # Standardize website URL
            website = standardize_url(website) if website else None

            # Check if company already exists
            self.cursor.execute('''
                SELECT company_id FROM companies WHERE company_name = ?
            ''', (company_name,))

            existing = self.cursor.fetchone()

            if not existing:
                # Create new company record
                self.cursor.execute('''
                    INSERT INTO companies (
                        company_name, website, city, validation_source, confidence_score
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (company_name, website, city, 'BPG', 0.85))

                company_id = self.cursor.lastrowid
                self.stats['companies_created'] += 1
            else:
                company_id = existing[0]
                # Update existing record if BPG has more info
                if website and not self.cursor.execute('SELECT website FROM companies WHERE company_id = ?', (company_id,)).fetchone()[0]:
                    self.cursor.execute('UPDATE companies SET website = ? WHERE company_id = ?', (website, company_id))

            # Create source mapping
            self.cursor.execute('''
                INSERT OR IGNORE INTO company_source_mapping (
                    company_id, source_type, source_id, match_confidence, match_method
                ) VALUES (?, ?, ?, ?, ?)
            ''', (company_id, 'biopharmguy', bpg_id, 1.0, 'direct_import'))

            self.stats['mappings_created'] += 1

            # Add focus areas
            if focus_areas:
                for area in focus_areas.split(','):
                    area = area.strip()
                    if area:
                        self.cursor.execute('''
                            INSERT OR IGNORE INTO company_focus_areas (
                                company_id, focus_area, extraction_method,
                                extraction_confidence, extraction_source
                            ) VALUES (?, ?, ?, ?, ?)
                        ''', (company_id, area, 'bpg_import', 0.85, 'BioPharmGuy'))

            companies_processed.add(norm_name)

        # Process Wikipedia companies
        self.cursor.execute('''
            SELECT wiki_id, company_name, website, headquarters_location, description_text
            FROM wikipedia_raw_imports
            WHERE import_batch = ?
        ''', (self.import_batch,))

        wiki_companies = self.cursor.fetchall()

        for wiki_id, company_name, website, location, description in wiki_companies:
            if not company_name:
                continue

            # Standardize website URL
            website = standardize_url(website) if website else None

            norm_name = self.normalize_company_name(company_name)

            # Try to match with existing companies
            best_match_id = None
            best_confidence = 0.0

            # Check all existing companies for matches
            self.cursor.execute('SELECT company_id, company_name, website FROM companies')
            existing_companies = self.cursor.fetchall()

            for existing_id, existing_name, existing_website in existing_companies:
                confidence = self.calculate_match_confidence(
                    company_name, existing_name, website, existing_website
                )

                if confidence > best_confidence:
                    best_confidence = confidence
                    best_match_id = existing_id

            if best_match_id and best_confidence >= 0.7:
                # Match found - create mapping
                company_id = best_match_id

                # Update validation source to 'Both' if from BPG too
                self.cursor.execute('''
                    UPDATE companies
                    SET validation_source = 'Both'
                    WHERE company_id = ? AND validation_source = 'BPG'
                ''', (company_id,))

                self.stats['duplicates_merged'] += 1
            else:
                # No match - create new company
                self.cursor.execute('''
                    INSERT INTO companies (
                        company_name, website, city, description,
                        validation_source, confidence_score
                    ) VALUES (?, ?, ?, ?, ?, ?)
                ''', (company_name, website, location, description, 'Wikipedia', 0.75))

                company_id = self.cursor.lastrowid
                self.stats['companies_created'] += 1

            # Create source mapping
            self.cursor.execute('''
                INSERT OR IGNORE INTO company_source_mapping (
                    company_id, source_type, source_id, match_confidence, match_method
                ) VALUES (?, ?, ?, ?, ?)
            ''', (company_id, 'wikipedia', wiki_id, best_confidence if best_confidence >= 0.7 else 1.0,
                 'fuzzy_match' if best_confidence >= 0.7 else 'direct_import'))

            self.stats['mappings_created'] += 1

        self.conn.commit()
        logging.info(f"Created {self.stats['companies_created']} merged company records")
        logging.info(f"Merged {self.stats['duplicates_merged']} duplicate companies")

    def import_enriched_data(self, enriched_csv_path: str):
        """Import existing enriched data and match to companies"""
        if not Path(enriched_csv_path).exists():
            logging.warning(f"Enriched CSV not found: {enriched_csv_path}")
            return

        logging.info(f"Importing enriched data from: {enriched_csv_path}")

        with open(enriched_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                company_name = row.get('Company Name', '').strip()
                if not company_name:
                    continue

                # Find matching company
                self.cursor.execute('SELECT company_id FROM companies WHERE company_name = ?', (company_name,))
                result = self.cursor.fetchone()

                if result:
                    company_id = result[0]

                    # Update with enriched data
                    self.cursor.execute('''
                        UPDATE companies SET
                            google_address = ?,
                            google_name = ?,
                            google_website = ?,
                            confidence_score = ?,
                            latitude = ?,
                            longitude = ?
                        WHERE company_id = ?
                    ''', (
                        row.get('Google_Address', ''),
                        row.get('Google_Name', ''),
                        row.get('Google_Website', ''),
                        float(row.get('Confidence_Score', 0)) if row.get('Confidence_Score') else None,
                        float(row.get('Latitude', 0)) if row.get('Latitude') else None,
                        float(row.get('Longitude', 0)) if row.get('Longitude') else None,
                        company_id
                    ))

                    # Add classification if present
                    company_stage = row.get('Company Stage', '').strip()
                    if company_stage:
                        self.cursor.execute('''
                            INSERT OR IGNORE INTO company_classifications (
                                company_id, company_stage, classification_method,
                                classification_confidence, classification_source
                            ) VALUES (?, ?, ?, ?, ?)
                        ''', (company_id, company_stage, 'enriched_import', 0.75, 'Previous Enrichment'))

        self.conn.commit()
        logging.info("Enriched data import complete")

    def generate_report(self):
        """Generate migration report with source statistics"""
        # Get statistics
        self.cursor.execute('SELECT COUNT(*) FROM biopharmguy_raw_imports WHERE import_batch = ?', (self.import_batch,))
        bpg_total = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM wikipedia_raw_imports WHERE import_batch = ?', (self.import_batch,))
        wiki_total = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM companies')
        total_companies = self.cursor.fetchone()[0]

        self.cursor.execute('SELECT COUNT(*) FROM company_source_mapping')
        total_mappings = self.cursor.fetchone()[0]

        # Get source distribution
        self.cursor.execute('''
            SELECT validation_source, COUNT(*)
            FROM companies
            GROUP BY validation_source
        ''')
        source_dist = self.cursor.fetchall()

        logging.info("="*60)
        logging.info("MIGRATION REPORT WITH SOURCE TRACKING")
        logging.info("="*60)
        logging.info(f"Import Batch: {self.import_batch}")
        logging.info("")
        logging.info("RAW DATA IMPORTED:")
        logging.info(f"  BioPharmGuy records: {bpg_total}")
        logging.info(f"  Wikipedia records: {wiki_total}")
        logging.info("")
        logging.info("MERGED RESULTS:")
        logging.info(f"  Total unique companies: {total_companies}")
        logging.info(f"  Source mappings created: {total_mappings}")
        logging.info(f"  Duplicates merged: {self.stats['duplicates_merged']}")
        logging.info("")
        logging.info("VALIDATION SOURCES:")
        for source, count in source_dist:
            logging.info(f"  {source:15s}: {count:4d}")
        logging.info("="*60)

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

def main():
    """Main migration function with source tracking"""
    # Configuration
    DB_PATH = "data/bayarea_biotech_sources.db"
    SCHEMA_PATH = "scripts/db/schema_v2.sql"
    BPG_CSV = "data/working/bpg_ca_raw.csv"
    WIKI_CSV = "data/working/wikipedia_companies.csv"
    ENRICHED_CSV = "data/working/companies_enriched_final.csv"

    logging.info("="*60)
    logging.info("ENHANCED MIGRATION WITH SOURCE TRACKING")
    logging.info("="*60)

    migrator = EnhancedDatabaseMigrator(DB_PATH, SCHEMA_PATH)

    try:
        # Step 1: Create database
        if not migrator.create_database():
            logging.error("Failed to create database")
            return 1

        # Step 2: Import raw BioPharmGuy data
        migrator.import_biopharmguy_raw(BPG_CSV)

        # Step 3: Import raw Wikipedia data
        migrator.import_wikipedia_raw(WIKI_CSV)

        # Step 4: Create merged company records
        migrator.create_merged_companies()

        # Step 5: Import existing enriched data
        migrator.import_enriched_data(ENRICHED_CSV)

        # Step 6: Generate report
        migrator.generate_report()

        logging.info("Migration completed successfully!")
        return 0

    except Exception as e:
        logging.error(f"Migration failed: {e}")
        traceback.print_exc()
        return 1

    finally:
        migrator.close()

if __name__ == "__main__":
    sys.exit(main())