"""Job Collector - Adzuna, USAJobs, Remotive APIs"""
import os
import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus

class JobCollector:
    """Collects job postings from working APIs"""
    
    # More specific search terms to avoid false positives like "Protestant"
    SEARCH_TERMS = [
        "paid protest",
        "rally attendee",
        "canvasser political",
        "petition signature",
        "grassroots organizer",
        "political activist",
        "campaign field",
        "community organizer political",
        "mobilization coordinator",
        "advocacy campaign"
    ]
    
    # Suspicion scoring keywords
    HIGH_SUSPICION = [
        "paid protest", "hold signs", "same day pay", "cash daily", 
        "immediate start", "no experience needed", "paid rally",
        "paid attendee", "crowd hire", "event attendee paid"
    ]
    MEDIUM_SUSPICION = [
        "canvass", "petition", "grassroots", "political campaign",
        "mobilize", "activist", "advocacy", "field organizer"
    ]
    URGENCY_INDICATORS = ["urgent", "immediate", "today", "asap", "now hiring", "start today"]
    
    # Words that indicate FALSE POSITIVES - skip these jobs
    FALSE_POSITIVE_TERMS = [
        "protestant", "chaplain", "pastor", "minister", "church",
        "rabbi", "imam", "religious", "clergy", "worship",
        "senior living", "nursing", "healthcare", "medical",
        "software protest", "test protest"  # tech jobs
    ]
    
    def __init__(self):
        self.adzuna_app_id = os.environ.get('ADZUNA_APP_ID')
        self.adzuna_app_key = os.environ.get('ADZUNA_APP_KEY')
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'AstroturfDetector/1.0'})
        self.calls_made = 0
    
    def collect(self, max_calls: int = 20) -> List[Dict[str, Any]]:
        """Collect jobs from all available APIs"""
        all_jobs = []
        
        # 1. Adzuna API (if credentials available)
        if self.adzuna_app_id and self.adzuna_app_key:
            print("  Fetching from Adzuna API...")
            adzuna_jobs = self._fetch_adzuna_jobs(max_calls // 2)
            all_jobs.extend(adzuna_jobs)
            print(f"    Found {len(adzuna_jobs)} Adzuna jobs")
        else:
            print("  Adzuna API not configured (set ADZUNA_APP_ID and ADZUNA_APP_KEY)")
        
        # 2. Remotive RSS (always works, no auth)
        print("  Fetching from Remotive RSS...")
        remotive_jobs = self._fetch_remotive_jobs()
        all_jobs.extend(remotive_jobs)
        print(f"    Found {len(remotive_jobs)} Remotive jobs")
        
        # 3. USAJobs API (always works, no auth for basic)
        print("  Fetching from USAJobs API...")
        usajobs = self._fetch_usajobs()
        all_jobs.extend(usajobs)
        print(f"    Found {len(usajobs)} USAJobs listings")
        
        # Filter out false positives
        filtered_jobs = [j for j in all_jobs if not self._is_false_positive(j)]
        
        # Deduplicate by title similarity
        seen_titles = set()
        unique_jobs = []
        for job in filtered_jobs:
            title_key = job.get('title', '')[:40].lower()
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_jobs.append(job)
        
        # Sort by suspicion score
        unique_jobs.sort(key=lambda x: x.get('suspicion_score', 0), reverse=True)
        
        return unique_jobs[:100]
    
    def _is_false_positive(self, job: dict) -> bool:
        """Check if job is a false positive (religious, healthcare, etc.)"""
        title = job.get('title', '').lower()
        company = job.get('company', '').lower()
        
        for term in self.FALSE_POSITIVE_TERMS:
            if term in title or term in company:
                return True
        return False
    
    def _fetch_adzuna_jobs(self, max_calls: int) -> List[Dict[str, Any]]:
        """Fetch from Adzuna Job Search API"""
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
                        
                        # Skip if false positive
                        if self._is_false_positive({'title': title, 'company': result.get('company', {}).get('display_name', '')}):
                            continue
                        
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
        """Fetch from Remotive RSS feed (no auth required)"""
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
                            
                            # Only include if relevant keywords AND not false positive
                            relevant = any(kw in title.lower() for kw in ['organizer', 'coordinator', 'community', 'outreach', 'campaign', 'advocacy', 'mobiliz'])
                            if relevant and not self._is_false_positive({'title': title, 'company': ''}):
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
        """Fetch from USAJobs API (government jobs)"""
        jobs = []
        base_url = "https://data.usajobs.gov/api/search"
        
        search_terms = ["community organizer", "public affairs campaign", "grassroots"]
        
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
                        
                        # Skip false positives
                        if self._is_false_positive({'title': title, 'company': matched.get('OrganizationName', '')}):
                            continue
                        
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
        """Calculate suspicion score 0-100"""
        score = 0
        text = f"{title} {description}".lower()
        
        # High suspicion keywords (+25 each, max 50)
        high_hits = sum(1 for kw in self.HIGH_SUSPICION if kw in text)
        score += min(high_hits * 25, 50)
        
        # Medium suspicion keywords (+10 each, max 30)
        medium_hits = sum(1 for kw in self.MEDIUM_SUSPICION if kw in text)
        score += min(medium_hits * 10, 30)
        
        # Urgency indicators (+5 each, max 20)
        urgency_hits = sum(1 for kw in self.URGENCY_INDICATORS if kw in text)
        score += min(urgency_hits * 5, 20)
        
        return min(score, 100)


if __name__ == '__main__':
    collector = JobCollector()
    jobs = collector.collect(max_calls=10)
    print(f"\nCollected {len(jobs)} total jobs")
    for job in jobs[:5]:
        print(f"  - {job['title'][:50]}... (score: {job['suspicion_score']})")
