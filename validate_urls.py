#!/usr/bin/env python3
import re
from urllib.parse import urlparse
from datetime import datetime

# Read the CSV file and parse it more robustly
csv_file = '/home/user/EastBayBiotechMap/data/final/companies.csv'
companies = []

with open(csv_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

    # Skip header
    header = lines[0].strip()

    i = 1
    while i < len(lines):
        line = lines[i].rstrip('\r\n')

        # Skip empty lines and multiline continuations
        if not line.strip() or (line and not line[0].isalpha()):
            i += 1
            continue

        # Parse the line - try to extract company name and website
        # Format: Company Name,Website URL,City,Address,...

        # Look for https:// or http:// to find the website
        url_match = re.search(r'(https?://[^,]+)', line)
        if url_match:
            url = url_match.group(1).strip('"').strip()
            # Extract company name - everything before the first URL
            before_url = line[:url_match.start()].rstrip(',').strip()
            # Company name is the first part
            if before_url:
                company_name = before_url
                # If there are leading commas, the company name might have been split
                # Try to reconstruct it
                if company_name.endswith(',Inc') or company_name.endswith(',LLC'):
                    company_name = company_name + '.'

                companies.append({
                    'name': company_name,
                    'website': url
                })

        i += 1

print(f"Total companies with websites: {len(companies)}")
print()

# Analyze URL formats
format_issues = []
valid_https = []
valid_http = []
other_issues = []

for company in companies:
    url = company['website']

    # Check protocol
    if url.startswith('https://'):
        valid_https.append(company)
    elif url.startswith('http://'):
        valid_http.append(company)
    else:
        format_issues.append({
            'company': company['name'],
            'url': url,
            'issue': 'Missing http:// or https://'
        })
        continue

    # Validate URL structure
    try:
        parsed = urlparse(url)
        if not parsed.netloc or len(parsed.netloc) == 0:
            other_issues.append({
                'company': company['name'],
                'url': url,
                'issue': 'No domain found'
            })
        elif not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', parsed.netloc):
            other_issues.append({
                'company': company['name'],
                'url': url,
                'issue': f'Invalid domain format: {parsed.netloc}'
            })
    except Exception as e:
        other_issues.append({
            'company': company['name'],
            'url': url,
            'issue': f'Parse error: {str(e)}'
        })

print(f"URL Protocol Analysis:")
print(f"  - HTTPS URLs: {len(valid_https)}")
print(f"  - HTTP URLs: {len(valid_http)}")
print(f"  - Missing protocol: {len(format_issues)}")
print(f"  - Other format issues: {len(other_issues)}")
print()

# Check for duplicate or suspicious domains
domain_count = {}
for company in valid_https + valid_http:
    try:
        parsed = urlparse(company['website'])
        domain = parsed.netloc.lower().replace('www.', '')
        if domain not in domain_count:
            domain_count[domain] = []
        domain_count[domain].append(company['name'])
    except:
        pass

suspicious_domains = {d: c for d, c in domain_count.items() if len(c) > 1}
print(f"Domains used by multiple companies: {len(suspicious_domains)}")
if suspicious_domains:
    for domain, companies_list in sorted(suspicious_domains.items())[:5]:
        print(f"  - {domain}: {', '.join(companies_list)}")
    if len(suspicious_domains) > 5:
        print(f"  ... and {len(suspicious_domains) - 5} more")
print()

# Generate comprehensive report
report_lines = []
report_lines.append("# Website URL Validation Report")
report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
report_lines.append("")

report_lines.append("## Summary")
report_lines.append(f"- **Total companies in dataset:** {len(companies)}")
report_lines.append(f"- **HTTPS URLs:** {len(valid_https)} ({int(len(valid_https)/len(companies)*100)}%)")
report_lines.append(f"- **HTTP URLs:** {len(valid_http)} ({int(len(valid_http)/len(companies)*100)}%)")
report_lines.append(f"- **URLs with format issues:** {len(format_issues) + len(other_issues)}")
report_lines.append("")

report_lines.append("## URL Format Analysis")
report_lines.append("")

report_lines.append("### Protocol Usage")
report_lines.append(f"- **HTTPS (secure):** {len(valid_https)} URLs - Best practice ✓")
report_lines.append(f"- **HTTP (insecure):** {len(valid_http)} URLs - Consider upgrading to HTTPS")
report_lines.append("")

if format_issues:
    report_lines.append("### URLs with Missing Protocol")
    report_lines.append(f"**Count:** {len(format_issues)}")
    report_lines.append("")
    for issue in format_issues:
        report_lines.append(f"- **{issue['company']}**: `{issue['url']}`")
    report_lines.append("")

if other_issues:
    report_lines.append("### URLs with Other Format Issues")
    report_lines.append(f"**Count:** {len(other_issues)}")
    report_lines.append("")
    for issue in other_issues:
        report_lines.append(f"- **{issue['company']}**: `{issue['url']}`")
        report_lines.append(f"  - Issue: {issue['issue']}")
    report_lines.append("")

if suspicious_domains:
    report_lines.append("### Potentially Problematic URLs")
    report_lines.append(f"**Shared domains (possibly acquired or using corporate domain):** {len(suspicious_domains)}")
    report_lines.append("")
    report_lines.append("These companies share the same domain - they may have been acquired or are using a parent company domain:")
    report_lines.append("")
    for domain in sorted(suspicious_domains.keys()):
        companies_list = suspicious_domains[domain]
        report_lines.append(f"- **{domain}**: {', '.join(companies_list)}")
    report_lines.append("")

report_lines.append("## Sample URL Format Inspection")
report_lines.append("")
report_lines.append("### Valid URLs - Sample (First 10)")
for company in (valid_https + valid_http)[:10]:
    try:
        parsed = urlparse(company['website'])
        report_lines.append(f"- {company['name']}: `{parsed.netloc}`")
    except:
        pass
report_lines.append("")

report_lines.append("## Detailed Issues List")
report_lines.append("")

all_issues = format_issues + other_issues

if all_issues:
    report_lines.append(f"### All Issues Found: {len(all_issues)} URLs")
    report_lines.append("")

    for idx, issue in enumerate(all_issues, 1):
        report_lines.append(f"{idx}. **{issue['company']}**")
        report_lines.append(f"   - URL: `{issue['url']}`")
        report_lines.append(f"   - Issue: {issue['issue']}")
        report_lines.append("")
else:
    report_lines.append("✓ All URLs have valid format!")
    report_lines.append("")

report_lines.append("## Recommendations")
report_lines.append("")
report_lines.append("### High Priority")

if len(valid_http) > 0:
    report_lines.append(f"1. **Upgrade {len(valid_http)} HTTP URL(s) to HTTPS**")
    report_lines.append("   - HTTPS should be standard for all web URLs")
    for company in valid_http:
        old_url = company['website']
        new_url = old_url.replace('http://', 'https://')
        report_lines.append(f"   - {company['name']}: Change `{old_url}` → `{new_url}`")
    report_lines.append("")

if format_issues:
    report_lines.append(f"2. **Fix {len(format_issues)} URLs missing protocol prefix**")
    report_lines.append("   - Add `https://` (preferred) or `http://` to the following URLs:")
    for issue in format_issues:
        report_lines.append(f"   - {issue['company']}: {issue['url']}")
    report_lines.append("")

if other_issues:
    report_lines.append(f"3. **Review {len(other_issues)} URLs with format errors**")
    report_lines.append("   - These may be malformed or contain invalid characters")
    report_lines.append("   - Check source data for transcription errors")
    report_lines.append("")

report_lines.append("### Medium Priority")
if suspicious_domains:
    report_lines.append("4. **Verify shared domain URLs**")
    report_lines.append(f"   - {len(suspicious_domains)} domains are shared by multiple companies")
    report_lines.append("   - Verify if these are acquisitions, parent companies, or duplicate entries:")
    report_lines.append("")
    for domain in sorted(suspicious_domains.keys()):
        companies_list = suspicious_domains[domain]
        report_lines.append(f"     - {domain}: {', '.join(companies_list)}")
    report_lines.append("")

report_lines.append("### Ongoing Maintenance")
report_lines.append("5. **Implement periodic validation**")
report_lines.append("   - Quarterly validation of all URLs")
report_lines.append("   - Monitor for domain changes or company acquisitions")
report_lines.append("   - Consider automated URL checking system")
report_lines.append("   - Test with: `curl -I https://url.com` to verify each domain is live")
report_lines.append("")

report_lines.append("## Methodology Notes")
report_lines.append("")
report_lines.append("- **Format Validation:** Checked all URLs for correct HTTP/HTTPS protocol prefix and valid domain structure")
report_lines.append("- **Domain Reachability:** In this environment, actual network testing cannot be performed")
report_lines.append("- **Recommendation:** Run comprehensive network testing in production environment with tools like curl/wget")
report_lines.append("- **Duplicate Detection:** Identified domains used by multiple companies for potential data quality issues")
report_lines.append("")

# Write report
report_file = '/home/user/EastBayBiotechMap/validation_websites.md'
with open(report_file, 'w') as f:
    f.write('\n'.join(report_lines))

print(f"✓ Report saved to: {report_file}")
print(f"✓ Total issues found: {len(all_issues)}")
