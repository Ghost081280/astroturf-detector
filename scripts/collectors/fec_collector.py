"""FEC Collector - Federal Election Commission Data"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any

class FECCollector:
    BASE_URL = "https://api.open.fec.gov/v1"
    
    def __init__(self):
        self.api_key = os.environ.get('FEC_API_KEY', 'DEMO_KEY')
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AstroturfDetector/1.0'})
    
    def collect(self, max_calls: int = 20) -> List[Dict[str, Any]]:
        results = []
        if self.calls_made < max_calls:
            results.extend(self._get_independent_expenditures())
        if self.calls_made < max_calls:
            results.extend(self._get_new_committees())
        return results
    
    def _get_independent_expenditures(self) -> List[Dict[str, Any]]:
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            params = {
                'api_key': self.api_key,
                'min_date': start_date.strftime('%Y-%m-%d'),
                'max_date': end_date.strftime('%Y-%m-%d'),
                'per_page': 50, 'sort': '-expenditure_date'
            }
            response = self.session.get(f"{self.BASE_URL}/schedules/schedule_e/", params=params, timeout=30)
            self.calls_made += 1
            if response.status_code == 200:
                data = response.json()
                return [{
                    'type': 'independent_expenditure', 'source': 'fec',
                    'committee_id': item.get('committee_id'),
                    'committee_name': item.get('committee', {}).get('name'),
                    'amount': item.get('expenditure_amount'),
                    'date': item.get('expenditure_date'),
                    'candidate_name': item.get('candidate_name'),
                    'support_oppose': item.get('support_oppose_indicator'),
                    'purpose': item.get('expenditure_description'),
                    'payee': item.get('payee_name'),
                    'state': item.get('candidate_office_state')
                } for item in data.get('results', [])]
            return []
        except Exception as e:
            print(f"  Error fetching independent expenditures: {e}")
            return []
    
    def _get_new_committees(self) -> List[Dict[str, Any]]:
        try:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=90)
            params = {
                'api_key': self.api_key,
                'min_first_file_date': start_date.strftime('%Y-%m-%d'),
                'committee_type': ['O', 'U', 'V', 'W'],
                'per_page': 50, 'sort': '-first_file_date'
            }
            response = self.session.get(f"{self.BASE_URL}/committees/", params=params, timeout=30)
            self.calls_made += 1
            if response.status_code == 200:
                data = response.json()
                return [{
                    'type': 'new_committee', 'source': 'fec',
                    'committee_id': item.get('committee_id'),
                    'name': item.get('name'),
                    'committee_type': item.get('committee_type'),
                    'designation': item.get('designation'),
                    'first_file_date': item.get('first_file_date'),
                    'state': item.get('state'), 'city': item.get('city'),
                    'treasurer_name': item.get('treasurer_name'),
                    'organization_type': item.get('organization_type')
                } for item in data.get('results', [])]
            return []
        except Exception as e:
            print(f"  Error fetching new committees: {e}")
            return []

if __name__ == '__main__':
    collector = FECCollector()
    data = collector.collect(max_calls=5)
    print(f"Collected {len(data)} records")
