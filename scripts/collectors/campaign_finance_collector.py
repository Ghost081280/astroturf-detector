"""Campaign Finance Collector - ProPublica + FEC PAC Search"""
import os
import requests
from datetime import datetime
from typing import List, Dict, Any

class CampaignFinanceCollector:
    """Collect dark money and campaign finance data from free APIs"""
    
    SUSPICIOUS_PATTERNS = [
        "citizens for", "americans for", "freedom fund", "liberty",
        "voices for", "coalition for", "alliance for", "action fund",
        "grassroots", "peoples", "families for", "committee for",
        "future of", "progress", "prosperity"
    ]
    
    def __init__(self):
        self.fec_api_key = os.environ.get('FEC_API_KEY', 'DEMO_KEY')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AstroturfDetector/1.0'})
        self.calls_made = 0
    
    def collect(self, max_calls: int = 15) -> List[Dict[str, Any]]:
        results = []
        
        print("    Fetching ProPublica data...")
        propublica_data = self._fetch_propublica_committees()
        results.extend(propublica_data)
        
        print("    Searching FEC for suspicious PACs...")
        fec_pacs = self._search_fec_committees()
        results.extend(fec_pacs)
        
        seen = set()
        unique = []
        for org in results:
            name_key = org.get('name', '')[:30].lower()
            if name_key and name_key not in seen:
                seen.add(name_key)
                unique.append(org)
        
        unique.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        return unique[:40]
    
    def _fetch_propublica_committees(self) -> List[Dict[str, Any]]:
        results = []
        try:
            url = "https://projects.propublica.org/itemizer/api/v1/recent_filings"
            response = self.session.get(url, timeout=30)
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                for filing in data.get('results', [])[:20]:
                    committee_name = filing.get('committee_name', '')
                    
                    results.append({
                        'type': 'pac_filing',
                        'source': 'propublica',
                        'name': committee_name,
                        'committee_id': filing.get('committee_id', ''),
                        'total_receipts': filing.get('total_receipts'),
                        'total_disbursements': filing.get('total_disbursements'),
                        'cash_on_hand': filing.get('cash_on_hand'),
                        'coverage_end_date': filing.get('coverage_end_date'),
                        'risk_score': self._calculate_risk(committee_name),
                        'date': datetime.utcnow().isoformat() + 'Z',
                        'sourceUrl': f"https://projects.propublica.org/itemizer/committee/{filing.get('committee_id', '')}",
                        'state': '',
                        'city': ''
                    })
            else:
                print(f"      ProPublica returned status {response.status_code}")
        except Exception as e:
            print(f"      ProPublica error: {e}")
        
        return results
    
    def _search_fec_committees(self) -> List[Dict[str, Any]]:
        results = []
        search_terms = ['citizens for', 'americans for', 'freedom', 'liberty fund', 'action fund', 'voices for']
        
        for term in search_terms[:5]:
            try:
                params = {
                    'api_key': self.fec_api_key,
                    'q': term,
                    'committee_type': ['O', 'U', 'V', 'W'],
                    'per_page': 10,
                    'sort': '-first_file_date'
                }
                
                response = self.session.get(
                    "https://api.open.fec.gov/v1/committees/",
                    params=params,
                    timeout=30
                )
                self.calls_made += 1
                
                if response.status_code == 200:
                    data = response.json()
                    for committee in data.get('results', []):
                        name = committee.get('name', '')
                        
                        results.append({
                            'type': 'super_pac',
                            'source': 'fec',
                            'name': name,
                            'committee_id': committee.get('committee_id'),
                            'committee_type': committee.get('committee_type'),
                            'designation': committee.get('designation'),
                            'first_file_date': committee.get('first_file_date'),
                            'state': committee.get('state', ''),
                            'city': committee.get('city', ''),
                            'risk_score': self._calculate_risk(name),
                            'date': datetime.utcnow().isoformat() + 'Z',
                            'sourceUrl': f"https://www.fec.gov/data/committee/{committee.get('committee_id')}/"
                        })
                else:
                    print(f"      FEC returned status {response.status_code} for '{term}'")
            except Exception as e:
                print(f"      FEC search error for '{term}': {e}")
        
        return results
    
    def _calculate_risk(self, name: str) -> int:
        score = 25
        name_lower = name.lower()
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in name_lower:
                score += 15
                break
        
        words = name.split()
        if 3 <= len(words) <= 4:
            score += 10
        
        vague = ['freedom', 'liberty', 'prosperity', 'progress', 'future', 'america', 'american']
        for word in vague:
            if word in name_lower:
                score += 10
                break
        
        if 'fund' in name_lower or 'action' in name_lower:
            score += 10
        
        if name_lower.startswith('committee for') or name_lower.startswith('committee to'):
            score += 15
        
        return min(score, 100)

if __name__ == '__main__':
    collector = CampaignFinanceCollector()
    data = collector.collect(max_calls=10)
    print(f"Collected {len(data)} organizations")
