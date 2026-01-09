"""Nonprofit Collector - IRS 990 Data via ProPublica API"""

import json
import requests
from datetime import datetime
from typing import List, Dict, Any
import re

class NonprofitCollector:
    """Collects 501(c)(4) organization data from ProPublica Nonprofit Explorer."""
    
    BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"
    
    NAME_PATTERNS = [
        r'^[A-Z][a-z]+ [A-Z][a-z]+ [A-Z][a-z]+$',
        r'(Citizens|Americans|People|Families|Voters) (For|Against|United|First)',
        r'(Safe|Freedom|Liberty|Justice|Action|Voice|Voices)',
        r'(Now|Today|Tomorrow|Future|Forward)',
        r'(Coalition|Alliance|Council|Committee|Fund)',
    ]
    
    SEARCH_TERMS = [
        'citizens for',
        'americans for', 
        'action fund',
        'voices for',
        'coalition',
        'alliance for',
        'freedom',
        'liberty',
        'justice now',
        'safe'
    ]
    
    TARGET_STATES = ['TX', 'CA', 'NY', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI', 'AZ', 'WA', 'CO', 'DC', 'VA']
    
    def __init__(self):
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AstroturfDetector/1.0 (Research Project)'
        })
    
    def collect(self, max_calls: int = 15) -> List[Dict[str, Any]]:
        """Collect 501(c)(4) organizations from ProPublica."""
        results = []
        
        for term in self.SEARCH_TERMS:
            if self.calls_made >= max_calls:
                break
            orgs = self._search_organizations(term)
            for org in orgs:
                risk_score = self._calculate_risk_score(org)
                org['risk_score'] = risk_score
                org['sourceUrl'] = f"https://projects.propublica.org/nonprofits/organizations/{org.get('ein', '')}"
                if risk_score >= 30:
                    results.append(org)
        
        seen_eins = set()
        unique_results = []
        for org in results:
            ein = org.get('ein')
            if ein and ein not in seen_eins:
                seen_eins.add(ein)
                unique_results.append(org)
        
        unique_results.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        return unique_results[:30]
    
    def _search_organizations(self, query: str) -> List[Dict[str, Any]]:
        """Search ProPublica API for organizations."""
        try:
            params = {
                'q': query,
                'c_code[id]': 4
            }
            
            response = self.session.get(
                f"{self.BASE_URL}/search.json",
                params=params,
                timeout=30
            )
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                organizations = []
                
                for org in data.get('organizations', [])[:20]:
                    state = org.get('state', '')
                    if state not in self.TARGET_STATES:
                        continue
                    
                    organizations.append({
                        'type': 'nonprofit',
                        'source': 'propublica',
                        'ein': org.get('ein'),
                        'name': org.get('name'),
                        'city': org.get('city'),
                        'state': org.get('state'),
                        'ntee_code': org.get('ntee_code'),
                        'subsection_code': org.get('subsection_code'),
                        'ruling_date': org.get('ruling_date'),
                        'total_revenue': org.get('income_amount'),
                        'total_assets': org.get('asset_amount'),
                        'tax_period': org.get('tax_period')
                    })
                
                return organizations
            return []
            
        except Exception as e:
            print(f"  Error searching organizations for '{query}': {e}")
            return []
    
    def _calculate_risk_score(self, org: Dict[str, Any]) -> int:
        """Calculate risk score based on astroturf indicators (0-100)."""
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
                    score += 25
                elif current_year - ruling_year <= 5:
                    score += 15
            except:
                pass
        
        if state == 'DE':
            score += 15
        
        revenue = org.get('total_revenue', 0) or 0
        if revenue > 1000000 and len(words) == 3:
            score += 15
        
        if state in ['TX', 'FL', 'OH', 'PA', 'GA', 'AZ', 'NC', 'MI']:
            score += 5
        
        return min(score, 100)


if __name__ == '__main__':
    collector = NonprofitCollector()
    data = collector.collect(max_calls=5)
    print(f"Collected {len(data)} organizations")
    for org in data[:5]:
        print(f"  - {org['name']} ({org['state']}) - Risk: {org['risk_score']}%")
