# Astroturf Detector

[![Live Site](https://img.shields.io/badge/Live_Site-ghost081280.github.io-8b5cf6?style=for-the-badge)](https://ghost081280.github.io/astroturf-detector/)
[![GitHub Actions](https://img.shields.io/badge/GitHub_Actions-Automated-2088FF?style=for-the-badge&logo=github-actions&logoColor=white)](https://github.com/Ghost081280/astroturf-detector/actions)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=for-the-badge)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![AI Powered](https://img.shields.io/badge/AI_Powered-Claude-f59e0b?style=for-the-badge&logo=anthropic&logoColor=white)](https://anthropic.com)

**Open-source intelligence engine monitoring for paid protest activity and manufactured grassroots movements across all 50 United States + DC.**

![Dashboard Preview](https://img.shields.io/badge/Status-Under_Active_Development-f59e0b?style=flat-square)

---

## What This Project Does

Astroturf Detector automatically scans multiple public data sources to identify potential **astroturfing** — fake grassroots campaigns funded by corporations, political operatives, or special interest groups to manufacture the appearance of organic public support.

### Real-World Examples We Track

- **Paid protesters** hired through services like Crowds on Demand ($60 to attend, $200 for speaking roles)
- **Fake advocacy groups** like "Dallas Justice Now" (a hoax BLM organization created by a billionaire hotelier)
- **Pink-slime news sites** that amplify manufactured campaigns
- **Suspicious job postings** on Craigslist advertising for "protesters," "rally attendees," or "brand ambassadors"
- **501(c)(4) dark money organizations** with generic names like "Citizens For [X]"

---

## Data Sources

| Source | What We Monitor |
|--------|-----------------|
| **ProPublica Nonprofit Explorer** | 501(c)(4) tax filings and dark money organizations |
| **FEC Campaign Finance API** | Political spending and PAC contributions |
| **Google News RSS** | Real-time news coverage of protests and advocacy |
| **DuckDuckGo Search** | Additional news and investigation articles |
| **Craigslist (All 50 States + DC)** | Job postings for paid protesters, rally attendees |
| **Claude AI Analysis** | Pattern detection and confidence scoring |

---

## What Gets Flagged

The system generates alerts when it detects:

- **Coordinated messaging** across multiple states with identical talking points
- **Generic organization names** following patterns like "Citizens For [X]", "[State] Freedom Fund"
- **Suspicious job postings** advertising protest/rally work with cash pay
- **Sudden appearance** of new advocacy groups around controversial issues
- **Geographic clustering** of activity in politically strategic locations
- **Connection to known services** like Crowds on Demand or The Hawthorn Group

---

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions (Daily)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│   │  Craigslist  │  │  ProPublica  │  │  FEC API     │          │
│   │  50 States   │  │  Nonprofits  │  │  Finance     │          │
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

High-activity states (shown in red on dashboard): AZ, CA, CO, FL, GA, MI, NY, OH, PA, TX, DC

---

## Contributing

Found a paid protest service we should track? Know of an astroturf campaign? 

- Open an issue with documentation/sources
- Submit a pull request with new data sources
- Help improve pattern detection algorithms

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
