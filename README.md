# Astroturf Detector 🇺🇸

**An open-source intelligence engine monitoring for paid protest activity and manufactured grassroots movements in the United States.**

🔗 **Live Dashboard**: [https://ghost081280.github.io/astroturf-detector/](https://ghost081280.github.io/astroturf-detector/)

---

## What This Project Does

Astroturf Detector is an automated monitoring system that:

1. **Scans real public data sources** for suspicious nonprofit activity
2. **Monitors news** for reports of paid protests and astroturfing
3. **Tracks campaign finance** through FEC filings
4. **Uses AI analysis** to identify patterns suggesting manufactured movements
5. **Provides transparency** through a public dashboard updated hourly

---

## Data Sources (What We Actually Use)

We believe in transparency. Here's exactly what data sources power this project:

| Source | Status | What It Provides |
|--------|--------|------------------|
| **ProPublica Nonprofit Explorer** | ✅ Active | Real 501(c)(4) tax filings, organization data, revenue/assets |
| **FEC API** | ✅ Active | Campaign finance, independent expenditures, new committee filings |
| **Google News RSS** | ✅ Active | Real-time news articles about protests, astroturfing, advocacy |
| **AI Analysis (Claude)** | ✅ Active | Pattern detection, risk scoring, alert generation |

### What We DON'T Have Access To

Being honest about limitations:

- ❌ **Real-time job board scraping** - No free API allows this legally. Job posting data shown is for demonstration/tracking patterns only.
- ❌ **State Corporate Registries** - No unified free API exists. Would require scraping 50 different state websites.
- ❌ **Direct IRS access** - We use ProPublica which aggregates IRS Form 990 data (with delays).
- ❌ **Social media monitoring** - Not implemented, privacy concerns.

---

## The Problem We're Addressing

What looks like organic public outrage is sometimes manufactured. Companies exist that openly advertise services to:

- Hire crowds of "protesters" at $25-64/hour
- Provide speakers for city council meetings with scripted talking points  
- Create fake advocacy organizations overnight
- Run campaigns that simulate grassroots support

This practice is called **astroturfing** - creating the illusion of grassroots support where none exists.

### Documented Cases

**New Orleans Power Plant (2018)**  
Energy company Entergy paid $55,000 to fill city council chambers with actors supporting a controversial gas plant. The city fined Entergy $5 million after the scheme was exposed.

**Dallas Influence Network (2020-2024)**  
A billionaire funded a network of fake advocacy groups including a hoax organization. Multiple groups were created through a protesters-for-hire firm, registered as shell corporations in Delaware.

---

## Detection Methodology

### Organization Risk Scoring

We flag 501(c)(4) organizations based on:

| Factor | Points | Rationale |
|--------|--------|-----------|
| Generic 3-word name | +15 | "Citizens For Freedom" pattern common in astroturf |
| Name matches suspicious patterns | +10 | Patriotic/action words often used |
| Formed within last 2 years | +25 | New orgs more likely to be purpose-built |
| Formed within last 5 years | +15 | Still relatively new |
| Delaware registration | +15 | Shell company haven |
| High revenue + generic name | +15 | Well-funded but vague purpose |
| Politically active state | +5 | TX, FL, OH, PA, etc. |

Organizations scoring 30+ are flagged for display.

### News Relevance Scoring

Articles are scored based on keywords:

- **High value (+20 each)**: "astroturf", "paid protest", "fake grassroots", "dark money"
- **Medium value (+10 each)**: "protest", "advocacy", "campaign", "nonprofit"
- **Location bonus (+5)**: US state or city mentioned

---

## Technical Architecture
```
GitHub Actions (Hourly)
         |
         v
+------------------+     +------------------+     +------------------+
|   Google News    |     |   ProPublica     |     |   FEC API        |
|   RSS Feed       |     |   Nonprofit API  |     |   (Campaign $)   |
+------------------+     +------------------+     +------------------+
         |                       |                       |
         +-----------------------+-----------------------+
                                 |
                                 v
                    +------------------------+
                    |   Claude AI Analysis   |
                    |   (Pattern Detection)  |
                    +------------------------+
                                 |
                                 v
                    +------------------------+
                    |   memory.json          |
                    |   alerts.json          |
                    +------------------------+
                                 |
                                 v
                    +------------------------+
                    |   GitHub Pages         |
                    |   Public Dashboard     |
                    +------------------------+
```

### Files Structure
```
astroturf-detector/
├── docs/                    # Frontend (GitHub Pages)
│   ├── index.html
│   ├── css/styles.css
│   ├── js/app.js
│   └── data/
│       ├── memory.json      # Scan results & history
│       └── alerts.json      # Active alerts
├── scripts/
│   ├── orchestrator.py      # Main scan coordinator
│   ├── collectors/
│   │   ├── news_collector.py      # Google News RSS
│   │   ├── nonprofit_collector.py # ProPublica API
│   │   ├── fec_collector.py       # FEC API
│   │   └── job_collector.py       # Job patterns (limited)
│   └── analyzers/
│       ├── ai_agent.py            # Claude analysis
│       └── pattern_analyzer.py    # Statistical patterns
└── .github/workflows/
    └── scan.yml             # Hourly automation
```

---

## What This Is NOT

- **Not a claim that all protests are fake.** The vast majority of protests are genuine.
- **Not surveillance of individuals.** We track organizations and patterns, not people.
- **Not politically biased.** Astroturfing happens across the political spectrum.
- **Not definitive proof.** Our detections are indicators, not conclusions.

---

## Limitations (Honest Assessment)

1. **Data delays**: Nonprofit filings lag 6-12 months behind actual activity
2. **No job board access**: Can't actually scrape Indeed/LinkedIn legally
3. **API rate limits**: Free tiers limit how much we can scan
4. **False positives**: Legitimate orgs can match suspicious patterns
5. **US only**: Currently focused on United States data sources

---

## Environment Variables

To run locally or in GitHub Actions:
```bash
ANTHROPIC_API_KEY=your_key_here  # Required for AI analysis
FEC_API_KEY=your_key_here        # Optional, uses DEMO_KEY if not set
```

---

## Running Locally
```bash
# Install dependencies
pip install -r requirements.txt

# Run a scan
cd scripts
python orchestrator.py

# Run with full scan
python orchestrator.py --full
```

---

## Contributing

We welcome contributions, especially:

- Additional public data source integrations
- Better pattern detection algorithms
- UI/UX improvements
- Documentation and fact-checking

---

## Legal

This project uses only legally accessible public data:
- ProPublica's public API
- FEC's public API  
- Public RSS feeds

Astroturfing itself is generally legal, though ethically questionable. We make no accusations of illegal activity.

---

## License

MIT License - See LICENSE file

---

**Status**: Active Development  
**Last Updated**: January 2026  
**Maintainer**: [@ghost081280](https://github.com/ghost081280)
