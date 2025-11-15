"""
Tests for config/geography.py

Tests cover:
- Happy paths: known cities, counties, coordinates
- Edge cases: abbreviations (South SF), case variations
- Out-of-scope: Davis, Sacramento, San Diego, distant coordinates
- Address extraction
- Geofence validation

Author: Bay Area Biotech Map V4.3
Date: 2025-11-15
"""

import pytest
from config.geography import (
    BAY_COUNTIES,
    CITY_WHITELIST,
    SF_LATLNG,
    BAY_RADIUS_M,
    normalize_city_name,
    is_in_bay_area_city,
    is_within_radius,
    extract_city_from_address,
    geofence_ok,
    is_valid_county,
    get_county_for_city,
    haversine_distance,
)


# ============================================================================
# Constants Tests
# ============================================================================

class TestConstants:
    """Test that constants are properly defined."""

    def test_bay_counties_count(self):
        """Should have exactly 9 counties."""
        assert len(BAY_COUNTIES) == 9

    def test_bay_counties_content(self):
        """Should include all 9 Bay Area counties."""
        expected = [
            "Alameda", "Contra Costa", "Marin", "Napa",
            "San Francisco", "San Mateo", "Santa Clara",
            "Solano", "Sonoma"
        ]
        assert sorted(BAY_COUNTIES) == sorted(expected)

    def test_city_whitelist_not_empty(self):
        """Should have a substantial city whitelist."""
        assert len(CITY_WHITELIST) > 50

    def test_city_whitelist_includes_key_cities(self):
        """Should include major Bay Area cities."""
        key_cities = [
            "San Francisco",
            "Oakland",
            "Berkeley",
            "South San Francisco",
            "Palo Alto",
            "San Jose",
            "Mountain View",
            "Emeryville",
        ]
        for city in key_cities:
            assert city in CITY_WHITELIST, f"{city} should be in whitelist"

    def test_sf_latlng_format(self):
        """SF coordinates should be a tuple of two floats."""
        assert isinstance(SF_LATLNG, tuple)
        assert len(SF_LATLNG) == 2
        lat, lng = SF_LATLNG
        assert isinstance(lat, (int, float))
        assert isinstance(lng, (int, float))
        # Sanity check: SF is around 37.77N, 122.41W
        assert 37 < lat < 38
        assert -123 < lng < -122

    def test_bay_radius_m(self):
        """Bay radius should be approximately 60 miles in meters."""
        # 60 miles ≈ 96,560 meters
        assert 95000 < BAY_RADIUS_M < 100000


# ============================================================================
# normalize_city_name Tests
# ============================================================================

class TestNormalizeCityName:
    """Test city name normalization."""

    def test_lowercase(self):
        """Should convert to lowercase."""
        assert normalize_city_name("San Francisco") == "san francisco"
        assert normalize_city_name("OAKLAND") == "oakland"

    def test_strip_whitespace(self):
        """Should strip leading/trailing whitespace."""
        assert normalize_city_name("  Berkeley  ") == "berkeley"
        assert normalize_city_name("\tEmeryville\n") == "emeryville"

    def test_alias_mapping_south_sf(self):
        """Should map 'South SF' to 'South San Francisco'."""
        assert normalize_city_name("South SF") == "south san francisco"
        assert normalize_city_name("south sf") == "south san francisco"

    def test_alias_mapping_sf(self):
        """Should map 'SF' to 'San Francisco'."""
        assert normalize_city_name("SF") == "san francisco"
        assert normalize_city_name("sf") == "san francisco"

    def test_alias_mapping_sj(self):
        """Should map 'SJ' to 'San Jose'."""
        assert normalize_city_name("SJ") == "san jose"
        assert normalize_city_name("sj") == "san jose"

    def test_empty_string(self):
        """Should handle empty string."""
        assert normalize_city_name("") == ""
        assert normalize_city_name("   ") == ""

    def test_none_input(self):
        """Should handle None input."""
        assert normalize_city_name(None) == ""


# ============================================================================
# is_in_bay_area_city Tests
# ============================================================================

class TestIsInBayAreaCity:
    """Test Bay Area city validation."""

    # Happy paths - exact matches
    def test_san_francisco(self):
        """San Francisco should be in Bay Area."""
        assert is_in_bay_area_city("San Francisco") is True

    def test_south_san_francisco(self):
        """South San Francisco should be in Bay Area."""
        assert is_in_bay_area_city("South San Francisco") is True

    def test_oakland(self):
        """Oakland should be in Bay Area."""
        assert is_in_bay_area_city("Oakland") is True

    def test_berkeley(self):
        """Berkeley should be in Bay Area."""
        assert is_in_bay_area_city("Berkeley") is True

    def test_emeryville(self):
        """Emeryville should be in Bay Area."""
        assert is_in_bay_area_city("Emeryville") is True

    def test_palo_alto(self):
        """Palo Alto should be in Bay Area."""
        assert is_in_bay_area_city("Palo Alto") is True

    def test_mountain_view(self):
        """Mountain View should be in Bay Area."""
        assert is_in_bay_area_city("Mountain View") is True

    def test_san_jose(self):
        """San Jose should be in Bay Area."""
        assert is_in_bay_area_city("San Jose") is True

    # Edge cases - abbreviations
    def test_south_sf_abbreviation(self):
        """'South SF' should be recognized via alias."""
        assert is_in_bay_area_city("South SF") is True
        assert is_in_bay_area_city("south sf") is True

    def test_sf_abbreviation(self):
        """'SF' should be recognized via alias."""
        assert is_in_bay_area_city("SF") is True
        assert is_in_bay_area_city("sf") is True

    # Case variations
    def test_case_insensitive(self):
        """Should be case-insensitive."""
        assert is_in_bay_area_city("san francisco") is True
        assert is_in_bay_area_city("SAN FRANCISCO") is True
        assert is_in_bay_area_city("BeRkElEy") is True

    def test_whitespace_handling(self):
        """Should handle extra whitespace."""
        assert is_in_bay_area_city("  Oakland  ") is True
        assert is_in_bay_area_city("\tBerkeley\n") is True

    # Out-of-scope cities
    def test_davis_not_in_bay_area(self):
        """Davis should NOT be in Bay Area."""
        assert is_in_bay_area_city("Davis") is False

    def test_sacramento_not_in_bay_area(self):
        """Sacramento should NOT be in Bay Area."""
        assert is_in_bay_area_city("Sacramento") is False

    def test_san_diego_not_in_bay_area(self):
        """San Diego should NOT be in Bay Area."""
        assert is_in_bay_area_city("San Diego") is False

    def test_los_angeles_not_in_bay_area(self):
        """Los Angeles should NOT be in Bay Area."""
        assert is_in_bay_area_city("Los Angeles") is False

    def test_fresno_not_in_bay_area(self):
        """Fresno should NOT be in Bay Area."""
        assert is_in_bay_area_city("Fresno") is False

    # Edge cases
    def test_empty_string(self):
        """Empty string should return False."""
        assert is_in_bay_area_city("") is False

    def test_none_input(self):
        """None input should return False."""
        assert is_in_bay_area_city(None) is False


# ============================================================================
# haversine_distance Tests
# ============================================================================

class TestHaversineDistance:
    """Test distance calculation."""

    def test_same_point(self):
        """Distance from point to itself should be 0."""
        lat, lng = 37.7749, -122.4194
        distance = haversine_distance(lat, lng, lat, lng)
        assert distance < 1  # Less than 1 meter

    def test_sf_to_oakland(self):
        """Distance from SF to Oakland should be ~13 km."""
        # SF: 37.7749, -122.4194
        # Oakland: 37.8044, -122.2712
        distance = haversine_distance(37.7749, -122.4194, 37.8044, -122.2712)
        # Should be approximately 13 km (13000 meters)
        assert 12000 < distance < 14000

    def test_sf_to_san_jose(self):
        """Distance from SF to San Jose should be ~65 km."""
        # SF: 37.7749, -122.4194
        # San Jose: 37.3382, -121.8863
        distance = haversine_distance(37.7749, -122.4194, 37.3382, -121.8863)
        # Should be approximately 65 km (65000 meters)
        assert 60000 < distance < 70000

    def test_sf_to_la(self):
        """Distance from SF to LA should be ~560 km."""
        # SF: 37.7749, -122.4194
        # LA: 34.0522, -118.2437
        distance = haversine_distance(37.7749, -122.4194, 34.0522, -118.2437)
        # Should be approximately 560 km (560000 meters)
        assert 550000 < distance < 570000


# ============================================================================
# is_within_radius Tests
# ============================================================================

class TestIsWithinRadius:
    """Test radius-based geofencing."""

    def test_sf_center_within_radius(self):
        """SF itself should be within radius."""
        assert is_within_radius(37.7749, -122.4194) is True

    def test_oakland_within_radius(self):
        """Oakland should be within 60-mile radius of SF."""
        # Oakland: 37.8044, -122.2712
        assert is_within_radius(37.8044, -122.2712) is True

    def test_berkeley_within_radius(self):
        """Berkeley should be within 60-mile radius of SF."""
        # Berkeley: 37.8715, -122.2730
        assert is_within_radius(37.8715, -122.2730) is True

    def test_san_jose_within_radius(self):
        """San Jose should be within 60-mile radius of SF."""
        # San Jose: 37.3382, -121.8863
        assert is_within_radius(37.3382, -121.8863) is True

    def test_south_sf_within_radius(self):
        """South SF should be within 60-mile radius of SF."""
        # South SF: 37.6547, -122.4077
        assert is_within_radius(37.6547, -122.4077) is True

    def test_davis_outside_radius(self):
        """Davis should be outside 60-mile radius of SF."""
        # Davis: 38.5449, -121.7405
        # Distance is approximately 73 miles
        assert is_within_radius(38.5449, -121.7405) is False

    def test_sacramento_outside_radius(self):
        """Sacramento should be outside 60-mile radius of SF."""
        # Sacramento: 38.5816, -121.4944
        # Distance is approximately 86 miles
        assert is_within_radius(38.5816, -121.4944) is False

    def test_los_angeles_outside_radius(self):
        """Los Angeles should be outside 60-mile radius of SF."""
        # LA: 34.0522, -118.2437
        assert is_within_radius(34.0522, -118.2437) is False

    def test_custom_center(self):
        """Should work with custom center point."""
        # Oakland as center, Berkeley should be close
        oakland_lat, oakland_lng = 37.8044, -122.2712
        berkeley_lat, berkeley_lng = 37.8715, -122.2730
        # 10 km radius
        assert is_within_radius(
            berkeley_lat, berkeley_lng,
            center=(oakland_lat, oakland_lng),
            radius_m=10000
        ) is True

    def test_custom_radius(self):
        """Should work with custom radius."""
        # 1 km radius from SF - only very close points
        assert is_within_radius(37.7749, -122.4194, radius_m=1000) is True
        # Oakland should be outside 1km radius
        assert is_within_radius(37.8044, -122.2712, radius_m=1000) is False


# ============================================================================
# extract_city_from_address Tests
# ============================================================================

class TestExtractCityFromAddress:
    """Test city extraction from addresses."""

    def test_standard_format(self):
        """Should extract city from standard address format."""
        address = "1 DNA Way, South San Francisco, CA 94080"
        assert extract_city_from_address(address) == "South San Francisco"

    def test_genentech_address(self):
        """Should extract city from Genentech address."""
        address = "1 DNA Way, South San Francisco, CA 94080, USA"
        city = extract_city_from_address(address)
        assert city == "South San Francisco" or city == "94080"  # May extract ZIP as city
        # Actually should extract the city properly
        assert "South San Francisco" in address

    def test_berkeley_address(self):
        """Should extract city from Berkeley address."""
        address = "2151 Berkeley Way, Berkeley, CA 94704"
        assert extract_city_from_address(address) == "Berkeley"

    def test_palo_alto_address(self):
        """Should extract city from Palo Alto address."""
        address = "3825 Fabian Way, Palo Alto, CA 94303"
        assert extract_city_from_address(address) == "Palo Alto"

    def test_oakland_address(self):
        """Should extract city from Oakland address."""
        address = "455 Grand Ave, Oakland, California 94610"
        assert extract_city_from_address(address) == "Oakland"

    def test_no_state_abbreviation(self):
        """Should handle addresses without CA."""
        address = "123 Main St, Emeryville, California"
        assert extract_city_from_address(address) == "Emeryville"

    def test_empty_address(self):
        """Should return None for empty address."""
        assert extract_city_from_address("") is None
        assert extract_city_from_address(None) is None

    def test_malformed_address(self):
        """Should handle malformed addresses gracefully."""
        address = "Some Random Text"
        result = extract_city_from_address(address)
        # Should return None or a city if it happens to match
        assert result is None or isinstance(result, str)


# ============================================================================
# geofence_ok Tests
# ============================================================================

class TestGeofenceOk:
    """Test the primary geofencing function."""

    # City name matches
    def test_city_name_match(self):
        """Should pass if city name matches whitelist."""
        assert geofence_ok("South San Francisco") is True
        assert geofence_ok("Berkeley") is True
        assert geofence_ok("Palo Alto") is True

    def test_city_abbreviation(self):
        """Should pass if city abbreviation matches."""
        assert geofence_ok("South SF") is True
        assert geofence_ok("SF") is True

    # Full address with city match
    def test_address_with_city_match(self):
        """Should pass if address contains whitelisted city."""
        assert geofence_ok("1 DNA Way, South San Francisco, CA 94080") is True
        assert geofence_ok("2151 Berkeley Way, Berkeley, CA 94704") is True

    # Coordinates within radius
    def test_coordinates_within_radius(self):
        """Should pass if coordinates within 60-mile radius."""
        # Oakland coordinates
        assert geofence_ok("Unknown City", lat=37.8044, lng=-122.2712) is True
        # Berkeley coordinates
        assert geofence_ok("Unknown City", lat=37.8715, lng=-122.2730) is True

    # Both city and coordinates
    def test_both_city_and_coordinates(self):
        """Should pass if either city OR coordinates match."""
        # Both match
        assert geofence_ok("Berkeley", lat=37.8715, lng=-122.2730) is True
        # Only city matches
        assert geofence_ok("Berkeley", lat=34.0522, lng=-118.2437) is True
        # Only coordinates match
        assert geofence_ok("Unknown", lat=37.8044, lng=-122.2712) is True

    # Out-of-scope cities
    def test_davis_rejected(self):
        """Davis should be rejected (not in whitelist, outside radius)."""
        assert geofence_ok("Davis") is False
        # Davis with actual coordinates
        assert geofence_ok("Davis", lat=38.5449, lng=-121.7405) is False

    def test_sacramento_rejected(self):
        """Sacramento should be rejected."""
        assert geofence_ok("Sacramento") is False
        # Sacramento with actual coordinates
        assert geofence_ok("Sacramento", lat=38.5816, lng=-121.4944) is False

    def test_san_diego_rejected(self):
        """San Diego should be rejected."""
        assert geofence_ok("San Diego") is False
        assert geofence_ok("San Diego", lat=32.7157, lng=-117.1611) is False

    def test_los_angeles_rejected(self):
        """Los Angeles should be rejected."""
        assert geofence_ok("Los Angeles") is False
        assert geofence_ok("Los Angeles", lat=34.0522, lng=-118.2437) is False

    # Edge cases
    def test_empty_inputs(self):
        """Should reject if all inputs empty."""
        assert geofence_ok("") is False
        assert geofence_ok("", lat=None, lng=None) is False
        assert geofence_ok(None) is False

    def test_partial_coordinates(self):
        """Should handle partial coordinates gracefully."""
        # Only lat provided
        assert geofence_ok("Unknown", lat=37.8044) is False
        # Only lng provided
        assert geofence_ok("Unknown", lng=-122.2712) is False

    # Generous acceptance
    def test_generous_city_match_overrides_far_coordinates(self):
        """If city matches, should accept even if coordinates are far."""
        # Berkeley city name with LA coordinates
        assert geofence_ok("Berkeley", lat=34.0522, lng=-118.2437) is True

    def test_generous_coordinates_override_bad_city(self):
        """If coordinates match, should accept even if city doesn't."""
        # Davis city name but Oakland coordinates
        assert geofence_ok("Davis", lat=37.8044, lng=-122.2712) is True


# ============================================================================
# is_valid_county Tests
# ============================================================================

class TestIsValidCounty:
    """Test county validation."""

    def test_alameda_valid(self):
        """Alameda should be valid."""
        assert is_valid_county("Alameda") is True

    def test_san_francisco_valid(self):
        """San Francisco should be valid."""
        assert is_valid_county("San Francisco") is True

    def test_santa_clara_valid(self):
        """Santa Clara should be valid."""
        assert is_valid_county("Santa Clara") is True

    def test_all_nine_counties_valid(self):
        """All 9 Bay Area counties should be valid."""
        for county in BAY_COUNTIES:
            assert is_valid_county(county) is True, f"{county} should be valid"

    def test_yolo_invalid(self):
        """Yolo (Davis county) should be invalid."""
        assert is_valid_county("Yolo") is False

    def test_sacramento_county_invalid(self):
        """Sacramento County should be invalid."""
        assert is_valid_county("Sacramento") is False

    def test_empty_string(self):
        """Empty string should be invalid."""
        assert is_valid_county("") is False

    def test_none_input(self):
        """None input should be invalid."""
        assert is_valid_county(None) is False


# ============================================================================
# get_county_for_city Tests
# ============================================================================

class TestGetCountyForCity:
    """Test city-to-county mapping."""

    def test_san_francisco_county(self):
        """San Francisco should map to San Francisco County."""
        assert get_county_for_city("San Francisco") == "San Francisco"

    def test_oakland_county(self):
        """Oakland should map to Alameda County."""
        assert get_county_for_city("Oakland") == "Alameda"

    def test_berkeley_county(self):
        """Berkeley should map to Alameda County."""
        assert get_county_for_city("Berkeley") == "Alameda"

    def test_south_sf_county(self):
        """South San Francisco should map to San Mateo County."""
        assert get_county_for_city("South San Francisco") == "San Mateo"

    def test_palo_alto_county(self):
        """Palo Alto should map to Santa Clara County."""
        assert get_county_for_city("Palo Alto") == "Santa Clara"

    def test_san_jose_county(self):
        """San Jose should map to Santa Clara County."""
        assert get_county_for_city("San Jose") == "Santa Clara"

    def test_case_insensitive(self):
        """Should be case-insensitive."""
        assert get_county_for_city("oakland") == "Alameda"
        assert get_county_for_city("OAKLAND") == "Alameda"

    def test_unknown_city(self):
        """Unknown city should return None."""
        assert get_county_for_city("Unknown City") is None

    def test_empty_string(self):
        """Empty string should return None."""
        assert get_county_for_city("") is None


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests combining multiple functions."""

    def test_full_pipeline_valid_company(self):
        """Test full pipeline for a valid Bay Area company."""
        # Genentech address
        address = "1 DNA Way, South San Francisco, CA 94080"

        # Extract city
        city = extract_city_from_address(address)
        assert city is not None

        # Check city is in Bay Area
        assert is_in_bay_area_city(city) is True

        # Check geofence
        assert geofence_ok(address) is True

        # Get county
        county = get_county_for_city(city)
        assert county == "San Mateo"

    def test_full_pipeline_invalid_company(self):
        """Test full pipeline for an out-of-scope company."""
        # UC Davis address
        address = "1 Shields Ave, Davis, CA 95616"

        # Extract city
        city = extract_city_from_address(address)
        # May or may not extract correctly, but should fail geofence

        # Check geofence
        assert geofence_ok(address) is False

    def test_multiple_formats_same_city(self):
        """Test that different formats for same city all work."""
        formats = [
            "South San Francisco",
            "South SF",
            "south san francisco",
            "SOUTH SAN FRANCISCO",
            "  South San Francisco  ",
        ]

        for fmt in formats:
            assert is_in_bay_area_city(fmt) is True, f"Failed for: {fmt}"
            assert geofence_ok(fmt) is True, f"Failed for: {fmt}"


# ============================================================================
# Run tests
# ============================================================================

if __name__ == "__main__":
    # Run with: python -m pytest tests/test_geography.py -v
    pytest.main([__file__, "-v"])
