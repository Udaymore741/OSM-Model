import os
import json
import requests
from typing import List, Dict, Any, Tuple

class GeminiAnalyzer:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        
    def _call_gemini_api(self, prompt: str) -> Dict[str, Any]:
        """Make a call to the Gemini API"""
        headers = {
            'Content-Type': 'application/json'
        }
        
        data = {
            "contents": [{
                "parts": [{
                    "text": prompt + "\nPlease respond with ONLY the JSON object, no markdown or other text."
                }]
            }]
        }
        
        url = f"{self.api_url}?key={self.api_key}"
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            response_data = response.json()
            
            if 'error' in response_data:
                print(f"API Error: {response_data['error']}")
                return {}
                
            # Extract the text content from the response
            if 'candidates' in response_data:
                for candidate in response_data['candidates']:
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
            
        except requests.exceptions.RequestException as e:
            print(f"Error calling Gemini API: {e}")
            return {}

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

    def analyze_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a GitHub issue to extract required skills"""
        prompt = f"""Analyze this GitHub issue and identify required skills:

Issue Title: {issue.get('title')}
Labels: {', '.join(label['name'] for label in issue.get('labels', []))}
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

        return self._call_gemini_api(prompt)

    def compare_skills(self, user_skills: Dict[str, Any], issue_skills: Dict[str, Any]) -> Dict[str, Any]:
        """Compare user skills with issue requirements"""
        prompt = f"""Compare these user skills and issue requirements:

User Skills:
{json.dumps(user_skills, indent=2)}

Issue Requirements:
{json.dumps(issue_skills, indent=2)}

Analyze the match and return a JSON object with these exact keys:
{{
  "matching_skills": ["list of skills the user has that match requirements"],
  "missing_skills": ["list of required skills the user is missing"],
  "match_percentage": 85.5,
  "match_level": "Strong Match/Partial Match/Weak Match",
  "experience_match": "Meets Requirements/Below Requirements/Exceeds Requirements"
}}"""

        result = self._call_gemini_api(prompt)
        if not result:
            return {
                "matching_skills": [],
                "missing_skills": [],
                "match_percentage": 0,
                "match_level": "Weak Match",
                "experience_match": "Unknown"
            }
        return result

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