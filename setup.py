#!/usr/bin/env python3
"""Setup script for East Bay Biotech Map project."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="eastbay-biotech-map",
    version="5.0.0",
    author="East Bay Biotech Map Team",
    description="A comprehensive biotech company database enrichment system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/EastBayBiotechMap",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Bio-Informatics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "requests>=2.25.0",
        "googlemaps>=4.10.0",
        "beautifulsoup4>=4.9.0",
        "pandas>=1.2.0",
        "python-dotenv>=0.19.0",
        "tenacity>=8.0.0",  # For retry logic
        "validators>=0.18.0",  # For input validation
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",
            "pytest-cov>=2.0",
            "black>=21.0",
            "flake8>=3.9.0",
            "mypy>=0.900",
        ]
    },
    entry_points={
        "console_scripts": [
            "biotech-classify=scripts.classify_company_stage_improved:main",
            "biotech-enrich=scripts.enrichment.run_exhaustive_enrichment:main",
            "biotech-fix-sec=scripts.fix_sec_classification:main",
            "biotech-fix-trials=scripts.fix_clinical_trials_classification:main",
        ],
    },
)