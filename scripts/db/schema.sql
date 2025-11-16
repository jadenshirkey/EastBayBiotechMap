-- East Bay Biotech Map Database Schema
-- Purpose: Structured storage for biotech company data with enrichment tracking
-- Database: SQLite 3.x

-- Drop existing tables if they exist (for clean migration)
DROP TABLE IF EXISTS api_calls;
DROP TABLE IF EXISTS data_quality_checks;
DROP TABLE IF EXISTS clinical_trials;
DROP TABLE IF EXISTS sec_edgar_data;
DROP TABLE IF EXISTS company_focus_areas;
DROP TABLE IF EXISTS company_classifications;
DROP TABLE IF EXISTS companies;

-- Core company table (replaces companies.csv)
CREATE TABLE companies (
    company_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_name TEXT NOT NULL,
    website TEXT,
    city TEXT,
    address TEXT,
    latitude REAL,
    longitude REAL,
    confidence_score REAL,
    validation_source TEXT,
    google_place_id TEXT,
    google_address TEXT,
    google_name TEXT,
    google_website TEXT,
    description TEXT,
    original_index INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Ensure unique company names
    UNIQUE(company_name)
);

-- Classification table (tracks company stage/type classifications)
CREATE TABLE company_classifications (
    classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    company_stage TEXT,
    classification_method TEXT, -- 'manual', 'keyword', 'sec_edgar', 'clinical_trials', 'ai'
    classification_confidence REAL,
    classification_source TEXT, -- Source identifier (e.g., 'SEC EDGAR', 'ClinicalTrials.gov')
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
    extraction_method TEXT, -- 'bpg', 'website', 'clinical_trials', 'ai', 'manual'
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
    check_type TEXT, -- 'geofence', 'website_validation', 'duplicate_check', 'confidence_threshold'
    check_status TEXT, -- 'pass', 'fail', 'warning', 'manual_review'
    check_message TEXT,
    check_details TEXT, -- JSON for additional data
    checked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (company_id) REFERENCES companies(company_id)
);

-- Create indexes for optimal query performance
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

-- Create views for common queries
CREATE VIEW IF NOT EXISTS v_company_summary AS
SELECT
    c.company_id,
    c.company_name,
    c.website,
    c.city,
    c.confidence_score,
    cc.company_stage,
    cc.classification_confidence,
    GROUP_CONCAT(DISTINCT cfa.focus_area) as focus_areas,
    sed.ticker,
    sed.company_status as sec_status,
    COUNT(DISTINCT ct.nct_id) as trial_count,
    MAX(ct.phase) as highest_phase
FROM companies c
LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
LEFT JOIN company_focus_areas cfa ON c.company_id = cfa.company_id
LEFT JOIN sec_edgar_data sed ON c.company_id = sed.company_id
LEFT JOIN clinical_trials ct ON c.company_id = ct.company_id
GROUP BY c.company_id;

-- Create trigger to update the updated_at timestamp
CREATE TRIGGER update_companies_timestamp
AFTER UPDATE ON companies
BEGIN
    UPDATE companies SET updated_at = CURRENT_TIMESTAMP WHERE company_id = NEW.company_id;
END;