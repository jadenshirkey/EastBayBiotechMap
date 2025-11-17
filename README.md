# California Biotech Map

An interactive map of biotechnology companies across California, with focus on the San Francisco Bay Area, created to help job seekers, researchers, and entrepreneurs explore the thriving biotech ecosystem.

## 🗺️ View the Map

**[🌐 Explore Full-Screen Map](https://jadenshirkey.github.io/EastBayBiotechMap/)** | **[📍 Open in Google My Maps](https://www.google.com/maps/d/u/0/edit?mid=1ywFxIIbkxvmyBVD2unuQ-1DCAR8eKi8&usp=sharing)**

> Full-screen interactive experience with embedded map, or open directly in Google My Maps for editing and sharing.

## About

This project maps **978 biotechnology companies** across California, with comprehensive coverage of major biotech hubs:
- **Bay Area**: San Francisco, South San Francisco, Emeryville, Berkeley, Oakland
- **San Diego**: La Jolla, Carlsbad, San Diego proper
- **Los Angeles**: Thousand Oaks, Irvine, LA proper
- **Peninsula**: Palo Alto, Mountain View, Sunnyvale, San Jose

Companies range from early-stage startups to commercial-stage biotech firms, spanning diverse areas including:
- Protein engineering and structural biology
- Gene editing (CRISPR) and gene therapy
- Cell therapy and immunotherapy
- Antibody discovery and development
- Synthetic biology and bioprocessing
- Diagnostics and research tools
- Computational biology and AI-driven drug discovery

### Features (V5 Framework - SQL Database Architecture)

- **SQL Database Backend**: Robust SQLite database replacing CSV files for data integrity and relationships
- **Multi-Source Enrichment**: Integration with SEC EDGAR and ClinicalTrials.gov APIs for comprehensive company intelligence
- **Advanced Classification**: Automated stage classification based on SEC filings, clinical trials, and public status
- **California Focus**: Intelligent filtering for California-based companies with address validation
- **Data Completeness**: Reduced "Unknown" classifications from 76% to 30% through enrichment pipeline

## Data

The map includes enriched information on:
- **Company locations** with Google-verified addresses and coordinates
- **Company websites** for direct access
- **Company stage** classification based on multiple data sources
- **Focus areas** - technology platforms and therapeutic areas
- **Clinical trials** count from ClinicalTrials.gov
- **SEC filings** count from EDGAR database

### Data Architecture

**Primary Database**: `data/bayarea_biotech_sources.db` (SQLite)
- Contains 2,491 total companies (nationwide)
- 978 California companies exported for mapping

**Export File**: [`data/final/companies.csv`](data/final/companies.csv)
- California-only subset optimized for Google My Maps
- Includes all required mapping fields

### Company Stage Distribution (California Export)
- **Private with SEC Filings**: 313 companies (32.0%)
- **Private**: 241 companies (24.6%)
- **Defunct**: 176 companies (18.0%)
- **Clinical Stage**: 134 companies (13.7%)
- **Public**: 114 companies (11.7%)

### Data Quality (V5)

The V5 framework ensures data integrity through:

**Multi-Source Validation**
- ✓ SEC EDGAR data for public/private status verification
- ✓ ClinicalTrials.gov for clinical stage validation
- ✓ Google Maps API for address verification
- ✓ Automated classification with safety flags

**Classification Logic**
- **Public**: Has valid ticker symbol on major exchange
- **Private with SEC Filings**: SEC filings but no ticker
- **Clinical Stage**: Active trials or completed within 2 years
- **Private**: No SEC filings or clinical trials
- **Defunct**: Explicitly marked as closed/inactive

**Data Enrichment Results**
- Successfully enriched 99% of companies
- Reduced "Unknown" classifications from 76% to 30%
- All California companies have verified addresses
- Clinical trials data for 1,080 companies
- SEC filings data for 600+ companies

## Use Cases

This map is designed for:
- **Job seekers** in biotechnology, particularly those with expertise in protein engineering, structural biology, and computational biology
- **Researchers** looking to understand the East Bay biotech landscape
- **Business developers** seeking partnership opportunities
- **Investors** exploring the regional biotech ecosystem
- **Students** considering career paths in biotechnology

## How It Was Created

This dataset is built using an automated Python pipeline with SQL database backend:

1. **Discovery**: Extracts companies from BioPharmGuy's directory and Wikipedia categories (2,491 raw entries)
2. **Database Import**: Stores in SQLite with proper relationships and data integrity
3. **Multi-Source Enrichment**:
   - Google Maps API for addresses and coordinates
   - SEC EDGAR API for public/private status and filing counts
   - ClinicalTrials.gov API for clinical trial data
4. **Intelligent Classification**: Rules-based categorization using enrichment data
5. **California Export**: Filters and exports 978 California companies for mapping

The pipeline achieves **99% enrichment success** with multiple data sources validated.

**Learn More:**
- **Full Methodology**: See [METHODOLOGY.md](METHODOLOGY.md) for complete pipeline architecture and data collection procedures
- **Run It Yourself**: See [scripts/README.md](scripts/README.md) for installation and usage instructions
- **Quality Assurance**: Validated against 80+ Bay Area cities with duplicate detection and URL verification

## Data Currency

- **Version**: v5.0 (SQL Database Architecture)
- **Framework**: V5 (SQL database with multi-source enrichment)
- **Last Updated**: November 16, 2025
- **Coverage**: California statewide (978 companies exported)
- **Database**: 2,491 companies nationwide in SQL database
- **Quality**: Multi-source validation with SEC and ClinicalTrials data

All company information is from publicly available sources: BioPharmGuy, Wikipedia, Google Maps API, SEC EDGAR, ClinicalTrials.gov.

### API Usage

The V5 pipeline uses multiple APIs with safety controls:

- **Google Maps API**: Address and coordinate enrichment
  - Cached to prevent redundant calls
  - WARNING: Can be expensive at scale (~$220 for full dataset)
  - Use --limit flag for testing

- **SEC EDGAR API**: Public company and filing data
  - Free API with rate limiting
  - Cached responses for efficiency

- **ClinicalTrials.gov API**: Clinical trial data
  - Free API with rate limiting
  - Cached for performance

All scripts include safety flags (--dry-run, --limit, --test-db) to prevent costly operations.

## Repository Structure

```
CaliforniaBiotechMap/
├── data/
│   ├── bayarea_biotech_sources.db   # Main SQL database (2,491 companies)
│   ├── final/
│   │   └── companies.csv            # California export for Google My Maps (978 companies)
│   ├── working/                     # Working directory for processing
│   └── backups/                     # Database backups with timestamps
├── scripts/
│   ├── db/                          # Database management scripts
│   │   ├── db_manager.py           # Database operations
│   │   └── migrate_with_sources.py  # Data import/migration
│   ├── enrichment/                  # API enrichment clients
│   │   ├── sec_edgar_client.py     # SEC EDGAR integration
│   │   └── clinicaltrials_client.py # ClinicalTrials.gov integration
│   ├── classify_company_stage_improved.py  # Classification with safety flags
│   ├── export_california_companies.py      # California-only export
│   └── parallel_enrichment.py              # Multi-threaded enrichment
├── config/
│   └── secure_config.py            # Configuration management
├── tests/                           # Test suites
├── index.html                       # GitHub Pages site
├── GOOGLE_MAPS_IMPORT_NOTES.md     # Import instructions
├── CLINICAL_STAGE_DEFINITION.md    # Clinical stage logic documentation
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

**Version**: v5.0
**Last Updated**: November 16, 2025
**Maintainer**: Jaden Shirkey
**Database**: SQLite with 2,491 companies
**Export**: 978 California companies
**Contributions welcome!** 🧬
