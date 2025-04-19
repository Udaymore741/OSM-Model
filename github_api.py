import requests
import base64
from typing import List, Dict, Any, Optional
import time
import json
import os
from datetime import datetime, timedelta

class GitHubAPI:
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            'Accept': 'application/vnd.github.v3+json',
            'Authorization': 'token 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'
        }
        self.cache_dir = "github_cache"  # Directory to store cache files
        self._ensure_cache_dir()
        self.cache_duration = 3600  # Cache duration in seconds (1 hour)
        self.rate_limit = self._check_rate_limit()

    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, key: str) -> str:
        """Get the file path for a cache key"""
        # Create a safe filename from the cache key
        safe_key = "".join(c for c in key if c.isalnum() or c in ('-', '_'))
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def _get_from_cache(self, key: str) -> Dict[str, Any]:
        """Get data from cache if it exists and is not expired"""
        cache_path = self._get_cache_path(key)
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
                # Check if cache is still valid
                if datetime.now().timestamp() - cached_data['timestamp'] < self.cache_duration:
                    return cached_data['data']
        return None

    def _save_to_cache(self, key: str, data: Any):
        """Save data to cache with current timestamp"""
        cache_path = self._get_cache_path(key)
        cache_data = {
            'timestamp': datetime.now().timestamp(),
            'data': data
        }
        with open(cache_path, 'w') as f:
            json.dump(cache_data, f)

    def _check_rate_limit(self) -> Dict[str, Any]:
        """Check GitHub API rate limit"""
        response = requests.get(f"{self.base_url}/rate_limit", headers=self.headers)
        if response.status_code == 200:
            return response.json()['resources']['core']
        return {'remaining': 0, 'reset': 0}

    def _wait_for_rate_limit(self):
        """Wait if rate limit is reached"""
        self.rate_limit = self._check_rate_limit()
        if self.rate_limit['remaining'] < 10:
            reset_time = self.rate_limit['reset']
            wait_time = (reset_time - time.time()) + 10
            if wait_time > 0:
                print(f"\nRate limit reached. Waiting {wait_time:.0f} seconds...")
                time.sleep(wait_time)

    def get_user_data(self, username: str) -> Dict[str, Any]:
        """Get user's GitHub profile data with caching"""
        cache_key = f"user_data_{username}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            self._wait_for_rate_limit()
            response = requests.get(f"{self.base_url}/users/{username}", headers=self.headers)
            if response.status_code == 200:
                user_data = response.json()
                self._save_to_cache(cache_key, {
                    'name': user_data.get('name'),
                    'bio': user_data.get('bio'),
                    'location': user_data.get('location'),
                    'company': user_data.get('company'),
                    'public_repos': user_data.get('public_repos', 0)
                })
                return {
                    'name': user_data.get('name'),
                    'bio': user_data.get('bio'),
                    'location': user_data.get('location'),
                    'company': user_data.get('company'),
                    'public_repos': user_data.get('public_repos', 0)
                }
            return {}
        except Exception as e:
            print(f"Error fetching user data: {str(e)}")
            return {}

    def get_user_repositories(self, username: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Get user's repositories with caching"""
        cache_key = f"user_repos_{username}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            self._wait_for_rate_limit()
            response = requests.get(
                f"{self.base_url}/users/{username}/repos",
                headers=self.headers,
                params={'sort': 'updated', 'per_page': limit}
            )
            if response.status_code == 200:
                repos = []
                for repo in response.json():
                    self._wait_for_rate_limit()
                    topics_response = requests.get(
                        f"{self.base_url}/repos/{username}/{repo['name']}/topics",
                        headers=self.headers
                    )
                    topics = topics_response.json().get('names', []) if topics_response.status_code == 200 else []
                    
                    repos.append({
                        'name': repo['name'],
                        'description': repo.get('description'),
                        'language': repo.get('language'),
                        'topics': topics,
                        'stars': repo.get('stargazers_count', 0),
                        'forks': repo.get('forks_count', 0)
                    })
                self._save_to_cache(cache_key, repos)
                return repos
            return []
        except Exception as e:
            print(f"Error fetching repositories: {str(e)}")
            return []

    def get_repository_issues(self, owner_repo: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get issues from a repository with caching"""
        # Split owner and repo if needed
        if '/' not in owner_repo:
            owner_repo = f"facebook/{owner_repo}"  # Default to facebook organization if not specified
        
        cache_key = f"repo_issues_{owner_repo}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            self._wait_for_rate_limit()
            response = requests.get(
                f"{self.base_url}/repos/{owner_repo}/issues",
                headers=self.headers,
                params={'state': 'all', 'sort': 'updated', 'per_page': limit}  # Changed to 'all' to get both open and closed issues
            )
            if response.status_code == 200:
                issues = []
                for issue in response.json():
                    self._wait_for_rate_limit()
                    labels = [label['name'] for label in issue.get('labels', [])]
                    assignee = issue.get('assignee', {}).get('login') if issue.get('assignee') else None
                    
                    issues.append({
                        'title': issue['title'],
                        'body': issue.get('body'),
                        'labels': labels,
                        'number': issue['number'],
                        'created_at': issue['created_at'],
                        'updated_at': issue['updated_at'],
                        'comments': issue.get('comments', 0),
                        'assignee': assignee,
                        'state': issue.get('state', 'open')  # Added state to track if issue is open or closed
                    })
                self._save_to_cache(cache_key, issues)
                return issues
            return []
        except Exception as e:
            print(f"Error fetching issues: {str(e)}")
            return []

    def get_pinned_repositories(self, username: str) -> List[Dict[str, Any]]:
        """Get user's pinned repositories using GraphQL API"""
        cache_key = f"pinned_repos_{username}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        query = """
        {
          user(login: "%s") {
            pinnedItems(first: 6, types: [REPOSITORY]) {
              nodes {
                ... on Repository {
                  name
                  description
                  url
                  languages(first: 5) {
                    nodes {
                      name
                    }
                  }
                  repositoryTopics(first: 10) {
                    nodes {
                      topic {
                        name
                      }
                    }
                  }
                }
              }
            }
          }
        }
        """ % username

        try:
            self._wait_for_rate_limit()
            response = requests.post(
                self.graphql_url,
                headers=self.headers,
                json={'query': query}
            )
            
            if response.status_code == 200:
                data = response.json()
                pinned_repos = []
                
                for repo in data.get('data', {}).get('user', {}).get('pinnedItems', {}).get('nodes', []):
                    if repo:
                        languages = [lang['name'] for lang in repo.get('languages', {}).get('nodes', [])]
                        topics = [topic['topic']['name'] for topic in repo.get('repositoryTopics', {}).get('nodes', [])]
                        
                        pinned_repos.append({
                            'name': repo.get('name'),
                            'description': repo.get('description'),
                            'url': repo.get('url'),
                            'languages': languages,
                            'topics': topics
                        })
                
                self._save_to_cache(cache_key, pinned_repos)
                return pinned_repos
            return []
        except Exception as e:
            print(f"Error fetching pinned repositories: {str(e)}")
            return []

    def get_profile_readme(self, username: str) -> Optional[str]:
        """Get user's profile README content if it exists"""
        cache_key = f"profile_readme_{username}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            self._wait_for_rate_limit()
            response = requests.get(
                f"{self.base_url}/repos/{username}/{username}/readme",
                headers=self.headers
            )
            
            if response.status_code == 200:
                content = response.json().get('content', '')
                if content:
                    readme_content = base64.b64decode(content).decode('utf-8')
                    self._save_to_cache(cache_key, readme_content)
                    return readme_content
            return None
        except Exception as e:
            print(f"Error fetching profile README: {str(e)}")
            return None

    def get_user_events(self, username: str, limit: int = 30) -> List[Dict[str, Any]]:
        """Get user's recent GitHub events/contributions"""
        cache_key = f"user_events_{username}_{limit}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            self._wait_for_rate_limit()
            response = requests.get(
                f"{self.base_url}/users/{username}/events/public",
                headers=self.headers,
                params={'per_page': limit}
            )
            
            if response.status_code == 200:
                events = []
                for event in response.json():
                    event_data = {
                        'type': event.get('type'),
                        'repo': event.get('repo', {}).get('name'),
                        'created_at': event.get('created_at')
                    }
                    
                    # Add specific data based on event type
                    if event['type'] == 'PushEvent':
                        event_data['commits'] = len(event.get('payload', {}).get('commits', []))
                    elif event['type'] in ['IssuesEvent', 'PullRequestEvent']:
                        event_data['action'] = event.get('payload', {}).get('action')
                    
                    events.append(event_data)
                
                self._save_to_cache(cache_key, events)
                return events
            return []
        except Exception as e:
            print(f"Error fetching user events: {str(e)}")
            return []

    def get_user_gists(self, username: str) -> List[Dict[str, Any]]:
        """Get user's public gists"""
        cache_key = f"user_gists_{username}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            self._wait_for_rate_limit()
            response = requests.get(
                f"{self.base_url}/users/{username}/gists",
                headers=self.headers
            )
            
            if response.status_code == 200:
                gists = []
                for gist in response.json():
                    files = list(gist.get('files', {}).keys())
                    gists.append({
                        'id': gist.get('id'),
                        'description': gist.get('description'),
                        'files': files,
                        'created_at': gist.get('created_at'),
                        'updated_at': gist.get('updated_at'),
                        'url': gist.get('html_url')
                    })
                
                self._save_to_cache(cache_key, gists)
                return gists
            return []
        except Exception as e:
            print(f"Error fetching user gists: {str(e)}")
            return []

    def get_repo_languages(self, username: str, repo: str) -> Dict[str, int]:
        """Get language statistics for a repository"""
        cache_key = f"repo_languages_{username}_{repo}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        try:
            self._wait_for_rate_limit()
            response = requests.get(
                f"{self.base_url}/repos/{username}/{repo}/languages",
                headers=self.headers
            )
            
            if response.status_code == 200:
                languages = response.json()
                self._save_to_cache(cache_key, languages)
                return languages
            return {}
        except Exception as e:
            print(f"Error fetching repository languages: {str(e)}")
            return {}

    def detect_tech_stack(self, username: str, repo: str) -> Dict[str, List[str]]:
        """Detect technology stack from repository files"""
        cache_key = f"tech_stack_{username}_{repo}"
        cached_data = self._get_from_cache(cache_key)
        if cached_data:
            return cached_data

        tech_indicators = {
            'JavaScript': ['package.json', '.eslintrc', '.babelrc', 'webpack.config.js', '.js', '.jsx'],
            'TypeScript': ['tsconfig.json', '.ts', '.tsx', 'tslint.json'],
            'Python': ['requirements.txt', 'setup.py', 'Pipfile', 'pyproject.toml', '.py'],
            'Java': ['pom.xml', 'build.gradle', '.java', 'gradle.properties'],
            'Dart': ['pubspec.yaml', '.dart'],
            'Flutter': ['pubspec.yaml', 'android/app/build.gradle', 'ios/Runner.xcodeproj'],
            'Docker': ['Dockerfile', 'docker-compose.yml', '.dockerignore'],
            'React': ['package.json', '.jsx', '.tsx', 'react', 'react-dom'],
            'Vue.js': ['vue.config.js', '.vue'],
            'Angular': ['angular.json', '.angular-cli.json'],
            'Node.js': ['package.json', 'server.js', 'app.js', 'index.js'],
            'Express': ['express', 'routes/', 'app.js'],
            'Django': ['manage.py', 'wsgi.py', 'asgi.py'],
            'Flask': ['requirements.txt', 'app.py', 'wsgi.py'],
            'Spring': ['pom.xml', 'application.properties', 'application.yml'],
            'CSS': ['.scss', '.sass', '.less', '.css', 'style.css', 'tailwind.config.js'],
            'HTML': ['.html', '.htm', 'index.html'],
            'Mobile': ['android/', 'ios/', 'App.js', 'MainActivity.java', 'AppDelegate.swift'],
            'Database': ['schema.sql', 'migrations/', 'models/', 'repositories/'],
            'Testing': ['test/', 'tests/', 'spec/', '__tests__/', 'jest.config.js', 'pytest.ini']
        }

        framework_dependencies = {
            'React': ['react', 'react-dom', 'create-react-app', 'next', 'gatsby'],
            'Vue.js': ['vue', '@vue/cli', 'nuxt'],
            'Angular': ['@angular/core', '@angular/cli'],
            'Express': ['express'],
            'Next.js': ['next'],
            'Gatsby': ['gatsby'],
            'NestJS': ['@nestjs/core'],
            'Flutter': ['flutter'],
            'Django': ['django'],
            'Flask': ['flask'],
            'Spring': ['spring-boot', 'spring-core'],
            'Mobile': ['react-native', 'ionic', 'cordova', 'capacitor']
        }

        try:
            self._wait_for_rate_limit()
            # First get the repository tree to check all files and directories
            response = requests.get(
                f"{self.base_url}/repos/{username}/{repo}/git/trees/main?recursive=1",
                headers=self.headers
            )
            
            if response.status_code == 404:
                # Try master branch if main doesn't exist
                response = requests.get(
                    f"{self.base_url}/repos/{username}/{repo}/git/trees/master?recursive=1",
                    headers=self.headers
                )
            
            detected_tech = {}
            files = []
            
            if response.status_code == 200:
                tree = response.json().get('tree', [])
                # Exclude node_modules and similar dependency directories
                files = [item['path'] for item in tree 
                        if item['type'] == 'blob' 
                        and not any(x in item['path'].lower() for x in ['node_modules/', 'vendor/', 'dist/', 'build/'])]
            else:
                # Fallback to contents API if tree API fails
                response = requests.get(
                    f"{self.base_url}/repos/{username}/{repo}/contents",
                    headers=self.headers
                )
                if response.status_code == 200:
                    contents = response.json()
                    files = [item['path'] for item in contents 
                            if item['type'] == 'file'
                            and not any(x in item['path'].lower() for x in ['node_modules/', 'vendor/', 'dist/', 'build/'])]
                    
                    # Also check for common subdirectories
                    for item in contents:
                        if (item['type'] == 'dir' and 
                            not any(x in item['path'].lower() for x in ['node_modules', 'vendor', 'dist', 'build'])):
                            subdir_response = requests.get(item['url'], headers=self.headers)
                            if subdir_response.status_code == 200:
                                subdir_contents = subdir_response.json()
                                files.extend([f"{item['name']}/{subitem['name']}" 
                                           for subitem in subdir_contents 
                                           if subitem['type'] == 'file'])
            
            # Check for package.json to detect JavaScript frameworks
            if 'package.json' in files:
                try:
                    pkg_response = requests.get(
                        f"{self.base_url}/repos/{username}/{repo}/contents/package.json",
                        headers=self.headers
                    )
                    if pkg_response.status_code == 200:
                        content = base64.b64decode(pkg_response.json()['content']).decode('utf-8')
                        pkg_data = json.loads(content)
                        all_deps = {
                            **pkg_data.get('dependencies', {}),
                            **pkg_data.get('devDependencies', {})
                        }
                        
                        # Check for frameworks in dependencies
                        for framework, deps in framework_dependencies.items():
                            if any(dep in all_deps for dep in deps):
                                detected_tech[framework] = ['package.json']
                                
                        # Add Node.js if it's a JavaScript project
                        if all_deps:
                            detected_tech['Node.js'] = ['package.json']
                except Exception as e:
                    print(f"Error parsing package.json: {str(e)}")
            
            # Check for pubspec.yaml to detect Flutter/Dart
            if 'pubspec.yaml' in files:
                try:
                    pubspec_response = requests.get(
                        f"{self.base_url}/repos/{username}/{repo}/contents/pubspec.yaml",
                        headers=self.headers
                    )
                    if pubspec_response.status_code == 200:
                        content = base64.b64decode(pubspec_response.json()['content']).decode('utf-8')
                        if 'flutter:' in content:
                            detected_tech['Flutter'] = ['pubspec.yaml']
                        detected_tech['Dart'] = ['pubspec.yaml']
                except Exception as e:
                    print(f"Error parsing pubspec.yaml: {str(e)}")
            
            # Check for other technology indicators
            for tech, indicators in tech_indicators.items():
                found_files = []
                for file in files:
                    if any(indicator in file for indicator in indicators):
                        found_files.append(file)
                if found_files:
                    if tech not in detected_tech:
                        detected_tech[tech] = []
                    detected_tech[tech].extend(found_files)
            
            # Clean up duplicates in file lists
            detected_tech = {k: list(set(v)) for k, v in detected_tech.items()}
            
            self._save_to_cache(cache_key, detected_tech)
            return detected_tech
            
        except Exception as e:
            print(f"Error detecting tech stack: {str(e)}")
            return {} 