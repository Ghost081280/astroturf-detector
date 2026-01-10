"""ProPublica Campaign Finance Collector - Enhanced PAC and Committee Tracking"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class ProPublicaCollector:
    """
    Collect campaign finance data from ProPublica's Campaign Finance API
    Free API, updated daily, covers FEC filings
    Docs: https://propublica.github.io/campaign-finance-api-docs/
    """
    
    BASE_URL = "https://api.propublica.org/campaign-finance/v1"
    
    # Keywords that suggest astroturf or dark money operations
    SUSPICIOUS_KEYWORDS = [
        'citizens', 'americans', 'freedom', 'liberty', 'voices', 
        'action', 'future', 'progress', 'prosperity', 'values',
        'families', 'coalition', 'alliance', 'leadership', 'grassroots'
    ]
    
    def __init__(self):
        self.api_key = os.environ.get('PROPUBLICA_API_KEY')
        self.session = requests.Session()
        if self.api_key:
            self.session.headers.update({'X-API-Key': self.api_key})
        self.calls_made = 0
    
    def collect(self, max_calls: int = 10) -> List[Dict[str, Any]]:
        """Collect suspicious committee data from ProPublica"""
        if not self.api_key:
            print("    ProPublica: No API key (set PROPUBLICA_API_KEY), skipping")
            return []
        
        results = []
        
        # Get current election cycle (even years)
        current_year = datetime.utcnow().year
        cycle = current_year if current_year % 2 == 0 else current_year - 1
        
        print(f"    Searching ProPublica for {cycle} cycle...")
        
        # 1. Get recent independent expenditure committees (Super PACs)
        if self.calls_made < max_calls:
            ie_committees = self._get_independent_expenditure_committees(cycle)
            results.extend(ie_committees)
        
        # 2. Get recently formed committees
        if self.calls_made < max_calls:
            new_committees = self._get_new_committees(cycle)
            results.extend(new_committees)
        
        # 3. Search for committees with suspicious names
        for keyword in self.SUSPICIOUS_KEYWORDS[:max_calls - self.calls_made]:
            if self.calls_made >= max_calls:
                break
            committees = self._search_committees(keyword, cycle)
            results.extend(committees)
        
        # Deduplicate
        seen = set()
        unique = []
        for item in results:
            cid = item.get('committee_id')
            if cid and cid not in seen:
                seen.add(cid)
                unique.append(item)
        
        # Sort by risk score
        unique.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        return unique[:30]
    
    def _get_independent_expenditure_committees(self, cycle: int) -> List[Dict]:
        """Get Super PACs making independent expenditures"""
        results = []
        try:
            url = f"{self.BASE_URL}/{cycle}/committees/super.json"
            response = self.session.get(url, timeout=30)
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                for committee in data.get('results', [])[:20]:
                    name = committee.get('name', '')
                    results.append({
                        'type': 'super_pac',
                        'source': 'propublica',
                        'committee_id': committee.get('id'),
                        'name': name,
                        'sponsor_name': committee.get('sponsor_name'),
                        'total_receipts': committee.get('total_receipts'),
                        'total_disbursements': committee.get('total_disbursements'),
                        'independent_expenditures': committee.get('independent_expenditures'),
                        'cycle': cycle,
                        'risk_score': self._calculate_risk(name, committee),
                        'sourceUrl': f"https://www.fec.gov/data/committee/{committee.get('id')}/",
                        'date': datetime.utcnow().isoformat() + 'Z'
                    })
            
        except Exception as e:
            print(f"      ProPublica Super PAC error: {e}")
        
        return results
    
    def _get_new_committees(self, cycle: int) -> List[Dict]:
        """Get recently formed committees"""
        results = []
        try:
            url = f"{self.BASE_URL}/{cycle}/committees/new.json"
            response = self.session.get(url, timeout=30)
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                for committee in data.get('results', [])[:15]:
                    name = committee.get('name', '')
                    results.append({
                        'type': 'new_committee',
                        'source': 'propublica',
                        'committee_id': committee.get('id'),
                        'name': name,
                        'city': committee.get('city'),
                        'state': committee.get('state'),
                        'committee_type': committee.get('committee_type'),
                        'designation': committee.get('designation'),
                        'filing_frequency': committee.get('filing_frequency'),
                        'cycle': cycle,
                        'risk_score': self._calculate_risk(name, committee, is_new=True),
                        'sourceUrl': f"https://www.fec.gov/data/committee/{committee.get('id')}/",
                        'date': datetime.utcnow().isoformat() + 'Z'
                    })
            
        except Exception as e:
            print(f"      ProPublica new committees error: {e}")
        
        return results
    
    def _search_committees(self, query: str, cycle: int) -> List[Dict]:
        """Search for committees by name"""
        results = []
        try:
            url = f"{self.BASE_URL}/{cycle}/committees/search.json"
            params = {'query': query}
            response = self.session.get(url, params=params, timeout=30)
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                for committee in data.get('results', [])[:10]:
                    name = committee.get('name', '')
                    results.append({
                        'type': 'political_committee',
                        'source': 'propublica',
                        'committee_id': committee.get('id'),
                        'name': name,
                        'city': committee.get('city'),
                        'state': committee.get('state'),
                        'party': committee.get('party'),
                        'committee_type': committee.get('committee_type'),
                        'cycle': cycle,
                        'search_term': query,
                        'risk_score': self._calculate_risk(name, committee),
                        'sourceUrl': f"https://www.fec.gov/data/committee/{committee.get('id')}/",
                        'date': datetime.utcnow().isoformat() + 'Z'
                    })
            
        except Exception as e:
            print(f"      ProPublica search error for '{query}': {e}")
        
        return results
    
    def _calculate_risk(self, name: str, committee: dict, is_new: bool = False) -> int:
        """Calculate risk score for astroturf indicators"""
        score = 20  # Base score
        name_lower = name.lower()
        
        # New committee bonus
        if is_new:
            score += 25
        
        # Suspicious name patterns
        patterns_found = 0
        for keyword in self.SUSPICIOUS_KEYWORDS:
            if keyword in name_lower:
                patterns_found += 1
        
        if patterns_found >= 2:
            score += 25
        elif patterns_found == 1:
            score += 10
        
        # Three-word names (common astroturf pattern)
        words = name.split()
        if 3 <= len(words) <= 4:
            score += 15
        
        # Vague purpose indicators
        vague_terms = ['fund', 'action', 'pac', 'committee for', 'committee to']
        for term in vague_terms:
            if term in name_lower:
                score += 10
                break
        
        # Independent expenditure only (Super PAC)
        if committee.get('committee_type') in ['O', 'U', 'V', 'W']:
            score += 15
        
        # High spending with generic name
        total = committee.get('total_disbursements') or 0
        if total > 1000000 and patterns_found >= 1:
            score += 15
        
        # Delaware registration (tax haven)
        if committee.get('state') == 'DE':
            score += 10
        
        return min(score, 100)


if __name__ == '__main__':
    collector = ProPublicaCollector()
    data = collector.collect(max_calls=5)
    print(f"Collected {len(data)} committees")
    for item in data[:5]:
        print(f"  - {item['name'][:50]}... (risk: {item['risk_score']})")
