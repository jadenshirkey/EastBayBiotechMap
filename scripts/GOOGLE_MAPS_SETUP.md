# Google Maps API Setup Guide

This guide walks you through setting up the Google Maps Places API for company data enrichment.

## Why Google Maps API?

The Places API provides:
- ✅ **Verified business addresses** (formatted with ZIP codes)
- ✅ **Website URLs** (if business claimed their listing)
- ✅ **Geocoded coordinates** (ready for map visualization)
- ✅ **90%+ coverage** for established biotech companies
- ✅ **Fast**: Processes 899 companies in ~10-15 minutes
- ✅ **Free tier**: $200/month credit covers ~40,000 searches

## Setup Steps (10 minutes)

### Step 1: Create Google Cloud Account

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Accept the terms of service
4. **You get $300 free credit** for the first 90 days (new accounts)

### Step 2: Create a New Project

1. Click the project dropdown (top left)
2. Click "New Project"
3. Name it: `EastBayBiotechMap`
4. Click "Create"

### Step 3: Enable Places API

1. Go to [APIs & Services > Library](https://console.cloud.google.com/apis/library)
2. Search for: `Places API`
3. Click on **"Places API"** (not "Places API (New)")
4. Click **"Enable"**

### Step 4: Create API Key

1. Go to [APIs & Services > Credentials](https://console.cloud.google.com/apis/credentials)
2. Click **"+ CREATE CREDENTIALS"**
3. Select **"API key"**
4. Your API key will be displayed - **COPY IT**
5. Click "Close"

### Step 5: Restrict API Key (Recommended)

1. Click on your newly created API key to edit it
2. Under "API restrictions":
   - Select "Restrict key"
   - Check **"Places API"** only
3. Click "Save"

### Step 6: Set Environment Variable

**On macOS/Linux:**
```bash
export GOOGLE_MAPS_API_KEY="your-api-key-here"
```

**On Windows (Command Prompt):**
```cmd
set GOOGLE_MAPS_API_KEY=your-api-key-here
```

**On Windows (PowerShell):**
```powershell
$env:GOOGLE_MAPS_API_KEY="your-api-key-here"
```

**Permanent (add to ~/.bashrc or ~/.zshrc):**
```bash
echo 'export GOOGLE_MAPS_API_KEY="your-api-key-here"' >> ~/.bashrc
source ~/.bashrc
```

### Step 7: Install Python Library

```bash
cd scripts
pip install -r requirements.txt
```

Or manually:
```bash
pip install googlemaps
```

## Usage

Run the enrichment script:

```bash
cd scripts
python3 enrich_with_google_maps.py
```

The script will:
1. Load companies from `data/final/companies.csv`
2. Find companies missing website/address
3. Search Google Maps for each company
4. Extract address, website, coordinates
5. Classify company stage
6. Save progress every 50 companies
7. Generate a report in `data/working/enrichment_report.txt`

## Pricing

**Free Tier:**
- $200/month credit (ongoing for all users)
- Places API Text Search: $0.032 per request
- Places API Place Details: $0.017 per request
- Combined: ~$0.049 per company

**For 899 companies:**
- Estimated cost: ~$44
- You have $200/month free credit
- **Well within free tier!**

**Rate Limits:**
- 1,000 requests per second (more than enough)
- No monthly quota limits

## Monitoring Usage

1. Go to [Google Cloud Console > Billing](https://console.cloud.google.com/billing)
2. Click on your billing account
3. View "Reports" to see API usage and costs
4. Set up billing alerts if desired

## Troubleshooting

### Error: "GOOGLE_MAPS_API_KEY environment variable not set"

Make sure you've exported the API key in your current terminal session:
```bash
echo $GOOGLE_MAPS_API_KEY  # Should print your key
```

### Error: "This API project is not authorized to use this API"

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Make sure the correct project is selected (top left dropdown)
3. Go to "APIs & Services > Enabled APIs"
4. Verify "Places API" is listed and enabled

### Error: "The provided API key is invalid"

1. Check your API key has no extra spaces or quotes
2. Verify it's a valid key in the [Credentials page](https://console.cloud.google.com/apis/credentials)
3. Make sure API restrictions allow "Places API"

### Low success rate (<70% addresses found)

- Google Maps may not have listings for very new startups
- Check the `enrichment_report.txt` for companies not found
- These may need manual research or web scraping fallback

## Security Notes

⚠️ **Keep your API key private!**
- Do NOT commit it to git
- Do NOT share it publicly
- Use environment variables only
- The key is already in `.gitignore` (if you add it to a config file)

## Next Steps

After enrichment completes:
1. Review `data/working/enrichment_report.txt`
2. Check companies not found in Google Maps
3. Optionally run web scraping fallback for missing data
4. Your data is now ready for map visualization!

---

**Questions?** Check the [Google Maps Platform Documentation](https://developers.google.com/maps/documentation/places/web-service)
