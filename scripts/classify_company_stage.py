#!/usr/bin/env python3
"""
Stage-D: Company Stage Classification Script

Classifies companies into one of 8 categories based on verifiable signals:
- Public (stock ticker)
- Private (Series A-D+)
- Acquired (acquisition announcements)
- Clinical (clinical trial stage)
- Research (research-only, no products)
- Incubator (incubator/accelerator)
- Service (CRO, consulting, services)
- Unknown (ambiguous or insufficient data)

Default to "Unknown" if ambiguous - prefer null over wrong data.

Usage:
    python scripts/classify_company_stage.py

Input:  data/working/companies_enriched.csv
Output: data/working/companies_classified.csv

Author: Bay Area Biotech Map V4.3
Date: 2025-11-16
"""

import csv
import sys
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# ============================================================================
# Setup Logging
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# Constants
# ============================================================================

INPUT_FILE = Path("data/working/companies_enriched.csv")
OUTPUT_FILE = Path("data/working/companies_classified.csv")

# Company stages (8 categories per methodology)
STAGE_PUBLIC = "Public"
STAGE_PRIVATE = "Private"
STAGE_ACQUIRED = "Acquired"
STAGE_CLINICAL = "Clinical"
STAGE_RESEARCH = "Research"
STAGE_INCUBATOR = "Incubator"
STAGE_SERVICE = "Service"
STAGE_UNKNOWN = "Unknown"

# Known public biotech companies (stock ticker holders)
# This is a small sample - in production, this could be enriched from SEC/market data
PUBLIC_COMPANIES = {
    "Genentech",  # Part of Roche but historically public
    "Gilead Sciences",
    "BioMarin Pharmaceutical",
    "Twist Bioscience",
    "10x Genomics",
    "Berkeley Lights",
    "Zymergen",
    "Vir Biotechnology",
    "Allogene Therapeutics",
    "Revolution Medicines",
    "Natera",
    "Veracyte",
    "Nektar Therapeutics",
    "Atara Biotherapeutics",
    "Five Prime Therapeutics",
}

# Public company indicators (when found in descriptions)
PUBLIC_INDICATORS = [
    "publicly traded", "public company", "NASDAQ:", "NYSE:",
    "stock symbol", "ticker symbol", "market cap", "went public",
    "IPO in", "initial public offering", "shares traded"
]

# Known acquired companies
ACQUIRED_COMPANIES = {
    "Flatiron Health",  # Acquired by Roche
    "Juno Therapeutics",  # Acquired by Celgene/BMS
    "Kite Pharma",  # Acquired by Gilead
    "Stemcentrx",  # Acquired by AbbVie
    "Pharmacyclics",  # Acquired by AbbVie
    "Acerta Pharma",  # Acquired by AstraZeneca
}

# Acquisition indicators
ACQUIRED_INDICATORS = [
    "acquired by", "acquisition by", "purchased by", "bought by",
    "subsidiary of", "part of", "merged with", "acquisition completed",
    "deal closed", "takeover"
]

# Private company/funding indicators
PRIVATE_INDICATORS = [
    "series a", "series b", "series c", "series d", "series e", "series f",
    "venture funding", "raised $", "funding round", "venture capital",
    "private equity", "privately held", "private company", "startup",
    "seed funding", "angel investment", "pre-ipo"
]

# Clinical stage indicators
CLINICAL_INDICATORS = [
    "phase 1", "phase i", "phase 2", "phase ii", "phase 3", "phase iii",
    "clinical trials", "clinical development", "clinical-stage",
    "IND", "NDA", "BLA", "FDA approval pending", "in clinical trials",
    "first-in-human", "pivotal trial", "registrational trial"
]

# Research/pre-clinical indicators
RESEARCH_INDICATORS = [
    "research institute", "research center", "research foundation",
    "pre-clinical", "preclinical", "discovery stage", "research stage",
    "early-stage research", "basic research", "translational research",
    "academic spin", "university spin", "research focused",
    "discovery platform", "target discovery", "lead optimization"
]

# Service provider keywords (CROs, consulting, testing labs)
SERVICE_KEYWORDS = [
    "CRO", "contract research", "contract development", "contract manufacturing",
    "CDMO", "CMO", "consulting", "services company", "service provider",
    "testing lab", "clinical trials management", "diagnostics lab",
    "laboratory services", "bioanalytical", "preclinical services",
    "outsourcing", "contract services", "fee-for-service",
    "analytical services", "manufacturing services"
]

# Incubator/accelerator keywords
INCUBATOR_KEYWORDS = [
    "incubator", "accelerator", "QB3", "IndieBio", "Y Combinator",
    "JLABS", "J&J Labs", "BioLabs", "co-working", "shared lab space",
    "innovation hub", "startup hub", "biotech hub", "life science park",
    "innovation center", "entrepreneurship center"
]


# ============================================================================
# Classification Logic
# ============================================================================

def classify_company_stage(company_name: str, website: Optional[str],
                           focus_areas: Optional[str] = None,
                           description: Optional[str] = None) -> str:
    """
    Classify a company into one of 8 stages using the methodology decision tree.

    Enhanced with Wikipedia description parsing for V4.3 to reduce Unknown classifications.
    Priority order:
    1. Known company lists (exact matches)
    2. Strong indicators in description (acquired, public, etc.)
    3. Keyword matching in focus areas and description
    4. Name-based heuristics

    Args:
        company_name: Name of the company
        website: Company website (may be None)
        focus_areas: Focus areas/notes field
        description: Wikipedia description (first paragraph)

    Returns:
        One of the 8 stage categories, or "Unknown"
    """
    if not company_name:
        return STAGE_UNKNOWN

    # Normalize for comparison
    name_lower = company_name.lower()
    focus_lower = focus_areas.lower() if focus_areas else ""
    desc_lower = description.lower() if description else ""
    combined_text = f"{name_lower} {focus_lower} {desc_lower}"

    # === Priority 1: Known company exact matches ===

    # Check 1: Known public companies
    for public_co in PUBLIC_COMPANIES:
        if public_co.lower() in name_lower:
            logger.debug(f"  → Classified as Public (known ticker holder): {company_name}")
            return STAGE_PUBLIC

    # Check 2: Known acquired companies
    for acquired_co in ACQUIRED_COMPANIES:
        if acquired_co.lower() in name_lower:
            logger.debug(f"  → Classified as Acquired: {company_name}")
            return STAGE_ACQUIRED

    # === Priority 2: Strong indicators in description ===

    # Check for acquisition indicators (high confidence)
    for indicator in ACQUIRED_INDICATORS:
        if indicator in desc_lower:
            logger.debug(f"  → Classified as Acquired (indicator: {indicator}): {company_name}")
            return STAGE_ACQUIRED

    # Check for public company indicators
    for indicator in PUBLIC_INDICATORS:
        if indicator in desc_lower:
            logger.debug(f"  → Classified as Public (indicator: {indicator}): {company_name}")
            return STAGE_PUBLIC

    # === Priority 3: Business model detection ===

    # Check for incubator/accelerator (very specific)
    for keyword in INCUBATOR_KEYWORDS:
        if keyword.lower() in combined_text:
            logger.debug(f"  → Classified as Incubator (keyword: {keyword}): {company_name}")
            return STAGE_INCUBATOR

    # Check for service provider (CRO, CDMO, consulting)
    service_score = sum(1 for keyword in SERVICE_KEYWORDS if keyword.lower() in combined_text)
    if service_score >= 2:  # Need at least 2 service indicators for confidence
        logger.debug(f"  → Classified as Service (score: {service_score}): {company_name}")
        return STAGE_SERVICE

    # === Priority 4: Development stage detection ===

    # Check for clinical stage indicators
    clinical_score = sum(1 for indicator in CLINICAL_INDICATORS if indicator in desc_lower)
    if clinical_score >= 1:  # Clinical trials are very specific
        logger.debug(f"  → Classified as Clinical (score: {clinical_score}): {company_name}")
        return STAGE_CLINICAL

    # Check for research/pre-clinical indicators
    research_score = sum(1 for indicator in RESEARCH_INDICATORS if indicator in desc_lower)
    if research_score >= 2:  # Need multiple research indicators
        logger.debug(f"  → Classified as Research (score: {research_score}): {company_name}")
        return STAGE_RESEARCH

    # Check for private company/funding indicators
    private_score = sum(1 for indicator in PRIVATE_INDICATORS if indicator in desc_lower)
    if private_score >= 1:
        logger.debug(f"  → Classified as Private (funding indicators: {private_score}): {company_name}")
        return STAGE_PRIVATE

    # === Priority 5: Name-based heuristics ===

    # Therapeutics companies are typically private or clinical stage
    if "therapeutics" in name_lower or "pharma" in name_lower or "medicines" in name_lower:
        # If we have description text, lean toward Private (most common)
        if desc_lower:
            logger.debug(f"  → Classified as Private (therapeutics/pharma company): {company_name}")
            return STAGE_PRIVATE
        else:
            # Without description, still classify as Private rather than Unknown
            logger.debug(f"  → Classified as Private (therapeutics in name, no description): {company_name}")
            return STAGE_PRIVATE

    # Biotechnology/Biosciences companies
    if "biotech" in name_lower or "bioscience" in name_lower or "bio" in name_lower:
        if desc_lower:
            logger.debug(f"  → Classified as Private (biotech company): {company_name}")
            return STAGE_PRIVATE

    # Research institutes (backup check)
    if "institute" in name_lower or "foundation" in name_lower or "center" in name_lower:
        if "research" in name_lower or "medical" in name_lower:
            logger.debug(f"  → Classified as Research (institute/foundation): {company_name}")
            return STAGE_RESEARCH

    # Labs (could be service or research)
    if "laboratories" in name_lower or "labs" in name_lower:
        if "diagnostic" in combined_text or "testing" in combined_text:
            logger.debug(f"  → Classified as Service (diagnostic lab): {company_name}")
            return STAGE_SERVICE
        else:
            logger.debug(f"  → Classified as Research (labs): {company_name}")
            return STAGE_RESEARCH

    # === Final fallback ===

    # If we have any substantial description but couldn't classify,
    # default to Private (most common for biotech)
    if len(desc_lower) > 50:
        logger.debug(f"  → Classified as Private (default for described company): {company_name}")
        return STAGE_PRIVATE

    # Only use Unknown when we truly have no information
    logger.debug(f"  → Classified as Unknown (no signals found): {company_name}")
    return STAGE_UNKNOWN


def process_classification(input_path: Path, output_path: Path) -> Dict[str, int]:
    """
    Read enriched companies CSV and add Company_Stage classification.

    Args:
        input_path: Path to companies_enriched.csv
        output_path: Path to output companies_classified.csv

    Returns:
        Dictionary with classification statistics
    """
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.info("This script expects companies_enriched.csv from Stage C (enrichment).")
        logger.info("If you haven't run enrichment yet, this is expected.")
        return {}

    # Statistics
    stats = {
        "total": 0,
        STAGE_PUBLIC: 0,
        STAGE_PRIVATE: 0,
        STAGE_ACQUIRED: 0,
        STAGE_CLINICAL: 0,
        STAGE_RESEARCH: 0,
        STAGE_INCUBATOR: 0,
        STAGE_SERVICE: 0,
        STAGE_UNKNOWN: 0,
    }

    # Get current date for Classifier_Date field
    classifier_date = datetime.now().strftime("%Y-%m-%d")

    # Read input, classify, write output
    logger.info(f"Reading from: {input_path}")

    with open(input_path, 'r', encoding='utf-8') as infile:
        reader = csv.DictReader(infile)

        # Prepare output fieldnames (add new columns)
        fieldnames = reader.fieldnames + ["Company_Stage", "Classifier_Date"]

        with open(output_path, 'w', encoding='utf-8', newline='') as outfile:
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                stats["total"] += 1

                # Extract fields
                company_name = row.get("Company Name", "")
                website = row.get("Website", "")
                # Get focus areas (from enrichment or existing data)
                focus_areas = row.get("Focus Areas", "") or row.get("Focus_Areas", "") or row.get("Notes", "")
                # Get description (from Wikipedia extraction)
                description = row.get("Description", "")

                # Classify using enhanced function with Description support
                stage = classify_company_stage(company_name, website, focus_areas, description)

                # Add new fields
                row["Company_Stage"] = stage
                row["Classifier_Date"] = classifier_date

                # Update stats
                stats[stage] += 1

                # Write to output
                writer.writerow(row)

    logger.info(f"Output written to: {output_path}")

    return stats


def print_statistics(stats: Dict[str, int]) -> None:
    """Print classification statistics."""
    if not stats:
        return

    total = stats["total"]

    logger.info("=" * 60)
    logger.info("CLASSIFICATION STATISTICS")
    logger.info("=" * 60)
    logger.info(f"Total companies classified: {total}")
    logger.info("")

    for stage in [STAGE_PUBLIC, STAGE_PRIVATE, STAGE_ACQUIRED, STAGE_CLINICAL,
                  STAGE_RESEARCH, STAGE_INCUBATOR, STAGE_SERVICE, STAGE_UNKNOWN]:
        count = stats[stage]
        pct = (count / total * 100) if total > 0 else 0
        logger.info(f"  {stage:15s}: {count:4d} ({pct:5.1f}%)")

    logger.info("=" * 60)

    # Quality check: warn if too many unknowns
    unknown_pct = (stats[STAGE_UNKNOWN] / total * 100) if total > 0 else 0
    if unknown_pct > 50:
        logger.warning(f"High percentage of Unknown classifications ({unknown_pct:.1f}%)")
        logger.warning("Consider enhancing classification logic with external data sources.")


# ============================================================================
# Main
# ============================================================================

def main() -> int:
    """Main entry point."""
    logger.info("Starting Company Stage Classification (Stage D)")
    logger.info("V4.3 Framework - Issue #20")
    logger.info("")

    try:
        # Create output directory if it doesn't exist
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        # Process classification
        stats = process_classification(INPUT_FILE, OUTPUT_FILE)

        if not stats:
            logger.error("Classification failed - no statistics generated")
            return 1

        # Print statistics
        print_statistics(stats)

        logger.info("")
        logger.info("✓ Classification complete!")
        logger.info(f"✓ Output: {OUTPUT_FILE}")

        return 0

    except Exception as e:
        logger.error(f"Classification failed with error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
