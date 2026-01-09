# Astroturf Detector

**An open-source intelligence engine that monitors for paid protest activity and manufactured grassroots movements.**

---

## The Problem

What looks like organic public outrage is sometimes manufactured. Companies exist that openly advertise services to:

- Hire crowds of "protesters" at $25-64/hour
- Provide speakers for city council meetings with scripted talking points  
- Create fake advocacy organizations overnight
- Run phone banking and letter-writing campaigns that simulate grassroots support

This practice is called **astroturfing** - creating the illusion of grassroots support where none exists.

### Documented Cases

**New Orleans Power Plant (2018)**  
Energy company Entergy paid $55,000 to fill city council chambers with actors in orange t-shirts supporting a controversial $210 million gas plant. Organizers told recruits to "tell nobody you're being paid." The city fined Entergy $5 million after an investigation exposed the scheme.

**Dallas Influence Network (2020-2024)**  
A billionaire hotelier funded a network of fake advocacy groups including a hoax Black Lives Matter organization called "Dallas Justice Now." Multiple groups were created through a protesters-for-hire firm, all registered as shell corporations in Delaware. A local journalist who exposed the network was sued by the donor - and won.

**How Common Is This?**  
One major crowd-for-hire company reported a 400% increase in paid protester requests in 2025. They claim "tens of thousands" of contractors nationwide and openly advertise the ability to deploy crowds "within 24 hours."

---

## What This Project Does

Astroturf Detector is an automated intelligence system that:

1. **Monitors job boards** for suspicious protest-related hiring activity
2. **Tracks nonprofit filings** for newly created advocacy organizations  
3. **Correlates data** to identify patterns that suggest manufactured movements
4. **Provides transparency** through a public dashboard anyone can access

### Detection Factors

| Factor | What We Look For |
|--------|------------------|
| **Job Posting Spikes** | Sudden increases in "protest," "canvasser," "community organizer" listings in specific cities |
| **Organization Red Flags** | Three-word generic names, Delaware incorporation, recent creation, no verifiable leadership |
| **Financial Patterns** | Nonprofits suddenly receiving large grants, vague expense descriptions like "media services" |
| **Timing Correlation** | Activity spikes before city council votes, permit hearings, or legislative sessions |
| **Geographic Anomalies** | "Local" organizations with out-of-state registration or leadership |

---

## The Data Sources

All data comes from public, legally accessible sources:

- **Federal Election Commission** - Campaign finance disclosures, independent expenditure reports
- **IRS Form 990 Database** - Nonprofit tax filings including revenue, expenses, and officer names
- **Public Job Boards** - Aggregated job posting data (no personal information collected)
- **State Corporate Registries** - Organization incorporation records

We do not scrape private data, social media accounts, or any information that isn't already public record.

---

## Understanding the Dashboard

### Activity Timeline
Shows detected events over time. Spikes may indicate coordinated activity around specific dates - such as city council meetings, elections, or corporate permit hearings.

### Geographic View
Heat map of suspicious activity by metropolitan area. Higher concentrations may indicate active astroturf campaigns.

### Alert Feed
Recent detections with confidence scores. Each alert includes:
- What triggered the detection
- Relevant public records
- Correlation with known events
- Confidence assessment

### Organization Profiles
When patterns point to specific entities, we provide:
- Public incorporation records
- Available 990 tax filings
- Timeline of detected activity
- Known connections to other flagged organizations

---

## What This Is NOT

- **Not a claim that all protests are fake.** The vast majority of protests are genuine expressions of public sentiment.
- **Not surveillance of protesters.** We track organizations and hiring patterns, not individuals.
- **Not politically biased.** Astroturfing happens across the political spectrum. We apply the same analysis regardless of the cause.
- **Not definitive proof.** Our detections are indicators that warrant further investigation, not conclusive evidence.

---

## Why Transparency Matters

Democracy depends on authentic public participation. When corporations or wealthy individuals can manufacture the appearance of grassroots support:

- **City councils** approve projects that communities actually oppose
- **Legislators** vote based on fabricated constituent pressure  
- **Media coverage** amplifies artificial movements as if they were real
- **Genuine activists** get drowned out by paid voices

Sunlight is the best disinfectant. This project aims to make the astroturf industry visible.

---

## How It Works (Technical Overview)

```
Scheduled Scans (GitHub Actions)
         |
         v
+------------------+     +------------------+     +------------------+
|   Job Board      |     |   FEC/IRS        |     |   State Corp     |
|   Aggregator     |     |   API Scraper    |     |   Registry       |
+------------------+     +------------------+     +------------------+
         |                       |                       |
         +-----------------------+-----------------------+
                                 |
                                 v
                    +------------------------+
                    |   AI Analysis Engine   |
                    |   (Pattern Detection)  |
                    +------------------------+
                                 |
                                 v
                    +------------------------+
                    |   Memory System        |
                    |   (Historical Context) |
                    +------------------------+
                                 |
                                 v
                    +------------------------+
                    |   Public Dashboard     |
                    |   (GitHub Pages)       |
                    +------------------------+
```

The system runs automated scans on a schedule, staying within free API tier limits. An AI agent analyzes collected data against historical patterns stored in the memory system. Significant findings are published to the public dashboard.

---

## Data Retention and Privacy

- No personal information is collected or stored
- All source data is already public record
- Detection results are aggregated patterns, not individual tracking
- The memory system stores event correlations, not personal data

---

## Limitations

- **Delayed data**: Government filings can lag 6-12 months behind actual activity
- **Incomplete coverage**: Not all astroturf activity leaves detectable traces
- **False positives**: Legitimate organizing can sometimes match suspicious patterns
- **Resource constraints**: Free-tier API limits mean we can't monitor everything

---

## Contributing

This is an open-source project. If you have expertise in:

- OSINT investigation techniques
- Nonprofit financial analysis
- Campaign finance law
- Data visualization
- AI/ML pattern detection

We welcome contributions. See the repository for technical documentation.

---

## Legal

This project engages only in legal research using publicly available data. We make no accusations of illegal activity - astroturfing itself is generally legal, though ethically questionable and sometimes involves violations of lobbying disclosure laws.

If you believe any information displayed is inaccurate, please open an issue with documentation and we will investigate.

---

## Contact

For media inquiries, partnership proposals, or to report suspected astroturf activity:

Open an issue on this repository or reach out through the channels listed in the project profile.

---

*"The term 'astroturf' was coined to describe organizations that try to present themselves as grassroots organizations and are actually initiated and funded by donors. The groups themselves are the 'astroturf.'"*  
— Anne Nelson, Columbia University School of International and Public Affairs

---

**License**: MIT  
**Status**: Active Development  
**Last Updated**: January 2026
