"""
Pytest configuration and fixtures for Bay Area Biotech Map V4.3.

This module provides shared fixtures for all tests, including:
- Red-team validation dataset (30 companies)
- Mock API responses
- Test data helpers
- Shared test utilities

Author: Bay Area Biotech Map V4.3
Date: 2025-11-15
"""

import csv
import os
from pathlib import Path
from typing import List, Dict

import pytest


# ============================================================================
# Path Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def tests_dir(project_root) -> Path:
    """Return the tests directory."""
    return project_root / "tests"


@pytest.fixture(scope="session")
def fixtures_dir(tests_dir) -> Path:
    """Return the fixtures directory."""
    return tests_dir / "fixtures"


# ============================================================================
# Red-Team Dataset Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def red_team_csv_path(fixtures_dir) -> Path:
    """Return path to red_team_companies.csv."""
    return fixtures_dir / "red_team_companies.csv"


@pytest.fixture(scope="session")
def red_team_companies(red_team_csv_path) -> List[Dict[str, str]]:
    """
    Load red-team validation dataset (30 companies).

    Categories:
    - easy_win: 10 clear Bay Area biotech companies
    - incubator: 5 incubator/multi-tenant addresses
    - alias_domain: 5 companies with unusual domains
    - city_edge: 5 city name edge cases (e.g., "South SF")
    - aggregator_only: 3 companies with aggregator domains only
    - out_of_scope: 2 out-of-area companies (Davis, Sacramento)

    Returns:
        List of company dictionaries with keys:
        Company Name, Website, City, County, Category, Notes
    """
    with open(red_team_csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)


@pytest.fixture
def red_team_by_category(red_team_companies) -> Dict[str, List[Dict[str, str]]]:
    """
    Group red-team companies by category.

    Returns:
        Dictionary mapping category → list of companies
    """
    categories = {}
    for company in red_team_companies:
        category = company.get('Category', 'unknown')
        if category not in categories:
            categories[category] = []
        categories[category].append(company)
    return categories


@pytest.fixture
def easy_wins(red_team_by_category) -> List[Dict[str, str]]:
    """Return the 10 easy-win Bay Area companies."""
    return red_team_by_category.get('easy_win', [])


@pytest.fixture
def incubator_tenants(red_team_by_category) -> List[Dict[str, str]]:
    """Return the 5 incubator tenant companies."""
    return red_team_by_category.get('incubator', [])


@pytest.fixture
def alias_domains(red_team_by_category) -> List[Dict[str, str]]:
    """Return the 5 alias-domain companies."""
    return red_team_by_category.get('alias_domain', [])


@pytest.fixture
def city_edge_cases(red_team_by_category) -> List[Dict[str, str]]:
    """Return the 5 city edge-case companies."""
    return red_team_by_category.get('city_edge', [])


@pytest.fixture
def aggregator_only(red_team_by_category) -> List[Dict[str, str]]:
    """Return the 3 aggregator-only companies."""
    return red_team_by_category.get('aggregator_only', [])


@pytest.fixture
def out_of_scope(red_team_by_category) -> List[Dict[str, str]]:
    """Return the 2 out-of-scope companies."""
    return red_team_by_category.get('out_of_scope', [])


# ============================================================================
# Test Data Helpers
# ============================================================================

@pytest.fixture
def sample_company() -> Dict[str, str]:
    """Return a sample company for quick testing."""
    return {
        'Company Name': 'Genentech',
        'Website': 'https://www.gene.com',
        'City': 'South San Francisco',
        'County': 'San Mateo',
        'Category': 'easy_win',
        'Notes': 'Clear biotech company with website'
    }


@pytest.fixture
def sample_urls() -> List[str]:
    """Return sample URLs for URL parsing tests."""
    return [
        'https://www.gene.com',
        'https://www.gilead.com/home',
        'https://corporate.biomarin.com/about',
        'http://example.com',  # HTTP (should upgrade to HTTPS)
        'www.noprotocol.com',  # Missing protocol
    ]


# ============================================================================
# Mock API Response Fixtures
# ============================================================================

@pytest.fixture
def mock_google_places_response():
    """Return a mock Google Places API response."""
    return {
        'candidates': [
            {
                'name': 'Genentech',
                'formatted_address': '1 DNA Way, South San Francisco, CA 94080, USA',
                'geometry': {
                    'location': {
                        'lat': 37.6547,
                        'lng': -122.3831
                    }
                },
                'place_id': 'ChIJmock123456',
                'types': ['establishment', 'point_of_interest'],
                'business_status': 'OPERATIONAL'
            }
        ],
        'status': 'OK'
    }


@pytest.fixture
def mock_place_details():
    """Return mock Place Details API response."""
    return {
        'result': {
            'name': 'Genentech',
            'formatted_address': '1 DNA Way, South San Francisco, CA 94080, USA',
            'website': 'https://www.gene.com',
            'types': ['establishment', 'point_of_interest'],
            'geometry': {
                'location': {
                    'lat': 37.6547,
                    'lng': -122.3831
                }
            },
            'business_status': 'OPERATIONAL',
            'place_id': 'ChIJmock123456'
        },
        'status': 'OK'
    }


# ============================================================================
# Environment Configuration
# ============================================================================

@pytest.fixture(scope="session", autouse=True)
def test_environment():
    """
    Set up test environment configuration.

    This fixture runs automatically before all tests.
    """
    # Set test-specific environment variables if needed
    os.environ['TESTING'] = '1'

    yield

    # Cleanup after all tests
    if 'TESTING' in os.environ:
        del os.environ['TESTING']


# ============================================================================
# Pytest Configuration Hooks
# ============================================================================

def pytest_configure(config):
    """
    Pytest configuration hook.

    Register custom markers here.
    """
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "geography: Geography module tests")
    config.addinivalue_line("markers", "helpers: Helper utilities tests")
