#!/usr/bin/env python3
"""
CSV to SQLite Migration Script
Migrates biotech company data from CSV to structured SQLite database
Preserves all existing data while adding structure for API enrichments
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

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/logs/migration.log'),
        logging.StreamHandler()
    ]
)

class DatabaseMigrator:
    def __init__(self, csv_path, db_path, schema_path):
        self.csv_path = Path(csv_path)
        self.db_path = Path(db_path)
        self.schema_path = Path(schema_path)
        self.conn = None
        self.cursor = None
        self.stats = {
            'total_rows': 0,
            'companies_inserted': 0,
            'classifications_inserted': 0,
            'focus_areas_inserted': 0,
            'errors': 0
        }

    def backup_existing_data(self):
        """Create backup of CSV and existing database if present"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # Backup CSV
        if self.csv_path.exists():
            backup_csv = self.csv_path.parent / f"{self.csv_path.stem}_backup_{timestamp}.csv"
            shutil.copy2(self.csv_path, backup_csv)
            logging.info(f"CSV backup created: {backup_csv}")

        # Backup existing database if it exists
        if self.db_path.exists():
            backup_db = self.db_path.parent / f"{self.db_path.stem}_backup_{timestamp}.db"
            shutil.copy2(self.db_path, backup_db)
            logging.info(f"Database backup created: {backup_db}")

        return timestamp

    def create_database(self):
        """Create SQLite database with schema from SQL file"""
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

            logging.info("Database schema created successfully")
            return True

        except Exception as e:
            logging.error(f"Failed to create database schema: {e}")
            return False

    def parse_focus_areas(self, focus_areas_str):
        """Parse focus areas from comma-separated string"""
        if not focus_areas_str or focus_areas_str.strip() == '':
            return []

        # Split by comma and clean each area
        areas = []
        for area in focus_areas_str.split(','):
            area = area.strip()
            if area:
                areas.append(area)
        return areas

    def calculate_confidence_score(self, row):
        """Calculate or extract confidence score"""
        # Use existing confidence score if available
        if 'Confidence_Score' in row and row['Confidence_Score']:
            try:
                return float(row['Confidence_Score'])
            except (ValueError, TypeError):
                pass

        # Default confidence based on validation source
        validation_source = row.get('Validation_Source', '').upper()
        if 'BPG' in validation_source:
            return 0.85
        elif 'WIKIPEDIA' in validation_source:
            return 0.75
        else:
            return 0.5

    def migrate_csv_data(self):
        """Import CSV data into SQLite database"""
        if not self.csv_path.exists():
            logging.error(f"CSV file not found: {self.csv_path}")
            return False

        try:
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 1):
                    self.stats['total_rows'] += 1

                    try:
                        # Extract and clean company data
                        company_name = row.get('Company Name', '').strip()
                        if not company_name:
                            logging.warning(f"Row {row_num}: Skipping empty company name")
                            self.stats['errors'] += 1
                            continue

                        # Insert company record
                        self.cursor.execute('''
                        INSERT OR IGNORE INTO companies (
                            company_name,
                            website,
                            city,
                            address,
                            latitude,
                            longitude,
                            confidence_score,
                            validation_source,
                            google_address,
                            google_name,
                            google_website,
                            description,
                            original_index,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                        ''', (
                            company_name,
                            row.get('Website', '').strip(),
                            row.get('City', '').strip(),
                            row.get('Address', '').strip() or row.get('Google_Address', '').strip(),
                            float(row['Latitude']) if row.get('Latitude') else None,
                            float(row['Longitude']) if row.get('Longitude') else None,
                            self.calculate_confidence_score(row),
                            row.get('Validation_Source', '').strip(),
                            row.get('Google_Address', '').strip(),
                            row.get('Google_Name', '').strip(),
                            row.get('Google_Website', '').strip(),
                            row.get('Description', '').strip(),
                            int(row['original_index']) if row.get('original_index') else row_num,
                        ))

                        # Check if insert was successful (rowcount > 0) or if it was ignored
                        if self.cursor.rowcount > 0:
                            self.stats['companies_inserted'] += 1
                            company_id = self.cursor.lastrowid
                        else:
                            # Company already exists, get its ID
                            self.cursor.execute('SELECT company_id FROM companies WHERE company_name = ?', (company_name,))
                            result = self.cursor.fetchone()
                            if result:
                                company_id = result[0]
                            else:
                                logging.error(f"Row {row_num}: Failed to get company_id for {company_name}")
                                continue

                        # Insert classification if present
                        company_stage = row.get('Company Stage', '').strip() or row.get('Company_Stage', '').strip()
                        if company_stage:
                            self.cursor.execute('''
                            INSERT INTO company_classifications (
                                company_id,
                                company_stage,
                                classification_method,
                                classification_confidence,
                                classification_source,
                                is_current
                            ) VALUES (?, ?, ?, ?, ?, 1)
                            ''', (
                                company_id,
                                company_stage,
                                'csv_import',
                                0.75,  # Default confidence for imported classifications
                                'Original CSV',
                            ))
                            if self.cursor.rowcount > 0:
                                self.stats['classifications_inserted'] += 1

                        # Insert focus areas
                        focus_areas_str = row.get('Focus Areas', '').strip() or row.get('Focus_Areas', '').strip()
                        focus_areas = self.parse_focus_areas(focus_areas_str)
                        for area in focus_areas:
                            self.cursor.execute('''
                            INSERT OR IGNORE INTO company_focus_areas (
                                company_id,
                                focus_area,
                                extraction_method,
                                extraction_confidence,
                                extraction_source
                            ) VALUES (?, ?, ?, ?, ?)
                            ''', (
                                company_id,
                                area,
                                'csv_import',
                                0.75,
                                'Original CSV'
                            ))
                            if self.cursor.rowcount > 0:
                                self.stats['focus_areas_inserted'] += 1

                        # Log progress every 100 rows
                        if row_num % 100 == 0:
                            logging.info(f"Processed {row_num} rows...")
                            self.conn.commit()

                    except Exception as e:
                        logging.error(f"Error processing row {row_num} ({company_name}): {e}")
                        self.stats['errors'] += 1
                        continue

                # Final commit
                self.conn.commit()
                logging.info(f"Migration complete: Processed {self.stats['total_rows']} rows")

                return True

        except Exception as e:
            logging.error(f"Critical error during migration: {e}")
            traceback.print_exc()
            if self.conn:
                self.conn.rollback()
            return False

    def validate_migration(self):
        """Validate data integrity after migration"""
        validation_results = {}

        try:
            # Count total companies
            self.cursor.execute("SELECT COUNT(*) FROM companies")
            total_companies = self.cursor.fetchone()[0]
            validation_results['total_companies'] = total_companies

            # Count classifications
            self.cursor.execute("SELECT COUNT(*) FROM company_classifications")
            total_classifications = self.cursor.fetchone()[0]
            validation_results['total_classifications'] = total_classifications

            # Count focus areas
            self.cursor.execute("SELECT COUNT(*) FROM company_focus_areas")
            total_focus_areas = self.cursor.fetchone()[0]
            validation_results['total_focus_areas'] = total_focus_areas

            # Count by company stage
            self.cursor.execute("""
            SELECT company_stage, COUNT(*)
            FROM company_classifications
            WHERE is_current = 1
            GROUP BY company_stage
            ORDER BY COUNT(*) DESC
            """)
            stage_distribution = self.cursor.fetchall()
            validation_results['stage_distribution'] = stage_distribution

            # Count by city
            self.cursor.execute("""
            SELECT city, COUNT(*)
            FROM companies
            WHERE city IS NOT NULL AND city != ''
            GROUP BY city
            ORDER BY COUNT(*) DESC
            LIMIT 10
            """)
            city_distribution = self.cursor.fetchall()
            validation_results['top_cities'] = city_distribution

            # Check for data loss
            csv_row_count = sum(1 for _ in open(self.csv_path)) - 1  # Subtract header
            validation_results['csv_rows'] = csv_row_count
            validation_results['data_loss'] = csv_row_count - total_companies

            # Log validation report
            logging.info("="*60)
            logging.info("VALIDATION REPORT")
            logging.info("="*60)
            logging.info(f"CSV rows: {csv_row_count}")
            logging.info(f"Companies in DB: {total_companies}")
            logging.info(f"Classifications: {total_classifications}")
            logging.info(f"Focus areas: {total_focus_areas}")
            logging.info(f"Data loss: {validation_results['data_loss']} rows")

            if validation_results['data_loss'] > 0:
                logging.warning(f"WARNING: {validation_results['data_loss']} rows were not migrated")
            else:
                logging.info("SUCCESS: All rows migrated successfully!")

            logging.info("\nCompany Stage Distribution:")
            for stage, count in stage_distribution:
                logging.info(f"  {stage or 'Unknown':20s}: {count:4d}")

            logging.info("\nTop Cities:")
            for city, count in city_distribution:
                logging.info(f"  {city:20s}: {count:4d}")

            return validation_results

        except Exception as e:
            logging.error(f"Validation failed: {e}")
            return None

    def generate_migration_report(self, validation_results, backup_timestamp):
        """Generate detailed migration report"""
        report_path = Path('data/reports') / f'migration_report_{backup_timestamp}.txt'
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, 'w') as f:
            f.write("="*70 + "\n")
            f.write("DATABASE MIGRATION REPORT\n")
            f.write("="*70 + "\n")
            f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source CSV: {self.csv_path}\n")
            f.write(f"Target DB: {self.db_path}\n\n")

            f.write("MIGRATION STATISTICS\n")
            f.write("-"*70 + "\n")
            f.write(f"Total CSV rows processed: {self.stats['total_rows']}\n")
            f.write(f"Companies inserted: {self.stats['companies_inserted']}\n")
            f.write(f"Classifications inserted: {self.stats['classifications_inserted']}\n")
            f.write(f"Focus areas inserted: {self.stats['focus_areas_inserted']}\n")
            f.write(f"Errors encountered: {self.stats['errors']}\n\n")

            if validation_results:
                f.write("VALIDATION RESULTS\n")
                f.write("-"*70 + "\n")
                f.write(f"Total companies in database: {validation_results['total_companies']}\n")
                f.write(f"Total classifications: {validation_results['total_classifications']}\n")
                f.write(f"Total focus areas: {validation_results['total_focus_areas']}\n")
                f.write(f"Data loss: {validation_results['data_loss']} rows\n\n")

                f.write("Company Stage Distribution:\n")
                for stage, count in validation_results.get('stage_distribution', []):
                    f.write(f"  {stage or 'Unknown':20s}: {count:4d}\n")
                f.write("\n")

                f.write("Top Cities:\n")
                for city, count in validation_results.get('top_cities', []):
                    f.write(f"  {city:20s}: {count:4d}\n")

            f.write("\n" + "="*70 + "\n")
            f.write("END OF REPORT\n")
            f.write("="*70 + "\n")

        logging.info(f"Migration report saved to: {report_path}")
        return report_path

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logging.info("Database connection closed")

def main():
    """Main migration function"""
    # Configuration
    CSV_PATH = "data/working/companies_enriched_final.csv"
    DB_PATH = "data/bayarea_biotech.db"
    SCHEMA_PATH = "scripts/db/schema.sql"

    logging.info("="*60)
    logging.info("SQLITE MIGRATION STARTING")
    logging.info("="*60)

    migrator = DatabaseMigrator(CSV_PATH, DB_PATH, SCHEMA_PATH)

    try:
        # Step 1: Backup existing data
        backup_timestamp = migrator.backup_existing_data()

        # Step 2: Create database with schema
        if not migrator.create_database():
            logging.error("Failed to create database")
            sys.exit(1)

        # Step 3: Migrate CSV data
        if not migrator.migrate_csv_data():
            logging.error("Migration failed")
            sys.exit(1)

        # Step 4: Validate migration
        validation_results = migrator.validate_migration()

        # Step 5: Generate report
        report_path = migrator.generate_migration_report(validation_results, backup_timestamp)

        # Success message
        if validation_results and validation_results['data_loss'] == 0:
            logging.info("="*60)
            logging.info("SUCCESS: Migration completed without data loss!")
            logging.info("="*60)
        else:
            logging.warning("Migration completed with warnings - check report for details")

        return 0

    except Exception as e:
        logging.error(f"Migration failed with critical error: {e}")
        traceback.print_exc()
        return 1

    finally:
        migrator.close()

if __name__ == "__main__":
    sys.exit(main())