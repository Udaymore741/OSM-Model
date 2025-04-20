import os
import json
import requests
import time
import logging
from typing import List, Dict, Any, Tuple, Optional

logger = logging.getLogger(__name__)

class GeminiAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        self.max_retries = 3
        self.retry_delay = 2  # seconds
        
    def _call_gemini_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}?key={self.api_key}"
        headers = {
            "Content-Type": "application/json",
        }
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }]
        }

        for attempt in range(self.max_retries):
            try:
                # Add exponential backoff
                if attempt > 0:
                    wait_time = min(2 ** attempt, 30)  # Cap at 30 seconds
                    logger.warning(f"Waiting {wait_time} seconds before retry {attempt + 1}...")
                    time.sleep(wait_time)
                    
                response = requests.post(url, headers=headers, json=data, timeout=30)
                
                if response.status_code == 429:  # Rate limit
                    wait_time = int(response.headers.get('Retry-After', 30))
                    logger.warning(f"Rate limited. Waiting {wait_time} seconds before retry...")
                    time.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                return response.json()
                
            except requests.exceptions.RequestException as e:
                logger.error(f"API call failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    continue
                else:
                    logger.error("Max retries reached. Giving up.")
                    return None
                    
        return None

    def analyze_user_profile(self, user_data: Dict[str, Any], repositories: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze a GitHub user's profile and repositories to extract their skills"""
        # Create a detailed prompt for user analysis
        repo_details = []
        for repo in repositories:
            repo_details.append(f"""
Repository: {repo.get('name')}
Description: {repo.get('description', 'No description')}
Language: {repo.get('language', 'Not specified')}
Topics: {', '.join(repo.get('topics', []))}
Stars: {repo.get('stargazers_count', 0)}
Forks: {repo.get('forks_count', 0)}
""")

        prompt = f"""Analyze this GitHub user's profile and provide a detailed skill assessment:

User Profile:
- Username: {user_data.get('login')}
- Public Repos: {user_data.get('public_repos')}
- Bio: {user_data.get('bio', 'Not provided')}
- Location: {user_data.get('location', 'Not provided')}
- Company: {user_data.get('company', 'Not provided')}

Repository Information:
{''.join(repo_details)}

Based on this information, create a JSON object with:
1. Primary programming languages they use
2. Frameworks and libraries they're familiar with
3. Development tools they use
4. Technical domains they work in
5. Skill levels for each identified skill

Return a JSON object with these exact keys:
{{
  "primary_languages": ["list of main programming languages"],
  "frameworks": ["list of frameworks and libraries"],
  "tools": ["list of development tools"],
  "domains": ["list of technical domains"],
  "skill_levels": {{"skill_name": "beginner/intermediate/advanced"}}
}}"""

        return self._call_gemini_api(prompt)

    def analyze_issue(self, issue: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a GitHub issue to extract required skills"""
        try:
            # Safely handle labels
            labels = issue.get('labels', [])
            if isinstance(labels, list):
                label_names = [label.get('name', '') if isinstance(label, dict) else str(label) for label in labels]
            else:
                label_names = [str(labels)]
            
            prompt = f"""Analyze this GitHub issue and identify required skills:

Issue Title: {issue.get('title', '')}
Labels: {', '.join(label_names)}
Description: {issue.get('body', 'No description provided')}

Based on this information, create a JSON object detailing:
1. Required programming languages
2. Required frameworks and libraries
3. Required technical knowledge
4. Required experience level
5. Issue complexity and priority

Return a JSON object with these exact keys:
{{
  "required_languages": ["list of required programming languages"],
  "required_frameworks": ["list of required frameworks"],
  "required_domain_knowledge": ["list of required technical knowledge"],
  "experience_level": "beginner/intermediate/advanced",
  "priority": "low/medium/high",
  "complexity": "low/medium/high"
}}"""

            # Add delay between API calls to avoid rate limiting
            time.sleep(1)  # 1 second delay between calls
            
            response = self._call_gemini_api(prompt)
            
            if not response:
                logger.error("Failed to get response from Gemini API")
                return None
                
            return self._parse_response(response)
            
        except Exception as e:
            logger.error(f"Error analyzing issue: {str(e)}")
            return None

    def _parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        # Extract the text content from the response
        if 'candidates' in response:
            for candidate in response['candidates']:
                if 'content' in candidate:
                    for part in candidate['content'].get('parts', []):
                        if 'text' in part:
                            text = part['text'].strip()
                            # Remove any markdown code block markers
                            text = text.replace('```json', '').replace('```', '').strip()
                            try:
                                # Try to parse the text as JSON
                                return json.loads(text)
                            except json.JSONDecodeError as e:
                                print(f"Failed to parse response as JSON: {e}")
                                print(f"Raw text: {text}")
                                return {}
        
        print("No valid response content found")
        return {}

    def compare_skills(self, user_skills: Dict[str, Any], required_skills: Dict[str, Any]) -> Dict[str, Any]:
        """Compare user skills with issue requirements"""
        prompt = f"""Compare these user skills and issue requirements:

User Skills:
{json.dumps(user_skills, indent=2)}

Issue Requirements:
{json.dumps(required_skills, indent=2)}

Analyze the match and return a JSON object with these exact keys:
{{
  "matching_skills": ["list of skills the user has that match requirements"],
  "missing_skills": ["list of required skills the user is missing"],
  "match_percentage": 85.5,
  "match_level": "Strong Match/Partial Match/Weak Match",
  "experience_match": "Meets Requirements/Below Requirements/Exceeds Requirements"
}}"""

        try:
            response = self._call_gemini_api(prompt)
            
            if not response:
                logger.error("Failed to get response from Gemini API for skill comparison")
                return {
                    "match_percentage": 0,
                    "match_level": "unknown",
                    "matching_skills": [],
                    "missing_skills": [],
                    "experience_match": "Unknown"
                }
                
            return self._parse_comparison_response(response)
            
        except Exception as e:
            logger.error(f"Error comparing skills: {str(e)}")
            return {
                "match_percentage": 0,
                "match_level": "unknown",
                "matching_skills": [],
                "missing_skills": [],
                "experience_match": "Unknown"
            }

    def _parse_comparison_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        if 'candidates' in response:
            for candidate in response['candidates']:
                if 'content' in candidate:
                    for part in candidate['content'].get('parts', []):
                        if 'text' in part:
                            text = part['text'].strip()
                            # Remove any markdown code block markers
                            text = text.replace('```json', '').replace('```', '').strip()
                            try:
                                # Try to parse the text as JSON
                                return json.loads(text)
                            except json.JSONDecodeError as e:
                                print(f"Failed to parse response as JSON: {e}")
                                print(f"Raw text: {text}")
                                return {}
        
        print("No valid response content found")
        return {}

    def _format_repos_for_prompt(self, repositories: List[Dict[str, Any]]) -> str:
        """Format repository information for the prompt"""
        repo_texts = []
        for repo in repositories:
            repo_text = f"""
            Repository: {repo.get('name')}
            Description: {repo.get('description', 'No description')}
            Language: {repo.get('language', 'Not specified')}
            Topics: {', '.join(repo.get('topics', []))}
            """
            repo_texts.append(repo_text)
        return '\n'.join(repo_texts)

    def _compare_experience_levels(self, user_skill_levels: Dict[str, str], required_level: str) -> str:
        """Compare user's skill levels with required experience level"""
        # Convert experience levels to numeric values
        level_values = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'unknown': 0
        }
        
        # Get the average user skill level
        if not user_skill_levels:
            return "Unknown"
            
        user_levels = [level_values.get(level.lower(), 0) for level in user_skill_levels.values()]
        avg_user_level = sum(user_levels) / len(user_levels)
        required_value = level_values.get(required_level.lower(), 0)
        
        if required_value == 0 or avg_user_level == 0:
            return "Unknown"
        elif avg_user_level >= required_value:
            return "Meets or Exceeds Requirements"
        else:
            return "Below Requirements"

def create_analyzer(api_key: str) -> GeminiAnalyzer:
    """Create a new instance of the GeminiAnalyzer"""
    return GeminiAnalyzer(api_key) 