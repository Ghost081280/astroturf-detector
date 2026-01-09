# Astroturf Detector

[![Live Site](https://img.shields.io/badge/Live_Site-ghost081280.github.io-8b5cf6?style=for-the-badge)](https://ghost081280.github.io/astroturf-detector/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Hourly-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/Ghost081280/astroturf-detector/actions)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![AI Powered](https://img.shields.io/badge/AI_Powered-Claude-f59e0b?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)

**Open-source intelligence engine monitoring for paid protest activity and manufactured grassroots movements across all 50 United States + DC.**

---

## What This Project Does

Astroturf Detector automatically scans multiple public data sources to identify potential **astroturfing** — fake grassroots campaigns funded by corporations, political operatives, or special interest groups to manufacture the appearance of organic public support.

### Real-World Examples We Track

- **Paid protesters** hired through services like Crowds on Demand ($60 to attend, $200 for speaking roles)
- **Fake advocacy groups** like "Dallas Justice Now" (a hoax BLM organization created by a billionaire hotelier)
- **Suspicious job postings** advertising for "protesters," "rally attendees," or "canvassers"
- **501(c)(4) dark money organizations** with generic names like "Citizens For [X]"
- **New political committees** with suspicious naming patterns

---

## Data Sources

### ✅ Working APIs

| Source | What We Monitor | Auth Required |
|--------|-----------------|---------------|
| **Adzuna Job API** | Job postings for organizers, canvassers, campaign staff | Yes (free key) |
| **USAJobs API** | Government/political job listings | No |
| **Remotive RSS** | Remote organizing and coordinator roles | No |
| **Google News RSS** | Real-time news coverage of protests and advocacy | No |
| **DuckDuckGo Search** | Additional news and investigation articles | No |
| **ProPublica Nonprofit Explorer** | 501(c)(4) tax filings and nonprofit formations | No |
| **ProPublica Itemizer API** | Recent campaign finance filings | No |
| **FEC API** | Independent expenditures, new political committees | Optional (DEMO_KEY works) |
| **Claude AI** | Pattern detection and confidence scoring | Yes |

### ❌ Removed/Discontinued

| Source | Reason |
|--------|--------|
| Craigslist | Blocked all scraping |
| OpenSecrets API | Discontinued April 2025 |
| FollowTheMoney | Merged with OpenSecrets, API discontinued |
| Indeed | No free API tier |

---

## What Gets Flagged

The system generates alerts when it detects:

- **Suspicious job postings** with keywords like "paid protest," "hold signs," "same day pay"
- **Generic organization names** following patterns like "Citizens For [X]", "[State] Freedom Fund"
- **Three-word patriotic names** common in astroturf operations
- **Recently formed nonprofits** (within 2 years) with vague purposes
- **Delaware incorporations** (common for shell organizations)
- **Geographic clustering** of activity in politically strategic states
- **Connection to known services** like Crowds on Demand or The Hawthorn Group

---

## Suspicion Scoring

### Job Postings (0-100)
- **+25 points:** "paid protest", "hold signs", "same day pay", "cash daily"
- **+10 points:** "protest", "rally", "canvass", "grassroots", "political"
- **+5 points:** "urgent", "immediate", "today", "asap"

### Organizations (0-100)
- **+25 points:** Formed within last 2 years
- **+15 points:** Generic patriotic name pattern
- **+15 points:** Delaware incorporation
- **+10 points:** Three-word name
- **+10 points:** Vague purpose words (freedom, liberty, prosperity)

---

## How It Works
```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Hourly)                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │   Adzuna     │  │  ProPublica  │  │  FEC API     │          │
│   │  + USAJobs   │  │  Nonprofits  │  │  Committees  │          │
│   │  + Remotive  │  │  + Itemizer  │  │              │          │
│   └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│          │                 │                 │                   │
│          └────────────────┼────────────────┘                    │
│                           ▼                                      │
│                  ┌────────────────┐                              │
│                  │  Google News   │                              │
│                  │  + DuckDuckGo  │                              │
│                  └────────┬───────┘                              │
│                           ▼                                      │
│                  ┌────────────────┐                              │
│                  │   Claude AI    │                              │
│                  │   Analysis     │                              │
│                  └────────┬───────┘                              │
│                           ▼                                      │
│                  ┌────────────────┐                              │
│                  │  memory.json   │                              │
│                  │  alerts.json   │                              │
│                  └────────────────┘                              │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │   GitHub Pages Site     │
              │   (Public Dashboard)    │
              └─────────────────────────┘
```

---

## Setup

### Required API Keys (GitHub Secrets)

| Secret | Required | Get It From |
|--------|----------|-------------|
| `ADZUNA_APP_ID` | Yes | [developer.adzuna.com](https://developer.adzuna.com) (free) |
| `ADZUNA_APP_KEY` | Yes | [developer.adzuna.com](https://developer.adzuna.com) (free) |
| `ANTHROPIC_API_KEY` | Yes | [console.anthropic.com](https://console.anthropic.com) |
| `FEC_API_KEY` | Optional | [api.open.fec.gov](https://api.open.fec.gov/developers) (uses DEMO_KEY if not set) |

### Local Development
```bash
# Clone the repo
git clone https://github.com/ghost081280/astroturf-detector.git
cd astroturf-detector

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ADZUNA_APP_ID="your_id"
export ADZUNA_APP_KEY="your_key"
export ANTHROPIC_API_KEY="your_key"

# Run a scan
cd scripts
python orchestrator.py
```

### Deployment

1. Fork this repository
2. Add API keys to **Settings → Secrets → Actions**
3. Enable GitHub Pages (**Settings → Pages → Source: main, /docs**)
4. GitHub Actions runs hourly scans automatically

---

## Documented Case Studies

### Entergy New Orleans (2017-2018)
~50 people in orange shirts appeared at city council meetings supporting a $210M power plant — many were paid actors. The CEO texted: *"This is war and we need all the foot soldiers we can muster."*

**Outcome:** $5 million fine — largest ever imposed by the city council

### Dallas Astroturf Network (2020-2024)
Billionaire Monty Bennett hired Crowds on Demand to create fake groups: Keep Dallas Safe, Dallas Justice Now (hoax BLM org), Save Texas Kids, Protect Texas Kids, Mission DFW. The Dallas Express (pink-slime news) ran 112+ articles amplifying them.

**Outcome:** Journalist Steven Monacelli won defamation lawsuit after exposing the network

---

## Coverage

**51 Regions Monitored:** All 50 US States + Washington DC

**Priority States (high political activity):** AZ, CA, CO, DC, FL, GA, IL, MI, NC, NJ, NY, OH, PA, TX, VA, WA

---

## Project Structure
```
astroturf-detector/
├── .github/workflows/
│   └── scan.yml              # Hourly GitHub Actions workflow
├── docs/
│   ├── css/styles.css        # Dashboard styling
│   ├── js/app.js             # Dashboard functionality
│   ├── data/
│   │   ├── memory.json       # Scan results and timeline
│   │   └── alerts.json       # Active alerts
│   └── index.html            # Public dashboard
├── scripts/
│   ├── collectors/
│   │   ├── job_collector.py          # Adzuna + USAJobs + Remotive
│   │   ├── news_collector.py         # Google News RSS
│   │   ├── ddg_collector.py          # DuckDuckGo search
│   │   ├── fec_collector.py          # FEC campaign finance
│   │   ├── nonprofit_collector.py    # ProPublica nonprofits
│   │   └── campaign_finance_collector.py  # ProPublica Itemizer + FEC
│   ├── analyzers/
│   │   ├── pattern_analyzer.py       # Statistical patterns
│   │   └── ai_agent.py               # Claude AI analysis
│   └── orchestrator.py               # Main coordinator
├── requirements.txt
└── README.md
```

---

## Contributing

Found a paid protest service we should track? Know of an astroturf campaign?

- Open an issue with documentation/sources
- Submit a pull request with new data sources
- Help improve pattern detection algorithms

**Priority areas:**
- New working job board APIs
- State corporate registry integrations
- Improved scoring algorithms
- International expansion

---

## Disclaimer

This tool monitors **publicly available data** to detect potential manufactured grassroots activity. It does not make accusations — it flags patterns that warrant further investigation. Always verify findings through additional research before drawing conclusions.

---

## Contact

**Developer:** [@Ghost081280](https://github.com/Ghost081280)

**Live Site:** [ghost081280.github.io/astroturf-detector](https://ghost081280.github.io/astroturf-detector/)

---

<p align="center">
  <i>Democracy works best when grassroots means grassroots.</i>
</p>
