#!/usr/bin/env python3
"""
ASTROTURF DETECTOR - Scan Orchestrator
United States Focus
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
    'max_api_calls_per_run': 50,
    'target_states': ['TX', 'CA', 'NY', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI', 'AZ', 'WA', 'CO', 'MA', 'VA', 'NJ', 'OR', 'LA', 'NV', 'DC']
}

def load_memory(data_dir):
    memory_path = data_dir / CONFIG['memory_file']
    try:
        with open(memory_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return create_default_memory()

def save_memory(data_dir, memory):
    memory_path = data_dir / CONFIG['memory_file']
    memory['lastScan'] = datetime.utcnow().isoformat() + 'Z'
    with open(memory_path, 'w') as f:
        json.dump(memory, f, indent=2)

def load_alerts(data_dir):
    alerts_path = data_dir / CONFIG['alerts_file']
    try:
        with open(alerts_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {'version': '1.0.0', 'alerts': [], 'archivedAlerts': []}

def save_alerts(data_dir, alerts):
    alerts_path = data_dir / CONFIG['alerts_file']
    alerts['lastUpdated'] = datetime.utcnow().isoformat() + 'Z'
    with open(alerts_path, 'w') as f:
        json.dump(alerts, f, indent=2)

def create_default_memory():
    return {
        'version': '1.0.0', 
        'lastScan': None, 
        'lastAnalysis': None,
        'stats': {
            'events': 0, 
            'alerts': 0, 
            'orgs': 0, 
            'totalScans': 0, 
            'newsArticles': 0,
            'nonprofitsMonitored': 0
        },
        'systemConfidence': 0, 
        'confidenceFactors': [],
        'timeline': [], 
        'flaggedOrganizations': [],
        'newsArticles': [],
        'recentNews': [],
        'correlations': {
            'jobSpikeEvents': [], 
            'orgFormationClusters': [], 
            'geographicHotspots': [],
            'newsCorrelations': []
        },
        'knownAstroturfPatterns': {
            'threeWordNames': [], 
            'delawareShells': [], 
            'prFirms': []
        },
        'documentedCases': [], 
        'analysisHistory': [], 
        'agentNotes': [],
        'dataSources': {
            'propublica': {'status': 'active', 'lastCall': None, 'description': 'ProPublica Nonprofit Explorer - 501(c)(4) tax filings'},
            'fec': {'status': 'active', 'lastCall': None, 'description': 'FEC API - Campaign finance and independent expenditures'},
            'googleNews': {'status': 'active', 'lastCall': None, 'description': 'Google News RSS - Real-time news monitoring'}
        }
    }

def run_collectors(memory, full_scan=False):
    print("\n=== Starting Data Collection (United States) ===\n")
    results = {'news': [], 'fec': [], 'nonprofits': [], 'errors': []}
    
    try:
        from collectors.news_collector import NewsCollector
        print("Running news collector (Google News RSS)...")
        news_collector = NewsCollector()
        results['news'] = news_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 3)
        memory['dataSources']['googleNews']['lastCall'] = datetime.utcnow().isoformat() + 'Z'
        memory['dataSources']['googleNews']['status'] = 'active'
        print(f"  Found {len(results['news'])} news articles")
    except Exception as e:
        print(f"  News collector error: {e}")
        results['errors'].append(f"News: {str(e)}")
    
    try:
        from collectors.fec_collector import FECCollector
        print("Running FEC collector...")
        fec_collector = FECCollector()
        results['fec'] = fec_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 3)
        memory['dataSources']['fec']['lastCall'] = datetime.utcnow().isoformat() + 'Z'
        memory['dataSources']['fec']['status'] = 'active'
        print(f"  Found {len(results['fec'])} FEC records")
    except Exception as e:
        print(f"  FEC collector error: {e}")
        results['errors'].append(f"FEC: {str(e)}")
    
    try:
        from collectors.nonprofit_collector import NonprofitCollector
        print("Running nonprofit collector (ProPublica)...")
        nonprofit_collector = NonprofitCollector()
        results['nonprofits'] = nonprofit_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 3)
        memory['dataSources']['propublica']['lastCall'] = datetime.utcnow().isoformat() + 'Z'
        memory['dataSources']['propublica']['status'] = 'active'
        print(f"  Found {len(results['nonprofits'])} nonprofit filings")
    except Exception as e:
        print(f"  Nonprofit collector error: {e}")
        results['errors'].append(f"Nonprofits: {str(e)}")
    
    return results

def run_analysis(memory, alerts, collected_data):
    print("\n=== Starting Analysis ===\n")
    patterns = {}
    
    news_articles = collected_data.get('news', [])
    if news_articles:
        cutoff = datetime.utcnow() - timedelta(days=7)
        recent_news = []
        for article in news_articles:
            try:
                article_date = datetime.fromisoformat(article['date'].replace('Z', '+00:00'))
                if article_date.replace(tzinfo=None) > cutoff:
                    recent_news.append(article)
            except:
                recent_news.append(article)
        
        memory['recentNews'] = recent_news[:20]
        memory['stats']['newsArticles'] = len(recent_news)
    
    nonprofits = collected_data.get('nonprofits', [])
    if nonprofits:
        for org in nonprofits:
            if org.get('ein'):
                org['sourceUrl'] = f"https://projects.propublica.org/nonprofits/organizations/{org['ein']}"
        memory['flaggedOrganizations'] = nonprofits[:20]
        memory['stats']['orgs'] = len(nonprofits)
    
    try:
        from analyzers.pattern_analyzer import PatternAnalyzer
        print("Running pattern analyzer...")
        analyzer = PatternAnalyzer(memory)
        patterns = analyzer.analyze(collected_data)
        memory['correlations'] = patterns.get('correlations', memory['correlations'])
    except Exception as e:
        print(f"  Pattern analyzer error: {e}")
    
    try:
        from analyzers.ai_agent import AIAgent
        print("Running AI agent...")
        ai_agent = AIAgent()
        analysis_result = ai_agent.analyze(memory=memory, new_data=collected_data, patterns=patterns)
        
        memory['systemConfidence'] = analysis_result.get('confidence', 0)
        memory['confidenceFactors'] = analysis_result.get('confidence_factors', [])
        
        memory['agentNotes'].append({
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'summary': analysis_result.get('summary', ''),
            'recommendations': analysis_result.get('recommendations', [])
        })
        memory['agentNotes'] = memory['agentNotes'][-100:]
        
        for alert in analysis_result.get('alerts', []):
            alert['id'] = f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{len(alerts['alerts'])}"
            alert['timestamp'] = datetime.utcnow().isoformat() + 'Z'
            alerts['alerts'].insert(0, alert)
        
        for event in analysis_result.get('timeline_events', []):
            event['id'] = f"event_{len(memory['timeline'])}"
            memory['timeline'].insert(0, event)
        
        print(f"  System confidence: {memory['systemConfidence']}%")
    except Exception as e:
        print(f"  AI agent error: {e}")
    
    cutoff = datetime.utcnow() - timedelta(days=30)
    active_alerts = []
    for alert in alerts.get('alerts', []):
        try:
            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
            if alert_time.replace(tzinfo=None) > cutoff:
                active_alerts.append(alert)
            else:
                alerts['archivedAlerts'].append(alert)
        except:
            active_alerts.append(alert)
    alerts['alerts'] = active_alerts[:50]
    memory['timeline'] = memory['timeline'][:1000]
    
    memory['stats']['events'] = len(memory['timeline'])
    memory['stats']['alerts'] = len(alerts['alerts'])
    memory['stats']['totalScans'] = memory['stats'].get('totalScans', 0) + 1
    memory['lastAnalysis'] = datetime.utcnow().isoformat() + 'Z'
    
    return memory, alerts

def main():
    parser = argparse.ArgumentParser(description='Astroturf Detector - United States')
    parser.add_argument('--full', action='store_true', help='Run full scan')
    parser.add_argument('--analyze-only', action='store_true', help='Skip collection')
    args = parser.parse_args()
    
    print("=" * 60)
    print("ASTROTURF DETECTOR - United States Monitor")
    print(f"Started at: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    
    data_dir = CONFIG['data_dir']
    data_dir.mkdir(parents=True, exist_ok=True)
    
    memory = load_memory(data_dir)
    alerts = load_alerts(data_dir)
    
    if not args.analyze_only:
        collected_data = run_collectors(memory, full_scan=args.full)
    else:
        collected_data = {'news': [], 'fec': [], 'nonprofits': [], 'errors': []}
    
    memory, alerts = run_analysis(memory, alerts, collected_data)
    save_memory(data_dir, memory)
    save_alerts(data_dir, alerts)
    
    print("\n" + "=" * 60)
    print("Scan completed successfully")
    print(f"  News articles: {memory['stats'].get('newsArticles', 0)}")
    print(f"  Organizations: {memory['stats'].get('orgs', 0)}")
    print(f"  Active alerts: {memory['stats'].get('alerts', 0)}")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
