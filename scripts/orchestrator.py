#!/usr/bin/env python3
"""
ASTROTURF DETECTOR - Scan Orchestrator
United States - All 50 States
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

CONFIG = {
    'data_dir': Path(__file__).parent.parent / 'docs' / 'data',
    'memory_file': 'memory.json',
    'alerts_file': 'alerts.json',
    'max_api_calls_per_run': 200,
}


def load_memory(data_dir):
    """Load existing memory from JSON file."""
    memory_path = data_dir / CONFIG['memory_file']
    try:
        with open(memory_path, 'r') as f:
            memory = json.load(f)
            # Ensure dataSources exists (FIX for 'dataSources' KeyError)
            if 'dataSources' not in memory:
                memory['dataSources'] = {
                    'propublica': {'status': 'active', 'lastCall': None},
                    'fec': {'status': 'active', 'lastCall': None},
                    'googleNews': {'status': 'active', 'lastCall': None},
                    'craigslist': {'status': 'active', 'lastCall': None}
                }
            return memory
    except FileNotFoundError:
        return create_default_memory()


def save_memory(data_dir, memory):
    """Save memory to JSON file."""
    memory_path = data_dir / CONFIG['memory_file']
    memory['lastScan'] = datetime.utcnow().isoformat() + 'Z'
    with open(memory_path, 'w') as f:
        json.dump(memory, f, indent=2)


def load_alerts(data_dir):
    """Load existing alerts from JSON file."""
    alerts_path = data_dir / CONFIG['alerts_file']
    try:
        with open(alerts_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'version': '1.0.0', 'alerts': [], 'archivedAlerts': []}


def save_alerts(data_dir, alerts):
    """Save alerts to JSON file."""
    alerts_path = data_dir / CONFIG['alerts_file']
    alerts['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
    with open(alerts_path, 'w') as f:
        json.dump(alerts, f, indent=2)


def create_default_memory():
    """Create default memory structure."""
    return {
        'version': '1.0.0',
        'lastScan': None,
        'lastAnalysis': None,
        'stats': {
            'events': 0,
            'alerts': 0,
            'orgs': 0,
            'jobs': 0,
            'totalScans': 0,
            'newsArticles': 0
        },
        'systemConfidence': 0,
        'confidenceFactors': [],
        'timeline': [],
        'flaggedOrganizations': [],
        'jobPostings': [],
        'recentNews': [],
        'jobPostingPatterns': {
            'totalJobs': 0,
            'weekOverWeekChange': 0,
            'cities': {},
            'keywords': {},
            'states': {}
        },
        'correlations': {
            'jobSpikeEvents': [],
            'orgFormationClusters': [],
            'geographicHotspots': []
        },
        'knownAstroturfPatterns': {
            'threeWordNames': [],
            'delawareShells': [],
            'prFirms': []
        },
        'agentNotes': [],
        'dataSources': {
            'propublica': {'status': 'active', 'lastCall': None},
            'fec': {'status': 'active', 'lastCall': None},
            'googleNews': {'status': 'active', 'lastCall': None},
            'craigslist': {'status': 'active', 'lastCall': None}
        }
    }


def run_collectors(memory, full_scan=False):
    """Run all data collectors."""
    print("\n=== Starting Data Collection (All 50 States) ===\n")
    results = {'news': [], 'fec': [], 'nonprofits': [], 'jobs': [], 'errors': []}
    
    # Ensure dataSources exists in memory
    if 'dataSources' not in memory:
        memory['dataSources'] = {
            'propublica': {'status': 'active', 'lastCall': None},
            'fec': {'status': 'active', 'lastCall': None},
            'googleNews': {'status': 'active', 'lastCall': None},
            'craigslist': {'status': 'active', 'lastCall': None}
        }
    
    # Job Collector - Craigslist across all 50 states
    try:
        from collectors.job_collector import JobCollector
        print("Running job collector (Craigslist - All 50 States)...")
        job_collector = JobCollector()
        results['jobs'] = job_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 4)
        memory['dataSources']['craigslist'] = {
            'lastCall': datetime.utcnow().isoformat() + 'Z',
            'status': 'active'
        }
        print(f"  Found {len(results['jobs'])} job postings")
    except Exception as e:
        print(f"  Job collector error: {e}")
        results['errors'].append(f"Jobs: {str(e)}")
    
    # News Collector - Google News RSS
    try:
        from collectors.news_collector import NewsCollector
        print("Running news collector (Google News RSS)...")
        news_collector = NewsCollector()
        results['news'] = news_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 4)
        memory['dataSources']['googleNews'] = {
            'lastCall': datetime.utcnow().isoformat() + 'Z',
            'status': 'active'
        }
        print(f"  Found {len(results['news'])} news articles")
    except Exception as e:
        print(f"  News collector error: {e}")
        results['errors'].append(f"News: {str(e)}")
    
    # FEC Collector - Campaign Finance
    try:
        from collectors.fec_collector import FECCollector
        print("Running FEC collector (Campaign Finance)...")
        fec_collector = FECCollector()
        results['fec'] = fec_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 4)
        memory['dataSources']['fec'] = {
            'lastCall': datetime.utcnow().isoformat() + 'Z',
            'status': 'active'
        }
        print(f"  Found {len(results['fec'])} FEC records")
    except Exception as e:
        print(f"  FEC collector error: {e}")
        results['errors'].append(f"FEC: {str(e)}")
    
    # Nonprofit Collector - ProPublica
    try:
        from collectors.nonprofit_collector import NonprofitCollector
        print("Running nonprofit collector (ProPublica - All 50 States)...")
        nonprofit_collector = NonprofitCollector()
        results['nonprofits'] = nonprofit_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 4)
        memory['dataSources']['propublica'] = {
            'lastCall': datetime.utcnow().isoformat() + 'Z',
            'status': 'active'
        }
        print(f"  Found {len(results['nonprofits'])} nonprofit filings")
    except Exception as e:
        print(f"  Nonprofit collector error: {e}")
        results['errors'].append(f"Nonprofits: {str(e)}")
    
    # DuckDuckGo News Collector
    try:
        from collectors.ddg_collector import DuckDuckGoCollector
        print("Running DuckDuckGo collector...")
        ddg_collector = DuckDuckGoCollector()
        ddg_results = ddg_collector.collect(max_calls=5)
        results['news'].extend(ddg_results)  # Add to existing news
        memory['dataSources']['duckduckgo'] = {
            'lastCall': datetime.utcnow().isoformat() + 'Z',
            'status': 'active'
        }
        print(f"  Found {len(ddg_results)} DuckDuckGo results")
    except Exception as e:
        print(f"  DuckDuckGo collector error: {e}")
        results['errors'].append(f"DuckDuckGo: {str(e)}")
    
    return results


def run_analysis(memory, alerts, collected_data):
    """Run analysis on collected data."""
    print("\n=== Starting Analysis ===\n")
    patterns = {}
    
    # Store job postings
    jobs = collected_data.get('jobs', [])
    if jobs:
        memory['jobPostings'] = jobs[:50]  # Store top 50
        memory['stats']['jobs'] = len(jobs)
        
        # Aggregate job patterns
        cities = {}
        keywords = {}
        states = {}
        
        for job in jobs:
            city = job.get('city', 'Unknown')
            state = job.get('state', 'Unknown')
            cities[city] = cities.get(city, 0) + 1
            states[state] = states.get(state, 0) + 1
            
            for kw in job.get('keywords', []):
                keywords[kw] = keywords.get(kw, 0) + 1
        
        memory['jobPostingPatterns'] = {
            'totalJobs': len(jobs),
            'weekOverWeekChange': 0,
            'cities': dict(sorted(cities.items(), key=lambda x: x[1], reverse=True)[:20]),
            'keywords': dict(sorted(keywords.items(), key=lambda x: x[1], reverse=True)[:20]),
            'states': dict(sorted(states.items(), key=lambda x: x[1], reverse=True))
        }
    
    # Store news articles
    news_articles = collected_data.get('news', [])
    if news_articles:
        cutoff = datetime.utcnow() - timedelta(days=7)
        recent_news = []
        for article in news_articles:
            try:
                article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                if article_date.replace(tzinfo=None) > cutoff:
                    recent_news.append(article)
            except (ValueError, KeyError):
                recent_news.append(article)
        
        memory['recentNews'] = recent_news[:20]
        memory['stats']['newsArticles'] = len(recent_news)
    
    # Store nonprofits
    nonprofits = collected_data.get('nonprofits', [])
    if nonprofits:
        for org in nonprofits:
            if org.get('ein') and not org.get('sourceUrl'):
                org['sourceUrl'] = f"https://projects.propublica.org/nonprofits/organizations/{org['ein']}"
        memory['flaggedOrganizations'] = nonprofits[:30]
        memory['stats']['orgs'] = len(nonprofits)
    
    # Pattern Analysis
    try:
        from analyzers.pattern_analyzer import PatternAnalyzer
        print("Running pattern analyzer...")
        analyzer = PatternAnalyzer(memory)
        patterns = analyzer.analyze(collected_data)
        memory['correlations'] = patterns.get('correlations', memory.get('correlations', {}))
    except Exception as e:
        print(f"  Pattern analyzer error: {e}")
    
    # AI Agent Analysis
    try:
        from analyzers.ai_agent import AIAgent
        print("Running AI agent...")
        ai_agent = AIAgent()
        analysis_result = ai_agent.analyze(
            memory=memory,
            new_data=collected_data,
            patterns=patterns
        )
        
        memory['systemConfidence'] = analysis_result.get('confidence', 0)
        memory['confidenceFactors'] = analysis_result.get('confidence_factors', [])
        
        # Ensure agentNotes exists
        if 'agentNotes' not in memory:
            memory['agentNotes'] = []
        
        memory['agentNotes'].insert(0, {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': analysis_result.get('summary', ''),
            'recommendations': analysis_result.get('recommendations', [])
        })
        memory['agentNotes'] = memory['agentNotes'][:100]
        
        for alert in analysis_result.get('alerts', []):
            alert['id'] = f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(alerts['alerts'])}"
            alert['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            alerts['alerts'].insert(0, alert)
        
        # Ensure timeline exists
        if 'timeline' not in memory:
            memory['timeline'] = []
        
        for event in analysis_result.get('timeline_events', []):
            event['id'] = f"event_{len(memory['timeline'])}"
            memory['timeline'].insert(0, event)
        
        print(f"  System confidence: {memory['systemConfidence']}%")
    except Exception as e:
        print(f"  AI agent error: {e}")
    
    # Cleanup old alerts
    cutoff = datetime.utcnow() - timedelta(days=30)
    active_alerts = []
    for alert in alerts.get('alerts', []):
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            if alert_time.replace(tzinfo=None) > cutoff:
                active_alerts.append(alert)
            else:
                if 'archivedAlerts' not in alerts:
                    alerts['archivedAlerts'] = []
                alerts['archivedAlerts'].append(alert)
        except (ValueError, KeyError):
            active_alerts.append(alert)
    
    alerts['alerts'] = active_alerts[:50]
    alerts['archivedAlerts'] = alerts.get('archivedAlerts', [])[-100:]
    
    # Ensure timeline exists before slicing
    if 'timeline' not in memory:
        memory['timeline'] = []
    memory['timeline'] = memory['timeline'][:1000]
    
    # Ensure stats exists
    if 'stats' not in memory:
        memory['stats'] = {}
    
    # Update stats
    memory['stats']['events'] = len(memory.get('timeline', []))
    memory['stats']['alerts'] = len(alerts.get('alerts', []))
    memory['stats']['totalScans'] = memory['stats'].get('totalScans', 0) + 1
    memory['lastAnalysis'] = datetime.utcnow().isoformat() + 'Z'
    
    return memory, alerts


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Astroturf Detector - All 50 States')
    parser.add_argument('--full', action='store_true', help='Run full scan')
    parser.add_argument('--analyze-only', action='store_true', help='Skip collection')
    args = parser.parse_args()
    
    print("=" * 60)
    print("ASTROTURF DETECTOR - United States (All 50 States)")
    print(f"Started at: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    
    data_dir = CONFIG['data_dir']
    data_dir.mkdir(parents=True, exist_ok=True)
    
    memory = load_memory(data_dir)
    alerts = load_alerts(data_dir)
    
    if not args.analyze_only:
        collected_data = run_collectors(memory, full_scan=args.full)
    else:
        collected_data = {'news': [], 'fec': [], 'nonprofits': [], 'jobs': [], 'errors': []}
    
    memory, alerts = run_analysis(memory, alerts, collected_data)
    
    save_memory(data_dir, memory)
    save_alerts(data_dir, alerts)
    
    print("\n" + "=" * 60)
    print("Scan completed successfully")
    print(f"  Job postings: {memory['stats'].get('jobs', 0)}")
    print(f"  News articles: {memory['stats'].get('newsArticles', 0)}")
    print(f"  Organizations: {memory['stats'].get('orgs', 0)}")
    print(f"  Active alerts: {memory['stats'].get('alerts', 0)}")
    print(f"  Timeline events: {memory['stats'].get('events', 0)}")
    print(f"  Total scans: {memory['stats'].get('totalScans', 0)}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
