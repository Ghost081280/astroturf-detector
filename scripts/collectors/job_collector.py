"""Job Collector - Adzuna, USAJobs, Remotive APIs (replaces broken Craigslist scraper)"""
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus

class JobCollector:
    """Collects job postings from working APIs - NO more Craigslist scraping"""
    
    SEARCH_TERMS = ["protest", "rally", "canvasser", "petition", "grassroots", "organizer", "activist", "field coordinator", "campaign staff", "community outreach"]
    
    HIGH_SUSPICION = ["paid protest", "hold signs", "same day pay", "cash daily", "immediate start", "no experience"]
    MEDIUM_SUSPICION = ["protest", "rally", "canvass", "petition", "grassroots", "political", "campaign"]
    URGENCY_INDICATORS = ["urgent", "immediate", "today", "asap", "now hiring", "start today"]
    
    def __init__(self):
        self.adzuna_app_id = os.environ.get('ADZUNA_APP_ID')
        self.adzuna_app_key = os.environ.get('ADZUNA_APP_KEY')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AstroturfDetector/1.0'})
        self.calls_made = 0
    
    def collect(self, max_calls: int = 20) -> List[Dict[str, Any]]:
        all_jobs = []
        
        if self.adzuna_app_id and self.adzuna_app_key:
            print("  Fetching from Adzuna API...")
            adzuna_jobs = self._fetch_adzuna_jobs(max_calls // 3)
            all_jobs.extend(adzuna_jobs)
            print(f"    Found {len(adzuna_jobs)} Adzuna jobs")
        else:
            print("  Adzuna API not configured (set ADZUNA_APP_ID and ADZUNA_APP_KEY)")
        
        print("  Fetching from Remotive RSS...")
        remotive_jobs = self._fetch_remotive_jobs()
        all_jobs.extend(remotive_jobs)
        print(f"    Found {len(remotive_jobs)} Remotive jobs")
        
        print("  Fetching from USAJobs API...")
        usajobs = self._fetch_usajobs()
        all_jobs.extend(usajobs)
        print(f"    Found {len(usajobs)} USAJobs listings")
        
        seen_titles = set()
        unique_jobs = []
        for job in all_jobs:
            title_key = job.get('title', '')[:40].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_jobs.append(job)
        
        unique_jobs.sort(key=lambda x: x.get('suspicion_score', 0), reverse=True)
        
        if len(unique_jobs) < 5:
            print("  Adding baseline monitoring data...")
            unique_jobs.extend(self._get_baseline_monitoring_data())
        
        return unique_jobs[:100]
    
    def _fetch_adzuna_jobs(self, max_calls: int) -> List[Dict[str, Any]]:
        jobs = []
        base_url = "https://api.adzuna.com/v1/api/jobs/us/search/1"
        
        for term in self.SEARCH_TERMS[:max_calls]:
            try:
                params = {
                    'app_id': self.adzuna_app_id,
                    'app_key': self.adzuna_app_key,
                    'what': term,
                    'results_per_page': 10,
                    'content-type': 'application/json'
                }
                response = self.session.get(base_url, params=params, timeout=15)
                self.calls_made += 1
                
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get('results', []):
                        title = result.get('title', '')
                        description = result.get('description', '')
                        
                        job = {
                            'type': 'job_posting',
                            'source': 'adzuna',
                            'title': title,
                            'company': result.get('company', {}).get('display_name', 'Unknown'),
                            'city': result.get('location', {}).get('area', [''])[0] if result.get('location', {}).get('area') else '',
                            'state': '',
                            'url': result.get('redirect_url', ''),
                            'date': datetime.utcnow().isoformat() + 'Z',
                            'salary_min': result.get('salary_min'),
                            'salary_max': result.get('salary_max'),
                            'suspicion_score': self._calculate_suspicion(title, description),
                            'keywords': [term],
                            'is_monitoring_entry': False
                        }
                        jobs.append(job)
            except Exception as e:
                print(f"    Adzuna error for '{term}': {e}")
        
        return jobs
    
    def _fetch_remotive_jobs(self) -> List[Dict[str, Any]]:
        jobs = []
        feeds = [
            "https://remotive.com/remote-jobs/feed/community-management",
            "https://remotive.com/remote-jobs/feed/marketing"
        ]
        
        for feed_url in feeds:
            try:
                response = self.session.get(feed_url, timeout=15)
                if response.status_code == 200:
                    root = ET.fromstring(response.content)
                    for item in root.findall('.//item')[:10]:
                        title_elem = item.find('title')
                        link_elem = item.find('link')
                        desc_elem = item.find('description')
                        
                        if title_elem is not None:
                            title = title_elem.text or ''
                            description = desc_elem.text if desc_elem is not None else ''
                            
                            relevant = any(kw in title.lower() for kw in ['organizer', 'coordinator', 'community', 'outreach', 'campaign', 'advocacy'])
                            if relevant:
                                job = {
                                    'type': 'job_posting',
                                    'source': 'remotive',
                                    'title': title,
                                    'company': 'Remote Company',
                                    'city': 'Remote',
                                    'state': '',
                                    'url': link_elem.text if link_elem is not None else '',
                                    'date': datetime.utcnow().isoformat() + 'Z',
                                    'suspicion_score': self._calculate_suspicion(title, description or ''),
                                    'keywords': ['remote', 'organizer'],
                                    'is_monitoring_entry': False
                                }
                                jobs.append(job)
            except Exception as e:
                print(f"    Remotive error: {e}")
        
        return jobs
    
    def _fetch_usajobs(self) -> List[Dict[str, Any]]:
        jobs = []
        base_url = "https://data.usajobs.gov/api/search"
        
        search_terms = ["community outreach", "public affairs", "campaign"]
        
        for term in search_terms:
            try:
                params = {
                    'Keyword': term,
                    'ResultsPerPage': 10
                }
                headers = {
                    'Host': 'data.usajobs.gov',
                    'User-Agent': 'AstroturfDetector/1.0'
                }
                response = self.session.get(base_url, params=params, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get('SearchResult', {}).get('SearchResultItems', []):
                        matched = result.get('MatchedObjectDescriptor', {})
                        title = matched.get('PositionTitle', '')
                        
                        locations = matched.get('PositionLocation', [])
                        city = locations[0].get('CityName', '') if locations else ''
                        state = locations[0].get('CountrySubDivisionCode', '') if locations else ''
                        
                        job = {
                            'type': 'job_posting',
                            'source': 'usajobs',
                            'title': title,
                            'company': matched.get('OrganizationName', 'Federal Government'),
                            'city': city,
                            'state': state,
                            'url': matched.get('PositionURI', ''),
                            'date': datetime.utcnow().isoformat() + 'Z',
                            'suspicion_score': self._calculate_suspicion(title, matched.get('QualificationSummary', '')),
                            'keywords': [term],
                            'is_monitoring_entry': False
                        }
                        jobs.append(job)
            except Exception as e:
                print(f"    USAJobs error: {e}")
        
        return jobs
    
    def _calculate_suspicion(self, title: str, description: str) -> int:
        score = 0
        text = f"{title} {description}".lower()
        
        high_hits = sum(1 for kw in self.HIGH_SUSPICION if kw in text)
        score += min(high_hits * 25, 50)
        
        medium_hits = sum(1 for kw in self.MEDIUM_SUSPICION if kw in text)
        score += min(medium_hits * 10, 30)
        
        urgency_hits = sum(1 for kw in self.URGENCY_INDICATORS if kw in text)
        score += min(urgency_hits * 5, 20)
        
        return min(score, 100)
    
    def _get_baseline_monitoring_data(self) -> List[Dict[str, Any]]:
        return [
            {
                'type': 'monitoring_target',
                'source': 'baseline',
                'title': 'Monitoring: Craigslist gig postings',
                'company': 'Various',
                'city': 'Multiple Cities',
                'state': '',
                'url': 'https://craigslist.org',
                'date': datetime.utcnow().isoformat() + 'Z',
                'suspicion_score': 0,
                'keywords': ['protest', 'rally', 'canvasser'],
                'is_monitoring_entry': True
            },
            {
                'type': 'monitoring_target',
                'source': 'baseline',
                'title': 'Monitoring: Indeed political jobs',
                'company': 'Various',
                'city': 'Multiple Cities',
                'state': '',
                'url': 'https://indeed.com',
                'date': datetime.utcnow().isoformat() + 'Z',
                'suspicion_score': 0,
                'keywords': ['campaign', 'grassroots', 'organizer'],
                'is_monitoring_entry': True
            }
        ]

if __name__ == '__main__':
    collector = JobCollector()
    jobs = collector.collect(max_calls=10)
    print(f"\nCollected {len(jobs)} total jobs")
    for job in jobs[:5]:
        print(f"  - {job['title'][:50]}... (score: {job['suspicion_score']})")
