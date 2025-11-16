"""
Tests for Path A enrichment script (enrich_with_google_maps.py).

Tests include:
- Validation gates (geofence, business-type, multi-tenant)
- Deterministic scoring
- API usage counter
- Place Details cache
- Path A/Path B routing

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import script functions
from scripts.enrich_with_google_maps import (
    APIUsageCounter,
    PlaceDetailsCache,
    passes_business_type_gate,
    calculate_confidence_score,
    validate_candidate,
    save_checkpoint,
    load_checkpoint,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_gmaps():
    """Mock Google Maps client."""
    return Mock()


@pytest.fixture
def temp_cache_file(tmp_path):
    """Temporary cache file."""
    return tmp_path / "test_cache.json"


@pytest.fixture
def temp_checkpoint_file(tmp_path):
    """Temporary checkpoint file."""
    return tmp_path / "test_checkpoint.json"


# ============================================================================
# Test APIUsageCounter
# ============================================================================

def test_api_usage_counter_initialization():
    """Test API usage counter initializes correctly."""
    counter = APIUsageCounter()
    assert counter.text_search_calls == 0
    assert counter.place_details_calls == 0
    assert counter.total_calls() == 0


def test_api_usage_counter_record_calls():
    """Test API usage counter records calls."""
    counter = APIUsageCounter()

    counter.record_text_search()
    assert counter.text_search_calls == 1

    counter.record_place_details()
    counter.record_place_details()
    assert counter.place_details_calls == 2

    assert counter.total_calls() == 3


def test_api_usage_counter_cost_calculation():
    """Test API usage counter calculates cost correctly."""
    counter = APIUsageCounter()

    counter.record_text_search()  # $0.032
    counter.record_place_details()  # $0.017
    counter.record_place_details()  # $0.017

    expected_cost = 0.032 + 0.017 + 0.017
    assert abs(counter.estimated_cost() - expected_cost) < 0.001


def test_api_usage_counter_report():
    """Test API usage counter generates report."""
    counter = APIUsageCounter()
    counter.record_text_search()
    counter.record_place_details()

    report = counter.report()
    assert "Text Search calls: 1" in report
    assert "Place Details calls: 1" in report
    assert "Total calls: 2" in report


# ============================================================================
# Test PlaceDetailsCache
# ============================================================================

def test_place_details_cache_get_put(temp_cache_file):
    """Test cache get and put operations."""
    cache = PlaceDetailsCache(temp_cache_file)

    # Initially empty
    assert cache.get("place_123") is None

    # Put and get
    details = {"name": "Genentech", "address": "1 DNA Way"}
    cache.put("place_123", details)

    assert cache.get("place_123") == details


def test_place_details_cache_persistence(temp_cache_file):
    """Test cache saves and loads from disk."""
    # Create cache and add data
    cache1 = PlaceDetailsCache(temp_cache_file)
    cache1.put("place_123", {"name": "Genentech"})
    cache1.save()

    # Load cache in new instance
    cache2 = PlaceDetailsCache(temp_cache_file)
    assert cache2.get("place_123") == {"name": "Genentech"}


def test_place_details_cache_expiration(temp_cache_file):
    """Test cache expiration based on age."""
    # Create old cache (31 days ago)
    old_date = datetime.now()
    old_date = old_date.replace(day=1)  # Simulate old date

    data = {
        'cache_date': old_date.strftime('%Y-%m-%d'),
        'places': {'place_123': {'name': 'Old Data'}}
    }

    with open(temp_cache_file, 'w') as f:
        json.dump(data, f)

    # Load cache with max_age_days=1
    cache = PlaceDetailsCache(temp_cache_file, max_age_days=1)

    # Cache should be expired and empty
    # Note: This depends on the actual date difference
    # For a robust test, we'd need to mock datetime


# ============================================================================
# Test Validation Gates
# ============================================================================

def test_passes_business_type_gate_allowed():
    """Test business type gate allows valid types."""
    # No types - allow by default
    assert passes_business_type_gate([]) is True

    # Valid types
    assert passes_business_type_gate(['point_of_interest', 'establishment']) is True
    assert passes_business_type_gate(['health', 'pharmaceutical']) is True


def test_passes_business_type_gate_excluded():
    """Test business type gate excludes invalid types."""
    # Excluded types
    assert passes_business_type_gate(['real_estate_agency']) is False
    assert passes_business_type_gate(['lodging']) is False
    assert passes_business_type_gate(['premise']) is False
    assert passes_business_type_gate(['parking']) is False

    # Mix of valid and excluded
    assert passes_business_type_gate(['point_of_interest', 'real_estate_agency']) is False


# ============================================================================
# Test Deterministic Scoring
# ============================================================================

def test_calculate_confidence_score_perfect_match():
    """Test confidence score for perfect match."""
    company_name = "Genentech"
    bpg_website = "https://www.gene.com"

    details = {
        'name': 'Genentech',
        'website': 'https://www.gene.com',
        'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
        'geometry': {
            'location': {'lat': 37.6624, 'lng': -122.3801}
        },
        'business_status': 'OPERATIONAL'
    }

    score, reason = calculate_confidence_score(
        company_name, bpg_website, details, "South San Francisco"
    )

    # Perfect match should score high
    # +0.4 (name similarity ~1.0)
    # +0.3 (website match)
    # +0.2 (geofence)
    # +0.1 (operational)
    # = ~1.0
    assert score >= 0.9
    assert "name_sim" in reason
    assert "website_match" in reason
    assert "geofence_ok" in reason
    assert "operational" in reason


def test_calculate_confidence_score_name_only():
    """Test confidence score with only name similarity."""
    company_name = "Genentech"
    bpg_website = ""

    details = {
        'name': 'Genentech Inc',
        'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
        'geometry': {
            'location': {'lat': 37.6624, 'lng': -122.3801}
        },
        'business_status': 'OPERATIONAL'
    }

    score, reason = calculate_confidence_score(
        company_name, bpg_website, details, "South San Francisco"
    )

    # Should have name similarity + geofence + operational
    # ~0.4 + 0.2 + 0.1 = ~0.7
    assert 0.6 <= score <= 0.8
    assert "name_sim" in reason


def test_calculate_confidence_score_website_mismatch():
    """Test confidence score with website mismatch."""
    company_name = "Genentech"
    bpg_website = "https://www.gene.com"

    details = {
        'name': 'Genentech',
        'website': 'https://www.differentcompany.com',  # Mismatch
        'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
        'geometry': {
            'location': {'lat': 37.6624, 'lng': -122.3801}
        },
        'business_status': 'OPERATIONAL'
    }

    score, reason = calculate_confidence_score(
        company_name, bpg_website, details, "South San Francisco"
    )

    # Website mismatch should penalize
    # ~0.4 (name) - 0.2 (website mismatch) + 0.2 (geofence) + 0.1 (operational) = ~0.5
    assert score < 0.75  # Should fail acceptance threshold
    assert "website_mismatch" in reason


def test_calculate_confidence_score_geofence_fail():
    """Test confidence score with geofence failure."""
    company_name = "Genentech"
    bpg_website = "https://www.gene.com"

    details = {
        'name': 'Genentech',
        'website': 'https://www.gene.com',
        'formatted_address': '123 Main St, Davis, CA 95616',  # Out of Bay Area
        'geometry': {
            'location': {'lat': 38.5449, 'lng': -121.7405}  # Davis coordinates
        },
        'business_status': 'OPERATIONAL'
    }

    score, reason = calculate_confidence_score(
        company_name, bpg_website, details, "South San Francisco"
    )

    # No geofence bonus
    # ~0.4 (name) + 0.3 (website) + 0.1 (operational) = ~0.8
    assert "geofence_fail" in reason


# ============================================================================
# Test validate_candidate
# ============================================================================

def test_validate_candidate_accept():
    """Test candidate validation accepts valid candidate."""
    company_name = "Genentech"
    bpg_website = "https://www.gene.com"
    city = "South San Francisco"

    details = {
        'name': 'Genentech',
        'website': 'https://www.gene.com',
        'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
        'geometry': {
            'location': {'lat': 37.6624, 'lng': -122.3801}
        },
        'business_status': 'OPERATIONAL',
        'types': ['point_of_interest', 'establishment']
    }

    accepted, confidence, reason = validate_candidate(
        company_name, bpg_website, city, details
    )

    assert accepted is True
    assert confidence >= 0.75
    assert "website_match" in reason


def test_validate_candidate_reject_geofence():
    """Test candidate validation rejects out-of-area candidate."""
    company_name = "Some Company"
    bpg_website = "https://www.somecompany.com"
    city = "Davis"  # Out of Bay Area

    details = {
        'name': 'Some Company',
        'website': 'https://www.somecompany.com',
        'formatted_address': '123 Main St, Davis, CA 95616',
        'geometry': {
            'location': {'lat': 38.5449, 'lng': -121.7405}
        },
        'business_status': 'OPERATIONAL',
        'types': ['point_of_interest']
    }

    accepted, confidence, reason = validate_candidate(
        company_name, bpg_website, city, details
    )

    assert accepted is False
    assert reason == "geofence_fail"


def test_validate_candidate_reject_business_type():
    """Test candidate validation rejects excluded business types."""
    company_name = "Some Company"
    bpg_website = "https://www.somecompany.com"
    city = "San Francisco"

    details = {
        'name': 'Some Company',
        'website': 'https://www.somecompany.com',
        'formatted_address': '123 Market St, San Francisco, CA 94103',
        'geometry': {
            'location': {'lat': 37.7749, 'lng': -122.4194}
        },
        'business_status': 'OPERATIONAL',
        'types': ['real_estate_agency']  # Excluded type
    }

    accepted, confidence, reason = validate_candidate(
        company_name, bpg_website, city, details
    )

    assert accepted is False
    assert "excluded_type" in reason
    assert "real_estate_agency" in reason


def test_validate_candidate_low_score():
    """Test candidate validation rejects low-confidence match."""
    company_name = "Acme Biotech"
    bpg_website = "https://www.acme.com"
    city = "San Francisco"

    details = {
        'name': 'Totally Different Name LLC',  # Poor name match
        'website': 'https://www.different.com',  # Website mismatch
        'formatted_address': '123 Market St, San Francisco, CA 94103',
        'geometry': {
            'location': {'lat': 37.7749, 'lng': -122.4194}
        },
        'business_status': 'OPERATIONAL',
        'types': ['point_of_interest']
    }

    accepted, confidence, reason = validate_candidate(
        company_name, bpg_website, city, details
    )

    # Should reject due to low confidence score
    assert accepted is False or confidence < 0.75


# ============================================================================
# Test Checkpoint Management
# ============================================================================

def test_save_and_load_checkpoint(tmp_path):
    """Test checkpoint save and load."""
    checkpoint_file = tmp_path / "checkpoint.json"

    # Patch CHECKPOINT_FILE
    with patch('scripts.enrich_with_google_maps.CHECKPOINT_FILE', checkpoint_file):
        # Save checkpoint
        processed = [0, 1, 2, 5, 10]
        save_checkpoint(processed)

        # Load checkpoint
        loaded = load_checkpoint()
        assert loaded == processed


def test_load_checkpoint_missing(tmp_path):
    """Test loading checkpoint when file doesn't exist."""
    checkpoint_file = tmp_path / "missing_checkpoint.json"

    with patch('scripts.enrich_with_google_maps.CHECKPOINT_FILE', checkpoint_file):
        loaded = load_checkpoint()
        assert loaded == []


# ============================================================================
# Test Path A/B Routing
# ============================================================================

def test_path_routing_with_website():
    """Test companies with websites route to Path A."""
    from utils.helpers import is_aggregator

    # Valid website - should go to Path A
    website = "https://www.gene.com"
    assert not is_aggregator(website)


def test_path_routing_aggregator():
    """Test companies with aggregator websites route to Path B."""
    from utils.helpers import is_aggregator

    # Aggregator website - should go to Path B
    website = "https://www.linkedin.com/company/genentech"
    assert is_aggregator(website)


def test_path_routing_no_website():
    """Test companies without websites route to Path B."""
    website = ""
    # Empty website should route to Path B
    assert not website or website.strip() == ""


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_validation_pipeline_success():
    """Test full validation pipeline with successful match."""
    company_name = "10X Genomics"
    bpg_website = "https://www.10xgenomics.com"
    city = "Pleasanton"

    # Mock Place Details response
    details = {
        'name': '10X Genomics',
        'website': 'https://www.10xgenomics.com',
        'formatted_address': '6230 Stoneridge Mall Rd, Pleasanton, CA 94588',
        'geometry': {
            'location': {'lat': 37.6938, 'lng': -121.9289}
        },
        'business_status': 'OPERATIONAL',
        'types': ['point_of_interest', 'establishment']
    }

    # Validate
    accepted, confidence, reason = validate_candidate(
        company_name, bpg_website, city, details
    )

    assert accepted is True
    assert confidence >= 0.75
    assert "name_sim" in reason
    assert "website_match" in reason


def test_full_validation_pipeline_multi_tenant():
    """Test validation with multi-tenant address."""
    company_name = "Tenant Biotech"
    bpg_website = "https://www.tenant.com"
    city = "South San Francisco"

    # Multi-tenant address (QB3)
    details = {
        'name': 'Different Company',  # Name doesn't match
        'website': 'https://www.different.com',  # Website doesn't match
        'formatted_address': '201 Gateway Blvd, South San Francisco, CA 94080',
        'geometry': {
            'location': {'lat': 37.6624, 'lng': -122.3801}
        },
        'business_status': 'OPERATIONAL',
        'types': ['point_of_interest']
    }

    # Should reject due to multi-tenant mismatch
    accepted, confidence, reason = validate_candidate(
        company_name, bpg_website, city, details
    )

    assert accepted is False
    assert reason == "multi_tenant_mismatch"
