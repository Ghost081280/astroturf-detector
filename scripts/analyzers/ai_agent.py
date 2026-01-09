"""AI Agent - Intelligent Analysis Engine using Claude API"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

class AIAgent:
    """Analyzes collected data using Claude API for pattern detection."""
    
    API_URL = "https://api.anthropic.com/v1/messages"
    MODEL = "claude-3-haiku-20240307"
    MAX_TOKENS = 2048
    
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.enabled = bool(self.api_key)
        if not self.enabled:
            print("  Warning: ANTHROPIC_API_KEY not set, using fallback analysis")
    
    def analyze(self, memory: Dict[str, Any], new_data: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Run AI analysis on collected data."""
        if not self.enabled:
            return self._fallback_analysis(memory, new_data, patterns)
        
        try:
            prompt = self._build_prompt(memory, new_data, patterns)
            response = self._call_api(prompt)
            return self._parse_response(response, memory, new_data)
        except Exception as e:
            print(f"  AI analysis error: {e}")
            return self._fallback_analysis(memory, new_data, patterns)
    
    def _build_prompt(self, memory: Dict[str, Any], new_data: Dict[str, Any], patterns: Dict[str, Any]) -> str:
        """Build analysis prompt for Claude."""
        
        news_summary = []
        for article in new_data.get('news', [])[:10]:
            news_summary.append({
                'title': article.get('title', '')[:100],
                'publisher': article.get('publisher'),
                'relevance': article.get('relevance_score', 0),
                'location': article.get('location', '')
            })
        
        org_summary = []
        for org in new_data.get('nonprofits', [])[:10]:
            org_summary.append({
                'name': org.get('name'),
                'state': org.get('state'),
                'risk_score': org.get('risk_score', 0),
                'ruling_date': org.get('ruling_date')
            })
        
        summary = {
            'news_articles': news_summary,
            'organizations': org_summary,
            'fec_records': len(new_data.get('fec', [])),
            'known_patterns': memory.get('knownAstroturfPatterns', {}).get('threeWordNames', [])[:5],
            'previous_alerts': len(memory.get('timeline', []))
        }
        
        return f"""You are an OSINT analyst detecting potential astroturf (fake grassroots) activity in the United States.

COLLECTED DATA:
{json.dumps(summary, indent=2)}

TASK: Analyze this data for signs of manufactured grassroots campaigns. Consider:
1. News articles mentioning paid protesters, fake advocacy, or astroturf
2. Organizations with suspicious naming patterns (generic 3-word names like "Citizens For X")
3. Recently formed 501(c)(4) organizations with large funding
4. Geographic clusters of similar organizations
5. Correlation between news events and organization activity

RESPOND WITH ONLY VALID JSON in this exact format:
{{
    "confidence": <0-100 overall confidence score>,
    "confidence_factors": [
        {{"factor": "<factor name>", "score": <0-100>, "detail": "<explanation>"}}
    ],
    "summary": "<2-3 sentence analysis summary>",
    "alerts": [
        {{
            "title": "<alert title>",
            "description": "<detailed description>",
            "severity": "high|medium|low",
            "confidence": <0-100>,
            "factors": [{{"name": "<factor>", "value": "<value>"}}],
            "locations": ["<state or city>"],
            "sources": ["<source urls or names>"]
        }}
    ],
    "timeline_events": [
        {{
            "date": "<ISO date>",
            "title": "<event title>",
            "description": "<description>",
            "type": "news|org|fec",
            "tags": ["<tag>"],
            "sourceUrl": "<url if available>"
        }}
    ],
    "recommendations": ["<actionable recommendation>"],
    "geographic_hotspots": ["<state abbreviation>"]
}}

Be specific about locations (US states/cities). Focus on United States activity only."""
    
    def _call_api(self, prompt: str) -> str:
        """Call Claude API."""
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": self.MODEL,
            "max_tokens": self.MAX_TOKENS,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(self.API_URL, headers=headers, json=data, timeout=60)
        
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code} - {response.text[:200]}")
        
        return response.json().get('content', [{}])[0].get('text', '{}')
    
    def _parse_response(self, response_text: str, memory: Dict, new_data: Dict) -> Dict[str, Any]:
        """Parse AI response."""
        try:
            text = response_text.strip()
            
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            if text.endswith('```'):
                text = text[:-3]
            
            result = json.loads(text.strip())
            
            return {
                'confidence': result.get('confidence', 50),
                'confidence_factors': result.get('confidence_factors', []),
                'summary': result.get('summary', ''),
                'alerts': result.get('alerts', []),
                'recommendations': result.get('recommendations', []),
                'timeline_events': result.get('timeline_events', []),
                'geographic_hotspots': result.get('geographic_hotspots', [])
            }
            
        except json.JSONDecodeError as e:
            print(f"  Failed to parse AI response: {e}")
            return self._fallback_analysis(memory, new_data, {})
    
    def _fallback_analysis(self, memory: Dict, new_data: Dict, patterns: Dict) -> Dict[str, Any]:
        """Fallback analysis when AI is unavailable."""
        alerts = []
        timeline_events = []
        confidence = 30
        confidence_factors = []
        
        news = new_data.get('news', [])
        high_relevance_news = [a for a in news if a.get('relevance_score', 0) >= 70]
        
        if high_relevance_news:
            confidence += 15
            confidence_factors.append({
                'factor': 'Relevant News Coverage',
                'score': min(len(high_relevance_news) * 10, 50),
                'detail': f'Found {len(high_relevance_news)} highly relevant news articles'
            })
            
            for article in high_relevance_news[:3]:
                timeline_events.append({
                    'date': article.get('date', datetime.utcnow().isoformat() + 'Z'),
                    'title': article.get('title', 'News Article')[:80],
                    'description': f"Source: {article.get('publisher', 'Unknown')}",
                    'type': 'news',
                    'tags': ['news', article.get('location', 'US') or 'US'],
                    'sourceUrl': article.get('url', '')
                })
        
        orgs = new_data.get('nonprofits', [])
        high_risk_orgs = [o for o in orgs if o.get('risk_score', 0) >= 60]
        
        if high_risk_orgs:
            confidence += 20
            confidence_factors.append({
                'factor': 'High-Risk Organizations',
                'score': min(len(high_risk_orgs) * 15, 60),
                'detail': f'Found {len(high_risk_orgs)} organizations with suspicious patterns'
            })
            
            states = list(set(o.get('state', 'Unknown') for o in high_risk_orgs))
            alerts.append({
                'title': f"Suspicious Organizations Detected in {', '.join(states[:3])}",
                'description': f"Found {len(high_risk_orgs)} 501(c)(4) organizations matching astroturf patterns including generic naming conventions and recent formation dates.",
                'severity': 'high' if len(high_risk_orgs) >= 3 else 'medium',
                'confidence': min(60 + len(high_risk_orgs) * 5, 90),
                'factors': [
                    {'name': 'Organizations Flagged', 'value': str(len(high_risk_orgs))},
                    {'name': 'States Affected', 'value': ', '.join(states[:5])},
                    {'name': 'Data Source', 'value': 'ProPublica Nonprofit Explorer'}
                ],
                'locations': states[:5],
                'sources': ['https://projects.propublica.org/nonprofits/']
            })
            
            for org in high_risk_orgs[:3]:
                timeline_events.append({
                    'date': datetime.utcnow().isoformat() + 'Z',
                    'title': f"Flagged: {org.get('name', 'Unknown')}",
                    'description': f"Risk score: {org.get('risk_score', 0)}% - {org.get('state', 'Unknown')}",
                    'type': 'org',
                    'tags': ['organization', org.get('state', 'US')],
                    'sourceUrl': org.get('sourceUrl', '')
                })
        
        confidence_factors.append({
            'factor': 'Data Freshness',
            'score': 80,
            'detail': 'Real-time data from verified sources'
        })
        
        confidence_factors.append({
            'factor': 'Source Reliability',
            'score': 85,
            'detail': 'ProPublica, FEC, and Google News RSS'
        })
        
        return {
            'confidence': min(confidence, 100),
            'confidence_factors': confidence_factors,
            'summary': f"Analyzed {len(news)} news articles and {len(orgs)} organizations. Found {len(high_risk_orgs)} high-risk organizations and {len(high_relevance_news)} relevant news stories.",
            'alerts': alerts,
            'recommendations': [
                "Monitor flagged organizations for increased activity",
                "Cross-reference news coverage with organization filings",
                "Track geographic patterns in new 501(c)(4) formations"
            ],
            'timeline_events': timeline_events,
            'geographic_hotspots': list(set(o.get('state', '') for o in high_risk_orgs if o.get('state')))[:5]
        }


if __name__ == '__main__':
    agent = AIAgent()
    test_data = {
        'news': [{'title': 'Test article', 'relevance_score': 75, 'publisher': 'Test'}],
        'nonprofits': [{'name': 'Citizens For Freedom', 'state': 'TX', 'risk_score': 70}],
        'fec': []
    }
    result = agent.analyze({}, test_data, {})
    print(json.dumps(result, indent=2))
