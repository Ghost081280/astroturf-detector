"""News Collector - Google News and DuckDuckGo"""
import os
import json
import requests
from datetime import datetime
from typing import List, Dict

class NewsCollector:
    # Search terms optimized for astroturf detection
    SEARCH_TERMS = [
        "paid protesters",
        "astroturf campaign",
        "fake grassroots",
        "crowds on demand",
        "paid activist",
        "manufactured outrage",
        "dark money protest",
        "crisis actors rally"
    ]
    
    def __init__(self):
        self.google_api_key = os.environ.get('GOOGLE_NEWS_API_KEY')
        self.google_cx = os.environ.get('GOOGLE_SEARCH_CX')
    
    def collect(self) -> List[Dict]:
        """Collect news from all sources"""
        results = []
        
        # Try Google News API
        if self.google_api_key and self.google_cx:
            results.extend(self._collect_google())
        
        # Always try DuckDuckGo (no API key needed)
        results.extend(self._collect_duckduckgo())
        
        # Dedupe by URL
        seen = set()
        unique = []
        for item in results:
            url = item.get('url', '')
            if url and url not in seen:
                seen.add(url)
                unique.append(item)
        
        return unique[:20]  # Top 20
    
    def _collect_google(self) -> List[Dict]:
        """Collect from Google Custom Search API"""
        results = []
        try:
            for term in self.SEARCH_TERMS[:4]:  # Limit to save API quota
                url = f"https://www.googleapis.com/customsearch/v1"
                params = {
                    'key': self.google_api_key,
                    'cx': self.google_cx,
                    'q': term,
                    'num': 5,
                    'sort': 'date'
                }
                response = requests.get(url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get('items', []):
                        results.append({
                            'title': item.get('title', ''),
                            'url': item.get('link', ''),
                            'snippet': item.get('snippet', ''),
                            'publisher': item.get('displayLink', ''),
                            'source': 'google',
                            'query': term,
                            'relevance_score': self._calculate_relevance(item, term),
                            'collected_at': datetime.utcnow().isoformat() + 'Z'
                        })
        except Exception as e:
            print(f"  Google News error: {e}")
        return results
    
    def _collect_duckduckgo(self) -> List[Dict]:
        """Collect from DuckDuckGo using duckduckgo-search library"""
        results = []
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                for term in self.SEARCH_TERMS[:3]:
                    try:
                        # Search news specifically
                        news_results = list(ddgs.news(term, max_results=5))
                        for item in news_results:
                            results.append({
                                'title': item.get('title', ''),
                                'url': item.get('url', ''),
                                'snippet': item.get('body', ''),
                                'publisher': item.get('source', 'DuckDuckGo'),
                                'source': 'duckduckgo',
                                'query': term,
                                'date': item.get('date', ''),
                                'relevance_score': self._calculate_relevance({'title': item.get('title', ''), 'snippet': item.get('body', '')}, term),
                                'collected_at': datetime.utcnow().isoformat() + 'Z'
                            })
                    except Exception as e:
                        print(f"    DDG search error for '{term}': {e}")
                        continue
        except ImportError:
            print("  DuckDuckGo: duckduckgo-search not installed, skipping")
        except Exception as e:
            print(f"  DuckDuckGo error: {e}")
        return results
    
    def _calculate_relevance(self, item: Dict, query: str) -> int:
        """Calculate relevance score 0-100"""
        score = 50
        title = (item.get('title', '') or '').lower()
        snippet = (item.get('snippet', '') or '').lower()
        
        # Boost for direct keyword matches
        keywords = ['paid', 'protest', 'astroturf', 'fake', 'manufactured', 'crowds on demand']
        for kw in keywords:
            if kw in title:
                score += 15
            if kw in snippet:
                score += 5
        
        return min(score, 100)


if __name__ == "__main__":
    collector = NewsCollector()
    results = collector.collect()
    print(f"Collected {len(results)} news items")
    for r in results[:3]:
        print(f"  - {r['title'][:60]}...")
