from typing import List, Dict, Any, Optional
from github_api import GitHubAPI

class GitHubFetcher:
    def __init__(self):
        self.api = GitHubAPI()

    def get_user_profile(self, username: str) -> Dict[str, Any]:
        """Fetch comprehensive user profile data from GitHub"""
        profile_data = self.api.get_user_data(username)
        if not profile_data:
            return {}

        # Get pinned repositories
        pinned_repos = self.api.get_pinned_repositories(username)
        
        # Get profile README
        profile_readme = self.api.get_profile_readme(username)
        
        # Get recent events/contributions
        recent_events = self.api.get_user_events(username, limit=30)
        
        # Get user's gists
        gists = self.api.get_user_gists(username)

        # Combine all data
        return {
            **profile_data,
            'pinned_repositories': pinned_repos,
            'profile_readme': profile_readme,
            'recent_events': recent_events,
            'gists': gists
        }

    def get_user_repositories(self, username: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Fetch user's repositories with enhanced data"""
        repos = self.api.get_user_repositories(username, limit)
        if not repos:
            return []

        enhanced_repos = []
        for repo in repos:
            # Get detailed language statistics
            languages = self.api.get_repo_languages(username, repo['name'])
            
            # Detect technology stack
            tech_stack = self.api.detect_tech_stack(username, repo['name'])
            
            # Only add repositories that have actual content
            if languages or tech_stack or repo.get('description'):
                enhanced_repos.append({
                    **repo,
                    'language_stats': languages,
                    'detected_tech_stack': tech_stack
                })

        return enhanced_repos

    def get_repository_issues(self, owner: str, repo: str, state: str = "open", per_page: int = 100) -> List[Dict[str, Any]]:
        """Fetch issues from a specific repository"""
        return self.api.get_repository_issues(owner_repo=f"{owner}/{repo}")

    def get_repository_languages(self, owner: str, repo: str) -> Dict[str, int]:
        """Fetch language statistics for a repository"""
        return self.api.get_repo_languages(owner, repo)

    def get_user_tech_profile(self, username: str) -> Dict[str, Any]:
        """Generate a comprehensive technology profile for the user"""
        profile = self.get_user_profile(username)
        repositories = self.get_user_repositories(username, limit=20)  # Increased limit for better analysis
        
        tech_profile = {
            'languages': set(),
            'frameworks': set(),
            'tools': set(),
            'domains': set()
        }

        # Process pinned repositories first as they're usually most representative
        for repo in profile.get('pinned_repositories', []):
            if repo.get('languages'):
                tech_profile['languages'].update(repo['languages'])
            if repo.get('topics'):
                # Categorize topics into appropriate sets
                for topic in repo['topics']:
                    topic_lower = topic.lower()
                    if any(lang.lower() in topic_lower for lang in ['javascript', 'python', 'java', 'typescript', 'ruby', 'php']):
                        tech_profile['languages'].add(topic.capitalize())
                    elif any(fw in topic_lower for fw in ['react', 'vue', 'angular', 'django', 'flask', 'spring', 'express']):
                        tech_profile['frameworks'].add(topic)
                    elif any(tool in topic_lower for tool in ['docker', 'kubernetes', 'aws', 'git', 'mongodb', 'postgresql']):
                        tech_profile['tools'].add(topic)
                    else:
                        tech_profile['domains'].add(topic)

        # Process all repositories
        for repo in repositories:
            # Add languages from stats
            if repo.get('language_stats'):
                tech_profile['languages'].update(repo['language_stats'].keys())
            
            # Add primary language if not in stats
            if repo.get('language') and repo['language'] not in tech_profile['languages']:
                tech_profile['languages'].add(repo['language'])
            
            # Add technologies from detected stack
            if repo.get('detected_tech_stack'):
                for tech, _ in repo['detected_tech_stack'].items():
                    if tech in ['React', 'Vue.js', 'Angular', 'Django', 'Flask', 'Spring', 'Express']:
                        tech_profile['frameworks'].add(tech)
                    elif tech in ['Docker', 'Kubernetes', 'Node.js', 'MongoDB', 'PostgreSQL']:
                        tech_profile['tools'].add(tech)
                    else:
                        tech_profile['languages'].add(tech)

            # Extract domains from description
            if repo.get('description'):
                desc_lower = repo['description'].lower()
                domain_keywords = {
                    'web': ['web', 'frontend', 'backend', 'fullstack'],
                    'mobile': ['mobile', 'android', 'ios', 'react-native', 'flutter'],
                    'data science': ['data science', 'machine learning', 'deep learning', 'ai'],
                    'devops': ['devops', 'ci/cd', 'docker', 'kubernetes'],
                    'blockchain': ['blockchain', 'web3', 'smart contract'],
                    'security': ['security', 'cryptography', 'authentication']
                }
                for domain, keywords in domain_keywords.items():
                    if any(keyword in desc_lower for keyword in keywords):
                        tech_profile['domains'].add(domain)

        # Extract additional info from README
        if profile.get('profile_readme'):
            readme_lower = profile['profile_readme'].lower()
            # Look for technology mentions in README
            tech_keywords = {
                'languages': ['javascript', 'python', 'java', 'typescript', 'ruby', 'php', 'c++', 'c#'],
                'frameworks': ['react', 'vue', 'angular', 'django', 'flask', 'spring', 'express'],
                'tools': ['docker', 'kubernetes', 'aws', 'git', 'mongodb', 'postgresql']
            }
            for category, keywords in tech_keywords.items():
                for keyword in keywords:
                    if keyword in readme_lower:
                        tech_profile[category].add(keyword.capitalize())

        # Clean up and sort the results
        return {k: sorted(list(v)) for k, v in tech_profile.items() if v} 