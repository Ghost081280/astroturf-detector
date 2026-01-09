#!/usr/bin/env python3
"""
ASTROTURF DETECTOR - Scan Orchestrator
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
    'job_keywords': ['protest', 'protester', 'canvasser', 'community organizer', 'grassroots', 'advocacy', 'rally', 'demonstration'],
    'target_cities': ['Washington DC', 'New York', 'Los Angeles', 'Dallas', 'Chicago', 'Phoenix', 'San Francisco', 'New Orleans', 'Austin', 'Denver', 'Atlanta', 'Seattle']
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
        'version': '1.0.0', 'lastScan': None, 'lastAnalysis': None,
        'stats': {'events': 0, 'alerts': 0, 'orgs': 0, 'totalScans': 0, 'jobPostingsTracked': 0, 'nonprofitsMonitored': 0},
        'systemConfidence': 0, 'timeline': [], 'flaggedOrganizations': [],
        'jobPostingPatterns': {'cities': {}, 'keywords': {}, 'weeklyTrends': []},
        'correlations': {'jobSpikeEvents': [], 'orgFormationClusters': [], 'geographicHotspots': []},
        'knownAstroturfPatterns': {'threeWordNames': [], 'delawareShells': [], 'prFirms': []},
        'documentedCases': [], 'analysisHistory': [], 'agentNotes': []
    }

def run_collectors(memory, full_scan=False):
    print("\n=== Starting Data Collection ===\n")
    results = {'jobs': [], 'fec': [], 'nonprofits': [], 'errors': []}
    
    try:
        from collectors.job_collector import JobCollector
        print("Running job collector...")
        job_collector = JobCollector(keywords=CONFIG['job_keywords'], cities=CONFIG['target_cities'])
        results['jobs'] = job_collector.collect(max_calls=CONFIG['max_api_calls_per_run'] // 3)
        print(f"  Found {len(results['jobs'])} relevant job postings")
    except Exception as e:
        print(f"  Job collector error: {e}")
    
    try:
        from collectors.fec_collector import FECCollector
        print("Running FEC collector...")
        results['fec'] = FECCollector().collect(max_calls=CONFIG['max_api_calls_per_run'] // 3)
        print(f"  Found {len(results['fec'])} independent expenditure records")
    except Exception as e:
        print(f"  FEC collector error: {e}")
    
    try:
        from collectors.nonprofit_collector import NonprofitCollector
        print("Running nonprofit collector...")
        results['nonprofits'] = NonprofitCollector().collect(max_calls=CONFIG['max_api_calls_per_run'] // 3)
        print(f"  Found {len(results['nonprofits'])} new 501(c)(4) filings")
    except Exception as e:
        print(f"  Nonprofit collector error: {e}")
    
    return results

def run_analysis(memory, alerts, collected_data):
    print("\n=== Starting Analysis ===\n")
    patterns = {}
    
    try:
        from analyzers.pattern_analyzer import PatternAnalyzer
        print("Running pattern analyzer...")
        analyzer = PatternAnalyzer(memory)
        patterns = analyzer.analyze(collected_data)
        memory['jobPostingPatterns'] = patterns.get('job_patterns', memory['jobPostingPatterns'])
        memory['correlations'] = patterns.get('correlations', memory['correlations'])
    except Exception as e:
        print(f"  Pattern analyzer error: {e}")
    
    try:
        from analyzers.ai_agent import AIAgent
        print("Running AI agent...")
        ai_agent = AIAgent()
        analysis_result = ai_agent.analyze(memory=memory, new_data=collected_data, patterns=patterns)
        
        memory['systemConfidence'] = analysis_result.get('confidence', 0)
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
    memory['stats']['orgs'] = len(memory.get('flaggedOrganizations', []))
    memory['stats']['totalScans'] = memory['stats'].get('totalScans', 0) + 1
    memory['lastAnalysis'] = datetime.utcnow().isoformat() + 'Z'
    
    return memory, alerts

def main():
    parser = argparse.ArgumentParser(description='Astroturf Detector Scan Orchestrator')
    parser.add_argument('--full', action='store_true', help='Run full scan')
    parser.add_argument('--analyze-only', action='store_true', help='Skip collection')
    args = parser.parse_args()
    
    print("=" * 60)
    print("ASTROTURF DETECTOR - Scan Orchestrator")
    print(f"Started at: {datetime.utcnow().isoformat()}Z")
    print("=" * 60)
    
    data_dir = CONFIG['data_dir']
    data_dir.mkdir(parents=True, exist_ok=True)
    
    memory = load_memory(data_dir)
    alerts = load_alerts(data_dir)
    
    if not args.analyze_only:
        collected_data = run_collectors(memory, full_scan=args.full)
    else:
        collected_data = {'jobs': [], 'fec': [], 'nonprofits': [], 'errors': []}
    
    memory, alerts = run_analysis(memory, alerts, collected_data)
    save_memory(data_dir, memory)
    save_alerts(data_dir, alerts)
    
    print("\n" + "=" * 60)
    print("Scan completed successfully")
    print("=" * 60)
    return 0

if __name__ == '__main__':
    sys.exit(main())
