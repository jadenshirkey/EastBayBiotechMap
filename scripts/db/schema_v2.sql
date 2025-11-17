-- East Bay Biotech Map Database Schema V2
-- Purpose: Structured storage for biotech company data with raw import tracking
-- Database: SQLite 3.x

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS api_calls;
DROP TABLE IF EXISTS data_quality_checks;
DROP TABLE IF EXISTS clinical_trials;
DROP TABLE IF EXISTS sec_edgar_data;
DROP TABLE IF EXISTS company_focus_areas;
DROP TABLE IF EXISTS company_classifications;
DROP TABLE IF EXISTS company_source_mapping;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS wikipedia_raw_imports;
DROP TABLE IF EXISTS biopharmguy_raw_imports;

-- ====================== RAW DATA IMPORT TABLES ======================

-- BioPharmGuy raw import data (preserves original BPG data)
CREATE TABLE biopharmguy_raw_imports (
    bpg_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    website TEXT,
    city TEXT,
    state TEXT,
    address TEXT,
    zip_code TEXT,
    county TEXT,
    phone TEXT,
    description TEXT,
    focus_areas TEXT,  -- Original comma-separated list
    employee_count TEXT,
    year_founded TEXT,
    company_type TEXT,  -- Original BPG classification
    source_url TEXT,
    import_batch TEXT,  -- Track different import runs
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data TEXT,  -- JSON dump of complete original row

    -- Index for matching
    UNIQUE(company_name, import_batch)
);

-- Wikipedia raw import data (preserves original Wikipedia data)
CREATE TABLE wikipedia_raw_imports (
    wiki_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    wikipedia_url TEXT,
    website TEXT,
    headquarters_location TEXT,
    founded_year TEXT,
    founder TEXT,
    industry TEXT,
    products TEXT,  -- Original products/services text
    revenue TEXT,
    employees TEXT,
    parent_company TEXT,
    subsidiaries TEXT,
    traded_as TEXT,  -- Stock exchange info
    isin TEXT,
    description_text TEXT,  -- First paragraph from Wikipedia
    infobox_data TEXT,  -- JSON of complete infobox data
    categories TEXT,  -- Wikipedia categories
    import_batch TEXT,  -- Track different import runs
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    raw_data TEXT,  -- JSON dump of complete original data

    -- Index for matching
    UNIQUE(company_name, import_batch)
);

-- ====================== CORE TABLES ======================

-- Core company table (merged/deduplicated data)
CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    website TEXT,
    city TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    confidence_score REAL,
    validation_source TEXT,  -- 'BPG', 'Wikipedia', 'Both', 'Google Maps', etc.
    google_place_id TEXT,
    google_address TEXT,
    google_name TEXT,
    google_website TEXT,
    description TEXT,
    original_index INTEGER,  -- From original CSV if applicable
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique company names
    UNIQUE(company_name)
);

-- Source mapping table (links companies to their raw import records)
CREATE TABLE company_source_mapping (
    mapping_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    source_type TEXT NOT NULL,  -- 'biopharmguy' or 'wikipedia'
    source_id INTEGER NOT NULL,  -- bpg_id or wiki_id
    match_confidence REAL,  -- Confidence in the match (0-1)
    match_method TEXT,  -- 'exact_name', 'fuzzy_name', 'website', 'manual'
    is_primary_source BOOLEAN DEFAULT 0,  -- Mark primary source for conflicts
    mapped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(company_id, source_type, source_id)
);

-- Classification table (tracks company stage/type classifications)
CREATE TABLE company_classifications (
    classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    company_stage TEXT,
    classification_method TEXT, -- 'manual', 'keyword', 'sec_edgar', 'clinical_trials', 'ai', 'bpg_import', 'wiki_import'
    classification_confidence REAL,
    classification_source TEXT, -- Source identifier (e.g., 'SEC EDGAR', 'ClinicalTrials.gov', 'BPG Type')
    classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    classifier_version TEXT,
    is_current BOOLEAN DEFAULT 1, -- Track current vs historical classifications
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Focus areas table (many-to-many: companies can have multiple focus areas)
CREATE TABLE company_focus_areas (
    focus_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    focus_area TEXT NOT NULL,
    extraction_method TEXT, -- 'bpg', 'wikipedia', 'website', 'clinical_trials', 'ai', 'manual'
    extraction_confidence REAL,
    extraction_source TEXT,
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- SEC EDGAR enrichment data
CREATE TABLE sec_edgar_data (
    edgar_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    cik TEXT,
    ticker TEXT,
    exchange TEXT,
    sic_code TEXT,
    company_name_edgar TEXT,
    filing_count INTEGER,
    latest_filing_date TEXT,
    latest_filing_type TEXT,
    company_status TEXT, -- 'public', 'formerly_public', 'subsidiary', 'acquired'
    match_confidence REAL, -- Confidence in the name/company match
    edgar_url TEXT,
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(cik)
);

-- ClinicalTrials.gov data
CREATE TABLE clinical_trials (
    trial_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    nct_id TEXT NOT NULL,
    trial_title TEXT,
    trial_status TEXT, -- 'Recruiting', 'Active, not recruiting', 'Completed', etc.
    phase TEXT, -- 'Phase 1', 'Phase 2', 'Phase 3', 'Phase 4', 'Early Phase 1'
    enrollment INTEGER,
    start_date TEXT,
    completion_date TEXT,
    conditions TEXT, -- JSON array of conditions
    interventions TEXT, -- JSON array of interventions
    locations TEXT, -- JSON array of trial locations
    sponsor_name TEXT, -- As listed in ClinicalTrials.gov
    match_confidence REAL, -- Confidence in the sponsor/company match
    clinicaltrials_url TEXT,
    enriched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id),
    UNIQUE(nct_id, company_id)
);

-- API call tracking (for cost management & debugging)
CREATE TABLE api_calls (
    call_id INTEGER PRIMARY KEY AUTOINCREMENT,
    api_provider TEXT NOT NULL, -- 'google_maps', 'sec_edgar', 'clinicaltrials', 'anthropic'
    endpoint TEXT,
    company_id INTEGER,
    request_params TEXT, -- JSON string
    response_status INTEGER,
    response_cached BOOLEAN DEFAULT 0,
    error_message TEXT,
    cost_estimate REAL, -- Estimated cost in USD
    rate_limit_remaining INTEGER,
    called_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Data quality & validation tracking
CREATE TABLE data_quality_checks (
    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    check_type TEXT, -- 'geofence', 'website_validation', 'duplicate_check', 'confidence_threshold', 'source_conflict'
    check_status TEXT, -- 'pass', 'fail', 'warning', 'manual_review'
    check_message TEXT,
    check_details TEXT, -- JSON for additional data
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- ====================== INDEXES ======================

-- Indexes for raw import tables
CREATE INDEX idx_bpg_company_name ON biopharmguy_raw_imports(company_name);
CREATE INDEX idx_bpg_city ON biopharmguy_raw_imports(city);
CREATE INDEX idx_bpg_import_batch ON biopharmguy_raw_imports(import_batch);

CREATE INDEX idx_wiki_company_name ON wikipedia_raw_imports(company_name);
CREATE INDEX idx_wiki_traded_as ON wikipedia_raw_imports(traded_as);
CREATE INDEX idx_wiki_import_batch ON wikipedia_raw_imports(import_batch);

-- Indexes for source mapping
CREATE INDEX idx_source_mapping_company ON company_source_mapping(company_id);
CREATE INDEX idx_source_mapping_source ON company_source_mapping(source_type, source_id);

-- Indexes for core tables (unchanged)
CREATE INDEX idx_companies_name ON companies(company_name);
CREATE INDEX idx_companies_website ON companies(website);
CREATE INDEX idx_companies_city ON companies(city);
CREATE INDEX idx_companies_confidence ON companies(confidence_score);

CREATE INDEX idx_classifications_company ON company_classifications(company_id);
CREATE INDEX idx_classifications_stage ON company_classifications(company_stage);
CREATE INDEX idx_classifications_current ON company_classifications(is_current);

CREATE INDEX idx_focus_company ON company_focus_areas(company_id);
CREATE INDEX idx_focus_area ON company_focus_areas(focus_area);

CREATE INDEX idx_sec_company ON sec_edgar_data(company_id);
CREATE INDEX idx_sec_cik ON sec_edgar_data(cik);
CREATE INDEX idx_sec_ticker ON sec_edgar_data(ticker);
CREATE INDEX idx_sec_status ON sec_edgar_data(company_status);

CREATE INDEX idx_trials_company ON clinical_trials(company_id);
CREATE INDEX idx_trials_nct ON clinical_trials(nct_id);
CREATE INDEX idx_trials_phase ON clinical_trials(phase);
CREATE INDEX idx_trials_status ON clinical_trials(trial_status);

CREATE INDEX idx_api_provider ON api_calls(api_provider);
CREATE INDEX idx_api_company ON api_calls(company_id);
CREATE INDEX idx_api_timestamp ON api_calls(called_at);

CREATE INDEX idx_quality_company ON data_quality_checks(company_id);
CREATE INDEX idx_quality_type ON data_quality_checks(check_type);
CREATE INDEX idx_quality_status ON data_quality_checks(check_status);

-- ====================== VIEWS ======================

-- View showing company with all sources
CREATE VIEW IF NOT EXISTS v_company_sources AS
SELECT
    c.company_id,
    c.company_name,
    c.website,
    c.validation_source,
    COUNT(CASE WHEN csm.source_type = 'biopharmguy' THEN 1 END) as bpg_sources,
    COUNT(CASE WHEN csm.source_type = 'wikipedia' THEN 1 END) as wiki_sources,
    MAX(CASE WHEN csm.source_type = 'biopharmguy' THEN csm.match_confidence END) as bpg_confidence,
    MAX(CASE WHEN csm.source_type = 'wikipedia' THEN csm.match_confidence END) as wiki_confidence
FROM companies c
LEFT JOIN company_source_mapping csm ON c.company_id = csm.company_id
GROUP BY c.company_id;

-- View showing enrichment status
CREATE VIEW IF NOT EXISTS v_enrichment_status AS
SELECT
    c.company_id,
    c.company_name,
    CASE WHEN sed.company_id IS NOT NULL THEN 1 ELSE 0 END as has_sec_data,
    CASE WHEN ct.company_id IS NOT NULL THEN 1 ELSE 0 END as has_trials_data,
    CASE WHEN cc.company_id IS NOT NULL THEN 1 ELSE 0 END as has_classification,
    CASE WHEN cfa.company_id IS NOT NULL THEN 1 ELSE 0 END as has_focus_areas
FROM companies c
LEFT JOIN sec_edgar_data sed ON c.company_id = sed.company_id
LEFT JOIN (SELECT DISTINCT company_id FROM clinical_trials) ct ON c.company_id = ct.company_id
LEFT JOIN (SELECT DISTINCT company_id FROM company_classifications WHERE is_current = 1) cc ON c.company_id = cc.company_id
LEFT JOIN (SELECT DISTINCT company_id FROM company_focus_areas) cfa ON c.company_id = cfa.company_id;

-- View for comprehensive company summary (updated)
CREATE VIEW IF NOT EXISTS v_company_summary AS
SELECT
    c.company_id,
    c.company_name,
    c.website,
    c.city,
    c.confidence_score,
    c.validation_source,
    cc.company_stage,
    cc.classification_confidence,
    GROUP_CONCAT(DISTINCT cfa.focus_area) as focus_areas,
    sed.ticker,
    sed.company_status as sec_status,
    COUNT(DISTINCT ct.nct_id) as trial_count,
    MAX(ct.phase) as highest_phase,
    vs.bpg_sources,
    vs.wiki_sources
FROM companies c
LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
LEFT JOIN company_focus_areas cfa ON c.company_id = cfa.company_id
LEFT JOIN sec_edgar_data sed ON c.company_id = sed.company_id
LEFT JOIN clinical_trials ct ON c.company_id = ct.company_id
LEFT JOIN v_company_sources vs ON c.company_id = vs.company_id
GROUP BY c.company_id;

-- ====================== TRIGGERS ======================

-- Trigger to update the updated_at timestamp
CREATE TRIGGER update_companies_timestamp
AFTER UPDATE ON companies
BEGIN
    UPDATE companies SET updated_at = CURRENT_TIMESTAMP WHERE company_id = NEW.company_id;
END;