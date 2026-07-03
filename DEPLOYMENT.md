# 🚀 Deployment Guide - Apollo.io Scraper for Apify

## ✅ Project is Ready for Apify Deployment!

This is a fully configured Apify Actor that can be deployed immediately.

---

## 📁 Project Structure

```
apollo-scraper/
├── __main__.py                 # Main Apify Actor entrypoint
├── INPUT_SCHEMA.json          # Apify input configuration
├── Dockerfile                 # Docker container config
├── requirements.txt           # Python dependencies
├── README.md                  # Actor documentation (shows on Apify)
│
├── .actor/
│   ├── actor.json            # Actor metadata
│   └── input.json            # Example input
│
└── src/
    ├── __init__.py
    ├── config.py             # Configuration
    ├── utils.py              # Utility functions
    ├── parser.py             # HTML parsing
    └── scraper.py            # Selenium scraping logic
```

---

## 🎯 How to Deploy to Apify

### Method 1: Deploy via Apify Console (Easiest)

1. **Create Apify Account**
   - Go to https://apify.com
   - Sign up for free account

2. **Create New Actor**
   - Click "Actors" → "Create new"
   - Choose "From scratch"

3. **Upload Code**
   - **Option A**: Connect GitHub repo
     - Push this code to GitHub
     - Connect repo in Apify Console
   
   - **Option B**: Direct upload
     - Zip entire project folder
     - Upload via Apify Console

4. **Build Actor**
   - Apify will automatically build using Dockerfile
   - Wait for build to complete

5. **Test Actor**
   - Use the example input from `.actor/input.json`
   - Replace with your Apollo credentials
   - Click "Start"

### Method 2: Deploy via Apify CLI

```bash
# Install Apify CLI
npm install -g apify-cli

# Login to Apify
apify login

# Initialize (if not already done)
apify init

# Deploy actor
apify push
```

---

## 🔑 Setting Up Input

When running the actor on Apify, configure this input:

```json
{
  "apolloEmail": "your@email.com",
  "apolloPassword": "your_password",
  "startUrls": [
    {
      "url": "https://app.apollo.io/#/search?query=YOUR_SEARCH"
    }
  ],
  "maxPages": 10,
  "enrichProfiles": true,
  "minDelay": 3,
  "maxDelay": 7,
  "proxyConfiguration": {
    "useApifyProxy": true
  }
}
```

### Required Fields:
- ✅ `apolloEmail` - Your Apollo.io email
- ✅ `apolloPassword` - Your Apollo.io password
- ✅ `startUrls` - At least one Apollo.io URL

### Optional Fields:
- `maxPages` (default: 10) - Max pages to scrape
- `enrichProfiles` (default: true) - Visit detail pages
- `minDelay` / `maxDelay` (default: 3 / 7) - Delay range in seconds
- `proxyConfiguration` - Recommended to use Apify proxies

---

## 🏃 Running Locally (Testing)

Before deploying, you can test locally:

```bash
# Install Apify CLI
npm install -g apify-cli

# Install dependencies
pip install -r requirements.txt

# Run locally
apify run
```

Or run directly with Python:
```bash
python __main__.py
```

---

## 📊 What Happens When Actor Runs

1. **Initialization**
   - Reads input from Apify
   - Validates credentials and URLs

2. **Browser Setup**
   - Launches headless Chrome
   - Configures anti-detection settings
   - Sets up Apify proxy (if configured)

3. **Login**
   - Attempts to load saved cookies
   - If no cookies, logs in with credentials
   - Saves cookies for next run

4. **Scraping**
   - Visits each URL
   - Detects page type (search/profile/company)
   - Scrapes all visible data
   - Handles pagination automatically
   - Optionally enriches with detail pages

5. **Output**
   - Pushes results to Apify dataset
   - Data available for download (JSON/CSV/Excel)

---

## 💰 Cost Estimate

### Apify Costs
- **Free Tier**: $5 worth of platform usage/month
  - ~5-10 hours of actor runtime
  - Enough for testing and small jobs

- **Personal Plan**: $49/month
  - ~100 hours of runtime
  - More storage and proxies

### Typical Usage
- **10 pages without enrichment**: ~2-3 minutes (~$0.02)
- **10 pages with enrichment**: ~10-15 minutes (~$0.10)
- **100 pages with enrichment**: ~1-2 hours (~$1-2)

### No Apollo Costs!
- ✅ Uses **FREE** Apollo account
- ✅ No API credits needed
- ✅ No paid subscription required

---

## ⚙️ Actor Configuration

The actor is pre-configured with:

✅ **Docker**: Apify Python + Selenium image  
✅ **Input Schema**: User-friendly input form  
✅ **Dataset**: Structured output format  
✅ **Categories**: Listed as SCRAPER  
✅ **Proxy Support**: Compatible with Apify proxies  

---

## 🐛 Troubleshooting

### Build Fails
- Check Dockerfile syntax
- Verify requirements.txt is valid
- Check Apify platform status

### Actor Fails on Run
- Verify Apollo credentials are correct
- Check input JSON is valid
- Review actor logs in Apify Console

### No Data Scraped
- Verify URLs are correct Apollo.io URLs
- Check if Apollo free searches are exhausted
- Enable debug logging to see details

### Slow Performance
- This is normal! Delays prevent detection
- Disable enrichment for faster runs
- Reduce maxPages

---

## 📈 Scaling Tips

### For Large Jobs
1. Split into multiple runs (100 pages each)
2. Use multiple start URLs
3. Disable enrichment initially
4. Run enrichment as separate job

### For Speed
1. Set `enrichProfiles: false`
2. Reduce delays to minimum
3. Use residential proxies
4. Process multiple URLs in parallel

### For Reliability
1. Enable Apify proxies
2. Use longer delays (5-10 seconds)
3. Process URLs sequentially
4. Monitor actor logs

---

## 🔒 Security Best Practices

1. **Credentials**
   - Store in Apify input (marked as secret)
   - Never commit to git
   - Rotate passwords periodically

2. **Proxies**
   - Always use Apify proxies for production
   - Prevents IP bans
   - Better success rates

3. **Rate Limiting**
   - Use default delays (3-7 seconds)
   - Don't scrape aggressively
   - Respect Apollo's limits

---

## 📞 Support

### Apify Support
- Apify docs: https://docs.apify.com
- Community forum: https://community.apify.com
- Support email: support@apify.com

### Actor Issues
- Check README.md
- Review actor logs
- Test input configuration

---

## ✅ Pre-Deployment Checklist

Before deploying, verify:

- [ ] Code is in correct structure
- [ ] Dockerfile is configured
- [ ] INPUT_SCHEMA.json is valid
- [ ] requirements.txt is complete
- [ ] README.md is informative
- [ ] .actor/actor.json is configured
- [ ] Tested locally (if possible)

---

## 🎉 You're Ready to Deploy!

Everything is configured and ready. Just:

1. ✅ Push code to Apify
2. ✅ Configure input with your credentials
3. ✅ Run the actor
4. ✅ Download your data!

**Deploy now and start scraping Apollo.io for free! 🚀**

---

*Apify Actor - Ready for Production ✅*





