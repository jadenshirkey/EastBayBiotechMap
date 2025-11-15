#!/usr/bin/env python3
"""
Tests for extract_biopharmguy_companies.py (V4.3 Stage-A).

Tests validate:
- HTML parsing and company extraction
- Website field capture from second <a> tag
- NO Bay Area filtering (all CA companies extracted)
- Deduplication logic
- Validation checks (>0 rows, no duplicates, valid URLs)
- Cache functionality
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from extract_biopharmguy_companies import (
    extract_companies_from_biopharmguy,
    deduplicate_companies,
    validate_extraction_output,
    is_valid_url,
    load_cached_html,
    save_html_to_cache,
    get_cache_path,
)


@pytest.fixture
def sample_html():
    """Load the sample BPG HTML fixture."""
    fixture_path = Path(__file__).parent / 'fixtures' / 'bpg_sample.html'
    with open(fixture_path, 'r', encoding='utf-8') as f:
        return f.read()


@pytest.fixture
def sample_soup(sample_html):
    """BeautifulSoup object from sample HTML."""
    return BeautifulSoup(sample_html, 'html.parser')


class TestExtraction:
    """Tests for company extraction from HTML."""

    def test_extract_all_ca_companies(self, sample_soup):
        """Test that ALL CA companies are extracted (no Bay Area filtering)."""
        companies = extract_companies_from_biopharmguy(sample_soup)

        # Should extract all companies including non-Bay Area
        # (Genentech x2, Gilead, BioMarin, Amgen, Regeneron)
        assert len(companies) == 6

        # Verify non-Bay Area companies are included
        company_names = [c['Company Name'] for c in companies]
        assert 'Amgen' in company_names  # Thousand Oaks (not Bay Area)
        assert 'Regeneron Pharmaceuticals' in company_names  # San Diego (not Bay Area)

    def test_website_field_extraction(self, sample_soup):
        """Test that Website field is captured from second <a> tag."""
        companies = extract_companies_from_biopharmguy(sample_soup)

        # Find Genentech entry
        genentech = next(c for c in companies if 'Genentech' in c['Company Name'])
        assert genentech['Website'] == 'https://www.genentech.com'

        # Find Gilead entry
        gilead = next(c for c in companies if 'Gilead' in c['Company Name'])
        assert gilead['Website'] == 'https://www.gilead.com'

        # Find BioMarin entry (no website)
        biomarin = next(c for c in companies if 'BioMarin' in c['Company Name'])
        assert biomarin['Website'] == ''

    def test_city_extraction(self, sample_soup):
        """Test city name extraction and abbreviation handling."""
        companies = extract_companies_from_biopharmguy(sample_soup)

        # Check standard city names
        gilead = next(c for c in companies if 'Gilead' in c['Company Name'])
        assert gilead['City'] == 'Foster City'

        # Check abbreviation handling (South SF → South San Francisco)
        genentech = [c for c in companies if 'Genentech' in c['Company Name']]
        cities = [c['City'] for c in genentech]
        assert 'South San Francisco' in cities

    def test_focus_area_extraction(self, sample_soup):
        """Test that Focus Area (description) is extracted."""
        companies = extract_companies_from_biopharmguy(sample_soup)

        genentech = next(c for c in companies if 'Genentech' in c['Company Name'])
        assert 'oncology' in genentech['Focus Area'].lower()

    def test_csv_schema(self, sample_soup):
        """Test that output has correct column schema."""
        companies = extract_companies_from_biopharmguy(sample_soup)

        expected_fields = ['Company Name', 'Website', 'City', 'Focus Area', 'Source URL', 'Notes']

        for company in companies:
            for field in expected_fields:
                assert field in company, f"Missing field: {field}"


class TestDeduplication:
    """Tests for deduplication logic."""

    def test_removes_duplicates(self, sample_soup):
        """Test that duplicate company names are removed."""
        companies = extract_companies_from_biopharmguy(sample_soup)

        # Before deduplication: 6 companies (Genentech appears twice)
        assert len(companies) == 6

        # After deduplication
        deduplicated = deduplicate_companies(companies)
        assert len(deduplicated) == 5

        # Verify only one Genentech
        genentech_count = sum(1 for c in deduplicated if 'Genentech' in c['Company Name'])
        assert genentech_count == 1

    def test_case_insensitive_deduplication(self):
        """Test that deduplication is case-insensitive."""
        companies = [
            {'Company Name': 'Genentech', 'Website': 'https://www.genentech.com', 'City': 'South San Francisco', 'Focus Area': '', 'Source URL': '', 'Notes': ''},
            {'Company Name': 'GENENTECH', 'Website': 'https://www.genentech.com', 'City': 'South San Francisco', 'Focus Area': '', 'Source URL': '', 'Notes': ''},
            {'Company Name': 'genentech', 'Website': 'https://www.genentech.com', 'City': 'South San Francisco', 'Focus Area': '', 'Source URL': '', 'Notes': ''},
        ]

        deduplicated = deduplicate_companies(companies)
        assert len(deduplicated) == 1


class TestValidation:
    """Tests for validation logic."""

    def test_validation_passes_valid_data(self, sample_soup):
        """Test that validation passes for valid extraction."""
        companies = extract_companies_from_biopharmguy(sample_soup)
        deduplicated = deduplicate_companies(companies)

        is_valid, errors = validate_extraction_output(deduplicated)
        assert is_valid is True
        assert len(errors) == 0

    def test_validation_fails_empty_output(self):
        """Test that validation fails for empty output."""
        companies = []

        is_valid, errors = validate_extraction_output(companies)
        assert is_valid is False
        assert len(errors) > 0
        assert 'ERROR: Extraction produced 0 rows' in errors[0]

    def test_validation_fails_duplicate_names(self):
        """Test that validation fails for duplicate names."""
        companies = [
            {'Company Name': 'Genentech', 'Website': 'https://www.genentech.com', 'City': 'South San Francisco', 'Focus Area': '', 'Source URL': '', 'Notes': ''},
            {'Company Name': 'Genentech', 'Website': 'https://www.genentech.com', 'City': 'South San Francisco', 'Focus Area': '', 'Source URL': '', 'Notes': ''},
        ]

        is_valid, errors = validate_extraction_output(companies)
        assert is_valid is False
        assert 'duplicate' in errors[0].lower()

    def test_validation_fails_invalid_urls(self):
        """Test that validation fails for invalid URLs."""
        companies = [
            {'Company Name': 'Test Company', 'Website': 'not-a-valid-url', 'City': 'San Francisco', 'Focus Area': '', 'Source URL': '', 'Notes': ''},
        ]

        is_valid, errors = validate_extraction_output(companies)
        assert is_valid is False
        assert 'invalid url' in errors[0].lower()


class TestURLValidation:
    """Tests for URL validation helper."""

    def test_valid_urls(self):
        """Test that valid URLs are recognized."""
        assert is_valid_url('https://www.example.com') is True
        assert is_valid_url('http://example.com') is True
        assert is_valid_url('https://subdomain.example.com/path') is True

    def test_empty_url_is_valid(self):
        """Test that empty string is considered valid (allowed)."""
        assert is_valid_url('') is True
        assert is_valid_url('  ') is True

    def test_invalid_urls(self):
        """Test that invalid URLs are rejected."""
        assert is_valid_url('not-a-url') is False
        assert is_valid_url('www.example.com') is False  # Missing scheme
        assert is_valid_url('just text') is False


class TestCaching:
    """Tests for HTML caching functionality."""

    def test_cache_path_format(self):
        """Test that cache path follows correct naming convention."""
        cache_path = get_cache_path()
        assert 'bpg_ca_' in cache_path.name
        assert '.html' in cache_path.name

        # Verify date format YYYYMMDD
        date_str = datetime.now().strftime('%Y%m%d')
        assert date_str in cache_path.name

    def test_save_and_load_cache(self, tmp_path, monkeypatch):
        """Test that HTML can be saved and loaded from cache."""
        # Use temporary directory for cache
        cache_dir = tmp_path / 'cache'
        monkeypatch.setattr('extract_biopharmguy_companies.CACHE_DIR', cache_dir)

        test_html = '<html><body>Test content</body></html>'

        # Save to cache
        save_html_to_cache(test_html)

        # Load from cache
        loaded_html = load_cached_html()
        assert loaded_html == test_html

    def test_cache_expiration(self, tmp_path, monkeypatch):
        """Test that cache expires after 7 days."""
        # Use temporary directory for cache
        cache_dir = tmp_path / 'cache'
        cache_dir.mkdir()
        monkeypatch.setattr('extract_biopharmguy_companies.CACHE_DIR', cache_dir)

        # Create old cache file (8 days old)
        old_date = datetime.now() - timedelta(days=8)
        old_date_str = old_date.strftime('%Y%m%d')
        old_cache_file = cache_dir / f'bpg_ca_{old_date_str}.html'

        old_cache_file.write_text('old content')

        # Try to load - should return None (expired)
        loaded_html = load_cached_html()
        assert loaded_html is None

        # Verify old file was deleted
        assert not old_cache_file.exists()


class TestStatistics:
    """Tests for extraction statistics calculation."""

    def test_website_coverage_calculation(self, sample_soup):
        """Test that website coverage statistics are correct."""
        companies = extract_companies_from_biopharmguy(sample_soup)
        deduplicated = deduplicate_companies(companies)

        total_rows = len(deduplicated)
        rows_with_website = sum(1 for c in deduplicated if c['Website'].strip() != '')
        coverage_percentage = (rows_with_website / total_rows * 100) if total_rows > 0 else 0

        # We have 5 deduplicated companies
        # Genentech, Gilead, Amgen, Regeneron have websites
        # BioMarin has empty website
        assert total_rows == 5
        assert rows_with_website == 4
        assert coverage_percentage == 80.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
