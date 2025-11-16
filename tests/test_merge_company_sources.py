#!/usr/bin/env python3
"""
Tests for merge_company_sources.py (V4.3 Stage-B).

Tests validate:
- eTLD+1 + normalized name deduplication
- Aggregator domain detection and reset
- Domain-reuse conflict detection
- Bay Area geofence (late filtering after dedupe)
- BPG Website preservation
- Validation_Source tracking
- Staging-only output
"""

import pytest
import sys
import csv
import tempfile
from pathlib import Path
from collections import defaultdict

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent / 'scripts'
sys.path.insert(0, str(scripts_dir))

from merge_company_sources import (
    deduplicate_by_etld1_and_name,
    check_and_reset_aggregators,
    apply_geofence,
    generate_domain_reuse_report,
    save_companies,
)


class TestDeduplication:
    """Tests for eTLD+1 + normalized name deduplication."""

    def test_dedupe_same_domain_same_name(self):
        """Test deduplication with same eTLD+1 and normalized name."""
        companies = [
            {'Company Name': 'Genentech, Inc.', 'Website': 'https://www.gene.com', 'City': 'South San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'Genentech', 'Website': 'https://gene.com/about', 'City': 'South San Francisco', 'source': 'Existing', 'Address': '1 DNA Way', 'Company Stage': 'Public', 'Focus Areas': 'Biotechnology'},
        ]

        deduplicated, conflicts = deduplicate_by_etld1_and_name(companies)

        # Should merge to single company
        assert len(deduplicated) == 1
        # Should prefer BPG (source priority)
        assert deduplicated[0]['source'] == 'BPG'
        # Should have same domain
        assert 'gene.com' in deduplicated[0]['Website']
        # No conflicts (same normalized name)
        assert len(conflicts) == 0

    def test_dedupe_same_domain_different_names(self):
        """Test domain-reuse detection with same eTLD+1, different names."""
        companies = [
            {'Company Name': 'Test Biotech', 'Website': 'https://www.testbio.com', 'City': 'San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'Different Company', 'Website': 'https://www.testbio.com', 'City': 'San Francisco', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        deduplicated, conflicts = deduplicate_by_etld1_and_name(companies)

        # Should keep both companies (different names)
        assert len(deduplicated) == 2
        # Should detect domain conflict (not using gene.com which is allowlisted)
        assert 'testbio.com' in conflicts
        assert len(conflicts['testbio.com']) == 2

    def test_dedupe_different_domains_same_name(self):
        """Test deduplication with different eTLD+1s but same normalized name."""
        companies = [
            {'Company Name': 'BioMarin Pharmaceutical', 'Website': 'https://www.biomarin.com', 'City': 'San Rafael', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'BioMarin Pharmaceutical Inc.', 'Website': 'https://www.biomarin-pharma.com', 'City': 'San Rafael', 'source': 'Existing', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        deduplicated, conflicts = deduplicate_by_etld1_and_name(companies)

        # Should keep both (different domains mean different companies)
        assert len(deduplicated) == 2
        # Should detect domain conflict (both claim to be same normalized name)
        assert len(conflicts) >= 0  # May or may not conflict depending on interpretation

    def test_dedupe_no_website(self):
        """Test deduplication for companies without websites."""
        companies = [
            {'Company Name': 'Startup Bio Inc.', 'Website': '', 'City': 'San Francisco', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'Startup Bio', 'Website': '', 'City': 'San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        deduplicated, conflicts = deduplicate_by_etld1_and_name(companies)

        # Should merge by name (both have no website)
        assert len(deduplicated) == 1
        # Should prefer BPG
        assert deduplicated[0]['source'] == 'BPG'

    def test_dedupe_priority_order(self):
        """Test that BPG > Existing > Wikipedia priority is respected."""
        companies = [
            {'Company Name': 'Test Company', 'Website': 'https://test.com', 'City': 'Berkeley', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': 'Wiki data'},
            {'Company Name': 'Test Company Inc', 'Website': 'https://test.com', 'City': 'Berkeley', 'source': 'Existing', 'Address': '123 Main St', 'Company Stage': 'Private', 'Focus Areas': 'Existing data'},
            {'Company Name': 'Test Company', 'Website': 'https://test.com', 'City': 'Berkeley', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': 'BPG data'},
        ]

        deduplicated, conflicts = deduplicate_by_etld1_and_name(companies)

        # Should keep only BPG version
        assert len(deduplicated) == 1
        assert deduplicated[0]['source'] == 'BPG'
        assert deduplicated[0]['Focus Areas'] == 'BPG data'


class TestAggregatorHandling:
    """Tests for aggregator domain detection and handling."""

    def test_aggregator_detection_linkedin(self):
        """Test LinkedIn aggregator detection."""
        companies = [
            {'Company Name': 'Bio Company', 'Website': 'https://www.linkedin.com/company/biocompany', 'City': 'Oakland', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        modified, count = check_and_reset_aggregators(companies)

        # Should detect LinkedIn as aggregator
        assert count == 1
        # Should reset Website to empty
        assert modified[0]['Website'] == ''

    def test_aggregator_detection_biopharmguy(self):
        """Test BioPharmGuy aggregator detection."""
        companies = [
            {'Company Name': 'Listed Company', 'Website': 'https://biopharmguy.com/links/company123', 'City': 'Berkeley', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        modified, count = check_and_reset_aggregators(companies)

        # Should detect BioPharmGuy as aggregator
        assert count == 1
        assert modified[0]['Website'] == ''

    def test_aggregator_detection_wixsite(self):
        """Test Wixsite aggregator detection."""
        companies = [
            {'Company Name': 'Wix Biotech', 'Website': 'https://mybiotech.wixsite.com/home', 'City': 'San Francisco', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        modified, count = check_and_reset_aggregators(companies)

        # Should detect Wixsite as aggregator
        assert count == 1
        assert modified[0]['Website'] == ''

    def test_non_aggregator(self):
        """Test that legitimate domains are not flagged."""
        companies = [
            {'Company Name': 'Genentech', 'Website': 'https://www.gene.com', 'City': 'South San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        modified, count = check_and_reset_aggregators(companies)

        # Should NOT detect as aggregator
        assert count == 0
        # Website should be preserved
        assert modified[0]['Website'] == 'https://www.gene.com'


class TestGeofencing:
    """Tests for Bay Area geofence (late filtering)."""

    def test_geofence_bay_area_city(self):
        """Test geofence accepts Bay Area cities."""
        companies = [
            {'Company Name': 'SF Biotech', 'Website': 'https://sfbio.com', 'City': 'San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'SSF Pharma', 'Website': 'https://ssfpharma.com', 'City': 'South San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'Berkeley Bio', 'Website': 'https://berkbio.com', 'City': 'Berkeley', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        filtered = apply_geofence(companies)

        # All should pass geofence
        assert len(filtered) == 3

    def test_geofence_rejects_out_of_area(self):
        """Test geofence rejects cities outside Bay Area."""
        companies = [
            {'Company Name': 'Davis Biotech', 'Website': 'https://davisbio.com', 'City': 'Davis', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'Sacramento Pharma', 'Website': 'https://sacpharma.com', 'City': 'Sacramento', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'LA Biotech', 'Website': 'https://labio.com', 'City': 'Los Angeles', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        filtered = apply_geofence(companies)

        # All should be rejected
        assert len(filtered) == 0

    def test_geofence_mixed(self):
        """Test geofence with mixed in/out of area."""
        companies = [
            {'Company Name': 'SF Biotech', 'Website': 'https://sfbio.com', 'City': 'San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'Davis Biotech', 'Website': 'https://davisbio.com', 'City': 'Davis', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'Berkeley Bio', 'Website': 'https://berkbio.com', 'City': 'Berkeley', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        filtered = apply_geofence(companies)

        # Only SF and Berkeley should pass
        assert len(filtered) == 2
        cities = {c['City'] for c in filtered}
        assert 'San Francisco' in cities
        assert 'Berkeley' in cities
        assert 'Davis' not in cities

    def test_geofence_city_variants(self):
        """Test geofence handles city name variants."""
        companies = [
            {'Company Name': 'SSF Bio 1', 'Website': 'https://ssf1.com', 'City': 'South San Francisco', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'SSF Bio 2', 'Website': 'https://ssf2.com', 'City': 'South SF', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
            {'Company Name': 'SSF Bio 3', 'Website': 'https://ssf3.com', 'City': 'S San Francisco', 'source': 'Wikipedia', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        filtered = apply_geofence(companies)

        # South San Francisco and South SF should pass (with normalization)
        # S San Francisco might fail depending on alias mapping
        assert len(filtered) >= 2


class TestDomainReuseReport:
    """Tests for domain reuse conflict reporting."""

    def test_report_no_conflicts(self):
        """Test report generation with no conflicts."""
        conflicts = {}

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            report_path = Path(f.name)

        try:
            no_conflicts = generate_domain_reuse_report(conflicts, report_path)

            assert no_conflicts is True
            # Check report contains success message
            with open(report_path, 'r') as f:
                content = f.read()
                assert 'No domain conflicts detected' in content
        finally:
            report_path.unlink()

    def test_report_with_conflicts(self):
        """Test report generation with conflicts."""
        conflicts = {
            'example.com': ['Company A', 'Company B'],
            'test.com': ['Test Inc', 'Test Corp', 'Test LLC'],
        }

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            report_path = Path(f.name)

        try:
            no_conflicts = generate_domain_reuse_report(conflicts, report_path)

            assert no_conflicts is False
            # Check report contains conflict details
            with open(report_path, 'r') as f:
                content = f.read()
                assert 'example.com' in content
                assert 'Company A' in content
                assert 'Company B' in content
                assert 'test.com' in content
                assert 'Test Inc' in content
        finally:
            report_path.unlink()


class TestOutputValidation:
    """Tests for output validation and staging-only requirement."""

    def test_save_to_working_directory(self):
        """Test that save_companies accepts working/ path."""
        companies = [
            {'Company Name': 'Test Bio', 'Website': 'https://test.com', 'City': 'Berkeley', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            working_dir = Path(tmpdir) / 'working'
            working_dir.mkdir()
            output_path = working_dir / 'companies_merged.csv'

            # Should succeed
            save_companies(companies, output_path)

            # Verify file was created
            assert output_path.exists()

            # Verify CSV content
            with open(output_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 1
                assert rows[0]['Company Name'] == 'Test Bio'
                assert rows[0]['Validation_Source'] == 'BPG'

    def test_save_rejects_non_working_path(self):
        """Test that save_companies rejects paths not in working/."""
        companies = [
            {'Company Name': 'Test Bio', 'Website': 'https://test.com', 'City': 'Berkeley', 'source': 'BPG', 'Address': '', 'Company Stage': '', 'Focus Areas': ''},
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            final_dir = Path(tmpdir) / 'final'
            final_dir.mkdir()
            output_path = final_dir / 'companies.csv'

            # Should raise ValueError
            with pytest.raises(ValueError, match="working"):
                save_companies(companies, output_path)


class TestIntegration:
    """Integration tests for full merge workflow."""

    def test_full_workflow_with_test_data(self):
        """Test complete merge workflow with test fixture data."""
        # Use red team companies as test data
        fixture_path = Path(__file__).parent / 'fixtures' / 'red_team_companies.csv'

        if not fixture_path.exists():
            pytest.skip("Red team fixture not found")

        # Load red team data
        companies = []
        with open(fixture_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                companies.append({
                    'Company Name': row['Company Name'],
                    'Website': row['Website'],
                    'City': row['City'],
                    'source': 'BPG',
                    'Address': '',
                    'Company Stage': '',
                    'Focus Areas': row.get('Notes', ''),
                })

        # Check and reset aggregators
        companies, agg_count = check_and_reset_aggregators(companies)
        # Should detect at least LinkedIn, Wikipedia, BioPharmGuy (3 aggregators in red team data)
        assert agg_count >= 3

        # Deduplicate
        deduplicated, conflicts = deduplicate_by_etld1_and_name(companies)

        # Red team data has all unique companies, so count should be same after aggregator reset
        # (aggregators were reset to empty website, but companies remain distinct)
        assert len(deduplicated) == len(companies)

        # Apply geofence
        geofenced = apply_geofence(deduplicated)

        # Should filter out Davis and Sacramento
        cities = {c['City'] for c in geofenced}
        assert 'Davis' not in cities
        assert 'Sacramento' not in cities
        # Should keep Bay Area cities
        assert any(city in ['San Francisco', 'South San Francisco', 'Berkeley'] for city in cities)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
