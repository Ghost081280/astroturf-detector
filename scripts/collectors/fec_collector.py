"""FEC Collector - Federal Election Commission Data"""
import os
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class FECCollector:
    BASE_URL = "https://api.open.fec.gov/v1"
    
    def __init__(self):
        self.api_key = os.environ.get('FEC_API_KEY', 'DEMO_KEY')
        self.calls_made = 0
        self.session = requests.Session()
    
    def collect(self, max_calls: int = 20) -> List[Dict[str, Any]]:
        results = []
        
        if self.calls_made < max_calls:
            results.extend(self._get_independent_expenditures())
        
        if self.calls_made < max_calls:
            results.extend(self._get_new_committees())
        
        return results
    
    def _get_independent_expenditures(self) -> List[Dict[str, Any]]:
        try:
            end = datetime.utcnow()
            start = end - timedelta(days=30)
            
            params = {
                'api_key': self.api_key,
                'min_date': start.strftime('%Y-%m-%d'),
                'max_date': end.strftime('%Y-%m-%d'),
                'per_page': 50,
                'sort': '-expenditure_date'
            }
            
            response = self.session.get(f"{self.BASE_URL}/schedules/schedule_e/", params=params, timeout=30)
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                return [{
                    'type': 'independent_expenditure',
                    'source': 'fec',
                    'committee_id': i.get('committee_id'),
                    'committee_name': i.get('committee', {}).get('name'),
                    'amount': i.get('expenditure_amount'),
                    'date': i.get('expenditure_date'),
                    'state': i.get('candidate_office_state')
                } for i in data.get('results', [])]
            
            return []
        except Exception as e:
            print(f"  FEC error: {e}")
            return []
    
    def _get_new_committees(self) -> List[Dict[str, Any]]:
        try:
            end = datetime.utcnow()
            start = end - timedelta(days=90)
            
            params = {
                'api_key': self.api_key,
                'min_first_file_date': start.strftime('%Y-%m-%d'),
                'committee_type': ['O', 'U', 'V', 'W'],
                'per_page': 50,
                'sort': '-first_file_date'
            }
            
            response = self.session.get(f"{self.BASE_URL}/committees/", params=params, timeout=30)
            self.calls_made += 1
            
            if response.status_code == 200:
                data = response.json()
                return [{
                    'type': 'new_committee',
                    'source': 'fec',
                    'committee_id': i.get('committee_id'),
                    'name': i.get('name'),
                    'committee_type': i.get('committee_type'),
                    'first_file_date': i.get('first_file_date'),
                    'state': i.get('state'),
                    'city': i.get('city')
                } for i in data.get('results', [])]
            
            return []
        except Exception as e:
            print(f"  FEC committees error: {e}")
            return []

if __name__ == '__main__':
    collector = FECCollector()
    data = collector.collect(max_calls=5)
    print(f"Collected {len(data)} FEC records")
