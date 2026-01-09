"""Nonprofit Collector - IRS 990 Data via ProPublica"""

import json
import requests
from datetime import datetime
from typing import List, Dict, Any
import re

class NonprofitCollector:
    BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"
    NAME_PATTERNS = [
        r'^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$',
        r'(Citizens|Americans|People|Families) (For|Against|United)',
        r'(Safe|Freedom|Liberty|Justice|Action|Voice)',
        r'(Now|Today|Tomorrow|Future|Forward)',
    ]
    
    def __init__(self):
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AstroturfDetector/1.0'})
    
    def collect(self, max_calls: int = 15) -> List[Dict[str, Any]]:
        results = []
        search_terms = ['citizens', 'americans for', 'action', 'voices', 'coalition']
        for term in search_terms:
            if self.calls_made >= max_calls:
                break
            orgs = self._search_organizations(term)
            for org in orgs:
                risk_score = self._calculate_risk_score(org)
                org['risk_score'] = risk_score
                if risk_score >= 30:
                    results.append(org)
        seen_eins = set()
        unique_results = []
        for org in results:
            if org.get('ein') not in seen_eins:
                seen_eins.add(org.get('ein'))
                unique_results.append(org)
        return unique_results
    
    def _search_organizations(self, query: str) -> List[Dict[str, Any]]:
        try:
            params = {'q': query, 'c_code[id]': 4}
            response = self.session.get(f"{self.BASE_URL}/search.json", params=params, timeout=30)
            self.calls_made += 1
            if response.status_code == 200:
                data = response.json()
                return [{
                    'type': 'nonprofit', 'source': 'propublica',
                    'ein': org.get('ein'), 'name': org.get('name'),
                    'city': org.get('city'), 'state': org.get('state'),
                    'ntee_code': org.get('ntee_code'),
                    'subsection_code': org.get('subsection_code'),
                    'ruling_date': org.get('ruling_date'),
                    'total_revenue': org.get('income_amount'),
                    'total_assets': org.get('asset_amount')
                } for org in data.get('organizations', [])[:20]]
            return []
        except Exception as e:
            print(f"  Error searching organizations: {e}")
            return []
    
    def _calculate_risk_score(self, org: Dict[str, Any]) -> int:
        score = 0
        name = org.get('name', '')
        state = org.get('state', '')
        ruling_date = org.get('ruling_date')
        words = name.split()
        if len(words) == 3:
            score += 15
        for pattern in self.NAME_PATTERNS:
            if re.search(pattern, name, re.IGNORECASE):
                score += 10
                break
        if ruling_date:
            try:
                ruling_year = int(str(ruling_date)[:4])
                current_year = datetime.utcnow().year
                if current_year - ruling_year <= 2:
                    score += 20
                elif current_year - ruling_year <= 5:
                    score += 10
            except:
                pass
        if state == 'DE':
            score += 10
        revenue = org.get('total_revenue', 0) or 0
        if revenue > 1000000 and len(words) == 3:
            score += 15
        return min(score, 100)

if __name__ == '__main__':
    collector = NonprofitCollector()
    data = collector.collect(max_calls=5)
    print(f"Collected {len(data)} organizations")
