"""News Collector - OSINT via Google News RSS"""

import requests
import re
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET


class NewsCollector:
    """Collects protest and astroturf related news from public sources."""
    
    GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    
    SEARCH_QUERIES = [
        "paid protesters",
        "astroturf campaign",
        "fake grassroots",
        "protesters for hire",
        "manufactured protest",
        "city council protesters",
        "advocacy group funding",
        "dark money protest",
        "501c4 political"
    ]
    
    def __init__(self):
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AstroturfDetector/1.0 (News Research Bot)'
        })
    
    def collect(self, max_calls: int = 10) -> List[Dict[str, Any]]:
        """Collect news articles from RSS feeds."""
        results = []
        
        for query in self.SEARCH_QUERIES:
            if self.calls_made >= max_calls:
                break
            
            articles = self._fetch_google_news(query)
            results.extend(articles)
            self.calls_made += 1
        
        # Deduplicate by title
        seen_titles = set()
        unique_results = []
        for article in results:
            title_key = article.get('title', '').lower()[:50]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_results.append(article)
        
        # Sort by date, newest first
        unique_results.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return unique_results[:50]
    
    def _fetch_google_news(self, query: str) -> List[Dict[str, Any]]:
        """Fetch articles from Google News RSS."""
        try:
            url = self.GOOGLE_NEWS_RSS.format(query=quote_plus(query))
            response = self.session.get(url, timeout=15)
            
            if response.status_code != 200:
                print(f"  Google News returned status {response.status_code} for query: {query}")
                return []
            
            # Parse RSS XML
            root = ET.fromstring(response.content)
            articles = []
            
            for item in root.findall('.//item')[:10]:
                title = item.find('title')
                link = item.find('link')
                pub_date = item.find('pubDate')
                source = item.find('source')
                
                if title is not None and link is not None:
                    # Parse date
                    date_str = None
                    if pub_date is not None and pub_date.text:
                        try:
                            # Parse RSS date format: "Sat, 04 Jan 2025 12:00:00 GMT"
                            cleaned_date = pub_date.text.replace(' GMT', '').replace(' EST', '').replace(' PST', '').replace(' EDT', '').replace(' PDT', '').strip()
                            date_obj = datetime.strptime(cleaned_date, '%a, %d %b %Y %H:%M:%S')
                            date_str = date_obj.isoformat() + 'Z'
                        except ValueError:
                            date_str = datetime.utcnow().isoformat() + 'Z'
                    else:
                        date_str = datetime.utcnow().isoformat() + 'Z'
                    
                    # Calculate relevance score
                    relevance = self._calculate_relevance(title.text, query)
                    
                    articles.append({
                        'type': 'news',
                        'source': 'google_news',
                        'title': title.text,
                        'url': link.text,
                        'date': date_str,
                        'publisher': source.text if source is not None else 'Unknown',
                        'query': query,
                        'relevance_score': relevance,
                        'location': self._extract_location(title.text)
                    })
            
            return articles
            
        except ET.ParseError as e:
            print(f"  XML parse error for query '{query}': {e}")
            return []
        except requests.RequestException as e:
            print(f"  Request error for query '{query}': {e}")
            return []
        except Exception as e:
            print(f"  Error fetching news for '{query}': {e}")
            return []
    
    def _calculate_relevance(self, title: str, query: str) -> int:
        """Calculate how relevant an article is (0-100)."""
        score = 50  # Base score
        title_lower = title.lower()
        
        # High-value keywords
        high_value = [
            'astroturf', 'paid protest', 'fake grassroots', 'dark money',
            'manufactured', 'hired crowd', 'for hire', 'paid activist',
            'front group', 'shell organization'
        ]
        for kw in high_value:
            if kw in title_lower:
                score += 20
        
        # Medium-value keywords
        medium_value = [
            'protest', 'advocacy', 'campaign', 'funding', '501c4',
            'nonprofit', 'city council', 'hearing', 'rally', 'demonstration',
            'activist', 'organizer', 'lobbyist'
        ]
        for kw in medium_value:
            if kw in title_lower:
                score += 10
        
        # Location mentions (US states/cities) add credibility
        if self._extract_location(title):
            score += 5
        
        return min(score, 100)
    
    def _extract_location(self, text: str) -> str:
        """Extract US location from text."""
        us_states = [
            'Alabama', 'Alaska', 'Arizona', 'Arkansas', 'California', 'Colorado',
            'Connecticut', 'Delaware', 'Florida', 'Georgia', 'Hawaii', 'Idaho',
            'Illinois', 'Indiana', 'Iowa', 'Kansas', 'Kentucky', 'Louisiana',
            'Maine', 'Maryland', 'Massachusetts', 'Michigan', 'Minnesota',
            'Mississippi', 'Missouri', 'Montana', 'Nebraska', 'Nevada',
            'New Hampshire', 'New Jersey', 'New Mexico', 'New York',
            'North Carolina', 'North Dakota', 'Ohio', 'Oklahoma', 'Oregon',
            'Pennsylvania', 'Rhode Island', 'South Carolina', 'South Dakota',
            'Tennessee', 'Texas', 'Utah', 'Vermont', 'Virginia', 'Washington',
            'West Virginia', 'Wisconsin', 'Wyoming', 'Washington DC', 'D.C.'
        ]
        
        major_cities = [
            'New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix',
            'Philadelphia', 'San Antonio', 'San Diego', 'Dallas', 'Austin',
            'San Francisco', 'Seattle', 'Denver', 'Boston', 'Atlanta',
            'Miami', 'Minneapolis', 'Detroit', 'Portland', 'Las Vegas',
            'New Orleans', 'Cleveland', 'Pittsburgh', 'Cincinnati', 'Milwaukee',
            'Sacramento', 'Kansas City', 'Tampa', 'Orlando', 'St. Louis'
        ]
        
        text_lower = text.lower()
        
        for location in major_cities + us_states:
            if location.lower() in text_lower:
                return location
        
        return ''


if __name__ == '__main__':
    collector = NewsCollector()
    articles = collector.collect(max_calls=5)
    print(f"Collected {len(articles)} news articles")
    for article in articles[:5]:
        print(f"  - {article['title'][:60]}... ({article['publisher']})")
        print(f"    Relevance: {article['relevance_score']}%, Location: {article['location'] or 'N/A'}")
