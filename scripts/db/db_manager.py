#!/usr/bin/env python3
"""
Database Access Layer for Biotech Company Database
Provides clean interface for all database operations with connection pooling and error handling
"""

import sqlite3
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple, Any
from contextlib import contextmanager
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Thread-safe database manager with connection pooling"""

    def __init__(self, db_path: str = "data/bayarea_biotech.db"):
        self.db_path = Path(db_path)
        self._local = threading.local()
        self._lock = threading.Lock()

    @property
    def connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection') or self._local.connection is None:
            self._local.connection = sqlite3.connect(str(self.db_path))
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
        return self._local.connection

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        conn = self.connection
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {e}")
            raise

    def close(self):
        """Close thread-local connection"""
        if hasattr(self._local, 'connection') and self._local.connection:
            self._local.connection.close()
            self._local.connection = None

    # ==================== Company Operations ====================

    def get_company(self, company_id: int) -> Optional[Dict]:
        """Get company by ID"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM companies WHERE company_id = ?
        """, (company_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_company_by_name(self, company_name: str) -> Optional[Dict]:
        """Get company by name"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM companies WHERE company_name = ?
        """, (company_name,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_all_companies(self, limit: Optional[int] = None, offset: int = 0) -> List[Dict]:
        """Get all companies with optional pagination"""
        cursor = self.connection.cursor()
        query = "SELECT * FROM companies ORDER BY company_name"
        params = []

        if limit is not None:
            # Validate inputs are integers
            if not isinstance(limit, int) or not isinstance(offset, int):
                raise ValueError("Limit and offset must be integers")
            if limit < 0 or offset < 0:
                raise ValueError("Limit and offset must be non-negative")

            query += " LIMIT ? OFFSET ?"
            params = [limit, offset]

        cursor.execute(query, params)
        return [dict(row) for row in cursor.fetchall()]

    def get_companies_for_enrichment(self, enrichment_type: str) -> List[Dict]:
        """Get companies that need specific enrichment"""
        cursor = self.connection.cursor()

        if enrichment_type == 'sec_edgar':
            # Get companies not yet checked by SEC EDGAR
            cursor.execute("""
                SELECT c.* FROM companies c
                LEFT JOIN sec_edgar_data sed ON c.company_id = sed.company_id
                WHERE sed.company_id IS NULL
                ORDER BY c.company_name
            """)
        elif enrichment_type == 'clinical_trials':
            # Get companies not yet checked for clinical trials
            cursor.execute("""
                SELECT DISTINCT c.* FROM companies c
                LEFT JOIN (
                    SELECT DISTINCT company_id FROM clinical_trials
                ) ct ON c.company_id = ct.company_id
                WHERE ct.company_id IS NULL
                ORDER BY c.company_name
            """)
        else:
            raise ValueError(f"Unknown enrichment type: {enrichment_type}")

        return [dict(row) for row in cursor.fetchall()]

    def update_company(self, company_id: int, **kwargs) -> bool:
        """Update company record"""
        if not kwargs:
            return False

        with self.transaction() as conn:
            cursor = conn.cursor()

            # Build update query
            fields = []
            values = []
            for key, value in kwargs.items():
                if key != 'company_id':
                    fields.append(f"{key} = ?")
                    values.append(value)

            values.append(company_id)
            query = f"UPDATE companies SET {', '.join(fields)} WHERE company_id = ?"

            cursor.execute(query, values)
            return cursor.rowcount > 0

    # ==================== Classification Operations ====================

    def add_classification(self, company_id: int, stage: str, method: str,
                          confidence: float, source: str) -> int:
        """Add new classification for a company"""
        with self.transaction() as conn:
            cursor = conn.cursor()

            # Mark previous classifications as not current
            cursor.execute("""
                UPDATE company_classifications
                SET is_current = 0
                WHERE company_id = ?
            """, (company_id,))

            # Insert new classification
            cursor.execute("""
                INSERT INTO company_classifications
                (company_id, company_stage, classification_method,
                 classification_confidence, classification_source, is_current)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (company_id, stage, method, confidence, source))

            return cursor.lastrowid

    def get_current_classification(self, company_id: int) -> Optional[Dict]:
        """Get current classification for a company"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM company_classifications
            WHERE company_id = ? AND is_current = 1
            ORDER BY classified_at DESC
            LIMIT 1
        """, (company_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ==================== SEC EDGAR Operations ====================

    def add_sec_edgar_data(self, company_id: int, sec_data: Dict) -> int:
        """Add SEC EDGAR data for a company"""
        with self.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR REPLACE INTO sec_edgar_data
                (company_id, cik, ticker, exchange, sic_code, company_name_edgar,
                 filing_count, latest_filing_date, latest_filing_type, company_status,
                 match_confidence, edgar_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                sec_data.get('cik'),
                sec_data.get('ticker'),
                sec_data.get('exchange'),
                sec_data.get('sic_code'),
                sec_data.get('company_name_edgar'),
                sec_data.get('filing_count'),
                sec_data.get('latest_filing_date'),
                sec_data.get('latest_filing_type'),
                sec_data.get('company_status'),
                sec_data.get('match_confidence'),
                sec_data.get('edgar_url')
            ))

            return cursor.lastrowid

    def get_sec_edgar_data(self, company_id: int) -> Optional[Dict]:
        """Get SEC EDGAR data for a company"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM sec_edgar_data WHERE company_id = ?
        """, (company_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    # ==================== Clinical Trials Operations ====================

    def add_clinical_trial(self, company_id: int, trial_data: Dict) -> int:
        """Add clinical trial data for a company"""
        with self.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR IGNORE INTO clinical_trials
                (company_id, nct_id, trial_title, trial_status, phase, enrollment,
                 start_date, completion_date, conditions, interventions, locations,
                 sponsor_name, match_confidence, clinicaltrials_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                trial_data.get('nct_id'),
                trial_data.get('trial_title'),
                trial_data.get('trial_status'),
                trial_data.get('phase'),
                trial_data.get('enrollment'),
                trial_data.get('start_date'),
                trial_data.get('completion_date'),
                json.dumps(trial_data.get('conditions', [])),
                json.dumps(trial_data.get('interventions', [])),
                json.dumps(trial_data.get('locations', [])),
                trial_data.get('sponsor_name'),
                trial_data.get('match_confidence'),
                trial_data.get('clinicaltrials_url')
            ))

            return cursor.lastrowid

    def get_company_trials(self, company_id: int) -> List[Dict]:
        """Get all clinical trials for a company"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT * FROM clinical_trials
            WHERE company_id = ?
            ORDER BY start_date DESC
        """, (company_id,))

        trials = []
        for row in cursor.fetchall():
            trial = dict(row)
            # Parse JSON fields
            trial['conditions'] = json.loads(trial.get('conditions', '[]'))
            trial['interventions'] = json.loads(trial.get('interventions', '[]'))
            trial['locations'] = json.loads(trial.get('locations', '[]'))
            trials.append(trial)

        return trials

    def get_trial_summary(self, company_id: int) -> Dict:
        """Get summary of clinical trials for a company"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT
                COUNT(*) as total_trials,
                SUM(CASE WHEN trial_status IN ('Recruiting', 'Active, not recruiting') THEN 1 ELSE 0 END) as active_trials,
                SUM(CASE WHEN trial_status = 'Completed' THEN 1 ELSE 0 END) as completed_trials,
                MAX(phase) as highest_phase
            FROM clinical_trials
            WHERE company_id = ?
        """, (company_id,))

        row = cursor.fetchone()
        return dict(row) if row else {}

    # ==================== Focus Area Operations ====================

    def add_focus_area(self, company_id: int, focus_area: str, method: str,
                      confidence: float, source: str) -> int:
        """Add focus area for a company"""
        with self.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR IGNORE INTO company_focus_areas
                (company_id, focus_area, extraction_method, extraction_confidence, extraction_source)
                VALUES (?, ?, ?, ?, ?)
            """, (company_id, focus_area, method, confidence, source))

            return cursor.lastrowid

    def get_company_focus_areas(self, company_id: int) -> List[str]:
        """Get all focus areas for a company"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT DISTINCT focus_area FROM company_focus_areas
            WHERE company_id = ?
            ORDER BY focus_area
        """, (company_id,))

        return [row[0] for row in cursor.fetchall()]

    # ==================== API Call Tracking ====================

    def log_api_call(self, provider: str, endpoint: str, company_id: Optional[int] = None,
                     status: int = 200, error: Optional[str] = None, cost: float = 0.0):
        """Log API call for tracking and debugging"""
        with self.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO api_calls
                (api_provider, endpoint, company_id, response_status, error_message, cost_estimate)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (provider, endpoint, company_id, status, error, cost))

    def get_api_call_stats(self, provider: Optional[str] = None) -> Dict:
        """Get API call statistics"""
        cursor = self.connection.cursor()

        where_clause = ""
        params = []
        if provider:
            where_clause = "WHERE api_provider = ?"
            params.append(provider)

        cursor.execute(f"""
            SELECT
                api_provider,
                COUNT(*) as total_calls,
                SUM(CASE WHEN response_status = 200 THEN 1 ELSE 0 END) as successful_calls,
                SUM(cost_estimate) as total_cost
            FROM api_calls
            {where_clause}
            GROUP BY api_provider
        """, params)

        stats = {}
        for row in cursor.fetchall():
            stats[row[0]] = {
                'total_calls': row[1],
                'successful_calls': row[2],
                'total_cost': row[3] or 0.0
            }

        return stats

    # ==================== Data Quality Operations ====================

    def add_quality_check(self, company_id: int, check_type: str, status: str,
                          message: str, details: Optional[Dict] = None):
        """Add data quality check result"""
        with self.transaction() as conn:
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO data_quality_checks
                (company_id, check_type, check_status, check_message, check_details)
                VALUES (?, ?, ?, ?, ?)
            """, (
                company_id,
                check_type,
                status,
                message,
                json.dumps(details) if details else None
            ))

    def get_quality_issues(self, status: str = 'fail') -> List[Dict]:
        """Get companies with quality issues"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT c.company_name, dqc.*
            FROM data_quality_checks dqc
            JOIN companies c ON dqc.company_id = c.company_id
            WHERE dqc.check_status = ?
            ORDER BY dqc.checked_at DESC
        """, (status,))

        return [dict(row) for row in cursor.fetchall()]

    # ==================== Statistics and Reporting ====================

    def get_enrichment_stats(self) -> Dict:
        """Get overall enrichment statistics"""
        cursor = self.connection.cursor()

        # Total companies
        cursor.execute("SELECT COUNT(*) FROM companies")
        total_companies = cursor.fetchone()[0]

        # Classification distribution
        cursor.execute("""
            SELECT company_stage, COUNT(*)
            FROM company_classifications
            WHERE is_current = 1
            GROUP BY company_stage
        """)
        classification_dist = dict(cursor.fetchall())

        # SEC EDGAR coverage
        cursor.execute("SELECT COUNT(*) FROM sec_edgar_data")
        sec_enriched = cursor.fetchone()[0]

        # Clinical trials coverage
        cursor.execute("SELECT COUNT(DISTINCT company_id) FROM clinical_trials")
        trials_enriched = cursor.fetchone()[0]

        # Focus areas coverage
        cursor.execute("SELECT COUNT(DISTINCT company_id) FROM company_focus_areas")
        focus_enriched = cursor.fetchone()[0]

        return {
            'total_companies': total_companies,
            'classification_distribution': classification_dist,
            'sec_enriched': sec_enriched,
            'sec_coverage': sec_enriched / total_companies * 100 if total_companies > 0 else 0,
            'trials_enriched': trials_enriched,
            'trials_coverage': trials_enriched / total_companies * 100 if total_companies > 0 else 0,
            'focus_enriched': focus_enriched,
            'focus_coverage': focus_enriched / total_companies * 100 if total_companies > 0 else 0,
        }

    def get_unknown_companies(self) -> List[Dict]:
        """Get companies with unknown classification"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT c.* FROM companies c
            LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
            WHERE cc.company_stage IS NULL OR cc.company_stage = 'Unknown' OR cc.company_stage = ''
            ORDER BY c.company_name
        """)

        return [dict(row) for row in cursor.fetchall()]

    def export_to_csv(self, output_path: str, include_enrichments: bool = True):
        """Export database to CSV format"""
        import csv

        cursor = self.connection.cursor()

        if include_enrichments:
            # Get enriched data view
            cursor.execute("""
                SELECT
                    c.*,
                    cc.company_stage,
                    cc.classification_confidence,
                    GROUP_CONCAT(DISTINCT cfa.focus_area) as focus_areas,
                    sed.ticker,
                    sed.cik,
                    sed.company_status as sec_status,
                    COUNT(DISTINCT ct.nct_id) as trial_count,
                    MAX(ct.phase) as highest_phase
                FROM companies c
                LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
                LEFT JOIN company_focus_areas cfa ON c.company_id = cfa.company_id
                LEFT JOIN sec_edgar_data sed ON c.company_id = sed.company_id
                LEFT JOIN clinical_trials ct ON c.company_id = ct.company_id
                GROUP BY c.company_id
                ORDER BY c.company_name
            """)
        else:
            cursor.execute("SELECT * FROM companies ORDER BY company_name")

        rows = cursor.fetchall()
        if not rows:
            logger.warning("No data to export")
            return

        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[d[0] for d in cursor.description])
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))

        logger.info(f"Exported {len(rows)} companies to {output_path}")


# Convenience functions for standalone use
def get_db_manager(db_path: str = "data/bayarea_biotech.db") -> DatabaseManager:
    """Get database manager instance"""
    return DatabaseManager(db_path)


def test_connection(db_path: str = "data/bayarea_biotech.db") -> bool:
    """Test database connection"""
    try:
        db = DatabaseManager(db_path)
        stats = db.get_enrichment_stats()
        logger.info(f"Database connected: {stats['total_companies']} companies found")
        db.close()
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


if __name__ == "__main__":
    # Test database connection if run directly
    if test_connection():
        print("Database connection successful!")
    else:
        print("Database connection failed!")