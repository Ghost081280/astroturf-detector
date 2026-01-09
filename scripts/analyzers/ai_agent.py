"""AI Agent - Claude API Analysis with Correlation Detection
Same token cost as before, but smarter prompts and Python-side pattern detection
"""
import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

class AIAgent:
    API_URL = "https://api.anthropic.com/v1/messages"
    MODEL = "claude-3-haiku-20240307"
    MAX_TOKENS = 2048
    
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.enabled = bool(self.api_key)
        if not self.enabled:
            print("  ANTHROPIC_API_KEY not set, using fallback")
    
    def analyze(self, memory: Dict[str, Any], new_data: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Main analysis entry point"""
        # First, do Python-side correlation (free)
        correlations = self._find_correlations(new_data)
        
        if not self.enabled:
            return self._fallback_analysis(memory, new_data, correlations)
        
        try:
            prompt = self._build_prompt(memory, new_data, correlations)
            response = self._call_api(prompt)
            result = self._parse_response(response, memory, new_data)
            result['connections'] = correlations
            return result
        except Exception as e:
            print(f"  AI error: {e}")
            result = self._fallback_analysis(memory, new_data, correlations)
            result['connections'] = correlations
            return result
    
    def _find_correlations(self, new_data: Dict) -> List[Dict]:
        """Find correlations between data sources (Python-side, no API cost)"""
        correlations = []
        jobs = new_data.get('jobs', [])
        news = new_data.get('news', [])
        orgs = new_data.get('nonprofits', []) + new_data.get('campaign_finance', [])
        
        # 1. Geographic correlation: Jobs in cities mentioned in news
        news_cities = set()
        city_keywords = ['dallas', 'los angeles', 'la', 'new york', 'nyc', 'chicago', 'houston', 
                        'phoenix', 'philadelphia', 'san antonio', 'san diego', 'austin', 'portland',
                        'seattle', 'minneapolis', 'denver', 'atlanta', 'miami', 'detroit', 'boston']
        
        for article in news:
            title_lower = (article.get('title', '') or '').lower()
            location = (article.get('location', '') or '').lower()
            for city in city_keywords:
                if city in title_lower or city in location:
                    news_cities.add(city)
        
        if news_cities:
            jobs_in_news_cities = []
            for job in jobs:
                job_city = (job.get('city', '') or '').lower()
                for news_city in news_cities:
                    if news_city in job_city or job_city in news_city:
                        jobs_in_news_cities.append(job)
                        break
            
            if jobs_in_news_cities:
                correlations.append({
                    'type': 'Geographic Match',
                    'description': f'{len(jobs_in_news_cities)} job posting(s) found in cities with protest-related news.',
                    'probability': min(55 + len(jobs_in_news_cities) * 8, 85),
                    'evidence': [{'type': 'Job', 'detail': j.get('title', '')[:80]} for j in jobs_in_news_cities[:3]]
                })
        
        # 2. Organization naming patterns (astroturf red flags)
        astroturf_patterns = ['freedom fund', 'liberty', 'citizens for', 'americans for', 
                             'action fund', 'leadership', 'voices for', 'families for']
        suspicious_orgs = []
        for org in orgs:
            name_lower = (org.get('name', '') or '').lower()
            for pattern in astroturf_patterns:
                if pattern in name_lower:
                    suspicious_orgs.append(org)
                    break
        
        if len(suspicious_orgs) >= 2:
            correlations.append({
                'type': 'Naming Pattern',
                'description': f'{len(suspicious_orgs)} orgs with generic patriotic names typical of astroturf.',
                'probability': min(50 + len(suspicious_orgs) * 5, 78),
                'evidence': [{'type': 'Org', 'detail': o.get('name', '')[:80]} for o in suspicious_orgs[:3]]
            })
        
        # 3. High-risk new organizations
        recent_high_risk = []
        for org in orgs:
            try:
                file_date = org.get('first_file_date', '')
                if file_date:
                    filed = datetime.strptime(file_date, '%Y-%m-%d')
                    days_old = (datetime.utcnow() - filed).days
                    risk = org.get('risk_score', 0)
                    if days_old < 180 and risk >= 70:
                        recent_high_risk.append(org)
            except:
                pass
        
        if recent_high_risk:
            correlations.append({
                'type': 'New High-Risk Orgs',
                'description': f'{len(recent_high_risk)} high-risk org(s) filed in last 6 months.',
                'probability': min(50 + len(recent_high_risk) * 12, 80),
                'evidence': [{'type': 'Filed', 'detail': f"{o.get('name', '')[:35]} ({o.get('first_file_date', '')})"} for o in recent_high_risk[:2]]
            })
        
        # 4. News clustering around "paid" keywords
        paid_news = [n for n in news if 'paid' in (n.get('title', '') or '').lower()]
        
        if len(paid_news) >= 2:
            correlations.append({
                'type': 'Paid Protest News',
                'description': f'{len(paid_news)} articles specifically about paid protesters.',
                'probability': min(40 + len(paid_news) * 8, 72),
                'evidence': [{'type': 'News', 'detail': n.get('title', '')[:100]} for n in paid_news[:2]]
            })
        
        # 5. State clustering
        state_counts = {}
        for job in jobs:
            state = job.get('state', '')
            if state:
                state_counts[state] = state_counts.get(state, 0) + (job.get('suspicion_score', 0) / 10)
        for org in orgs:
            state = org.get('state', '')
            if state:
                state_counts[state] = state_counts.get(state, 0) + (org.get('risk_score', 0) / 10)
        
        hot_states = [(s, c) for s, c in state_counts.items() if c > 20]
        hot_states.sort(key=lambda x: x[1], reverse=True)
        
        if hot_states:
            top_state = hot_states[0]
            correlations.append({
                'type': 'State Hotspot',
                'description': f'{top_state[0]} showing concentrated activity.',
                'probability': min(45 + int(top_state[1]), 75),
                'evidence': [{'type': 'State', 'detail': f'{s} (score: {int(c)})'} for s, c in hot_states[:3]]
            })
        
        correlations.sort(key=lambda x: x.get('probability', 0), reverse=True)
        return correlations[:6]
    
    def _build_prompt(self, memory: Dict, new_data: Dict, correlations: List) -> str:
        """Build a focused prompt for the AI"""
        news_summary = [{'title': a.get('title', '')[:80], 'relevance': a.get('relevance_score', 0)} 
                       for a in new_data.get('news', [])[:8]]
        org_summary = [{'name': o.get('name', '')[:50], 'risk': o.get('risk_score', 0)} 
                      for o in new_data.get('nonprofits', [])[:6]]
        job_summary = [{'title': j.get('title', '')[:40], 'score': j.get('suspicion_score', 0)} 
                      for j in new_data.get('jobs', [])[:5]]
        
        correlation_summary = [{'type': c['type'], 'prob': c['probability']} for c in correlations[:4]]
        
        return f"""You are analyzing data for astroturf (fake grassroots) detection in the US.

DATA:
- News: {len(news_summary)} articles (top: {max([n['relevance'] for n in news_summary], default=0)}%)
- Orgs: {len(org_summary)} flagged (top: {max([o['risk'] for o in org_summary], default=0)}%)  
- Jobs: {len(job_summary)} tracked (top: {max([j['score'] for j in job_summary], default=0)}%)
- Correlations: {json.dumps(correlation_summary)}

NEWS: {[n['title'][:60] for n in news_summary[:3]]}

Respond with ONLY valid JSON:
{{"confidence":NUMBER_35_TO_85,"confidence_factors":[{{"factor":"NAME","score":NUMBER,"detail":"WHY"}}],"summary":"ONE_SENTENCE","alerts":[{{"title":"TITLE","description":"DESCRIPTION","confidence":NUMBER,"sources":["SRC"]}}],"hot_states":["TX","CA"]}}"""
    
    def _call_api(self, prompt: str) -> str:
        """Call Claude API"""
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        payload = {
            'model': self.MODEL,
            'max_tokens': self.MAX_TOKENS,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        response = requests.post(self.API_URL, headers=headers, json=payload, timeout=60)
        if response.status_code == 200:
            data = response.json()
            return data.get('content', [{}])[0].get('text', '{}')
        else:
            raise Exception(f"API error: {response.status_code}")
    
    def _parse_response(self, response_text: str, memory: Dict, new_data: Dict) -> Dict[str, Any]:
        """Parse AI response"""
        try:
            text = response_text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            
            result = json.loads(text)
            
            alerts = []
            for a in result.get('alerts', []):
                if isinstance(a, dict):
                    alerts.append({
                        'title': a.get('title', 'Alert'),
                        'description': a.get('description', ''),
                        'confidence': a.get('confidence', 50),
                        'sources': a.get('sources', []),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })
            
            return {
                'systemConfidence': result.get('confidence', 50),
                'confidenceFactors': result.get('confidence_factors', []),
                'agentNotes': [{
                    'summary': result.get('summary', 'Analysis complete'),
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }],
                'alerts': alerts,
                'hot_states': result.get('hot_states', [])
            }
        except json.JSONDecodeError as e:
            print(f"  JSON parse error: {e}")
            return self._fallback_analysis(memory, new_data, [])
    
    def _fallback_analysis(self, memory: Dict, new_data: Dict, correlations: List) -> Dict[str, Any]:
        """Fallback when API unavailable"""
        news_count = len(new_data.get('news', []))
        org_count = len(new_data.get('nonprofits', []))
        job_count = len(new_data.get('jobs', []))
        
        confidence = 35
        factors = []
        alerts = []
        
        # News factor
        if news_count > 5:
            high_relevance = len([n for n in new_data.get('news', []) if n.get('relevance_score', 0) >= 60])
            news_score = min(high_relevance * 8 + 40, 80)
            confidence += 10
            factors.append({'factor': 'News Coverage', 'score': news_score, 'detail': f'{high_relevance} high-relevance articles'})
            
            paid_news = [n for n in new_data.get('news', []) if 'paid' in (n.get('title', '') or '').lower()]
            if paid_news:
                alerts.append({
                    'title': f'{len(paid_news)} articles about paid protesters',
                    'description': f'News mentions paid protesters: {paid_news[0].get("title", "")[:60]}',
                    'confidence': min(50 + len(paid_news) * 10, 75),
                    'sources': ['Google News', 'DuckDuckGo'],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
        
        # Org factor
        if org_count > 3:
            high_risk = len([o for o in new_data.get('nonprofits', []) if o.get('risk_score', 0) >= 70])
            org_score = min(high_risk * 12 + 35, 85)
            confidence += 10
            factors.append({'factor': 'Organization Risk', 'score': org_score, 'detail': f'{high_risk} high-risk orgs'})
            
            if high_risk >= 3:
                alerts.append({
                    'title': f'{high_risk} high-risk organizations detected',
                    'description': 'Multiple organizations flagged with suspicious patterns.',
                    'confidence': min(55 + high_risk * 5, 80),
                    'sources': ['FEC', 'ProPublica'],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
        
        # Job factor
        if job_count > 0:
            high_suspicion = len([j for j in new_data.get('jobs', []) if j.get('suspicion_score', 0) >= 50])
            job_score = min(high_suspicion * 10 + 30, 75)
            confidence += 5
            factors.append({'factor': 'Job Postings', 'score': job_score, 'detail': f'{high_suspicion} suspicious postings'})
            
            if high_suspicion >= 2:
                alerts.append({
                    'title': f'{high_suspicion} suspicious job postings',
                    'description': 'Job postings with suspicious keywords detected.',
                    'confidence': min(45 + high_suspicion * 8, 70),
                    'sources': ['Adzuna', 'USAJobs'],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
        
        # Correlation-based alerts
        for corr in correlations[:2]:
            if corr.get('probability', 0) >= 60:
                alerts.append({
                    'title': f"Pattern: {corr.get('type', 'Unknown')}",
                    'description': corr.get('description', ''),
                    'confidence': corr.get('probability', 50),
                    'sources': [e.get('type', 'Data') for e in corr.get('evidence', [])[:3]],
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })
        
        # Hot states
        state_activity = {}
        for job in new_data.get('jobs', []):
            state = job.get('state', '')
            if state:
                state_activity[state] = state_activity.get(state, 0) + job.get('suspicion_score', 0)
        for org in new_data.get('nonprofits', []):
            state = org.get('state', '')
            if state:
                state_activity[state] = state_activity.get(state, 0) + org.get('risk_score', 0)
        
        hot_states = sorted(state_activity.items(), key=lambda x: x[1], reverse=True)[:3]
        hot_states = [s[0] for s in hot_states if s[1] > 50]
        
        return {
            'systemConfidence': min(confidence, 85),
            'confidenceFactors': factors[:3],
            'agentNotes': [{
                'summary': f'Monitoring {news_count} news, {org_count} orgs, {job_count} jobs. {len(alerts)} alerts.',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }],
            'alerts': alerts,
            'hot_states': hot_states,
            'connections': correlations
        }


if __name__ == "__main__":
    agent = AIAgent()
    test_data = {
        'news': [{'title': 'Paid protesters spotted at Dallas rally', 'relevance_score': 75}],
        'jobs': [{'title': 'Rally Support Staff', 'city': 'Dallas', 'state': 'TX', 'suspicion_score': 65}],
        'nonprofits': [{'name': 'Citizens for Freedom PAC', 'risk_score': 72, 'state': 'TX'}]
    }
    result = agent.analyze({}, test_data, {})
    print(json.dumps(result, indent=2))
