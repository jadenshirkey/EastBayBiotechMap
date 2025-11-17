#!/usr/bin/env python3
"""
SEC EDGAR API Client
Identifies public biotech companies and enriches with filing data
Uses free SEC EDGAR API with no authentication required
"""

import requests
import json
import time
import logging
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta
import sqlite3
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import RequestException, Timeout, ConnectionError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SECEdgarClient:
    """Client for SEC EDGAR API interactions"""

    def __init__(self, user_agent: str = None):
        """Initialize SEC EDGAR client

        Args:
            user_agent: Required by SEC (should include email)
        """
        import os

        if not user_agent:
            user_agent = os.environ.get("SEC_EDGAR_USER_AGENT")

        # Validate User-Agent is provided and not the default placeholder
        if not user_agent or "youremail@example.com" in user_agent or "@example.com" in user_agent:
            raise ValueError(
                "SEC EDGAR requires a valid User-Agent with your email address.\n"
                "Please set the SEC_EDGAR_USER_AGENT environment variable.\n"
                "Format: 'YourAppName/1.0 (your.email@domain.com)'\n"
                "This is required by SEC Terms of Service to identify API users."
            )

        # Validate email format in User-Agent
        import re
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if not re.search(email_pattern, user_agent):
            raise ValueError(
                "User-Agent must include a valid email address.\n"
                "Format: 'YourAppName/1.0 (your.email@domain.com)'"
            )

        self.headers = {
            "User-Agent": user_agent,
            "Accept": "application/json"
        }

        logger.info(f"SEC EDGAR client initialized with User-Agent: {user_agent}")

        # SEC endpoints
        self.base_url = "https://data.sec.gov"
        self.submissions_url = "https://data.sec.gov/submissions"
        # Use the endpoint that includes exchange data
        self.tickers_url = "https://www.sec.gov/files/company_tickers_exchange.json"
        self.search_url = "https://efts.sec.gov/LATEST/search-index"

        # Rate limiting (SEC allows 10 requests per second)
        self.rate_limit_delay = 0.1  # 100ms between requests
        self.last_request_time = 0

        # Cache for company tickers
        self.tickers_cache = {}
        self.tickers_loaded = False

    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)

        self.last_request_time = time.time()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((RequestException, Timeout, ConnectionError)),
        before_sleep=lambda retry_state: logger.warning(f"Retrying SEC API request (attempt {retry_state.attempt_number})...")
    )
    def _make_request(self, url: str, timeout: int = 30) -> requests.Response:
        """Make HTTP request with retry logic"""
        self._rate_limit()
        response = requests.get(url, headers=self.headers, timeout=timeout)
        response.raise_for_status()
        return response

    def load_company_tickers(self) -> bool:
        """Load all company tickers from SEC

        Returns:
            bool: True if successful
        """
        if self.tickers_loaded:
            return True

        try:
            response = self._make_request(self.tickers_url)

            data = response.json()

            # Build multiple lookup indices
            for entry in data.values():
                cik = str(entry.get('cik_str', '')).zfill(10)
                ticker = entry.get('ticker', '').upper()
                title = entry.get('title', '').upper()
                # Extract exchange data from the new endpoint
                exchange = entry.get('exchange', '').upper() if entry.get('exchange') else None

                # Index by ticker
                if ticker:
                    self.tickers_cache[ticker] = {
                        'cik': cik,
                        'ticker': ticker,
                        'company_name': title,
                        'exchange': exchange  # Now populated from data
                    }

                # Index by normalized company name
                norm_name = self._normalize_company_name(title)
                if norm_name:
                    self.tickers_cache[norm_name] = {
                        'cik': cik,
                        'ticker': ticker,
                        'company_name': title,
                        'exchange': exchange
                    }

            self.tickers_loaded = True
            logger.info(f"Loaded {len(self.tickers_cache)} ticker mappings")
            return True

        except Exception as e:
            logger.error(f"Failed to load company tickers: {e}")
            return False

    def _normalize_company_name(self, name: str) -> str:
        """Normalize company name for matching

        Args:
            name: Company name to normalize

        Returns:
            str: Normalized name
        """
        if not name:
            return ""

        # Convert to uppercase
        name = name.upper()

        # Remove common suffixes
        suffixes = [
            r'\s+INC\.?$', r'\s+INCORPORATED$', r'\s+CORP\.?$',
            r'\s+CORPORATION$', r'\s+LLC\.?$', r'\s+L\.?L\.?C\.?$',
            r'\s+LTD\.?$', r'\s+LIMITED$', r'\s+PLC\.?$',
            r'\s+CO\.?$', r'\s+COMPANY$', r'\s+LP\.?$',
            r'\s+L\.?P\.?$', r'\s+HOLDINGS?$', r'\s+GROUP$',
            r'\s+INTERNATIONAL$', r'\s+USA?$', r'\s+AMERICAS?$'
        ]

        for suffix in suffixes:
            name = re.sub(suffix, '', name, flags=re.IGNORECASE)

        # Remove special characters except spaces
        name = re.sub(r'[^\w\s]', '', name)

        # Normalize whitespace
        name = ' '.join(name.split())

        return name.strip()

    def search_by_name(self, company_name: str) -> Optional[Dict]:
        """Search for company by name

        Args:
            company_name: Company name to search

        Returns:
            Dict with company data or None
        """
        if not self.tickers_loaded:
            self.load_company_tickers()

        # Try exact match first
        norm_name = self._normalize_company_name(company_name)
        if norm_name in self.tickers_cache:
            match = self.tickers_cache[norm_name]
            logger.info(f"Exact match for {company_name}: {match['ticker']}")
            return {
                **match,
                'match_confidence': 0.95,
                'match_type': 'exact_name'
            }

        # Try fuzzy matching
        best_match = self._fuzzy_match(company_name)
        if best_match:
            return best_match

        # Try SEC search API as fallback
        return self._search_sec_api(company_name)

    def _fuzzy_match(self, company_name: str) -> Optional[Dict]:
        """Fuzzy match company name against ticker cache

        Args:
            company_name: Company name to match

        Returns:
            Best match or None
        """
        norm_name = self._normalize_company_name(company_name)
        if not norm_name:
            return None

        words = set(norm_name.split())
        if len(words) < 2:  # Too short for reliable fuzzy matching
            return None

        best_match = None
        best_score = 0

        for cached_name, data in self.tickers_cache.items():
            if not isinstance(cached_name, str):
                continue

            cached_words = set(cached_name.split())

            # Calculate Jaccard similarity
            intersection = len(words & cached_words)
            union = len(words | cached_words)

            if union > 0:
                score = intersection / union

                # Require at least 60% similarity
                if score > 0.6 and score > best_score:
                    best_score = score
                    best_match = {
                        **data,
                        'match_confidence': score,
                        'match_type': 'fuzzy_name'
                    }

        if best_match:
            logger.info(f"Fuzzy match for {company_name}: {best_match['ticker']} (score: {best_score:.2f})")

        return best_match

    def _search_sec_api(self, company_name: str) -> Optional[Dict]:
        """Search using SEC's search API

        Args:
            company_name: Company name to search

        Returns:
            Company data or None
        """
        try:
            self._rate_limit()

            params = {
                'q': company_name,
                'category': 'custom',
                'forms': '10-K,10-Q,8-K,DEF 14A'
            }

            response = requests.get(
                self.search_url,
                params=params,
                headers=self.headers,
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()

                hits = data.get('hits', {}).get('hits', [])
                if hits:
                    hit = hits[0]['_source']

                    ciks = hit.get('ciks', [])
                    tickers = hit.get('tickers', [])
                    names = hit.get('display_names', [])

                    if ciks and ciks[0]:
                        return {
                            'cik': str(ciks[0]).zfill(10),
                            'ticker': tickers[0] if tickers else None,
                            'company_name': names[0] if names else company_name,
                            'match_confidence': 0.7,
                            'match_type': 'sec_search'
                        }

            return None

        except Exception as e:
            logger.debug(f"SEC search failed for {company_name}: {e}")
            return None

    def get_company_filings(self, cik: str, limit: int = 10) -> Tuple[List[Dict], Optional[str]]:
        """Get recent filings for a company and extract SIC code

        Args:
            cik: Company CIK number
            limit: Maximum number of filings to return

        Returns:
            Tuple of (List of filing dictionaries, SIC code)
        """
        try:
            # Format CIK with leading zeros
            cik = str(cik).zfill(10)

            self._rate_limit()

            url = f"{self.submissions_url}/CIK{cik}.json"
            response = requests.get(url, headers=self.headers, timeout=10)

            if response.status_code == 404:
                return [], None

            response.raise_for_status()
            data = response.json()

            # Extract SIC code
            sic_code = data.get('sic', None)
            if sic_code:
                sic_code = str(sic_code)

            filings = []
            recent = data.get('filings', {}).get('recent', {})

            if recent:
                forms = recent.get('form', [])
                dates = recent.get('filingDate', [])
                accessions = recent.get('accessionNumber', [])

                for i in range(min(limit, len(forms))):
                    filings.append({
                        'form': forms[i] if i < len(forms) else None,
                        'filing_date': dates[i] if i < len(dates) else None,
                        'accession_number': accessions[i] if i < len(accessions) else None
                    })

            return filings, sic_code

        except Exception as e:
            logger.error(f"Failed to get filings for CIK {cik}: {e}")
            return [], None

    def classify_company_status(self, cik: str) -> Tuple[str, float, Optional[str]]:
        """Classify company status based on filings

        Args:
            cik: Company CIK number

        Returns:
            Tuple of (status, confidence, sic_code)
        """
        filings, sic_code = self.get_company_filings(cik, limit=20)

        if not filings:
            return 'unknown', 0.0, sic_code

        # Check for recent filings
        latest_filing = filings[0] if filings else None
        if not latest_filing:
            return 'unknown', 0.0, sic_code

        filing_date_str = latest_filing.get('filing_date')
        if not filing_date_str:
            return 'unknown', 0.0, sic_code

        try:
            filing_date = datetime.strptime(filing_date_str, '%Y-%m-%d')
            days_since_filing = (datetime.now() - filing_date).days

            # Check filing types
            recent_forms = [f.get('form', '') for f in filings[:10]]

            # Active public company (recent 10-K or 10-Q)
            if any(form in ['10-K', '10-Q'] for form in recent_forms[:5]):
                if days_since_filing < 180:
                    return 'public', 0.95, sic_code
                elif days_since_filing < 365:
                    return 'public', 0.85, sic_code
                else:
                    return 'formerly_public', 0.75, sic_code

            # Check for acquisition indicators
            if any(form in ['SC 13D', 'SC 13G', 'SC TO-T'] for form in recent_forms):
                return 'acquired', 0.8, sic_code

            # Has SEC filings but not regular reporting
            if recent_forms:
                return 'public', 0.7, sic_code

            return 'unknown', 0.0, sic_code

        except Exception as e:
            logger.error(f"Error classifying company status: {e}")
            return 'unknown', 0.0, sic_code

    def enrich_company(self, company_name: str, website: str = None) -> Optional[Dict]:
        """Full enrichment pipeline for a company

        Args:
            company_name: Company name
            website: Company website (optional)

        Returns:
            Enriched company data or None
        """
        # Search for company
        match = self.search_by_name(company_name)

        if not match:
            return None

        # Get additional data
        cik = match.get('cik')
        if cik:
            # Get recent filings and SIC code
            filings, sic_code = self.get_company_filings(cik, limit=10)
            match['filings'] = filings
            match['filing_count'] = len(filings)
            match['sic_code'] = sic_code  # Add SIC code to match

            if filings:
                match['latest_filing_date'] = filings[0].get('filing_date')
                match['latest_filing_type'] = filings[0].get('form')

            # Classify status (also returns SIC code but we already have it)
            status, confidence, _ = self.classify_company_status(cik)
            match['company_status'] = status
            match['status_confidence'] = confidence

            # Build EDGAR URL
            match['edgar_url'] = f"https://www.sec.gov/cgi-bin/browse-edgar?CIK={cik}"

        # Note: exchange should already be in match from search_by_name if available
        return match


class SECEdgarEnricher:
    """Enricher class for batch processing companies"""

    def __init__(self, db_path: str, user_agent: str = None):
        """Initialize enricher

        Args:
            db_path: Path to SQLite database
            user_agent: SEC required user agent with email
        """
        self.db_path = Path(db_path)
        self.client = SECEdgarClient(user_agent)
        self.conn = None
        self.cursor = None

        # Statistics
        self.stats = {
            'processed': 0,
            'found': 0,
            'public': 0,
            'errors': 0
        }

    def connect_db(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close_db(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def get_companies_to_process(self) -> List[Tuple]:
        """Get companies that need SEC enrichment

        Returns:
            List of (company_id, company_name, website) tuples
        """
        self.cursor.execute("""
            SELECT c.company_id, c.company_name, c.website
            FROM companies c
            LEFT JOIN sec_edgar_data sed ON c.company_id = sed.company_id
            WHERE sed.company_id IS NULL
            ORDER BY c.company_name
        """)

        return self.cursor.fetchall()

    def save_sec_data(self, company_id: int, sec_data: Dict):
        """Save SEC data to database

        Args:
            company_id: Company ID
            sec_data: SEC enrichment data
        """
        try:
            # Insert SEC data (including exchange and SIC code)
            self.cursor.execute("""
                INSERT INTO sec_edgar_data (
                    company_id, cik, ticker, exchange, sic_code, company_name_edgar,
                    filing_count, latest_filing_date, latest_filing_type,
                    company_status, match_confidence, edgar_url
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_id,
                sec_data.get('cik'),
                sec_data.get('ticker'),
                sec_data.get('exchange'),  # Now populated from API
                sec_data.get('sic_code'),  # Now populated from API
                sec_data.get('company_name'),
                sec_data.get('filing_count', 0),
                sec_data.get('latest_filing_date'),
                sec_data.get('latest_filing_type'),
                sec_data.get('company_status'),
                sec_data.get('match_confidence'),
                sec_data.get('edgar_url')
            ))

            # Update classification if public
            if sec_data.get('company_status') == 'public':
                self.cursor.execute("""
                    INSERT INTO company_classifications (
                        company_id, company_stage, classification_method,
                        classification_confidence, classification_source
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    company_id, 'Public', 'sec_edgar',
                    sec_data.get('status_confidence', 0.9),
                    'SEC EDGAR'
                ))

            # Log API call
            self.cursor.execute("""
                INSERT INTO api_calls (
                    api_provider, endpoint, company_id, response_status
                ) VALUES (?, ?, ?, ?)
            """, ('sec_edgar', 'company_search', company_id, 200))

            self.conn.commit()

        except Exception as e:
            logger.error(f"Failed to save SEC data: {e}")
            self.conn.rollback()

    def process_all(self):
        """Process all companies for SEC enrichment"""
        try:
            self.connect_db()

            # Load ticker cache first
            logger.info("Loading SEC ticker cache...")
            if not self.client.load_company_tickers():
                logger.error("Failed to load ticker cache")
                return

            # Get companies to process
            companies = self.get_companies_to_process()
            total = len(companies)

            logger.info(f"Processing {total} companies for SEC enrichment")

            for company_id, company_name, website in companies:
                self.stats['processed'] += 1

                # Progress indicator
                if self.stats['processed'] % 10 == 0:
                    pct = (self.stats['processed'] / total) * 100
                    logger.info(f"Progress: {self.stats['processed']}/{total} ({pct:.1f}%)")

                # Enrich company
                sec_data = self.client.enrich_company(company_name, website)

                if sec_data:
                    self.stats['found'] += 1

                    if sec_data.get('company_status') == 'public':
                        self.stats['public'] += 1
                        logger.info(f"PUBLIC: {company_name} -> {sec_data.get('ticker')}")

                    self.save_sec_data(company_id, sec_data)
                else:
                    # Mark as checked even if not found
                    self.cursor.execute("""
                        INSERT INTO api_calls (
                            api_provider, endpoint, company_id, response_status
                        ) VALUES (?, ?, ?, ?)
                    """, ('sec_edgar', 'company_search', company_id, 404))
                    self.conn.commit()

            # Final statistics
            logger.info("="*60)
            logger.info("SEC EDGAR ENRICHMENT COMPLETE")
            logger.info("="*60)
            logger.info(f"Processed: {self.stats['processed']} companies")
            logger.info(f"Found in SEC: {self.stats['found']}")
            logger.info(f"Public companies: {self.stats['public']}")
            logger.info(f"Match rate: {(self.stats['found']/total*100):.1f}%")

        except Exception as e:
            logger.error(f"Processing failed: {e}")

        finally:
            self.close_db()


if __name__ == "__main__":
    # Test the client
    import sys

    if len(sys.argv) > 1:
        # Test single company
        client = SECEdgarClient()
        result = client.enrich_company(sys.argv[1])
        if result:
            print(json.dumps(result, indent=2))
        else:
            print(f"No match found for {sys.argv[1]}")
    else:
        # Run full enrichment
        enricher = SECEdgarEnricher("data/bayarea_biotech_sources.db")
        enricher.process_all()