"""Pattern Analyzer - Statistical Pattern Detection"""

import json
from datetime import datetime
from typing import Dict, Any, List
from collections import defaultdict
import re

class PatternAnalyzer:
    SUSPICIOUS_NAME_PATTERNS = [
        r'^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$',
        r'(Keep|Save|Protect) \w+ (Safe|Now|First)',
        r'(Citizens|Americans|People|Families|Voters) (For|Against|United|First)',
        r'\w+ (Justice|Action|Voice|Voices) (Now|Today)',
    ]
    
    def __init__(self, memory: Dict[str, Any]):
        self.memory = memory
        self.historical_patterns = memory.get('jobPostingPatterns', {})
        self.known_cases = memory.get('documentedCases', [])
    
    def analyze(self, collected_data: Dict[str, Any]) -> Dict[str, Any]:
        results = {
            'job_patterns': self._analyze_job_patterns(collected_data.get('jobs', [])),
            'org_patterns': self._analyze_org_patterns(collected_data.get('nonprofits', [])),
            'financial_patterns': self._analyze_financial_patterns(collected_data.get('fec', [])),
            'correlations': self._find_correlations(collected_data),
            'anomalies': []
        }
        results['anomalies'] = self._detect_anomalies(results)
        return results
    
    def _analyze_job_patterns(self, jobs: List[Dict]) -> Dict[str, Any]:
        patterns = {'cities': defaultdict(int), 'keywords': defaultdict(int), 'weeklyTrends': [], 'spikes': []}
        for job in jobs:
            city = job.get('city', 'Unknown')
            patterns['cities'][city] += 1
            for keyword in job.get('keywords_tracked', []):
                patterns['keywords'][keyword] += 1
        patterns['cities'] = dict(patterns['cities'])
        patterns['keywords'] = dict(patterns['keywords'])
        historical_cities = self.historical_patterns.get('cities', {})
        for city, count in patterns['cities'].items():
            historical_count = historical_cities.get(city, 0)
            if historical_count > 0 and count > historical_count * 2:
                patterns['spikes'].append({
                    'type': 'city_spike', 'city': city, 'current': count,
                    'historical': historical_count,
                    'increase_pct': ((count - historical_count) / historical_count) * 100
                })
        return patterns
    
    def _analyze_org_patterns(self, orgs: List[Dict]) -> Dict[str, Any]:
        patterns = {'name_flags': [], 'geographic_clusters': [], 'formation_clusters': [], 'high_risk_orgs': []}
        for org in orgs:
            name = org.get('name', '')
            risk_score = org.get('risk_score', 0)
            for pattern in self.SUSPICIOUS_NAME_PATTERNS:
                if re.search(pattern, name, re.IGNORECASE):
                    patterns['name_flags'].append({'name': name, 'pattern_matched': pattern, 'ein': org.get('ein'), 'state': org.get('state')})
                    break
            if risk_score >= 50:
                patterns['high_risk_orgs'].append({'name': name, 'ein': org.get('ein'), 'risk_score': risk_score, 'state': org.get('state'), 'ruling_date': org.get('ruling_date')})
        patterns['geographic_clusters'] = self._detect_geographic_clusters(orgs)
        patterns['formation_clusters'] = self._detect_formation_clusters(orgs)
        return patterns
    
    def _analyze_financial_patterns(self, fec_data: List[Dict]) -> Dict[str, Any]:
        patterns = {'large_expenditures': [], 'new_committees': [], 'expenditure_clusters': []}
        for record in fec_data:
            if record.get('type') == 'independent_expenditure':
                amount = record.get('amount', 0) or 0
                if amount > 100000:
                    patterns['large_expenditures'].append({'committee': record.get('committee_name'), 'amount': amount, 'date': record.get('date'), 'purpose': record.get('purpose'), 'support_oppose': record.get('support_oppose')})
            elif record.get('type') == 'new_committee':
                patterns['new_committees'].append({'name': record.get('name'), 'committee_id': record.get('committee_id'), 'first_file_date': record.get('first_file_date'), 'state': record.get('state'), 'type': record.get('committee_type')})
        return patterns
    
    def _find_correlations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        correlations = {'jobSpikeEvents': [], 'orgFormationClusters': [], 'geographicHotspots': []}
        job_cities = set(job.get('city') for job in data.get('jobs', []) if job.get('city'))
        org_cities = set(org.get('city') for org in data.get('nonprofits', []) if org.get('city'))
        for city in job_cities.intersection(org_cities):
            correlations['geographicHotspots'].append({'city': city, 'has_job_activity': True, 'has_org_activity': True, 'correlation_strength': 'moderate'})
        return correlations
    
    def _detect_geographic_clusters(self, orgs: List[Dict]) -> List[Dict]:
        state_counts = defaultdict(list)
        for org in orgs:
            state = org.get('state')
            if state:
                state_counts[state].append(org)
        return [{'state': state, 'count': len(state_orgs), 'organizations': [o.get('name') for o in state_orgs[:5]]} for state, state_orgs in state_counts.items() if len(state_orgs) >= 3]
    
    def _detect_formation_clusters(self, orgs: List[Dict]) -> List[Dict]:
        by_year = defaultdict(list)
        for org in orgs:
            ruling_date = org.get('ruling_date')
            if ruling_date:
                try:
                    year = int(str(ruling_date)[:4])
                    by_year[year].append(org)
                except:
                    pass
        current_year = datetime.utcnow().year
        return [{'year': year, 'count': len(by_year[year]), 'organizations': [o.get('name') for o in by_year[year][:5]]} for year in [current_year, current_year - 1] if len(by_year.get(year, [])) >= 3]
    
    def _detect_anomalies(self, analysis_results: Dict) -> List[Dict]:
        anomalies = []
        for spike in analysis_results.get('job_patterns', {}).get('spikes', []):
            if spike.get('increase_pct', 0) > 100:
                anomalies.append({'type': 'job_spike', 'severity': 'high' if spike['increase_pct'] > 200 else 'medium', 'description': f"Job postings in {spike['city']} increased {spike['increase_pct']:.0f}%", 'data': spike})
        for org in analysis_results.get('org_patterns', {}).get('high_risk_orgs', []):
            if org.get('risk_score', 0) >= 70:
                anomalies.append({'type': 'high_risk_org', 'severity': 'high', 'description': f"High-risk organization detected: {org['name']}", 'data': org})
        for cluster in analysis_results.get('org_patterns', {}).get('geographic_clusters', []):
            if cluster.get('count', 0) >= 5:
                anomalies.append({'type': 'geographic_cluster', 'severity': 'medium', 'description': f"Cluster of {cluster['count']} organizations in {cluster['state']}", 'data': cluster})
        return anomalies

if __name__ == '__main__':
    memory = {'jobPostingPatterns': {}, 'documentedCases': []}
    analyzer = PatternAnalyzer(memory)
    test_data = {'jobs': [{'city': 'Dallas', 'keywords_tracked': ['protest']}], 'nonprofits': [{'name': 'Keep Dallas Safe', 'state': 'TX', 'risk_score': 75}], 'fec': []}
    results = analyzer.analyze(test_data)
    print(json.dumps(results, indent=2))
