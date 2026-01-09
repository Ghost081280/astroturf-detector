"""AI Agent - Claude API Analysis"""
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
        if not self.enabled:
            return self._fallback_analysis(memory, new_data, patterns)
        
        try:
            prompt = self._build_prompt(memory, new_data, patterns)
            response = self._call_api(prompt)
            return self._parse_response(response, memory, new_data)
        except Exception as e:
            print(f"  AI error: {e}")
            return self._fallback_analysis(memory, new_data, patterns)
    
    def _build_prompt(self, memory: Dict, new_data: Dict, patterns: Dict) -> str:
        news_summary = [{'title': a.get('title', '')[:100], 'publisher': a.get('publisher'), 'relevance': a.get('relevance_score', 0)} for a in new_data.get('news', [])[:10]]
        org_summary = [{'name': o.get('name'), 'state': o.get('state'), 'risk': o.get('risk_score', 0)} for o in new_data.get('nonprofits', [])[:10]]
        job_summary = [{'title': j.get('title', '')[:50], 'city': j.get('city'), 'score': j.get('suspicion_score', 0)} for j in new_data.get('jobs', [])[:5]]
        
        summary = {'news': news_summary, 'organizations': org_summary, 'jobs': job_summary}
        
        return f"""You are an OSINT analyst detecting astroturf (fake grassroots) activity in the US.

DATA COLLECTED:
{json.dumps(summary, indent=2)}

Analyze for signs of coordinated astroturf activity. Respond with ONLY valid JSON:
{{"confidence":50,"confidence_factors":[{{"factor":"Data Quality","score":50,"detail":"explanation"}}],"summary":"Brief assessment","alerts":[],"recommendations":["recommendation"]}}"""
    
    def _call_api(self, prompt: str) -> str:
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
        try:
            text = response_text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            result = json.loads(text)
            return {
                'systemConfidence': result.get('confidence', 50),
                'confidenceFactors': result.get('confidence_factors', []),
                'agentNotes': [{'summary': result.get('summary', 'Analysis complete'), 'timestamp': datetime.utcnow().isoformat() + 'Z'}],
                'alerts': result.get('alerts', []),
                'recommendations': result.get('recommendations', [])
            }
        except json.JSONDecodeError:
            return self._fallback_analysis(memory, new_data, {})
    
    def _fallback_analysis(self, memory: Dict, new_data: Dict, patterns: Dict) -> Dict[str, Any]:
        news_count = len(new_data.get('news', []))
        org_count = len(new_data.get('nonprofits', []))
        job_count = len(new_data.get('jobs', []))
        
        confidence = 35
        factors = []
        
        if news_count > 5:
            confidence += 10
            factors.append({'factor': 'News Coverage', 'score': min(news_count * 5, 80), 'detail': f'{news_count} relevant articles found'})
        
        if org_count > 3:
            confidence += 10
            high_risk = len([o for o in new_data.get('nonprofits', []) if o.get('risk_score', 0) >= 50])
            factors.append({'factor': 'Organization Risk', 'score': min(high_risk * 15 + 30, 85), 'detail': f'{high_risk} high-risk orgs identified'})
        
        if job_count > 0:
            suspicious = len([j for j in new_data.get('jobs', []) if j.get('suspicion_score', 0) >= 40])
            if suspicious > 0:
                confidence += 15
                factors.append({'factor': 'Job Postings', 'score': min(suspicious * 10 + 40, 90), 'detail': f'{suspicious} suspicious postings'})
        
        if not factors:
            factors.append({'factor': 'Data Collection', 'score': 40, 'detail': 'Limited data available'})
        
        return {
            'systemConfidence': min(confidence, 85),
            'confidenceFactors': factors,
            'agentNotes': [{'summary': f'Automated scan: {news_count} news, {org_count} orgs, {job_count} jobs tracked', 'timestamp': datetime.utcnow().isoformat() + 'Z'}],
            'alerts': [],
            'recommendations': ['Continue monitoring data sources', 'Review high-risk organizations']
        }

if __name__ == '__main__':
    agent = AIAgent()
    result = agent._fallback_analysis({}, {'news': [], 'nonprofits': [], 'jobs': []}, {})
    print(json.dumps(result, indent=2))
