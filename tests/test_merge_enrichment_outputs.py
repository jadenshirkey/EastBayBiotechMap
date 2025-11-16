"""
Tests for merge_enrichment_outputs.py script.

Tests include:
- Loading CSV files
- Deduplication logic
- Field normalization
- Merging Path A and Path B outputs

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import sys
import csv
import pytest
from pathlib import Path
from unittest.mock import patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import script functions
from scripts.merge_enrichment_outputs import (
    load_csv,
    deduplicate_companies,
    normalize_fields,
)


# ============================================================================
# Test load_csv
# ============================================================================

def test_load_csv_success(tmp_path):
    """Test loading CSV file."""
    # Create test CSV
    csv_file = tmp_path / "test.csv"
    with open(csv_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['Company Name', 'Website', 'City'])
        writer.writeheader()
        writer.writerow({'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'City': 'South San Francisco'})
        writer.writerow({'Company Name': 'BioMarin', 'Website': 'https://www.biomarin.com', 'City': 'San Rafael'})

    # Load
    rows = load_csv(csv_file)

    assert len(rows) == 2
    assert rows[0]['Company Name'] == 'Genentech'
    assert rows[1]['Company Name'] == 'BioMarin'


def test_load_csv_missing_file(tmp_path):
    """Test loading non-existent CSV file."""
    csv_file = tmp_path / "missing.csv"

    rows = load_csv(csv_file)

    assert rows == []


# ============================================================================
# Test deduplicate_companies
# ============================================================================

def test_deduplicate_companies_no_duplicates():
    """Test deduplication with no duplicates."""
    companies = [
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.95'},
        {'Company Name': 'BioMarin', 'Website': 'https://www.biomarin.com', 'Confidence': '0.90'},
        {'Company Name': 'Gilead', 'Website': 'https://www.gilead.com', 'Confidence': '0.92'},
    ]

    result = deduplicate_companies(companies)

    assert len(result) == 3


def test_deduplicate_companies_exact_duplicates():
    """Test deduplication with exact duplicates."""
    companies = [
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.95'},
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.95'},
        {'Company Name': 'BioMarin', 'Website': 'https://www.biomarin.com', 'Confidence': '0.90'},
    ]

    result = deduplicate_companies(companies)

    assert len(result) == 2
    assert result[0]['Company Name'] == 'Genentech'
    assert result[1]['Company Name'] == 'BioMarin'


def test_deduplicate_companies_case_insensitive():
    """Test deduplication is case-insensitive."""
    companies = [
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.95'},
        {'Company Name': 'GENENTECH', 'Website': 'https://www.gene.com', 'Confidence': '0.90'},
        {'Company Name': 'genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.85'},
    ]

    result = deduplicate_companies(companies)

    assert len(result) == 1
    # Should keep the one with highest confidence
    assert result[0]['Confidence'] == '0.95'


def test_deduplicate_companies_prefer_higher_confidence():
    """Test deduplication prefers higher confidence."""
    companies = [
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.75', 'Address': ''},
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.95', 'Address': '1 DNA Way'},
    ]

    result = deduplicate_companies(companies)

    assert len(result) == 1
    assert result[0]['Confidence'] == '0.95'
    assert result[0]['Address'] == '1 DNA Way'


def test_deduplicate_companies_prefer_more_complete():
    """Test deduplication prefers more complete data when confidence equal."""
    companies = [
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.90', 'Address': '', 'City': ''},
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.90', 'Address': '1 DNA Way', 'City': 'South San Francisco'},
    ]

    result = deduplicate_companies(companies)

    assert len(result) == 1
    assert result[0]['Address'] == '1 DNA Way'
    assert result[0]['City'] == 'South San Francisco'


def test_deduplicate_companies_empty_names():
    """Test deduplication skips empty company names."""
    companies = [
        {'Company Name': '', 'Website': 'https://www.gene.com', 'Confidence': '0.95'},
        {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'Confidence': '0.90'},
    ]

    result = deduplicate_companies(companies)

    assert len(result) == 1
    assert result[0]['Company Name'] == 'Genentech'


# ============================================================================
# Test normalize_fields
# ============================================================================

def test_normalize_fields_path_a():
    """Test field normalization for Path A data."""
    companies = [
        {
            'Company Name': 'Genentech',
            'Website': 'https://www.gene.com',
            'City': 'South San Francisco',
            'Address': '1 DNA Way',
            'Company Stage': '',
            'Focus Areas': '',
            'Validation_Source': 'PathA',
            'Place_ID': 'place_123',
            'Confidence_Det': '0.95',
            'Validation_Reason': 'name_sim=0.98(+0.39); website_match(gene.com,+0.3); geofence_ok(+0.2)'
        }
    ]

    result = normalize_fields(companies)

    assert len(result) == 1
    assert result[0]['Company Name'] == 'Genentech'
    assert result[0]['Confidence'] == '0.95'
    assert result[0]['Validation_Notes'] == 'name_sim=0.98(+0.39); website_match(gene.com,+0.3); geofence_ok(+0.2)'
    assert result[0]['Validation_Source'] == 'PathA'


def test_normalize_fields_path_b():
    """Test field normalization for Path B data."""
    companies = [
        {
            'Company Name': '10X Genomics',
            'Website': 'https://www.10xgenomics.com',
            'City': 'Pleasanton',
            'Address': '6230 Stoneridge Mall Rd',
            'Company Stage': '',
            'Focus Areas': '',
            'Validation_Source': 'PathB',
            'Place_ID': 'place_456',
            'Confidence': '0.92',
            'Validation_JSON': '{"in_bay_area": true, "is_business": true, "brand_domain_ok": true, "reasoning": "Strong match"}'
        }
    ]

    result = normalize_fields(companies)

    assert len(result) == 1
    assert result[0]['Company Name'] == '10X Genomics'
    assert result[0]['Confidence'] == '0.92'
    assert result[0]['Validation_Notes'] == '{"in_bay_area": true, "is_business": true, "brand_domain_ok": true, "reasoning": "Strong match"}'
    assert result[0]['Validation_Source'] == 'PathB'


def test_normalize_fields_missing_fields():
    """Test field normalization handles missing fields."""
    companies = [
        {
            'Company Name': 'Test Company',
            'Website': 'https://www.test.com',
        }
    ]

    result = normalize_fields(companies)

    assert len(result) == 1
    assert result[0]['Company Name'] == 'Test Company'
    assert result[0]['Website'] == 'https://www.test.com'
    assert result[0]['City'] == ''
    assert result[0]['Address'] == ''
    assert result[0]['Confidence'] == ''
    assert result[0]['Validation_Source'] == ''


def test_normalize_fields_mixed_sources():
    """Test field normalization with mixed Path A and Path B data."""
    companies = [
        {
            'Company Name': 'Genentech',
            'Website': 'https://www.gene.com',
            'City': 'South San Francisco',
            'Address': '1 DNA Way',
            'Validation_Source': 'PathA',
            'Place_ID': 'place_123',
            'Confidence_Det': '0.95',
            'Validation_Reason': 'PathA validation'
        },
        {
            'Company Name': '10X Genomics',
            'Website': 'https://www.10xgenomics.com',
            'City': 'Pleasanton',
            'Address': '6230 Stoneridge Mall Rd',
            'Validation_Source': 'PathB',
            'Place_ID': 'place_456',
            'Confidence': '0.92',
            'Validation_JSON': '{"in_bay_area": true}'
        }
    ]

    result = normalize_fields(companies)

    assert len(result) == 2
    assert result[0]['Validation_Source'] == 'PathA'
    assert result[0]['Validation_Notes'] == 'PathA validation'
    assert result[1]['Validation_Source'] == 'PathB'
    assert result[1]['Validation_Notes'] == '{"in_bay_area": true}'


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_merge_pipeline():
    """Test full merge pipeline."""
    # Mock Path A data
    path_a = [
        {
            'Company Name': 'Genentech',
            'Website': 'https://www.gene.com',
            'City': 'South San Francisco',
            'Address': '1 DNA Way',
            'Validation_Source': 'PathA',
            'Confidence_Det': '0.95',
            'Validation_Reason': 'PathA validation',
            'Place_ID': 'place_123'
        },
        {
            'Company Name': 'BioMarin',
            'Website': 'https://www.biomarin.com',
            'City': 'San Rafael',
            'Address': '105 Digital Drive',
            'Validation_Source': 'PathA',
            'Confidence_Det': '0.90',
            'Validation_Reason': 'PathA validation',
            'Place_ID': 'place_456'
        }
    ]

    # Mock Path B data
    path_b = [
        {
            'Company Name': '10X Genomics',
            'Website': 'https://www.10xgenomics.com',
            'City': 'Pleasanton',
            'Address': '6230 Stoneridge Mall Rd',
            'Validation_Source': 'PathB',
            'Confidence': '0.92',
            'Validation_JSON': '{"in_bay_area": true}',
            'Place_ID': 'place_789'
        },
        {
            'Company Name': 'Genentech',  # Duplicate
            'Website': 'https://www.gene.com',
            'City': 'South San Francisco',
            'Address': '1 DNA Way',
            'Validation_Source': 'PathB',
            'Confidence': '0.85',  # Lower confidence
            'Validation_JSON': '{"in_bay_area": true}',
            'Place_ID': 'place_123'
        }
    ]

    # Combine
    all_companies = path_a + path_b

    # Deduplicate
    deduplicated = deduplicate_companies(all_companies)

    # Should remove duplicate Genentech (keep PathA version with higher confidence)
    assert len(deduplicated) == 3

    # Normalize
    normalized = normalize_fields(deduplicated)

    assert len(normalized) == 3

    # Verify standard fields
    for company in normalized:
        assert 'Company Name' in company
        assert 'Website' in company
        assert 'City' in company
        assert 'Address' in company
        assert 'Company Stage' in company
        assert 'Focus Areas' in company
        assert 'Validation_Source' in company
        assert 'Place_ID' in company
        assert 'Confidence' in company
        assert 'Validation_Notes' in company

    # Verify Genentech has PathA data (higher confidence)
    genentech = [c for c in normalized if c['Company Name'] == 'Genentech'][0]
    assert genentech['Validation_Source'] == 'PathA'
    assert genentech['Confidence'] == '0.95'
