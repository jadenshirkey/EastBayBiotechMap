#!/usr/bin/env python3
"""
Test script to verify ClinicalTrials API fixes
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enrichment.clinicaltrials_client import ClinicalTrialsClient, ClinicalTrialsEnricher
from db.db_manager import DatabaseManager

def test_api_client():
    """Test the API client with known companies"""
    print("=" * 80)
    print("TESTING CLINICALTRIALS API CLIENT")
    print("=" * 80)

    client = ClinicalTrialsClient()

    # Test companies known to have clinical trials
    test_companies = [
        "Genentech",
        "Gilead Sciences",
        "Amgen",
        "Moderna",
        "BioMarin"
    ]

    for company_name in test_companies:
        print(f"\n{'='*60}")
        print(f"Testing: {company_name}")
        print(f"{'='*60}")

        # Search for trials
        studies = client.search_by_sponsor(company_name, max_studies=5)

        print(f"Found {len(studies)} trials")

        if studies:
            # Parse first study
            for i, study in enumerate(studies[:2], 1):
                trial_data = client.parse_study(study)

                print(f"\nTrial {i}:")
                print(f"  NCT ID: {trial_data.get('nct_id')}")
                print(f"  Title: {trial_data.get('trial_title', '')[:80]}...")
                print(f"  Status: {trial_data.get('trial_status')}")
                print(f"  Phase: {trial_data.get('phase')}")
                print(f"  Sponsor: {trial_data.get('sponsor_name')}")
                print(f"  Match confidence: {client.calculate_match_confidence(company_name, trial_data.get('sponsor_name', '')):.2f}")
        else:
            print("  ⚠ No trials found")

    print("\n" + "=" * 80)
    print("API CLIENT TEST COMPLETE")
    print("=" * 80)

def test_enricher():
    """Test the enricher with a small sample"""
    print("\n\n" + "=" * 80)
    print("TESTING CLINICALTRIALS ENRICHER")
    print("=" * 80)

    enricher = ClinicalTrialsEnricher()

    # Get first 3 companies from database
    db = DatabaseManager('data/bayarea_biotech_sources.db')
    companies = db.get_companies_for_enrichment('clinical_trials')[:3]

    print(f"\nTesting with {len(companies)} companies from database:")
    for company in companies:
        print(f"  - {company['company_name']}")

    print("\n" + "-" * 80)

    for company in companies:
        print(f"\nProcessing: {company['company_name']}")
        result = enricher.enrich_company(company)

        if result:
            print(f"  ✓ Found {result['trials_count']} trials")
            print(f"    Stage: {result['stage']}")
            print(f"    Confidence: {result['confidence']:.2f}")
        else:
            print(f"  - No trials found")

    print("\n" + "=" * 80)
    print("ENRICHER TEST COMPLETE")
    print("=" * 80)
    print(f"Statistics:")
    print(f"  Total processed: {enricher.stats['total_processed']}")
    print(f"  Trials found: {enricher.stats['trials_found']}")
    print(f"  Clinical stage identified: {enricher.stats['clinical_stage']}")
    print(f"  Errors: {enricher.stats['errors']}")

def test_stage_classification():
    """Test the stage classification logic"""
    print("\n\n" + "=" * 80)
    print("TESTING STAGE CLASSIFICATION")
    print("=" * 80)

    enricher = ClinicalTrialsEnricher()

    # Test various trial scenarios
    test_cases = [
        {
            'name': 'Phase 3 Active',
            'trials': [
                {'phase': 'PHASE3', 'trial_status': 'Recruiting'},
                {'phase': 'PHASE2', 'trial_status': 'Completed'}
            ]
        },
        {
            'name': 'Phase 2 Active',
            'trials': [
                {'phase': 'PHASE2', 'trial_status': 'Recruiting'},
                {'phase': 'PHASE1', 'trial_status': 'Completed'}
            ]
        },
        {
            'name': 'Phase 1 Active',
            'trials': [
                {'phase': 'PHASE1', 'trial_status': 'Recruiting'}
            ]
        },
        {
            'name': 'No Phase Info',
            'trials': [
                {'trial_status': 'Recruiting'}
            ]
        },
        {
            'name': 'Only Completed',
            'trials': [
                {'phase': 'PHASE2', 'trial_status': 'Completed'}
            ]
        },
        {
            'name': 'No Trials',
            'trials': []
        }
    ]

    for test_case in test_cases:
        stage, confidence = enricher.classify_company_stage(test_case['trials'])
        print(f"\n{test_case['name']}:")
        print(f"  Stage: {stage}")
        print(f"  Confidence: {confidence:.2f}")
        print(f"  Trials: {test_case['trials']}")

if __name__ == "__main__":
    # Run all tests
    test_api_client()
    test_enricher()
    test_stage_classification()

    print("\n\n" + "=" * 80)
    print("ALL TESTS COMPLETE")
    print("=" * 80)
