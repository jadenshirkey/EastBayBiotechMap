#!/usr/bin/env python3
"""
ClinicalTrials.gov API Client for Company Enrichment
Identifies clinical-stage companies through trial sponsorship
"""

import requests
import json
import time
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import re
from difflib import SequenceMatcher
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from db.db_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ClinicalTrialsClient:
    """Client for ClinicalTrials.gov API v2"""

    BASE_URL = "https://clinicaltrials.gov/api/v2"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'Accept': 'application/json',
            'User-Agent': 'EastBayBiotechMap/1.0'
        })
        self.rate_limit_delay = 0.5  # 500ms between requests
        self.last_request_time = 0

    def _rate_limit(self):
        """Implement rate limiting"""
        elapsed = time.time() - self.last_request_time
        if elapsed < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - elapsed)
        self.last_request_time = time.time()

    def search_by_sponsor(self, company_name: str, max_studies: int = 100) -> List[Dict]:
        """
        Search for clinical trials by sponsor or collaborator name

        Args:
            company_name: Name of the company to search
            max_studies: Maximum number of studies to return

        Returns:
            List of clinical trial records
        """
        self._rate_limit()

        # Build query using the generic query.term parameter which searches all fields including sponsors
        # API v2 uses pipe-separated field names, not comma-separated
        params = {
            'query.spons': company_name,  # Search sponsor field
            'pageSize': min(max_studies, 1000),  # API v2 allows up to 1000 per page
            'format': 'json'
            # Don't specify fields to get full data structure
        }

        try:
            response = self.session.get(
                f"{self.BASE_URL}/studies",
                params=params,
                timeout=30
            )
            response.raise_for_status()

            data = response.json()
            studies = data.get('studies', [])

            # Also search as collaborator if no results as sponsor
            if not studies:
                # Try with generic term search which searches more fields
                params = {
                    'query.term': company_name,
                    'pageSize': min(max_studies, 1000),
                    'format': 'json'
                }

                response = self.session.get(
                    f"{self.BASE_URL}/studies",
                    params=params,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()
                studies = data.get('studies', [])

            return studies

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to search trials for {company_name}: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response text: {e.response.text[:500]}")
            return []

    def get_study_details(self, nct_id: str) -> Optional[Dict]:
        """Get detailed information for a specific study"""
        self._rate_limit()

        try:
            response = self.session.get(
                f"{self.BASE_URL}/studies/{nct_id}",
                params={'format': 'json'},
                timeout=30
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get study {nct_id}: {e}")
            return None

    def parse_study(self, study_data: Dict) -> Dict:
        """Parse study data into standardized format"""
        # Handle nested structure
        protocol_section = study_data.get('protocolSection', {})
        id_module = protocol_section.get('identificationModule', {})
        status_module = protocol_section.get('statusModule', {})
        design_module = protocol_section.get('designModule', {})
        conditions_module = protocol_section.get('conditionsModule', {})
        arms_module = protocol_section.get('armsInterventionsModule', {})
        contacts_module = protocol_section.get('contactsLocationsModule', {})
        sponsor_module = protocol_section.get('sponsorCollaboratorsModule', {})

        # Extract phase
        phases = design_module.get('phases', [])
        phase = phases[0] if phases else None

        # Extract enrollment
        enrollment_info = design_module.get('enrollmentInfo', {})
        enrollment = enrollment_info.get('count', 0)

        # Extract dates
        start_date_struct = status_module.get('startDateStruct', {})
        completion_date_struct = status_module.get('completionDateStruct', {})

        # Extract locations
        locations = []
        location_list = contacts_module.get('locations', [])
        for loc in location_list[:5]:  # Limit to first 5 locations
            locations.append({
                'city': loc.get('city'),
                'state': loc.get('state'),
                'country': loc.get('country')
            })

        # Extract conditions
        conditions = conditions_module.get('conditions', [])

        # Extract interventions
        interventions = []
        intervention_list = arms_module.get('interventions', [])
        for intervention in intervention_list:
            interventions.append({
                'type': intervention.get('type'),
                'name': intervention.get('name')
            })

        # Extract sponsor info
        lead_sponsor = sponsor_module.get('leadSponsor', {})
        collaborators = sponsor_module.get('collaborators', [])

        return {
            'nct_id': id_module.get('nctId'),
            'trial_title': id_module.get('briefTitle'),
            'trial_status': status_module.get('overallStatus'),
            'phase': phase,
            'enrollment': enrollment,
            'start_date': start_date_struct.get('date'),
            'completion_date': completion_date_struct.get('date'),
            'conditions': conditions,
            'interventions': interventions,
            'locations': locations,
            'sponsor_name': lead_sponsor.get('name'),
            'collaborators': [c.get('name') for c in collaborators],
            'clinicaltrials_url': f"https://clinicaltrials.gov/study/{id_module.get('nctId')}"
        }

    def calculate_match_confidence(self, company_name: str, sponsor_name: str) -> float:
        """Calculate confidence in sponsor/company name match"""
        if not company_name or not sponsor_name:
            return 0.0

        # Normalize names
        def normalize(name):
            # Remove common suffixes
            name = re.sub(r'\b(Inc|LLC|Corp|Corporation|Ltd|Limited|Co|Company)\b\.?', '', name, flags=re.IGNORECASE)
            # Remove special characters and extra spaces
            name = re.sub(r'[^\w\s]', ' ', name)
            name = ' '.join(name.split()).lower()
            return name

        norm_company = normalize(company_name)
        norm_sponsor = normalize(sponsor_name)

        # Exact match after normalization
        if norm_company == norm_sponsor:
            return 1.0

        # Check if one contains the other
        if norm_company in norm_sponsor or norm_sponsor in norm_company:
            return 0.9

        # Fuzzy matching
        similarity = SequenceMatcher(None, norm_company, norm_sponsor).ratio()

        # Adjust confidence based on similarity
        if similarity > 0.85:
            return 0.85
        elif similarity > 0.75:
            return 0.75
        elif similarity > 0.65:
            return 0.65
        else:
            return similarity

class ClinicalTrialsEnricher:
    """Enricher for batch processing companies through ClinicalTrials.gov"""

    def __init__(self, db_path: str = "data/bayarea_biotech_sources.db"):
        self.db = DatabaseManager(db_path)
        self.client = ClinicalTrialsClient()
        self.stats = {
            'total_processed': 0,
            'trials_found': 0,
            'clinical_stage': 0,
            'errors': 0
        }

    def classify_company_stage(self, trials: List[Dict]) -> Tuple[str, float]:
        """
        Classify company stage based on clinical trials

        Returns:
            Tuple of (stage, confidence)
        """
        if not trials:
            return ('Unknown', 0.0)

        # Normalize phase names to standard format
        def normalize_phase(phase):
            if not phase:
                return None
            # Convert PHASE1, PHASE2, etc. to Phase 1, Phase 2
            phase = str(phase).upper().replace('_', ' ')
            if 'PHASE' in phase:
                # PHASE1 -> Phase 1, PHASE2 -> Phase 2
                phase = phase.replace('PHASE', 'Phase ')
            return phase

        # Count trials by phase
        phase_counts = {
            'Phase 4': 0,
            'Phase 3': 0,
            'Phase 2 Phase 3': 0,
            'Phase 2': 0,
            'Phase 1 Phase 2': 0,
            'Phase 1': 0,
            'Early Phase 1': 0
        }

        active_count = 0
        completed_count = 0

        for trial in trials:
            phase = normalize_phase(trial.get('phase'))
            if phase:
                # Count by phase (handle multiple variations)
                if '4' in phase:
                    phase_counts['Phase 4'] += 1
                if '3' in phase:
                    phase_counts['Phase 3'] += 1
                if '2' in phase and '3' in phase:
                    phase_counts['Phase 2 Phase 3'] += 1
                elif '2' in phase:
                    phase_counts['Phase 2'] += 1
                if '1' in phase and '2' in phase:
                    phase_counts['Phase 1 Phase 2'] += 1
                elif '1' in phase:
                    phase_counts['Phase 1'] += 1
                if 'EARLY' in phase.upper():
                    phase_counts['Early Phase 1'] += 1

            status = trial.get('trial_status')
            if status in ['RECRUITING', 'ACTIVE_NOT_RECRUITING', 'ENROLLING_BY_INVITATION',
                         'Recruiting', 'Active, not recruiting', 'Enrolling by invitation']:
                active_count += 1
            elif status in ['COMPLETED', 'Completed']:
                completed_count += 1

        # Determine stage based on highest phase with active/recent trials
        if phase_counts['Phase 4'] > 0 or phase_counts['Phase 3'] > 0:
            # Has late-stage trials - likely public or late-stage private
            return ('Public/Late-Stage', 0.85)
        elif phase_counts['Phase 2'] > 0 or phase_counts['Phase 2 Phase 3'] > 0:
            # Phase 2 clinical stage
            return ('Clinical Stage', 0.90)
        elif phase_counts['Phase 1'] > 0 or phase_counts['Phase 1 Phase 2'] > 0 or phase_counts['Early Phase 1'] > 0:
            # Phase 1 clinical stage
            return ('Clinical Stage', 0.85)
        elif active_count > 0:
            # Has active trials but phase unknown
            return ('Clinical Stage', 0.70)
        elif completed_count > 0:
            # Only completed trials
            return ('Clinical Stage', 0.65)
        else:
            return ('Unknown', 0.0)

    def enrich_company(self, company: Dict) -> Optional[Dict]:
        """Enrich a single company with clinical trials data"""
        company_name = company['company_name']
        company_id = company['company_id']

        try:
            # Search for trials
            studies = self.client.search_by_sponsor(company_name, max_studies=50)

            if not studies:
                # Try alternate name formats
                alt_names = self.generate_alternate_names(company_name)
                for alt_name in alt_names:
                    studies = self.client.search_by_sponsor(alt_name, max_studies=50)
                    if studies:
                        break

            if studies:
                self.stats['trials_found'] += 1

                # Parse and save trials
                saved_trials = []
                for study in studies[:20]:  # Limit to 20 most relevant
                    trial_data = self.client.parse_study(study)

                    # Calculate match confidence
                    sponsor_name = trial_data.get('sponsor_name', '')
                    confidence = self.client.calculate_match_confidence(company_name, sponsor_name)

                    if confidence > 0.5:  # Only save if reasonable match
                        trial_data['match_confidence'] = confidence

                        # Save to database
                        self.db.add_clinical_trial(company_id, trial_data)
                        saved_trials.append(trial_data)

                if saved_trials:
                    # Classify company stage
                    stage, stage_confidence = self.classify_company_stage(saved_trials)

                    if stage != 'Unknown':
                        self.stats['clinical_stage'] += 1

                        # Update classification
                        self.db.add_classification(
                            company_id,
                            stage,
                            'clinical_trials',
                            stage_confidence,
                            'ClinicalTrials.gov'
                        )

                    # Log API call
                    self.db.log_api_call(
                        'clinicaltrials',
                        'search',
                        company_id,
                        200,
                        None,
                        0.0  # Free API
                    )

                    return {
                        'company_name': company_name,
                        'trials_count': len(saved_trials),
                        'stage': stage,
                        'confidence': stage_confidence
                    }

            return None

        except Exception as e:
            logger.error(f"Failed to enrich {company_name}: {e}")
            self.stats['errors'] += 1

            # Log API error
            self.db.log_api_call(
                'clinicaltrials',
                'search',
                company_id,
                500,
                str(e),
                0.0
            )

            return None

    def generate_alternate_names(self, company_name: str) -> List[str]:
        """Generate alternate name formats for better matching"""
        alternates = []

        # Remove common suffixes
        base_name = re.sub(r'\b(Inc|LLC|Corp|Corporation|Ltd|Limited|Co|Company)\b\.?', '',
                          company_name, flags=re.IGNORECASE).strip()

        if base_name != company_name:
            alternates.append(base_name)

        # Try with different suffixes
        if not any(suffix in company_name.upper() for suffix in ['INC', 'LLC', 'CORP']):
            alternates.append(f"{base_name}, Inc.")
            alternates.append(f"{base_name} Inc")

        # Handle special characters
        if '&' in company_name:
            alternates.append(company_name.replace('&', 'and'))
        elif ' and ' in company_name.lower():
            alternates.append(company_name.replace(' and ', ' & '))

        return alternates[:3]  # Limit to 3 alternates

    def run_enrichment(self, limit: Optional[int] = None, sample: bool = False):
        """
        Run clinical trials enrichment for all companies

        Args:
            limit: Maximum number of companies to process
            sample: If True, only process a small sample
        """
        # Get companies to enrich
        companies = self.db.get_companies_for_enrichment('clinical_trials')

        if sample:
            # For sample run, just process first 10
            companies = companies[:10]
        elif limit:
            companies = companies[:limit]

        total = len(companies)
        logger.info(f"Processing {total} companies for clinical trials enrichment")

        enriched_companies = []

        for i, company in enumerate(companies, 1):
            self.stats['total_processed'] += 1

            # Process company
            result = self.enrich_company(company)

            if result:
                enriched_companies.append(result)
                logger.info(f"CLINICAL: {result['company_name']} -> {result['trials_count']} trials, {result['stage']}")
            else:
                logger.info(f"NO TRIALS: {company['company_name']}")

            # Progress update
            if i % 10 == 0:
                logger.info(f"Progress: {i}/{total} ({i/total*100:.1f}%)")

        # Final statistics
        logger.info("="*60)
        logger.info("CLINICAL TRIALS ENRICHMENT COMPLETE")
        logger.info("="*60)
        logger.info(f"Total processed: {self.stats['total_processed']}")
        logger.info(f"Companies with trials: {self.stats['trials_found']}")
        logger.info(f"Clinical stage identified: {self.stats['clinical_stage']}")
        logger.info(f"Errors: {self.stats['errors']}")

        # Get updated statistics
        db_stats = self.db.get_enrichment_stats()
        logger.info(f"Clinical trials coverage: {db_stats['trials_coverage']:.1f}%")

        return enriched_companies

def main():
    """Main function for standalone execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Enrich companies with ClinicalTrials.gov data')
    parser.add_argument('--sample', action='store_true', help='Run sample enrichment (10 companies)')
    parser.add_argument('--limit', type=int, help='Limit number of companies to process')
    args = parser.parse_args()

    enricher = ClinicalTrialsEnricher()

    if args.sample:
        logger.info("Running sample enrichment (10 companies)...")
        enricher.run_enrichment(sample=True)
    else:
        enricher.run_enrichment(limit=args.limit)

if __name__ == "__main__":
    main()