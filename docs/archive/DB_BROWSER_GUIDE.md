# DB Browser for SQLite - Visualization Guide

## Quick Start

1. **Open Database**: File → Open Database → Navigate to `data/bayarea_biotech_sources.db`
2. **Execute SQL Tab**: This is where you'll spend most of your time
3. **Copy queries from `db_browser_queries.sql` and paste them here**

## DB Browser Visualization Features

### 1. Built-in Plotting (DB Browser 3.12+)
After running a query in the Execute SQL tab:
- Click the **"Plot"** button in the results panel
- Choose chart type (Line, Bar, Scatter, etc.)
- Select X and Y axes from your query columns
- The plot appears in a new tab

### 2. Export for External Visualization
From any query result:
- **Export to CSV**: Right-click results → Export as CSV
- **Copy to Clipboard**: Select all (Ctrl+A) → Copy (Ctrl+C)
- Paste into Excel, Google Sheets, or Tableau

### 3. Formatting Tips for Better Readability

#### Use ORDER BY for sorted results:
```sql
SELECT * FROM companies
ORDER BY company_name;  -- Alphabetical
ORDER BY updated_at DESC;  -- Most recent first
```

#### Use LIMIT for manageable result sets:
```sql
SELECT * FROM clinical_trials
LIMIT 100;  -- Show only first 100 rows
```

#### Format numbers nicely:
```sql
SELECT
    company_name,
    PRINTF('$%.2f', revenue) as formatted_revenue,
    PRINTF('%,d', employee_count) as employees
FROM companies;
```

## Top 5 Queries for Quick Insights

### 1. Company Dashboard View
```sql
-- Complete company profile with all enrichment data
SELECT
    c.company_name,
    c.website,
    c.city,
    cc.company_stage,
    COUNT(DISTINCT ct.trial_id) as trials,
    s.ticker,
    GROUP_CONCAT(DISTINCT cf.focus_area) as focus_areas
FROM companies c
LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
LEFT JOIN clinical_trials ct ON c.company_id = ct.company_id
LEFT JOIN sec_edgar_data s ON c.company_id = s.company_id
LEFT JOIN company_focus_areas cf ON c.company_id = cf.company_id
GROUP BY c.company_id
ORDER BY c.company_name;
```

### 2. Geographic Heatmap Data
```sql
-- For creating geographic visualizations
SELECT
    city,
    latitude,
    longitude,
    COUNT(*) as company_density,
    AVG(confidence_score) as avg_confidence
FROM companies
WHERE latitude IS NOT NULL
GROUP BY city, latitude, longitude
ORDER BY company_density DESC;
```

### 3. Investment Potential Ranking
```sql
-- Companies ranked by activity and growth indicators
SELECT
    c.company_name,
    cc.company_stage,
    COUNT(DISTINCT ct.trial_id) as active_trials,
    MAX(ct.enrollment) as max_enrollment,
    s.filing_count,
    CASE
        WHEN cc.company_stage = 'Clinical Stage' AND COUNT(DISTINCT ct.trial_id) > 3 THEN 'High'
        WHEN cc.company_stage = 'Private with SEC Filings' THEN 'Medium'
        ELSE 'Standard'
    END as investment_interest
FROM companies c
JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
LEFT JOIN clinical_trials ct ON c.company_id = ct.company_id AND ct.trial_status LIKE '%ACTIVE%'
LEFT JOIN sec_edgar_data s ON c.company_id = s.company_id
GROUP BY c.company_id
HAVING active_trials > 0 OR s.filing_count > 0
ORDER BY active_trials DESC, s.filing_count DESC;
```

### 4. Timeline View
```sql
-- Activity timeline for trend analysis
SELECT
    DATE(enriched_at) as date,
    'Clinical Trial Added' as event_type,
    COUNT(*) as event_count
FROM clinical_trials
GROUP BY DATE(enriched_at)
UNION ALL
SELECT
    DATE(enriched_at) as date,
    'SEC Filing Added' as event_type,
    COUNT(*) as event_count
FROM sec_edgar_data
GROUP BY DATE(enriched_at)
ORDER BY date DESC;
```

### 5. Search Any Company
```sql
-- Quick company search (replace 'Genentech' with your search term)
SELECT
    c.*,
    cc.company_stage,
    COUNT(ct.trial_id) as trial_count,
    s.ticker
FROM companies c
LEFT JOIN company_classifications cc ON c.company_id = cc.company_id AND cc.is_current = 1
LEFT JOIN clinical_trials ct ON c.company_id = ct.company_id
LEFT JOIN sec_edgar_data s ON c.company_id = s.company_id
WHERE c.company_name LIKE '%Genentech%'
GROUP BY c.company_id;
```

## Advanced Tips

### Creating Views for Frequent Queries
In DB Browser:
1. Run your query
2. Menu: View → Create View
3. Name it (e.g., "company_summary")
4. Now you can query it simply: `SELECT * FROM company_summary`

### Using Filters in Browse Data Tab
1. Go to Browse Data tab
2. Click filter icon next to any column
3. Use operators: =, !=, >, <, LIKE, etc.
4. Example: In company_stage column, filter = 'Public'

### Keyboard Shortcuts
- **F5**: Execute selected SQL
- **Ctrl+R**: Execute all SQL
- **Ctrl+T**: New tab
- **Ctrl+Shift+C**: Copy with headers

## Export Options

1. **File → Export → Database to SQL**: Create backup
2. **File → Export → Table as CSV**: Export specific table
3. **Right-click query results → Export**: Export query results
4. **File → Export → Database to JSON**: For web applications

## Color Coding for Better Visualization

When viewing results, you can:
- Click column headers to sort
- Drag column borders to resize
- Right-click for export options
- Use Ctrl+F to search within results

## Troubleshooting

- **Query too slow?** Add indexes: Structure tab → Create Index
- **Too many results?** Always use LIMIT clause
- **Can't see all columns?** Scroll right or resize window
- **Need to undo changes?** File → Revert Changes

## Next Steps

1. Try the queries in `db_browser_queries.sql`
2. Modify them for your specific needs
3. Create views for frequently used queries
4. Export interesting results for presentation