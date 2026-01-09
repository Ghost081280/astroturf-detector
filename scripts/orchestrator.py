#!/usr/bin/env python3
"""
Astroturf Detector - Main Orchestrator
"""
import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from collectors.job_collector import JobCollector
from collectors.news_collector import NewsCollector
from collectors.ddg_collector import DuckDuckGoCollector
from collectors.fec_collector import FECCollector
from collectors.nonprofit_collector import NonprofitCollector
from collectors.campaign_finance_collector import CampaignFinanceCollector
from analyzers.pattern_analyzer import PatternAnalyzer
from analyzers.ai_agent import AIAgent

DOCS_DATA = Path(__file__).parent.parent / 'docs' / 'data'
MEMORY_FILE = DOCS_DATA / 'memory.json'
ALERTS_FILE = DOCS_DATA / 'alerts.json'

def load_memory() -> dict:
    if MEMORY_FILE.exists():
        try:
            with open(MEMORY_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("  Warning: Corrupted memory.json, starting fresh")
    
    return {
        'version': '2.0',
        'lastScan': None,
        'stats': {'events': 0, 'alerts': 0, 'orgs': 0, 'newsArticles': 0},
        'timeline': [],
        'jobPostings': [],
        'jobPostingPatterns': {'totalJobs': 0, 'keywords': {}},
        'flaggedOrganizations': [],
        'recentNews': [],
        'systemConfidence': 50,
        'confidenceFactors': [],
        'agentNotes': [],
        'knownAstroturfPatterns': {
            'threeWordNames': ['Citizens for Progress', 'Americans for Prosperity'],
            'highActivityStates': ['TX', 'CA', 'FL', 'NY', 'PA', 'OH', 'GA', 'NC', 'MI', 'AZ']
        }
    }

def load_alerts() -> dict:
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("  Warning: Corrupted alerts.json, starting fresh")
    
    return {'alerts': [], 'archivedAlerts': []}

def save_memory(memory: dict):
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, 'w') as f:
        json.dump(memory, f, indent=2)

def save_alerts(alerts: dict):
    DOCS_DATA.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, 'w') as f:
        json.dump(alerts, f, indent=2)

def run_collectors() -> dict:
    print("\n=== Running Collectors ===")
    collected = {
        'jobs': [],
        'news': [],
        'nonprofits': [],
        'fec': [],
        'campaign_finance': []
    }
    
    print("\n[1/6] Job Collector")
    try:
        job_collector = JobCollector()
        collected['jobs'] = job_collector.collect(max_calls=15)
        print(f"  Collected {len(collected['jobs'])} job postings")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[2/6] News Collector")
    try:
        news_collector = NewsCollector()
        collected['news'] = news_collector.collect(max_calls=7)
        print(f"  Collected {len(collected['news'])} news articles")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[3/6] DuckDuckGo Collector")
    try:
        ddg_collector = DuckDuckGoCollector()
        ddg_results = ddg_collector.collect(max_calls=5)
        collected['news'].extend(ddg_results)
        print(f"  Collected {len(ddg_results)} DDG results")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[4/6] FEC Collector")
    try:
        fec_collector = FECCollector()
        collected['fec'] = fec_collector.collect(max_calls=10)
        print(f"  Collected {len(collected['fec'])} FEC records")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[5/6] Nonprofit Collector")
    try:
        nonprofit_collector = NonprofitCollector()
        collected['nonprofits'] = nonprofit_collector.collect(max_calls=10)
        print(f"  Collected {len(collected['nonprofits'])} nonprofits")
    except Exception as e:
        print(f"  Error: {e}")
    
    print("\n[6/6] Campaign Finance Collector")
    try:
        campaign_collector = CampaignFinanceCollector()
        collected['campaign_finance'] = campaign_collector.collect(max_calls=12)
        print(f"  Collected {len(collected['campaign_finance'])} campaign finance records")
    except Exception as e:
        print(f"  Error: {e}")
    
    return collected

def run_analysis(memory: dict, collected: dict) -> dict:
    print("\n=== Running Analysis ===")
    
    print("\n[1/2] Pattern Analyzer")
    try:
        analyzer = PatternAnalyzer(memory)
        patterns = analyzer.analyze(collected)
        print(f"  Found {len(patterns.get('job_patterns', {}).get('cities', {}))} city patterns")
    except Exception as e:
        print(f"  Error: {e}")
        patterns = {}
    
    print("\n[2/2] AI Agent")
    try:
        agent = AIAgent()
        ai_results = agent.analyze(memory, collected, patterns)
        print(f"  Confidence: {ai_results.get('systemConfidence', 50)}%")
    except Exception as e:
        print(f"  Error: {e}")
        ai_results = {'systemConfidence': 50, 'confidenceFactors': [], 'agentNotes': [], 'alerts': []}
    
    return {**patterns, **ai_results}

def update_memory(memory: dict, collected: dict, analysis: dict) -> dict:
    now = datetime.utcnow()
    timestamp = now.isoformat() + 'Z'
    
    memory['lastScan'] = timestamp
    
    real_jobs = [j for j in collected.get('jobs', []) if not j.get('is_monitoring_entry', False)]
    memory['jobPostings'] = real_jobs[:50]
    
    keywords = {}
    for job in collected.get('jobs', []):
        for kw in job.get('keywords', []):
            keywords[kw] = keywords.get(kw, 0) + 1
    memory['jobPostingPatterns'] = {
        'totalJobs': len(real_jobs),
        'keywords': keywords
    }
    
    all_orgs = collected.get('nonprofits', []) + collected.get('campaign_finance', [])
    all_orgs.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
    memory['flaggedOrganizations'] = all_orgs[:30]
    
    memory['recentNews'] = collected.get('news', [])[:50]
    
    memory['systemConfidence'] = analysis.get('systemConfidence', 50)
    memory['confidenceFactors'] = analysis.get('confidenceFactors', [])
    memory['agentNotes'] = analysis.get('agentNotes', [])
    
    new_events = []
    
    for job in real_jobs[:10]:
        if job.get('suspicion_score', 0) >= 30:
            new_events.append({
                'type': 'job_posting',
                'title': f"Job: {job.get('title', 'Unknown')[:60]}",
                'description': f"Suspicion score: {job.get('suspicion_score', 0)}% - {job.get('city', '')} {job.get('state', '')}",
                'date': timestamp,
                'sourceUrl': job.get('url', ''),
                'tags': job.get('keywords', [])[:3]
            })
    
    for article in collected.get('news', [])[:10]:
        if article.get('relevance_score', 0) >= 50:
            new_events.append({
                'type': 'news',
                'title': article.get('title', 'News Article')[:80],
                'description': f"Source: {article.get('publisher', 'Unknown')} | Relevance: {article.get('relevance_score', 0)}%",
                'date': article.get('date', timestamp),
                'sourceUrl': article.get('url', ''),
                'tags': ['news', article.get('query', '')]
            })
    
    for org in all_orgs[:5]:
        if org.get('risk_score', 0) >= 40:
            new_events.append({
                'type': 'organization',
                'title': f"Org: {org.get('name', 'Unknown')[:60]}",
                'description': f"Risk score: {org.get('risk_score', 0)}% - {org.get('state', '')}",
                'date': timestamp,
                'sourceUrl': org.get('sourceUrl', ''),
                'tags': ['nonprofit', org.get('source', '')]
            })
    
    existing = memory.get('timeline', [])
    combined = new_events + existing
    
    seen = set()
    unique = []
    for event in combined:
        key = event.get('title', '')[:50].lower()
        if key not in seen:
            seen.add(key)
            unique.append(event)
    
    unique.sort(key=lambda x: x.get('date', ''), reverse=True)
    memory['timeline'] = unique[:1000]
    
    memory['stats'] = {
        'events': len(memory['timeline']),
        'alerts': len(analysis.get('alerts', [])),
        'orgs': len(memory['flaggedOrganizations']),
        'newsArticles': len(memory['recentNews'])
    }
    
    return memory

def update_alerts(alerts_data: dict, analysis: dict) -> dict:
    now = datetime.utcnow()
    cutoff = now - timedelta(days=30)
    
    current = alerts_data.get('alerts', [])
    archived = alerts_data.get('archivedAlerts', [])
    
    still_active = []
    for alert in current:
        try:
            alert_date = datetime.fromisoformat(alert.get('timestamp', '').replace('Z', ''))
            if alert_date >= cutoff:
                still_active.append(alert)
            else:
                archived.append(alert)
        except:
            still_active.append(alert)
    
    for alert in analysis.get('alerts', []):
        alert['timestamp'] = now.isoformat() + 'Z'
        still_active.append(alert)
    
    alerts_data['alerts'] = still_active[:100]
    alerts_data['archivedAlerts'] = archived[:500]
    
    return alerts_data

def main():
    print("=" * 60)
    print("ASTROTURF DETECTOR - Scan Starting")
    print(f"Time: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    
    memory = load_memory()
    alerts_data = load_alerts()
    
    collected = run_collectors()
    analysis = run_analysis(memory, collected)
    
    memory = update_memory(memory, collected, analysis)
    alerts_data = update_alerts(alerts_data, analysis)
    
    save_memory(memory)
    save_alerts(alerts_data)
    
    print("\n" + "=" * 60)
    print("SCAN COMPLETE")
    print(f"  Timeline events: {len(memory['timeline'])}")
    print(f"  Jobs tracked: {memory['jobPostingPatterns']['totalJobs']}")
    print(f"  Organizations: {len(memory['flaggedOrganizations'])}")
    print(f"  News articles: {len(memory['recentNews'])}")
    print(f"  Confidence: {memory['systemConfidence']}%")
    print("=" * 60)

if __name__ == '__main__':
    main()
