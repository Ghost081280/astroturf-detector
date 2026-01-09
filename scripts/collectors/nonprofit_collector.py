"""Nonprofit Collector - ProPublica API"""
import requests
from datetime import datetime
from typing import List, Dict, Any

class NonprofitCollector:
    BASE_URL = "https://projects.propublica.org/nonprofits/api/v2"
    SEARCH_TERMS = ['citizens for', 'americans for', 'action fund', 'voices for', 'coalition', 'alliance for', 'freedom', 'liberty', 'justice now', 'safe']
    TARGET_STATES = ['TX', 'CA', 'NY', 'FL', 'IL', 'PA', 'OH', 'GA', 'NC', 'MI', 'AZ', 'WA', 'CO', 'DC', 'VA', 'NJ', 'MA', 'MD', 'TN', 'IN']
    
    def __init__(self):
        self.calls_made = 0
        self.session = requests.Session()
    
    def collect(self, max_calls: int = 15) -> List[Dict[str, Any]]:
        results = []
        
        for term in self.SEARCH_TERMS:
            if self.calls_made >= max_calls:
                break
            orgs = self._search_organizations(term)
            for org in orgs:
                org['risk_score'] = self._calc_risk(org)
                org['sourceUrl'] = f"https://projects.propublica.org/nonprofits/organizations/{org.get('ein', '')}"
                if org['risk_score'] >= 30:
                    results.append(org)
        
        seen = set()
        unique = []
        for org in results:
            ein = org.get('ein')
            if ein and ein not in seen:
                seen.add(ein)
                unique.append(org)
        
        unique.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        return unique[:30]
    
    def _search_organizations(self, query: str) -> List[Dict[str, Any]]:
        try:
            params = {'q': query, 'c_code[id]': 4}
            response = self.session.get(f"{self.BASE_URL}/search.json", params=params, timeout=30)
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                orgs = []
                
                for org in data.get('organizations', [])[:20]:
                    state = org.get('state', '')
                    if state not in self.TARGET_STATES:
                        continue
                    
                    orgs.append({
                        'type': 'nonprofit',
                        'source': 'propublica',
                        'ein': org.get('ein'),
                        'name': org.get('name'),
                        'city': org.get('city'),
                        'state': state,
                        'ntee_code': org.get('ntee_code'),
                        'ruling_date': org.get('ruling_date'),
                        'total_revenue': org.get('income_amount'),
                        'total_assets': org.get('asset_amount')
                    })
                
                return orgs
            return []
        except Exception as e:
            print(f"  ProPublica error: {e}")
            return []
    
    def _calc_risk(self, org: Dict[str, Any]) -> int:
        score = 0
        name = org.get('name', '')
        state = org.get('state', '')
        
        words = name.split()
        if len(words) == 3:
            score += 15
        
        patterns = ['citizens for', 'americans for', 'freedom', 'liberty', 'action fund', 'voices for']
        for p in patterns:
            if p in name.lower():
                score += 10
                break
        
        ruling = org.get('ruling_date')
        if ruling:
            try:
                year = int(str(ruling)[:4])
                if datetime.utcnow().year - year <= 2:
                    score += 25
                elif datetime.utcnow().year - year <= 5:
                    score += 15
            except:
                pass
        
        if state == 'DE':
            score += 15
        
        if state in ['TX', 'FL', 'OH', 'PA', 'GA', 'AZ', 'NC', 'MI']:
            score += 5
        
        return min(score, 100)

if __name__ == '__main__':
    collector = NonprofitCollector()
    data = collector.collect(max_calls=5)
    print(f"Collected {len(data)} orgs")
