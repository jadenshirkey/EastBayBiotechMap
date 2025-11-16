"""
Tests for Path B enrichment script (path_b_enrichment.py).

Tests include:
- Tool definitions and wrappers (search_places, get_place_details)
- JSON schema validation
- Anthropic usage counter
- Acceptance logic (confidence, geofence, business-type, aggregator)
- Tool use controller loop (mocked)

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import sys
import json
import pytest
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import script functions
from scripts.path_b_enrichment import (
    SEARCH_PLACES_TOOL,
    GET_PLACE_DETAILS_TOOL,
    COMPANY_ENRICHMENT_SCHEMA,
    AnthropicUsageCounter,
    search_places_tool,
    get_place_details_tool,
    accept_enrichment_result,
    TOOL_REGISTRY,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_gmaps():
    """Mock Google Maps client."""
    return Mock()


@pytest.fixture
def setup_tool_registry(mock_gmaps):
    """Setup TOOL_REGISTRY with mock gmaps."""
    TOOL_REGISTRY['gmaps'] = mock_gmaps
    yield
    # Cleanup
    if 'gmaps' in TOOL_REGISTRY:
        del TOOL_REGISTRY['gmaps']


# ============================================================================
# Test Tool Definitions
# ============================================================================

def test_search_places_tool_definition():
    """Test search_places tool definition has required fields."""
    assert SEARCH_PLACES_TOOL['name'] == 'search_places'
    assert 'description' in SEARCH_PLACES_TOOL
    assert 'input_schema' in SEARCH_PLACES_TOOL

    schema = SEARCH_PLACES_TOOL['input_schema']
    assert schema['type'] == 'object'
    assert 'query' in schema['properties']
    assert 'query' in schema['required']


def test_get_place_details_tool_definition():
    """Test get_place_details tool definition has required fields."""
    assert GET_PLACE_DETAILS_TOOL['name'] == 'get_place_details'
    assert 'description' in GET_PLACE_DETAILS_TOOL
    assert 'input_schema' in GET_PLACE_DETAILS_TOOL

    schema = GET_PLACE_DETAILS_TOOL['input_schema']
    assert schema['type'] == 'object'
    assert 'place_id' in schema['properties']
    assert 'place_id' in schema['required']


# ============================================================================
# Test JSON Schema
# ============================================================================

def test_company_enrichment_schema():
    """Test company_enrichment_result schema structure."""
    assert COMPANY_ENRICHMENT_SCHEMA['name'] == 'company_enrichment_result'
    assert COMPANY_ENRICHMENT_SCHEMA['strict'] is True

    schema = COMPANY_ENRICHMENT_SCHEMA['schema']
    assert schema['type'] == 'object'

    # Check required fields
    required = schema['required']
    assert 'company_name' in required
    assert 'website' in required
    assert 'address' in required
    assert 'city' in required
    assert 'confidence' in required
    assert 'validation' in required

    # Check validation object
    validation = schema['properties']['validation']
    assert validation['type'] == 'object'
    assert 'in_bay_area' in validation['properties']
    assert 'is_business' in validation['properties']
    assert 'brand_domain_ok' in validation['properties']
    assert 'reasoning' in validation['properties']


def test_schema_allows_null_fields():
    """Test schema allows null for optional fields."""
    schema = COMPANY_ENRICHMENT_SCHEMA['schema']
    properties = schema['properties']

    # Website, address, city should allow null
    assert 'anyOf' in properties['website']
    assert 'anyOf' in properties['address']
    assert 'anyOf' in properties['city']


# ============================================================================
# Test Tool Wrappers
# ============================================================================

def test_search_places_tool_success(setup_tool_registry, mock_gmaps):
    """Test search_places_tool with successful response."""
    # Mock Google Maps response
    mock_gmaps.places.return_value = {
        'status': 'OK',
        'results': [
            {
                'place_id': 'place_123',
                'name': 'Genentech',
                'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
                'types': ['point_of_interest', 'establishment']
            },
            {
                'place_id': 'place_456',
                'name': 'Genentech Inc',
                'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
                'types': ['establishment']
            }
        ]
    }

    # Call tool
    result = search_places_tool(query="Genentech South San Francisco CA biotech")

    # Verify
    assert result['status'] == 'OK'
    assert result['result_count'] == 2
    assert len(result['results']) == 2
    assert result['results'][0]['place_id'] == 'place_123'
    assert result['results'][0]['name'] == 'Genentech'


def test_search_places_tool_with_location_bias(setup_tool_registry, mock_gmaps):
    """Test search_places_tool with location bias."""
    mock_gmaps.places.return_value = {
        'status': 'OK',
        'results': []
    }

    # Call tool with location bias
    result = search_places_tool(
        query="Genentech biotech",
        location_bias="37.6624,-122.3801"
    )

    # Verify location was parsed and passed
    call_args = mock_gmaps.places.call_args
    assert call_args[1]['location'] == {'lat': 37.6624, 'lng': -122.3801}


def test_search_places_tool_no_results(setup_tool_registry, mock_gmaps):
    """Test search_places_tool with no results."""
    mock_gmaps.places.return_value = {
        'status': 'ZERO_RESULTS',
        'results': []
    }

    result = search_places_tool(query="Nonexistent Company")

    assert result['status'] == 'ZERO_RESULTS'
    assert result['result_count'] == 0
    assert result['results'] == []


def test_search_places_tool_error(setup_tool_registry, mock_gmaps):
    """Test search_places_tool with API error."""
    mock_gmaps.places.side_effect = Exception("API Error")

    result = search_places_tool(query="Test Company")

    assert result['status'] == 'ERROR'
    assert 'error' in result
    assert result['result_count'] == 0


def test_get_place_details_tool_success(setup_tool_registry, mock_gmaps):
    """Test get_place_details_tool with successful response."""
    # Mock Google Maps response
    mock_gmaps.place.return_value = {
        'status': 'OK',
        'result': {
            'name': 'Genentech',
            'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
            'website': 'https://www.gene.com',
            'types': ['point_of_interest', 'establishment'],
            'geometry': {
                'location': {'lat': 37.6624, 'lng': -122.3801}
            },
            'business_status': 'OPERATIONAL'
        }
    }

    # Call tool
    result = get_place_details_tool(place_id="place_123")

    # Verify
    assert result['status'] == 'OK'
    assert result['place_id'] == 'place_123'
    assert result['name'] == 'Genentech'
    assert result['website'] == 'https://www.gene.com'
    assert result['latitude'] == 37.6624
    assert result['longitude'] == -122.3801
    assert result['business_status'] == 'OPERATIONAL'


def test_get_place_details_tool_error(setup_tool_registry, mock_gmaps):
    """Test get_place_details_tool with API error."""
    mock_gmaps.place.side_effect = Exception("API Error")

    result = get_place_details_tool(place_id="place_123")

    assert result['status'] == 'ERROR'
    assert 'error' in result


def test_get_place_details_tool_not_found(setup_tool_registry, mock_gmaps):
    """Test get_place_details_tool with place not found."""
    mock_gmaps.place.return_value = {
        'status': 'NOT_FOUND'
    }

    result = get_place_details_tool(place_id="invalid_place_id")

    assert result['status'] == 'NOT_FOUND'
    assert 'error' in result


# ============================================================================
# Test AnthropicUsageCounter
# ============================================================================

def test_anthropic_usage_counter_initialization():
    """Test usage counter initializes correctly."""
    counter = AnthropicUsageCounter()
    assert counter.total_calls == 0
    assert counter.total_input_tokens == 0
    assert counter.total_output_tokens == 0
    assert counter.total_tokens() == 0


def test_anthropic_usage_counter_record_usage():
    """Test usage counter records usage."""
    counter = AnthropicUsageCounter()

    # Mock usage object
    usage1 = Mock()
    usage1.input_tokens = 100
    usage1.output_tokens = 50

    counter.record_usage(usage1)

    assert counter.total_calls == 1
    assert counter.total_input_tokens == 100
    assert counter.total_output_tokens == 50
    assert counter.total_tokens() == 150

    # Record another
    usage2 = Mock()
    usage2.input_tokens = 200
    usage2.output_tokens = 75

    counter.record_usage(usage2)

    assert counter.total_calls == 2
    assert counter.total_input_tokens == 300
    assert counter.total_output_tokens == 125
    assert counter.total_tokens() == 425


def test_anthropic_usage_counter_report():
    """Test usage counter generates report."""
    counter = AnthropicUsageCounter()

    usage = Mock()
    usage.input_tokens = 1000
    usage.output_tokens = 500

    counter.record_usage(usage)

    report = counter.report()

    assert "Total calls: 1" in report
    assert "Input tokens: 1,000" in report
    assert "Output tokens: 500" in report
    assert "Total tokens: 1,500" in report


# ============================================================================
# Test Acceptance Logic
# ============================================================================

def test_accept_enrichment_result_success():
    """Test acceptance logic accepts valid result."""
    result = {
        'company_name': 'Genentech',
        'website': 'https://www.gene.com',
        'address': '1 DNA Way, South San Francisco, CA 94080',
        'city': 'South San Francisco',
        'place_id': 'place_123',
        'confidence': 0.95,
        'validation': {
            'in_bay_area': True,
            'is_business': True,
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'Perfect match: name, website, and location all confirmed'
        }
    }

    accepted, enriched_data = accept_enrichment_result(result, 'Genentech')

    assert accepted is True
    assert enriched_data['Company Name'] == 'Genentech'
    assert enriched_data['Website'] == 'https://www.gene.com'
    assert enriched_data['Address'] == '1 DNA Way, South San Francisco, CA 94080'
    assert enriched_data['City'] == 'South San Francisco'
    assert enriched_data['Confidence'] == '0.950'
    assert enriched_data['Validation_Source'] == 'PathB'


def test_accept_enrichment_result_reject_low_confidence():
    """Test acceptance logic rejects low confidence."""
    result = {
        'company_name': 'Test Company',
        'website': 'https://www.test.com',
        'address': '123 Main St, San Francisco, CA',
        'city': 'San Francisco',
        'place_id': 'place_456',
        'confidence': 0.65,  # Below threshold
        'validation': {
            'in_bay_area': True,
            'is_business': True,
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'Low confidence due to weak name match'
        }
    }

    accepted, enriched_data = accept_enrichment_result(result, 'Test Company')

    assert accepted is False
    assert enriched_data['Website'] == ''  # Nulled
    assert enriched_data['Address'] == ''  # Nulled
    assert 'Rejection_Reason' in enriched_data


def test_accept_enrichment_result_reject_not_bay_area():
    """Test acceptance logic rejects non-Bay Area location."""
    result = {
        'company_name': 'Davis Company',
        'website': 'https://www.davisco.com',
        'address': '123 Main St, Davis, CA 95616',
        'city': 'Davis',
        'place_id': 'place_789',
        'confidence': 0.90,
        'validation': {
            'in_bay_area': False,  # Not in Bay Area
            'is_business': True,
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'Location is outside 9-county Bay Area'
        }
    }

    accepted, enriched_data = accept_enrichment_result(result, 'Davis Company')

    assert accepted is False
    assert enriched_data['Website'] == ''
    assert 'Rejection_Reason' in enriched_data


def test_accept_enrichment_result_reject_not_business():
    """Test acceptance logic rejects non-business types."""
    result = {
        'company_name': 'Real Estate LLC',
        'website': 'https://www.realtor.com',
        'address': '123 Market St, San Francisco, CA',
        'city': 'San Francisco',
        'place_id': 'place_999',
        'confidence': 0.85,
        'validation': {
            'in_bay_area': True,
            'is_business': False,  # Not a valid business type
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'Business type is real_estate_agency (excluded)'
        }
    }

    accepted, enriched_data = accept_enrichment_result(result, 'Real Estate LLC')

    assert accepted is False
    assert enriched_data['Website'] == ''


def test_accept_enrichment_result_reject_aggregator():
    """Test acceptance logic rejects aggregator websites."""
    result = {
        'company_name': 'Some Company',
        'website': 'https://www.linkedin.com/company/some-company',  # Aggregator
        'address': '123 Main St, San Francisco, CA',
        'city': 'San Francisco',
        'place_id': 'place_111',
        'confidence': 0.80,
        'validation': {
            'in_bay_area': True,
            'is_business': True,
            'brand_domain_ok': False,  # Aggregator
            'multi_tenant_ok': True,
            'reasoning': 'Website is aggregator (LinkedIn)'
        }
    }

    accepted, enriched_data = accept_enrichment_result(result, 'Some Company')

    assert accepted is False
    assert enriched_data['Website'] == ''


def test_accept_enrichment_result_null_fields():
    """Test acceptance logic handles null fields correctly."""
    result = {
        'company_name': 'Unknown Company',
        'website': None,
        'address': None,
        'city': None,
        'place_id': None,
        'confidence': 0.50,
        'validation': {
            'in_bay_area': False,
            'is_business': False,
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'No valid candidates found'
        }
    }

    accepted, enriched_data = accept_enrichment_result(result, 'Unknown Company')

    assert accepted is False
    assert enriched_data['Website'] == ''
    assert enriched_data['Address'] == ''
    assert enriched_data['City'] == ''
    assert enriched_data['Place_ID'] == ''


# ============================================================================
# Test Tool Use Controller Loop (Mocked)
# ============================================================================

def test_run_structured_enrichment_mock():
    """Test run_structured_enrichment with mocked Anthropic response."""
    from scripts.path_b_enrichment import run_structured_enrichment

    # Mock Anthropic client
    mock_client = Mock()
    mock_counter = AnthropicUsageCounter()

    # Mock response - end_turn with JSON
    mock_response = Mock()
    mock_response.stop_reason = 'end_turn'

    # Mock content with JSON result
    json_result = {
        'company_name': 'Genentech',
        'website': 'https://www.gene.com',
        'address': '1 DNA Way, South San Francisco, CA 94080',
        'city': 'South San Francisco',
        'place_id': 'place_123',
        'confidence': 0.95,
        'validation': {
            'in_bay_area': True,
            'is_business': True,
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'Perfect match'
        }
    }

    mock_text_block = Mock()
    mock_text_block.text = json.dumps(json_result)
    mock_response.content = [mock_text_block]

    # Mock usage
    mock_usage = Mock()
    mock_usage.input_tokens = 500
    mock_usage.output_tokens = 200
    mock_response.usage = mock_usage

    # Setup mock client
    mock_client.messages.create.return_value = mock_response

    # Call function
    result = run_structured_enrichment(
        company_name='Genentech',
        city='South San Francisco',
        client=mock_client,
        counter=mock_counter
    )

    # Verify
    assert result['company_name'] == 'Genentech'
    assert result['confidence'] == 0.95
    assert result['validation']['in_bay_area'] is True

    # Verify usage recorded
    assert mock_counter.total_calls == 1
    assert mock_counter.total_input_tokens == 500
    assert mock_counter.total_output_tokens == 200


def test_run_structured_enrichment_tool_use():
    """Test run_structured_enrichment with tool use."""
    from scripts.path_b_enrichment import run_structured_enrichment

    # Setup mock gmaps
    mock_gmaps = Mock()
    TOOL_REGISTRY['gmaps'] = mock_gmaps

    # Mock Google Maps responses
    mock_gmaps.places.return_value = {
        'status': 'OK',
        'results': [
            {
                'place_id': 'place_123',
                'name': 'Genentech',
                'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
                'types': ['establishment']
            }
        ]
    }

    mock_gmaps.place.return_value = {
        'status': 'OK',
        'result': {
            'name': 'Genentech',
            'formatted_address': '1 DNA Way, South San Francisco, CA 94080',
            'website': 'https://www.gene.com',
            'types': ['establishment'],
            'geometry': {'location': {'lat': 37.6624, 'lng': -122.3801}},
            'business_status': 'OPERATIONAL'
        }
    }

    # Mock Anthropic client
    mock_client = Mock()
    mock_counter = AnthropicUsageCounter()

    # Mock first response - tool use
    mock_response1 = Mock()
    mock_response1.stop_reason = 'tool_use'

    mock_tool_use = Mock()
    mock_tool_use.type = 'tool_use'
    mock_tool_use.name = 'search_places'
    mock_tool_use.input = {'query': 'Genentech South San Francisco CA biotech'}
    mock_tool_use.id = 'toolu_123'

    mock_response1.content = [mock_tool_use]
    mock_response1.usage = Mock(input_tokens=400, output_tokens=100)

    # Mock second response - end_turn with JSON
    mock_response2 = Mock()
    mock_response2.stop_reason = 'end_turn'

    json_result = {
        'company_name': 'Genentech',
        'website': 'https://www.gene.com',
        'address': '1 DNA Way, South San Francisco, CA 94080',
        'city': 'South San Francisco',
        'place_id': 'place_123',
        'confidence': 0.95,
        'validation': {
            'in_bay_area': True,
            'is_business': True,
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'Perfect match'
        }
    }

    mock_text_block = Mock()
    mock_text_block.text = json.dumps(json_result)
    mock_response2.content = [mock_text_block]
    mock_response2.usage = Mock(input_tokens=600, output_tokens=250)

    # Setup mock client to return different responses
    mock_client.messages.create.side_effect = [mock_response1, mock_response2]

    # Call function
    result = run_structured_enrichment(
        company_name='Genentech',
        city='South San Francisco',
        client=mock_client,
        counter=mock_counter
    )

    # Verify
    assert result['company_name'] == 'Genentech'
    assert result['confidence'] == 0.95

    # Verify two API calls were made
    assert mock_client.messages.create.call_count == 2

    # Verify usage recorded for both calls
    assert mock_counter.total_calls == 2
    assert mock_counter.total_input_tokens == 1000  # 400 + 600
    assert mock_counter.total_output_tokens == 350  # 100 + 250

    # Cleanup
    del TOOL_REGISTRY['gmaps']


# ============================================================================
# Integration Tests
# ============================================================================

def test_full_path_b_pipeline():
    """Test full Path B pipeline with mocked responses."""
    # Setup mock gmaps
    mock_gmaps = Mock()
    TOOL_REGISTRY['gmaps'] = mock_gmaps

    # Mock successful search and details
    mock_gmaps.places.return_value = {
        'status': 'OK',
        'results': [
            {
                'place_id': 'place_123',
                'name': '10X Genomics',
                'formatted_address': '6230 Stoneridge Mall Rd, Pleasanton, CA 94588',
                'types': ['establishment']
            }
        ]
    }

    mock_gmaps.place.return_value = {
        'status': 'OK',
        'result': {
            'name': '10X Genomics',
            'formatted_address': '6230 Stoneridge Mall Rd, Pleasanton, CA 94588',
            'website': 'https://www.10xgenomics.com',
            'types': ['point_of_interest', 'establishment'],
            'geometry': {'location': {'lat': 37.6938, 'lng': -121.9289}},
            'business_status': 'OPERATIONAL'
        }
    }

    # Test search_places_tool
    search_result = search_places_tool(query="10X Genomics Pleasanton CA biotech")
    assert search_result['status'] == 'OK'
    assert len(search_result['results']) > 0

    # Test get_place_details_tool
    details_result = get_place_details_tool(place_id='place_123')
    assert details_result['status'] == 'OK'
    assert details_result['name'] == '10X Genomics'

    # Test acceptance logic with good result
    enrichment_result = {
        'company_name': '10X Genomics',
        'website': 'https://www.10xgenomics.com',
        'address': '6230 Stoneridge Mall Rd, Pleasanton, CA 94588',
        'city': 'Pleasanton',
        'place_id': 'place_123',
        'confidence': 0.92,
        'validation': {
            'in_bay_area': True,
            'is_business': True,
            'brand_domain_ok': True,
            'multi_tenant_ok': True,
            'reasoning': 'Strong match on all criteria'
        }
    }

    accepted, enriched_data = accept_enrichment_result(enrichment_result, '10X Genomics')
    assert accepted is True
    assert enriched_data['Validation_Source'] == 'PathB'
    assert enriched_data['Confidence'] == '0.920'

    # Cleanup
    del TOOL_REGISTRY['gmaps']
