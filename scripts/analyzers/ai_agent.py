"""AI Agent - Intelligent Analysis Engine using Claude API"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, List

class AIAgent:
    API_URL = "https://api.anthropic.com/v1/messages"
    MODEL = "claude-3-haiku-20240307"
    MAX_TOKENS = 1024
    
    def __init__(self):
        self.api_key = os.environ.get('ANTHROPIC_API_KEY')
        self.enabled = bool(self.api_key)
        if not self.enabled:
            print("  Warning: ANTHROPIC_API_KEY not set, AI analysis disabled")
    
    def analyze(self, memory: Dict[str, Any], new_data: Dict[str, Any], patterns: Dict[str, Any]) -> Dict[str, Any]:
        if not self.enabled:
            return self._fallback_analysis(patterns)
        try:
            prompt = self._build_prompt(memory, new_data, patterns)
            response = self._call_api(prompt)
            return self._parse_response(response)
        except Exception as e:
            print(f"  AI analysis error: {e}")
            return self._fallback_analysis(patterns)
    
    def _build_prompt(self, memory: Dict[str, Any], new_data: Dict[str, Any], patterns: Dict[str, Any]) -> str:
        summary = {
            'anomalies': patterns.get('anomalies', [])[:5],
            'high_risk_orgs': patterns.get('org_patterns', {}).get('high_risk_orgs', [])[:3],
            'job_spikes': patterns.get('job_patterns', {}).get('spikes', [])[:3],
            'geographic_hotspots': patterns.get('correlations', {}).get('geographicHotspots', [])[:3],
            'recent_alerts': len(memory.get('timeline', [])),
            'known_patterns': memory.get('knownAstroturfPatterns', {}).get('threeWordNames', [])[:5]
        }
        return f"""Analyze this data for potential astroturf activity.

DATA SUMMARY:
{json.dumps(summary, indent=2)}

TASK: Assess likelihood (0-100 confidence), identify concerns, generate alerts, provide recommendations.

RESPONSE FORMAT (JSON only):
{{"confidence": <0-100>, "summary": "<assessment>", "alerts": [{{"title": "<title>", "description": "<desc>", "severity": "high|medium|low", "confidence": <0-100>, "factors": [{{"name": "<factor>", "value": "<value>"}}]}}], "recommendations": ["<rec1>"], "timeline_events": [{{"date": "<ISO date>", "title": "<title>", "description": "<desc>", "type": "job|org|event", "tags": ["<tag>"]}}]}}

Respond with ONLY valid JSON."""
    
    def _call_api(self, prompt: str) -> str:
        headers = {"x-api-key": self.api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
        data = {"model": self.MODEL, "max_tokens": self.MAX_TOKENS, "messages": [{"role": "user", "content": prompt}]}
        response = requests.post(self.API_URL, headers=headers, json=data, timeout=60)
        if response.status_code != 200:
            raise Exception(f"API error: {response.status_code}")
        return response.json().get('content', [{}])[0].get('text', '{}')
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        try:
            text = response_text.strip()
            for prefix in ['```json', '```']:
                if text.startswith(prefix):
                    text = text[len(prefix):]
            if text.endswith('```'):
                text = text[:-3]
            result = json.loads(text)
            return {'confidence': result.get('confidence', 0), 'summary': result.get('summary', ''), 'alerts': result.get('alerts', []), 'recommendations': result.get('recommendations', []), 'timeline_events': result.get('timeline_events', [])}
        except json.JSONDecodeError as e:
            print(f"  Failed to parse AI response: {e}")
            return self._fallback_analysis({})
    
    def _fallback_analysis(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        alerts, timeline_events, confidence = [], [], 0
        for anomaly in patterns.get('anomalies', [])[:5]:
            severity = anomaly.get('severity', 'low')
            confidence += 10 if severity == 'high' else 5
            alerts.append({'title': f"Detected: {anomaly.get('type', 'Unknown')}", 'description': anomaly.get('description', ''), 'severity': severity, 'confidence': 50, 'factors': [{'name': 'Type', 'value': anomaly.get('type', 'unknown')}, {'name': 'Source', 'value': 'pattern_analysis'}]})
            timeline_events.append({'date': datetime.utcnow().isoformat() + 'Z', 'title': anomaly.get('description', 'Pattern detected'), 'description': f"Automated detection: {anomaly.get('type', 'unknown')}", 'type': 'event', 'tags': [anomaly.get('type', 'unknown'), severity]})
        return {'confidence': min(confidence, 100), 'summary': f"Detected {len(patterns.get('anomalies', []))} potential anomalies requiring review.", 'alerts': alerts, 'recommendations': ["Review flagged organizations manually", "Monitor geographic hotspots for activity changes"], 'timeline_events': timeline_events}

if __name__ == '__main__':
    agent = AIAgent()
    test_patterns = {'anomalies': [{'type': 'high_risk_org', 'severity': 'high', 'description': 'Test org detected'}]}
    result = agent.analyze({'timeline': [], 'knownAstroturfPatterns': {'threeWordNames': ['Keep Dallas Safe']}}, {'jobs': [], 'nonprofits': [], 'fec': []}, test_patterns)
    print(json.dumps(result, indent=2))
