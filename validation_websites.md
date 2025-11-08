# Website URL Validation Report
Generated: 2025-11-08 10:19:45

## Summary
- **Total companies in dataset:** 271
- **HTTPS URLs:** 270 (99%)
- **HTTP URLs:** 1 (0%)
- **URLs with format issues:** 0

## URL Format Analysis

### Protocol Usage
- **HTTPS (secure):** 270 URLs - Best practice ✓
- **HTTP (insecure):** 1 URLs - Consider upgrading to HTTPS

### Potentially Problematic URLs
**Shared domains (possibly acquired or using corporate domain):** 3

These companies share the same domain - they may have been acquired or are using a parent company domain:

- **acurex.com**: AcureX Biosciences, AcureX Therapeutics
- **ancorabiotech.com**: Ancora Biotech, Ancora Bio
- **atum.bio**: ATUM, ATUM (DNA2.0)

## Sample URL Format Inspection

### Valid URLs - Sample (First 10)
- ARMO BioSciences: `www.lilly.com`
- ATUM: `www.atum.bio`
- Abalone Bio: `www.abalonebio.com`
- AbbVie: `www.abbvie.com`
- Accelero Biostructures: `accelerobio.com`
- Acepodia: `www.acepodia.com`
- Acrigen Biosciences: `www.acrigen.com`
- Actym Therapeutics: `www.actym.com`
- AcureX Biosciences: `www.acurex.com`
- Adanate: `www.adanate.com`

## Detailed Issues List

✓ All URLs have valid format!

## Recommendations

### High Priority
1. **Upgrade 1 HTTP URL(s) to HTTPS**
   - HTTPS should be standard for all web URLs
   - Atreca: Change `http://atreca.com` → `https://atreca.com`

### Medium Priority
4. **Verify shared domain URLs**
   - 3 domains are shared by multiple companies
   - Verify if these are acquisitions, parent companies, or duplicate entries:

     - acurex.com: AcureX Biosciences, AcureX Therapeutics
     - ancorabiotech.com: Ancora Biotech, Ancora Bio
     - atum.bio: ATUM, ATUM (DNA2.0)

### Ongoing Maintenance
5. **Implement periodic validation**
   - Quarterly validation of all URLs
   - Monitor for domain changes or company acquisitions
   - Consider automated URL checking system
   - Test with: `curl -I https://url.com` to verify each domain is live

## Methodology Notes

- **Format Validation:** Checked all URLs for correct HTTP/HTTPS protocol prefix and valid domain structure
- **Domain Reachability:** In this environment, actual network testing cannot be performed
- **Recommendation:** Run comprehensive network testing in production environment with tools like curl/wget
- **Duplicate Detection:** Identified domains used by multiple companies for potential data quality issues
