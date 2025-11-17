-- Create test subset database with 50 diverse companies
-- This script creates a smaller database for testing without risking API costs

ATTACH DATABASE 'data/bayarea_biotech_sources.db' AS prod;

-- Create all necessary tables with same structure
CREATE TABLE companies AS SELECT * FROM prod.companies WHERE 1=0;
CREATE TABLE company_classifications AS SELECT * FROM prod.company_classifications WHERE 1=0;
CREATE TABLE sec_edgar_data AS SELECT * FROM prod.sec_edgar_data WHERE 1=0;
CREATE TABLE clinical_trials AS SELECT * FROM prod.clinical_trials WHERE 1=0;
CREATE TABLE company_focus_areas AS SELECT * FROM prod.company_focus_areas WHERE 1=0;
CREATE TABLE company_source_mapping AS SELECT * FROM prod.company_source_mapping WHERE 1=0;
CREATE TABLE biopharmguy_raw_imports AS SELECT * FROM prod.biopharmguy_raw_imports WHERE 1=0;
CREATE TABLE wikipedia_raw_imports AS SELECT * FROM prod.wikipedia_raw_imports WHERE 1=0;
CREATE TABLE api_calls AS SELECT * FROM prod.api_calls WHERE 1=0;
CREATE TABLE data_quality_checks AS SELECT * FROM prod.data_quality_checks WHERE 1=0;

-- Create a temporary view for easier selection
CREATE TEMP VIEW classified_companies AS
SELECT c.company_id, c.company_name, cc.company_stage
FROM prod.companies c
JOIN prod.company_classifications cc ON c.company_id = cc.company_id
WHERE cc.is_current = 1;

-- Insert 10 Public companies (with tickers)
INSERT INTO companies
SELECT * FROM prod.companies
WHERE company_id IN (
    SELECT c.company_id
    FROM classified_companies c
    JOIN prod.sec_edgar_data s ON c.company_id = s.company_id
    WHERE c.company_stage = 'Public'
    AND s.ticker IS NOT NULL
    LIMIT 10
);

-- Insert 10 Private with SEC Filings (no tickers)
INSERT OR IGNORE INTO companies
SELECT * FROM prod.companies
WHERE company_id IN (
    SELECT c.company_id
    FROM classified_companies c
    WHERE c.company_stage = 'Private with SEC Filings'
    LIMIT 10
);

-- Insert 10 Clinical Stage companies
INSERT OR IGNORE INTO companies
SELECT * FROM prod.companies
WHERE company_id IN (
    SELECT c.company_id
    FROM classified_companies c
    WHERE c.company_stage = 'Clinical Stage'
    LIMIT 10
);

-- Insert 10 Private companies
INSERT OR IGNORE INTO companies
SELECT * FROM prod.companies
WHERE company_id IN (
    SELECT c.company_id
    FROM classified_companies c
    WHERE c.company_stage = 'Private'
    LIMIT 10
);

-- Insert 5 Defunct companies
INSERT OR IGNORE INTO companies
SELECT * FROM prod.companies
WHERE company_id IN (
    SELECT c.company_id
    FROM classified_companies c
    WHERE c.company_stage = 'Defunct'
    LIMIT 5
);

-- Insert 5 Unknown companies
INSERT OR IGNORE INTO companies
SELECT * FROM prod.companies
WHERE company_id IN (
    SELECT c.company_id
    FROM classified_companies c
    WHERE c.company_stage = 'Unknown'
    LIMIT 5
);

-- Now copy related data for these companies
INSERT INTO company_classifications
SELECT * FROM prod.company_classifications
WHERE company_id IN (SELECT company_id FROM companies);

INSERT INTO sec_edgar_data
SELECT * FROM prod.sec_edgar_data
WHERE company_id IN (SELECT company_id FROM companies);

INSERT INTO clinical_trials
SELECT * FROM prod.clinical_trials
WHERE company_id IN (SELECT company_id FROM companies);

INSERT INTO company_focus_areas
SELECT * FROM prod.company_focus_areas
WHERE company_id IN (SELECT company_id FROM companies);

INSERT INTO company_source_mapping
SELECT * FROM prod.company_source_mapping
WHERE company_id IN (SELECT company_id FROM companies);

-- Verify the subset
SELECT 'Test subset created with:' as message;
SELECT company_stage, COUNT(*) as count
FROM companies c
JOIN company_classifications cc ON c.company_id = cc.company_id
WHERE cc.is_current = 1
GROUP BY company_stage
ORDER BY count DESC;

DETACH DATABASE prod;