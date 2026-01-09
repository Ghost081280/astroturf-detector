#!/usr/bin/env python3
"""Astroturf Detector Orchestrator - Coordinates data collection and AI analysis"""
import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent))

from analyzers.ai_agent import AIAgent

class Orchestrator:
    def __init__(self):
        self.base_path = Path(__file__).parent.parent
        self.data_path = self.base_path / 'docs' / 'data'
        self.memory_file = self.data_path / 'memory.json'
        self.alerts_file = self.data_path / 'alerts.json'
        
        # Ensure data directory exists
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.ai_agent = AIAgent()
    
    def load_memory(self) -> dict:
        """Load existing memory or create new"""
        if self.memory_file.exists():
            try:
                with open(self.memory_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return self._init_memory()
    
    def _init_memory(self) -> dict:
        """Initialize empty memory structure"""
        return {
            'lastScan': None,
            'stats': {'events': 0, 'alerts': 0, 'orgs': 0, 'newsArticles': 0},
            'systemConfidence': 35,
            'confidenceFactors': [],
            'agentNotes': [],
            'timeline': [],
            'recentNews': [],
            'jobPostings': [],
            'jobPostingPatterns': {'totalJobs': 0},
            'flaggedOrganizations': [],
            'connections': []
        }
    
    def save_memory(self, memory: dict):
        """Save memory to file"""
        with open(self.memory_file, 'w') as f:
            json.dump(memory, f, indent=2, default=str)
        print(f"  Memory saved to {self.memory_file}")
    
    def save_alerts(self, alerts: list):
        """Save alerts to separate file"""
        with open(self.alerts_file, 'w') as f:
            json.dump({'alerts': alerts, 'lastUpdated': datetime.utcnow().isoformat() + 'Z'}, f, indent=2)
        print(f"  Alerts saved to {self.alerts_file}")
    
    def run_collectors(self) -> dict:
        """Run all data collectors and return combined results"""
        print("\n=== Running Data Collectors ===")
        results = {
            'news': [],
            'jobs': [],
            'nonprofits': [],
            'campaign_finance': []
        }
        
        # Try to import and run each collector
        collectors = [
            ('collectors.news_collector', 'NewsCollector', 'news'),
            ('collectors.job_collector', 'JobCollector', 'jobs'),
            ('collectors.nonprofit_collector', 'NonprofitCollector', 'nonprofits'),
            ('collectors.fec_collector', 'FECCollector', 'campaign_finance')
        ]
        
        for module_name, class_name, result_key in collectors:
            try:
                module = __import__(module_name, fromlist=[class_name])
                collector_class = getattr(module, class_name)
                collector = collector_class()
                data = collector.collect()
                results[result_key] = data if isinstance(data, list) else []
                print(f"  {class_name}: {len(results[result_key])} items")
            except ImportError as e:
                print(f"  {class_name}: Not available ({e})")
            except Exception as e:
                print(f"  {class_name}: Error - {e}")
        
        return results
    
    def update_memory(self, memory: dict, new_data: dict, ai_result: dict) -> dict:
        """Update memory with new data and AI analysis"""
        now = datetime.utcnow().isoformat() + 'Z'
        
        # Update timestamp
        memory['lastScan'] = now
        
        # Update news (keep top 20 by relevance)
        existing_urls = {n.get('url') for n in memory.get('recentNews', [])}
        for article in new_data.get('news', []):
            if article.get('url') and article['url'] not in existing_urls:
                memory['recentNews'].append(article)
        
        # Sort by relevance and keep top 20
        memory['recentNews'] = sorted(
            memory.get('recentNews', []),
            key=lambda x: x.get('relevance_score', 0),
            reverse=True
        )[:20]
        
        # Update jobs
        existing_job_ids = {j.get('id') or j.get('url') for j in memory.get('jobPostings', [])}
        for job in new_data.get('jobs', []):
            job_id = job.get('id') or job.get('url')
            if job_id and job_id not in existing_job_ids:
                memory['jobPostings'].append(job)
        memory['jobPostings'] = memory['jobPostings'][-50:]  # Keep last 50
        memory['jobPostingPatterns'] = {'totalJobs': len(memory['jobPostings'])}
        
        # Update organizations
        existing_org_ids = {o.get('ein') or o.get('name') for o in memory.get('flaggedOrganizations', [])}
        for org in new_data.get('nonprofits', []) + new_data.get('campaign_finance', []):
            org_id = org.get('ein') or org.get('name')
            if org_id and org_id not in existing_org_ids:
                memory['flaggedOrganizations'].append(org)
        memory['flaggedOrganizations'] = memory['flaggedOrganizations'][-30:]  # Keep last 30
        
        # Update from AI result
        memory['systemConfidence'] = ai_result.get('systemConfidence', memory.get('systemConfidence', 50))
        memory['confidenceFactors'] = ai_result.get('confidenceFactors', [])
        memory['connections'] = ai_result.get('connections', [])
        
        if ai_result.get('agentNotes'):
            memory['agentNotes'] = ai_result['agentNotes'] + memory.get('agentNotes', [])
            memory['agentNotes'] = memory['agentNotes'][:10]  # Keep last 10 notes
        
        # Add to timeline
        for article in new_data.get('news', [])[:3]:
            memory['timeline'].append({
                'type': 'news',
                'title': article.get('title', 'News Article'),
                'date': now,
                'sourceUrl': article.get('url')
            })
        
        for job in new_data.get('jobs', [])[:2]:
            if job.get('suspicion_score', 0) >= 50:
                memory['timeline'].append({
                    'type': 'job_posting',
                    'title': f"Suspicious job: {job.get('title', 'Unknown')}",
                    'date': now,
                    'sourceUrl': job.get('url')
                })
        
        for org in new_data.get('nonprofits', [])[:2]:
            if org.get('risk_score', 0) >= 70:
                memory['timeline'].append({
                    'type': 'organization',
                    'title': f"Flagged org: {org.get('name', 'Unknown')}",
                    'date': now,
                    'sourceUrl': org.get('sourceUrl')
                })
        
        # Sort timeline and keep recent
        memory['timeline'] = sorted(
            memory.get('timeline', []),
            key=lambda x: x.get('date', ''),
            reverse=True
        )[:100]
        
        # Update stats
        memory['stats'] = {
            'events': len(memory.get('timeline', [])),
            'alerts': len(ai_result.get('alerts', [])),
            'orgs': len(memory.get('flaggedOrganizations', [])),
            'newsArticles': len(memory.get('recentNews', []))
        }
        
        return memory
    
    def run(self):
        """Main orchestration loop"""
        print("\n" + "="*60)
        print("ASTROTURF DETECTOR - Hourly Scan")
        print(f"Started: {datetime.utcnow().isoformat()}Z")
        print("="*60)
        
        # Load existing memory
        memory = self.load_memory()
        print(f"\nLoaded memory with {len(memory.get('timeline', []))} timeline events")
        
        # Run collectors
        new_data = self.run_collectors()
        total_items = sum(len(v) for v in new_data.values())
        print(f"\nCollected {total_items} total items")
        
        # Run AI analysis
        print("\n=== Running AI Analysis ===")
        ai_result = self.ai_agent.analyze(memory, new_data, {})
        print(f"  Confidence: {ai_result.get('systemConfidence', 'N/A')}%")
        print(f"  Alerts generated: {len(ai_result.get('alerts', []))}")
        print(f"  Connections found: {len(ai_result.get('connections', []))}")
        
        # Update memory
        memory = self.update_memory(memory, new_data, ai_result)
        
        # Save results
        self.save_memory(memory)
        self.save_alerts(ai_result.get('alerts', []))
        
        print("\n" + "="*60)
        print("SCAN COMPLETE")
        print(f"Stats: {json.dumps(memory['stats'])}")
        print("="*60 + "\n")
        
        return memory


if __name__ == "__main__":
    orchestrator = Orchestrator()
    orchestrator.run()
