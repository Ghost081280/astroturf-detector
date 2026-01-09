"""DuckDuckGo News Collector"""
import requests
import re
from datetime import datetime
from typing import List, Dict, Any
from urllib.parse import quote_plus, unquote

class DuckDuckGoCollector:
    SEARCH_URL = "https://html.duckduckgo.com/html/"
    SEARCH_QUERIES = ["paid protesters news", "astroturf campaign politics", "fake grassroots organization", "crowds on demand protest", "501c4 dark money"]
    
    def __init__(self):
        self.calls_made = 0
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
    
    def collect(self, max_calls: int = 5) -> List[Dict[str, Any]]:
        results = []
        for query in self.SEARCH_QUERIES:
            if self.calls_made >= max_calls:
                break
            articles = self._search(query)
            results.extend(articles)
            self.calls_made += 1
        
        seen = set()
        unique = []
        for item in results:
            key = item.get('title', '')[:50].lower()
            if key not in seen:
                seen.add(key)
                unique.append(item)
        
        return unique[:30]
    
    def _search(self, query: str) -> List[Dict[str, Any]]:
        try:
            data = {'q': query, 'kl': 'us-en'}
            response = self.session.post(self.SEARCH_URL, data=data, timeout=15)
            if response.status_code != 200:
                return []
            
            results = []
            pattern = r'<a[^>]*class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)</a>'
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            
            for url, title in matches[:10]:
                if 'uddg=' in url:
                    actual = re.search(r'uddg=([^&]+)', url)
                    if actual:
                        url = unquote(actual.group(1))
                
                relevance = self._calc_relevance(title, query)
                results.append({
                    'type': 'news',
                    'source': 'duckduckgo',
                    'title': title.strip(),
                    'url': url,
                    'date': datetime.utcnow().isoformat() + 'Z',
                    'query': query,
                    'relevance_score': relevance,
                    'location': ''
                })
            
            return results
        except Exception as e:
            print(f"  DDG error: {e}")
            return []
    
    def _calc_relevance(self, title: str, query: str) -> int:
        score = 50
        title_lower = title.lower()
        
        high = ['astroturf', 'paid protest', 'fake grassroots', 'dark money', 'crowds on demand']
        for kw in high:
            if kw in title_lower:
                score += 20
        
        return min(score, 100)

if __name__ == '__main__':
    collector = DuckDuckGoCollector()
    results = collector.collect(max_calls=2)
    print(f"Found {len(results)} results")
