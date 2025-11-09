# Bay Area Biotech Map

An interactive map of biotechnology companies across the San Francisco Bay Area, created to help job seekers, researchers, and entrepreneurs explore the thriving biotech ecosystem.

## 🗺️ View the Map

**[🌐 Explore Full-Screen Map](https://jadenshirkey.github.io/EastBayBiotechMap/)** | **[📍 Open in Google My Maps](https://www.google.com/maps/d/u/0/edit?mid=1ywFxIIbkxvmyBVD2unuQ-1DCAR8eKi8&usp=sharing)**

> Full-screen interactive experience with embedded map, or open directly in Google My Maps for editing and sharing.

## About

This project maps **1,210 biotechnology companies** across the entire San Francisco Bay Area, including:
- **East Bay**: Emeryville, Berkeley, Oakland, Alameda, Fremont, Pleasanton
- **Peninsula**: South San Francisco, Redwood City, Menlo Park, San Mateo
- **San Francisco**: SF proper
- **South Bay**: Palo Alto, Mountain View, Sunnyvale, San Jose
- **North Bay**: San Rafael, Novato

Companies range from early-stage startups to commercial-stage biotech firms, spanning diverse areas including:
- Protein engineering and structural biology
- Gene editing (CRISPR) and gene therapy
- Cell therapy and immunotherapy
- Antibody discovery and development
- Synthetic biology and bioprocessing
- Diagnostics and research tools
- Computational biology and AI-driven drug discovery

## Data

The map includes information on:
- **Company locations** with verified addresses
- **Company websites** for direct access
- **Company stage** (startup, pre-clinical, clinical-stage, commercial)
- **Technology platform** descriptions and focus areas

### Data File

The production dataset is available as **[`data/final/companies.csv`](data/final/companies.csv)**, containing:
- **Company Name**
- **Website**
- **City**
- **Address** (full street address)
- **Company Stage** (Startup, Pre-clinical, Clinical, Commercial, Tools/Services, Academic/Gov't)
- **Notes** (technology platform and focus areas)

**Data Dictionary**: See [`docs/DATA_DICTIONARY.md`](docs/DATA_DICTIONARY.md) for complete column definitions.

## Use Cases

This map is designed for:
- **Job seekers** in biotechnology, particularly those with expertise in protein engineering, structural biology, and computational biology
- **Researchers** looking to understand the East Bay biotech landscape
- **Business developers** seeking partnership opportunities
- **Investors** exploring the regional biotech ecosystem
- **Students** considering career paths in biotechnology

## How It Was Created

This map was compiled through systematic research and data consolidation:
1. Multiple biotech company directories aggregated and deduplicated
2. Address verification for all 169 companies
3. Technology platform categorization from company websites
4. Quality checks and validation
5. Data organized using Python scripts (see [`scripts/`](scripts/))

**See [METHODOLOGY.md](METHODOLOGY.md) for detailed methodology and future plans.**

## Data Currency

- **Version**: v3.0
- **Last Updated**: January 8, 2025
- **Companies**: 1,210 across the Bay Area
- **Address completion**: 100% (all companies have verified addresses)

All company information is from publicly available sources: company websites, business registries, and press releases.

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
