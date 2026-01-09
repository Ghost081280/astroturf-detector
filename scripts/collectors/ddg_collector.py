"""DuckDuckGo News Collector - Additional news source"""

import requests
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus


class DuckDuckGoCollector:
    """Collects news from DuckDuckGo search (no API key required)."""
    
    # DuckDuckGo HTML search (no official API, but we can parse results)
    SEARCH_URL = "https://html.duckduckgo.com/html/"
    
    SEARCH_QUERIES = [
        "paid protesters news",
        "astroturf campaign politics",
        "fake grassroots organization",
        "crowds on demand protest",
        "501c4 dark money",
    ]
    
    def __init__(self):
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def collect(self, max_calls: int = 5) -> List[Dict[str, Any]]:
        """Collect news from DuckDuckGo searches."""
        results = []
        
        for query in self.SEARCH_QUERIES:
            if self.calls_made >= max_calls:
                break
            
            articles = self._search(query)
            results.extend(articles)
            self.calls_made += 1
        
        # Deduplicate
        seen = set()
        unique = []
        for item in results:
            key = item.get('title', '')[:50].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique[:30]
    
    def _search(self, query: str) -> List[Dict[str, Any]]:
        """Search DuckDuckGo and parse results."""
        try:
            data = {'q': query, 'kl': 'us-en'}
            response = self.session.post(self.SEARCH_URL, data=data, timeout=15)
            
            if response.status_code != 200:
                print(f"  DuckDuckGo returned {response.status_code}")
                return []
            
            # Parse HTML results (simple regex approach)
            import re
            results = []
            
            # Find result links and snippets
            # DuckDuckGo HTML format: <a class="result__a" href="...">title</a>
            pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            
            for url, title in matches[:10]:
                # Skip DuckDuckGo redirect URLs, extract actual URL
                if 'uddg=' in url:
                    actual_url = re.search(r'uddg=([^&]+)', url)
                    if actual_url:
                        from urllib.parse import unquote
                        url = unquote(actual_url.group(1))
                
                relevance = self._calculate_relevance(title, query)
                
                results.append({
                    'type': 'news',
                    'source': 'duckduckgo',
                    'title': title.strip(),
                    'url': url,
                    'date': datetime.utcnow().isoformat() + 'Z',
                    'query': query,
                    'relevance_score': relevance,
                    'location': self._extract_location(title)
                })
            
            return results
            
        except Exception as e:
            print(f"  DuckDuckGo error for '{query}': {e}")
            return []
    
    def _calculate_relevance(self, title: str, query: str) -> int:
        """Calculate relevance score."""
        score = 50
        title_lower = title.lower()
        
        high_value = ['astroturf', 'paid protest', 'fake grassroots', 'dark money', 'crowds on demand']
        for kw in high_value:
            if kw in title_lower:
                score += 20
        
        medium_value = ['protest', 'advocacy', '501c4', 'nonprofit', 'campaign']
        for kw in medium_value:
            if kw in title_lower:
                score += 10
        
        return min(score, 100)
    
    def _extract_location(self, text: str) -> str:
        """Extract US location from text."""
        states = ['Texas', 'California', 'Florida', 'New York', 'Ohio', 'Georgia', 
                  'Pennsylvania', 'Michigan', 'Arizona', 'Washington', 'Colorado',
                  'Dallas', 'Houston', 'Austin', 'Los Angeles', 'New Orleans']
        
        for loc in states:
            if loc.lower() in text.lower():
                return loc
        return ''


if __name__ == '__main__':
    collector = DuckDuckGoCollector()
    results = collector.collect(max_calls=3)
    print(f"Found {len(results)} results")
    for r in results[:5]:
        print(f"  - {r['title'][:60]}...")
