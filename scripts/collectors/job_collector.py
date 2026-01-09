"""Job Collector - Employment Listing Aggregator"""

import json
import requests
from datetime import datetime
from typing import List, Dict, Any

class JobCollector:
    SUSPICIOUS_KEYWORDS = ['paid protest', 'paid protester', 'protest organizer', 'rally organizer', 'demonstration', 'activist for hire', 'crowd hire', 'event actor', 'political actor']
    LEGITIMATE_KEYWORDS = ['community organizer', 'canvasser', 'field organizer', 'grassroots organizer', 'campaign staff', 'advocacy']
    
    def __init__(self, keywords: List[str] = None, cities: List[str] = None):
        self.keywords = keywords or self.LEGITIMATE_KEYWORDS
        self.cities = cities or []
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AstroturfDetector/1.0'})
    
    def collect(self, max_calls: int = 20) -> List[Dict[str, Any]]:
        results = []
        for city in self.cities:
            if self.calls_made >= max_calls:
                break
            trend_data = self._get_city_trends(city)
            if trend_data:
                results.append(trend_data)
        keyword_trends = self._analyze_keyword_trends()
        if keyword_trends:
            results.extend(keyword_trends)
        return results
    
    def _get_city_trends(self, city: str) -> Dict[str, Any]:
        self.calls_made += 1
        return {
            'type': 'job_trend', 'source': 'aggregated', 'city': city,
            'date': datetime.utcnow().isoformat() + 'Z',
            'keywords_tracked': self.keywords,
            'metrics': {'total_listings': 0, 'week_over_week_change': 0, 'suspicious_listings': 0, 'avg_pay_offered': None},
            'notable_postings': []
        }
    
    def _analyze_keyword_trends(self) -> List[Dict[str, Any]]:
        results = []
        for keyword in self.SUSPICIOUS_KEYWORDS[:5]:
            self.calls_made += 1
            results.append({
                'type': 'keyword_trend', 'source': 'aggregated', 'keyword': keyword,
                'date': datetime.utcnow().isoformat() + 'Z', 'is_suspicious': True,
                'metrics': {'current_count': 0, 'baseline_count': 0, 'percent_change': 0, 'top_cities': []}
            })
        return results
    
    def detect_spike(self, historical_data: List[Dict], current_data: Dict) -> Dict[str, Any]:
        if not historical_data:
            return {'is_spike': False, 'confidence': 0}
        historical_counts = [d.get('metrics', {}).get('total_listings', 0) for d in historical_data]
        if not historical_counts:
            return {'is_spike': False, 'confidence': 0}
        avg = sum(historical_counts) / len(historical_counts)
        std_dev = (sum((x - avg) ** 2 for x in historical_counts) / len(historical_counts)) ** 0.5
        current_count = current_data.get('metrics', {}).get('total_listings', 0)
        if std_dev > 0:
            z_score = (current_count - avg) / std_dev
            is_spike = z_score > 2
            confidence = min(int(z_score * 25), 100) if z_score > 0 else 0
        else:
            is_spike = current_count > avg * 1.5
            confidence = 50 if is_spike else 0
            z_score = None
        return {'is_spike': is_spike, 'confidence': confidence, 'baseline_avg': avg, 'current_value': current_count, 'z_score': z_score}

if __name__ == '__main__':
    collector = JobCollector(cities=['Washington DC', 'Dallas', 'Los Angeles'])
    data = collector.collect(max_calls=10)
    print(f"Collected {len(data)} trend records")
