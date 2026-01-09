"""Campaign Finance Collector - FEC Committee Search for Suspicious PACs"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class CampaignFinanceCollector:
    """Collect campaign finance data from FEC API"""
    
    FEC_BASE = "https://api.open.fec.gov/v1"
    
    # Suspicious name patterns common in astroturf organizations
    SUSPICIOUS_PATTERNS = [
        "citizens for", "americans for", "freedom fund", "liberty",
        "voices for", "coalition for", "alliance for", "action fund",
        "grassroots", "peoples", "families for", "committee for",
        "future of", "progress", "prosperity"
    ]
    
    def __init__(self):
        self.api_key = os.environ.get('FEC_API_KEY', 'DEMO_KEY')
        self.session = requests.Session()
        self.calls_made = 0
    
    def collect(self, max_calls: int = 10) -> List[Dict[str, Any]]:
        """Collect suspicious committee data from FEC"""
        results = []
        
        print("    Searching FEC for suspicious PACs...")
        
        # Search for committees with suspicious name patterns
        for pattern in self.SUSPICIOUS_PATTERNS[:max_calls]:
            if self.calls_made >= max_calls:
                break
            
            committees = self._search_committees(pattern)
            results.extend(committees)
            self.calls_made += 1
        
        # Deduplicate by committee ID
        seen = set()
        unique = []
        for item in results:
            cid = item.get('committee_id')
            if cid and cid not in seen:
                seen.add(cid)
                unique.append(item)
        
        # Sort by risk score
        unique.sort(key=lambda x: x.get('risk_score', 0), reverse=True)
        
        return unique[:40]
    
    def _search_committees(self, query: str) -> List[Dict[str, Any]]:
        """Search FEC for committees matching query"""
        try:
            params = {
                'api_key': self.api_key,
                'q': query,
                'committee_type': ['O', 'U', 'V', 'W'],  # Outside groups, Super PACs
                'per_page': 20,
                'sort': '-first_file_date'
            }
            
            response = self.session.get(
                f"{self.FEC_BASE}/committees/",
                params=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = []
                
                for committee in data.get('results', []):
                    name = committee.get('name', '')
                    
                    results.append({
                        'type': 'political_committee',
                        'source': 'fec',
                        'committee_id': committee.get('committee_id'),
                        'name': name,
                        'city': committee.get('city'),
                        'state': committee.get('state'),
                        'committee_type': committee.get('committee_type'),
                        'designation': committee.get('designation'),
                        'first_file_date': committee.get('first_file_date'),
                        'risk_score': self._calculate_risk(name, committee),
                        'sourceUrl': f"https://www.fec.gov/data/committee/{committee.get('committee_id')}/",
                        'date': datetime.utcnow().isoformat() + 'Z'
                    })
                
                return results
            return []
            
        except Exception as e:
            print(f"      FEC search error for '{query}': {e}")
            return []
    
    def _calculate_risk(self, name: str, committee: dict) -> int:
        """Calculate risk score based on committee characteristics"""
        score = 25  # Base score for matching suspicious pattern
        name_lower = name.lower()
        
        # Additional suspicious patterns
        for pattern in self.SUSPICIOUS_PATTERNS:
            if pattern in name_lower:
                score += 15
                break
        
        # Three-word names
        words = name.split()
        if len(words) == 3:
            score += 10
        
        # Vague purpose words
        vague = ['freedom', 'liberty', 'prosperity', 'progress', 'future', 'american']
        for word in vague:
            if word in name_lower:
                score += 10
                break
        
        # "Fund" or "Action" in name
        if 'fund' in name_lower or 'action' in name_lower:
            score += 10
        
        # "Committee for" or "Committee to"
        if 'committee for' in name_lower or 'committee to' in name_lower:
            score += 15
        
        # Recent formation (within last 2 years)
        first_file = committee.get('first_file_date')
        if first_file:
            try:
                file_date = datetime.strptime(first_file, '%Y-%m-%d')
                if (datetime.utcnow() - file_date).days < 730:
                    score += 20
            except:
                pass
        
        return min(score, 100)


if __name__ == '__main__':
    collector = CampaignFinanceCollector()
    data = collector.collect(max_calls=3)
    print(f"Collected {len(data)} campaign finance records")
    for item in data[:5]:
        print(f"  - {item['name'][:50]}... (risk: {item['risk_score']})")
