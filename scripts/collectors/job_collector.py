"""Job Collector - Craigslist Job Scraper for All 50 States"""

import requests
import re
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus
import time


class JobCollector:
    """Scrapes Craigslist gig and job postings for protest-related activity."""
    
    # All 50 states + DC - major Craigslist city for each
    CRAIGSLIST_CITIES = {
        # State: craigslist subdomain
        'AL': 'birmingham',
        'AK': 'anchorage',
        'AZ': 'phoenix',
        'AR': 'littlerock',
        'CA': 'losangeles',
        'CO': 'denver',
        'CT': 'hartford',
        'DE': 'delaware',
        'FL': 'miami',
        'GA': 'atlanta',
        'HI': 'honolulu',
        'ID': 'boise',
        'IL': 'chicago',
        'IN': 'indianapolis',
        'IA': 'desmoines',
        'KS': 'kansascity',
        'KY': 'louisville',
        'LA': 'neworleans',
        'ME': 'maine',
        'MD': 'baltimore',
        'MA': 'boston',
        'MI': 'detroit',
        'MN': 'minneapolis',
        'MS': 'jackson',
        'MO': 'stlouis',
        'MT': 'billings',
        'NE': 'omaha',
        'NV': 'lasvegas',
        'NH': 'nh',
        'NJ': 'newjersey',
        'NM': 'albuquerque',
        'NY': 'newyork',
        'NC': 'charlotte',
        'ND': 'fargo',
        'OH': 'cleveland',
        'OK': 'oklahomacity',
        'OR': 'portland',
        'PA': 'philadelphia',
        'RI': 'providence',
        'SC': 'charleston',
        'SD': 'siouxfalls',
        'TN': 'nashville',
        'TX': 'dallas',
        'UT': 'saltlakecity',
        'VT': 'burlington',
        'VA': 'norfolk',
        'WA': 'seattle',
        'WV': 'charlestonwv',
        'WI': 'milwaukee',
        'WY': 'wyoming',
        'DC': 'washingtondc'
    }
    
    # Additional major cities for high-population states
    EXTRA_CITIES = {
        'CA': ['sfbay', 'sandiego', 'sacramento'],
        'TX': ['houston', 'austin', 'sanantonio'],
        'FL': ['tampa', 'orlando', 'jacksonville'],
        'NY': ['buffalo', 'albany'],
        'PA': ['pittsburgh'],
        'OH': ['columbus', 'cincinnati'],
        'IL': ['springfieldil'],
        'GA': ['savannah'],
        'NC': ['raleigh'],
        'WA': ['spokane'],
        'AZ': ['tucson'],
        'CO': ['cosprings'],
        'MI': ['grandrapids'],
        'TN': ['memphis', 'knoxville']
    }
    
    # Keywords that suggest paid protest/astroturf activity
    SUSPICIOUS_KEYWORDS = [
        'paid protest',
        'protest sign',
        'rally attendee', 
        'demonstration',
        'hold signs',
        'peaceful protest',
        'political event',
        'grassroots',
        'advocacy event',
        'town hall',
        'city council',
        'public hearing',
        'civic event',
        'campaign event'
    ]
    
    # Broader search terms to find gigs
    SEARCH_TERMS = [
        'protest',
        'rally',
        'canvasser',
        'organizer',
        'activist',
        'campaign',
        'petition',
        'signature gatherer',
        'event staff political',
        'community outreach'
    ]
    
    def __init__(self):
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
    
    def collect(self, max_calls: int = 100) -> List[Dict[str, Any]]:
        """Collect job postings from Craigslist across all 50 states."""
        results = []
        cities_to_scan = self._get_priority_cities()
        
        for state, city in cities_to_scan:
            if self.calls_made >= max_calls:
                break
            
            for search_term in self.SEARCH_TERMS[:3]:  # Top 3 terms per city
                if self.calls_made >= max_calls:
                    break
                
                jobs = self._search_craigslist(city, state, search_term)
                results.extend(jobs)
                
                # Be respectful - small delay between requests
                time.sleep(0.5)
        
        # Deduplicate by title + city
        seen = set()
        unique_results = []
        for job in results:
            key = f"{job.get('title', '')[:50]}_{job.get('city', '')}"
            if key not in seen:
                seen.add(key)
                unique_results.append(job)
        
        # Sort by suspicion score
        unique_results.sort(key=lambda x: x.get('suspicion_score', 0), reverse=True)
        
        return unique_results[:100]  # Return top 100
    
    def _get_priority_cities(self) -> List[tuple]:
        """Get list of cities to scan, prioritizing high-activity states."""
        cities = []
        
        # Priority states (politically active)
        priority_states = ['TX', 'CA', 'FL', 'NY', 'PA', 'OH', 'GA', 'NC', 'MI', 'AZ', 
                          'WA', 'CO', 'VA', 'NJ', 'IL', 'DC', 'NV', 'WI', 'MN', 'OR']
        
        # Add priority states first
        for state in priority_states:
            if state in self.CRAIGSLIST_CITIES:
                cities.append((state, self.CRAIGSLIST_CITIES[state]))
                # Add extra cities for this state
                if state in self.EXTRA_CITIES:
                    for extra_city in self.EXTRA_CITIES[state]:
                        cities.append((state, extra_city))
        
        # Add remaining states
        for state, city in self.CRAIGSLIST_CITIES.items():
            if state not in priority_states:
                cities.append((state, city))
        
        return cities
    
    def _search_craigslist(self, city: str, state: str, search_term: str) -> List[Dict[str, Any]]:
        """Search Craigslist gigs section for a city."""
        results = []
        
        # Search both gigs (ggg) and jobs (jjj) sections
        sections = ['ggg', 'jjj']
        
        for section in sections:
            try:
                url = f"https://{city}.craigslist.org/search/{section}?query={quote_plus(search_term)}"
                
                response = self.session.get(url, timeout=15)
                self.calls_made += 1
                
                if response.status_code == 200:
                    jobs = self._parse_craigslist_html(response.text, city, state, search_term, section)
                    results.extend(jobs)
                elif response.status_code == 403:
                    print(f"  Blocked by Craigslist for {city} - trying next city")
                    break
                    
            except requests.RequestException as e:
                print(f"  Error fetching {city} {section}: {e}")
                continue
        
        return results
    
    def _parse_craigslist_html(self, html: str, city: str, state: str, search_term: str, section: str) -> List[Dict[str, Any]]:
        """Parse Craigslist HTML to extract job listings."""
        results = []
        
        # Find all result rows - Craigslist uses <li class="cl-static-search-result">
        # or <li class="result-row"> depending on version
        
        # Pattern for newer Craigslist format
        pattern = r'<li[^>]*class="[^"]*cl-static-search-result[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*>.*?<span[^>]*class="[^"]*label[^"]*"[^>]*>([^<]+)</span>.*?</li>'
        
        matches = re.findall(pattern, html, re.DOTALL | re.IGNORECASE)
        
        # Also try older format
        if not matches:
            pattern2 = r'<a[^>]*href="(https?://[^"]*craigslist[^"]+/([^/]+)/d/[^"]+)"[^>]*class="[^"]*result-title[^"]*"[^>]*>([^<]+)</a>'
            matches2 = re.findall(pattern2, html, re.DOTALL | re.IGNORECASE)
            for url, category, title in matches2:
                matches.append((url, title))
        
        # Simpler fallback - just find titles and links
        if not matches:
            title_pattern = r'<a[^>]*href="(/[^"]+/\d+\.html)"[^>]*>([^<]+)</a>'
            matches = re.findall(title_pattern, html)
            matches = [(f"https://{city}.craigslist.org{url}", title) for url, title in matches]
        
        for match in matches[:20]:  # Limit per search
            if len(match) >= 2:
                url = match[0]
                title = match[1].strip()
                
                # Skip if title is too short or generic
                if len(title) < 10:
                    continue
                
                # Calculate suspicion score
                suspicion_score = self._calculate_suspicion(title)
                
                # Only include if somewhat relevant
                if suspicion_score >= 20 or search_term.lower() in title.lower():
                    results.append({
                        'type': 'job_posting',
                        'source': 'craigslist',
                        'title': title,
                        'url': url if url.startswith('http') else f"https://{city}.craigslist.org{url}",
                        'city': city,
                        'state': state,
                        'section': 'gigs' if section == 'ggg' else 'jobs',
                        'search_term': search_term,
                        'suspicion_score': suspicion_score,
                        'date': datetime.utcnow().isoformat() + 'Z',
                        'keywords': self._extract_keywords(title)
                    })
        
        return results
    
    def _calculate_suspicion(self, title: str) -> int:
        """Calculate how suspicious a job posting is (0-100)."""
        score = 0
        title_lower = title.lower()
        
        # High suspicion keywords
        high_value = [
            'paid protest', 'hold signs', 'rally attendee', 'protest sign',
            'demonstration', 'political event', 'grassroots', 'town hall',
            'city council', 'public hearing', 'cash daily', 'same day pay'
        ]
        for kw in high_value:
            if kw in title_lower:
                score += 25
        
        # Medium suspicion keywords  
        medium_value = [
            'protest', 'rally', 'canvass', 'petition', 'campaign',
            'activist', 'organizer', 'advocacy', 'political', 'signatures',
            'event staff', 'street team', 'brand ambassador'
        ]
        for kw in medium_value:
            if kw in title_lower:
                score += 10
        
        # Pay indicators (often associated with paid protests)
        pay_indicators = ['$/hr', 'per hour', 'daily pay', 'cash', 'paid', '$15', '$20', '$25', '$50']
        for indicator in pay_indicators:
            if indicator in title_lower:
                score += 5
        
        # Urgency indicators
        urgency = ['immediate', 'urgent', 'today', 'tomorrow', 'this week', 'asap']
        for word in urgency:
            if word in title_lower:
                score += 5
        
        return min(score, 100)
    
    def _extract_keywords(self, title: str) -> List[str]:
        """Extract relevant keywords from title."""
        keywords = []
        title_lower = title.lower()
        
        all_keywords = [
            'protest', 'rally', 'canvass', 'petition', 'campaign', 'activist',
            'organizer', 'advocacy', 'political', 'grassroots', 'signatures',
            'demonstration', 'march', 'event', 'staff', 'paid'
        ]
        
        for kw in all_keywords:
            if kw in title_lower:
                keywords.append(kw)
        
        return keywords


if __name__ == '__main__':
    collector = JobCollector()
    print("Starting Craigslist scan across all 50 states...")
    jobs = collector.collect(max_calls=50)
    print(f"\nCollected {len(jobs)} job postings")
    
    print("\nTop 10 most suspicious:")
    for job in jobs[:10]:
        print(f"  [{job['state']}] {job['title'][:60]}...")
        print(f"       Score: {job['suspicion_score']}% | {job['url']}")
