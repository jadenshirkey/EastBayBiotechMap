# Bay Area Biotech Map

An interactive map of biotechnology companies across the San Francisco Bay Area, created to help job seekers, researchers, and entrepreneurs explore the thriving biotech ecosystem.

## 🗺️ View the Map

**[🌐 Explore Full-Screen Map](https://jadenshirkey.github.io/EastBayBiotechMap/)** | **[📍 Open in Google My Maps](https://www.google.com/maps/d/u/0/edit?mid=1ywFxIIbkxvmyBVD2unuQ-1DCAR8eKi8&usp=sharing)**

> Full-screen interactive experience with embedded map, or open directly in Google My Maps for editing and sharing.

## About

This project maps **biotechnology companies** across the entire San Francisco Bay Area (9-county region), including:
- **East Bay**: Emeryville, Berkeley, Oakland, Alameda, Fremont, Pleasanton
- **Peninsula**: South San Francisco, Redwood City, Menlo Park, San Mateo
- **San Francisco**: SF proper
- **South Bay**: Palo Alto, Mountain View, Sunnyvale, San Jose
- **North Bay**: San Rafael, Novato, Marin County

Companies range from early-stage startups to commercial-stage biotech firms, spanning diverse areas including:
- Protein engineering and structural biology
- Gene editing (CRISPR) and gene therapy
- Cell therapy and immunotherapy
- Antibody discovery and development
- Synthetic biology and bioprocessing
- Diagnostics and research tools
- Computational biology and AI-driven drug discovery

### Features (V4.3 Framework)

- **Two-Path Enrichment**: BPG-first approach with intelligent fallback to AI validation
- **Comprehensive Quality Gates**: 6 automated validators ensuring data integrity
- **Confidence Scoring**: Tiered system (1-4) with deterministic scoring for Path A
- **Manual Review Process**: Spot-checks for high-confidence entries, full review for flagged items
- **Staging → Promotion Flow**: All processing happens in working/ directory; final/ only written after QC passes

## Data

The map includes information on:
- **Company locations** with verified addresses
- **Company websites** for direct access
- **Company stage** (Public, Private, Clinical, Research, etc.)
- **Focus areas** - factual technology platform descriptions

### Data File

The production dataset is available as **[`data/final/companies.csv`](data/final/companies.csv)**, containing:
- **Company Name**
- **Website**
- **City**
- **Address** (full street address)
- **Company_Stage** (Public, Private, Acquired, Clinical, Research, Incubator, Service, Unknown)
- **Focus_Areas** (technology platform and therapeutic focus)

### Data Quality (V4.3)

The V4.3 framework includes comprehensive quality gates to ensure data integrity:

**Quality Gates (All Must Pass)**
- ✓ All URLs validated (HTTPS or blank)
- ✓ All locations within Bay Area geofence (9-county + city whitelist)
- ✓ Zero duplicate domains (excluding allowlist)
- ✓ Zero aggregator domains (LinkedIn, Crunchbase, etc.)
- ✓ All companies with addresses have Place IDs
- ✓ Zero out-of-scope locations (Davis, Sacramento, etc.)

**Confidence Tiers**
- **Tier 1 (≥0.95)**: BPG + Google confirm same domain - Target: ≥70%
- **Tier 2 (0.90-0.95)**: BPG ground truth, Google mismatch - Target: ≥10%
- **Tier 3 (0.75-0.90)**: AI validated (Path B enrichment) - Target: ≤10%
- **Tier 4 (<0.75)**: Flagged for manual review - Target: 0%

**Manual Review Process**
- 10 random spot-checks from Tier 1/2 companies
- All Tier 4 companies manually reviewed before promotion
- Address verification against company websites

**Data Dictionary**: See [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) for complete column definitions.

## Use Cases

This map is designed for:
- **Job seekers** in biotechnology, particularly those with expertise in protein engineering, structural biology, and computational biology
- **Researchers** looking to understand the East Bay biotech landscape
- **Business developers** seeking partnership opportunities
- **Investors** exploring the regional biotech ecosystem
- **Students** considering career paths in biotechnology

## How It Was Created

<<<<<<< HEAD
This map is built using the **V4.3 automated pipeline** with systematic data flow from extraction through validation:

**Pipeline Overview (Stages A → F)**

1. **Stage A - Extraction**: BioPharmGuy CA-wide scraping with Website field capture
2. **Stage B - Merge & Geofence**: eTLD+1 deduplication, late geofencing, aggregator filtering
3. **Stage C - Enrichment**:
   - **Path A** (Python + Google Maps): For companies with BPG Website - deterministic validation
   - **Path B** (Anthropic structured outputs): For companies without Website - AI validation
4. **Stage D - Classification**: Company stage using methodology decision tree
5. **Stage E - Focus Extraction**: Factual focus areas from company websites (≤200 chars)
6. **Stage F - QC & Promotion**:
   - Automated validators (6 gates)
   - Manual review queues (spot-checks + Tier 4)
   - Promotion to final/ (only after all checks pass)

**See [METHODOLOGY.md](METHODOLOGY.md) for detailed methodology.**
**See [docs/V4.3_WORK_PLAN.md](docs/V4.3_WORK_PLAN.md) for complete implementation plan.**
=======
This dataset is built using an automated Python pipeline that processes over 1,300 companies:

1. **Discovery**: Extracts companies from BioPharmGuy's industry directory and Wikipedia categories (~1,300 raw entries)
2. **Deduplication**: Merges sources using normalized company names and domain matching to eliminate duplicates
3. **Enrichment**: Retrieves addresses and websites via Google Maps Places API using a two-tier search strategy
4. **Classification**: Categorizes companies into 8 development stages (Pre-clinical to Commercial) using keyword analysis
5. **Validation**: Applies geographic boundaries (9-county Bay Area) and multi-layer quality checks

The pipeline achieves **95% data completeness** with addresses verified for all companies.

**Learn More:**
- **Full Methodology**: See [METHODOLOGY.md](METHODOLOGY.md) for complete pipeline architecture and data collection procedures
- **Run It Yourself**: See [scripts/README.md](scripts/README.md) for installation and usage instructions
- **Quality Assurance**: Validated against 80+ Bay Area cities with duplicate detection and URL verification
>>>>>>> b3ce82c (Document automated pipeline architecture and fix script paths)

## Data Currency

- **Version**: v4.3
- **Framework**: V4.3 (Staging → Promotion with QC gates)
- **Last Updated**: See `data/final/last_updated.txt`
- **Coverage**: 9-county Bay Area (Alameda, Contra Costa, Marin, Napa, San Francisco, San Mateo, Santa Clara, Solano, Sonoma)
- **Quality**: All companies pass 6 automated validators + manual review

All company information is from publicly available sources: BioPharmGuy, Wikipedia, Google Maps API, company websites.

### API Costs

The V4.3 pipeline uses commercial APIs with cost monitoring:

- **Google Maps API** (Path A enrichment): ~$0.049/company baseline
  - Text Search: $0.032 per call
  - Place Details: $0.017 per call
  - Includes caching to reduce redundant calls

- **Anthropic Claude** (Path B enrichment): Measured empirically via token usage
  - Model: Claude Sonnet 4.5
  - Temperature: 0 (deterministic)
  - Structured outputs with tool use (Google Places API integration)

Cost reports generated in `data/working/api_usage_report.txt` and `data/working/anthropic_usage_report.txt`.

## Repository Structure

```
BayAreaBiotechMap/
├── data/
│   ├── final/companies.csv          # Production dataset (use this!)
│   └── working/companies_merged.csv # Working version
├── scripts/                         # Python data processing scripts
├── docs/
│   ├── MAP_SETUP.md                # How to create/update Google My Maps
│   ├── DATA_DICTIONARY.md          # Column definitions
│   ├── WORKFLOW.md                 # Data collection procedures
│   └── EXPANSION_STRATEGY.md       # Future growth plans
├── index.html                       # GitHub Pages site (full-screen map)
├── PROJECT_PLAN.md                 # Overall project roadmap
└── README.md                       # This file
```

## Contributing

We welcome contributions! If you notice:
- **Outdated information** (company moved, closed, acquired)
- **Missing companies** (biotech companies we don't have)
- **Address errors** or broken links
- **Other corrections** or suggestions

**Please open an issue** with details, or submit a pull request with the updated data.

## Map Display Legend

Companies are color-coded by development stage in Google My Maps:
- 🔴 **Red**: Clinical-Stage Biotech
- 🟠 **Orange**: Pre-clinical/Startup
- 🟢 **Green**: Commercial-Stage Biotech
- 🔵 **Blue**: Tools/Services/CDMO
- ⚪ **Gray**: Academic/Government Labs

## Quick Start: Create Your Own Map

Want to create an interactive map from this data?

1. **Download the data**: [`data/final/companies.csv`](data/final/companies.csv)
2. **Follow the guide**: [`docs/MAP_SETUP.md`](docs/MAP_SETUP.md)
3. **Import to Google My Maps** (5 minutes)
4. **Share your map!**

## Future Plans

This is v1.0 - a solid foundation. Future enhancements:
- **Phase 2**: Add careers page URLs to help job seekers apply directly
- **Phase 3**: Expand to 250-300 companies (see [EXPANSION_STRATEGY.md](docs/EXPANSION_STRATEGY.md))
- **Phase 4**: Custom interactive web map with advanced filtering

See [METHODOLOGY.md](METHODOLOGY.md) for the full roadmap.

## Acknowledgments

Data compiled as part of a biotech job search project in the San Francisco Bay Area. Created to help others navigate the regional biotech ecosystem.

## License

MIT License - see [LICENSE](LICENSE) file.

Data in this repository is provided for informational purposes. All company information is from publicly available sources.

---

**Version**: v3.0
**Last Updated**: January 8, 2025
**Maintainer**: Jaden Shirkey
**Contributions welcome!** 🧬
