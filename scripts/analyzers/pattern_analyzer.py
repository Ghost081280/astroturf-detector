"""Pattern Analyzer - Statistical pattern detection"""
import re
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict

class PatternAnalyzer:
    
    SUSPICIOUS_NAME_PATTERNS = [
        r'^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$',
        r'(Keep|Save|Protect) \w+ (Safe|Now|First)',
        r'(Citizens|Americans|People|Families|Voters) (For|Against|United|First)',
        r'(Freedom|Liberty|Justice|Truth) (Fund|Foundation|Alliance|Coalition)'
    ]
    
    def __init__(self, memory: Dict[str, Any]):
        self.memory = memory
    
    def analyze(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        results = {
            'job_patterns': self._analyze_jobs(collected_data.get('jobs', [])),
            'org_patterns': self._analyze_orgs(collected_data.get('nonprofits', [])),
            'news_patterns': self._analyze_news(collected_data.get('news', [])),
            'correlations': {
                'jobSpikeEvents': [],
                'orgFormationClusters': [],
                'geographicHotspots': []
            },
            'anomalies': []
        }
        
        results['correlations']['geographicHotspots'] = self._detect_hotspots(collected_data)
        return results
    
    def _analyze_jobs(self, jobs: List[Dict]) -> Dict[str, Any]:
        patterns = {
            'cities': defaultdict(int),
            'keywords': defaultdict(int),
            'high_suspicion_count': 0,
            'spikes': []
        }
        
        for job in jobs:
            city = job.get('city', 'Unknown')
            if city:
                patterns['cities'][city] += 1
            
            for kw in job.get('keywords', []):
                patterns['keywords'][kw] += 1
            
            if job.get('suspicion_score', 0) >= 50:
                patterns['high_suspicion_count'] += 1
        
        return {
            'cities': dict(patterns['cities']),
            'keywords': dict(patterns['keywords']),
            'high_suspicion_count': patterns['high_suspicion_count'],
            'spikes': patterns['spikes']
        }
    
    def _analyze_orgs(self, orgs: List[Dict]) -> Dict[str, Any]:
        patterns = {
            'name_flags': [],
            'high_risk_orgs': [],
            'state_distribution': defaultdict(int),
            'recent_formations': []
        }
        
        for org in orgs:
            name = org.get('name', '')
            risk = org.get('risk_score', 0)
            state = org.get('state', '')
            
            for pattern in self.SUSPICIOUS_NAME_PATTERNS:
                if re.search(pattern, name, re.IGNORECASE):
                    patterns['name_flags'].append({
                        'name': name,
                        'pattern': pattern,
                        'state': state
                    })
                    break
            
            if risk >= 50:
                patterns['high_risk_orgs'].append({
                    'name': name,
                    'risk_score': risk,
                    'state': state
                })
            
            if state:
                patterns['state_distribution'][state] += 1
        
        return {
            'name_flags': patterns['name_flags'],
            'high_risk_orgs': patterns['high_risk_orgs'],
            'state_distribution': dict(patterns['state_distribution']),
            'recent_formations': patterns['recent_formations']
        }
    
    def _analyze_news(self, articles: List[Dict]) -> Dict[str, Any]:
        patterns = {
            'high_relevance_count': 0,
            'sources': defaultdict(int),
            'topics': defaultdict(int)
        }
        
        for article in articles:
            if article.get('relevance_score', 0) >= 60:
                patterns['high_relevance_count'] += 1
            
            source = article.get('publisher', article.get('source', 'Unknown'))
            patterns['sources'][source] += 1
            
            query = article.get('query', '')
            if query:
                patterns['topics'][query] += 1
        
        return {
            'high_relevance_count': patterns['high_relevance_count'],
            'sources': dict(patterns['sources']),
            'topics': dict(patterns['topics'])
        }
    
    def _detect_hotspots(self, collected: Dict[str, Any]) -> List[Dict[str, Any]]:
        state_activity = defaultdict(int)
        
        for job in collected.get('jobs', []):
            state = job.get('state', '')
            if state:
                state_activity[state] += 2
        
        for org in collected.get('nonprofits', []):
            state = org.get('state', '')
            if state:
                state_activity[state] += 1
        
        if not state_activity:
            return []
        
        avg = sum(state_activity.values()) / len(state_activity)
        hotspots = []
        
        for state, count in sorted(state_activity.items(), key=lambda x: x[1], reverse=True)[:10]:
            if count > avg:
                hotspots.append({
                    'state': state,
                    'activity_score': count,
                    'above_average': round((count / avg - 1) * 100, 1)
                })
        
        return hotspots

if __name__ == '__main__':
    analyzer = PatternAnalyzer({})
    test_data = {
        'jobs': [{'city': 'Dallas', 'state': 'TX', 'keywords': ['protest'], 'suspicion_score': 60}],
        'nonprofits': [{'name': 'Citizens for Progress', 'state': 'TX', 'risk_score': 55}]
    }
    results = analyzer.analyze(test_data)
    print(f"Analysis complete")
