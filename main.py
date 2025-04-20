import json
from gemini_analyzer import create_analyzer
from github_fetcher import GitHubFetcher
import sys
from typing import Dict, Any, Optional
import logging
import traceback
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def format_skill_list(skills: list) -> str:
    """Format a list of skills with proper formatting"""
    if not skills:
        return "None"
    return ", ".join(skills)

def calculate_score_out_of_10(match_percentage: float) -> float:
    """Convert match percentage to score out of 10"""
    return round((match_percentage / 100) * 10, 1)

def display_user_profile(profile: dict):
    """Display comprehensive user profile information"""
    print("\nUser Profile:")
    print(f"Name: {profile.get('name', 'N/A')}")
    print(f"Bio: {profile.get('bio', 'N/A')}")
    print(f"Location: {profile.get('location', 'N/A')}")
    print(f"Company: {profile.get('company', 'N/A')}")
    
    print("\nPinned Repositories:")
    for repo in profile.get('pinned_repositories', []):
        print(f"\n- {repo['name']}")
        print(f"  Description: {repo.get('description', 'N/A')}")
        print(f"  Languages: {format_skill_list(repo.get('languages', []))}")
        print(f"  Topics: {format_skill_list(repo.get('topics', []))}")
    
    print("\nRecent Activity:")
    for event in profile.get('recent_events', [])[:5]:  # Show last 5 events
        print(f"- {event['type']} on {event['repo']} ({event['created_at']})")
    
    if profile.get('gists'):
        print("\nRecent Gists:")
        for gist in profile['gists'][:3]:  # Show last 3 gists
            print(f"- {gist.get('description', 'No description')} ({len(gist['files'])} files)")

def analyze_github_user(username: str) -> Optional[Dict[str, Any]]:
    """Analyze a GitHub user's profile and return recommendations"""
    logger.debug(f"Starting analysis for user: {username}")
    
    try:
        # Initialize the GitHub fetcher
        github = GitHubFetcher()
        logger.debug("Initialized GitHub fetcher")
        
        # Fetch comprehensive user profile and repositories
        logger.debug(f"Fetching user profile for: {username}")
        user_data = github.get_user_profile(username)
        if not user_data:
            logger.error(f"Could not fetch user profile for: {username}")
            return None
        logger.debug(f"Successfully fetched user profile for: {username}")
        
        # Fetch repositories with enhanced data
        logger.debug(f"Fetching repositories for: {username}")
        repositories = github.get_user_repositories(username)
        if not repositories:
            logger.error(f"Could not fetch repositories for: {username}")
            return None
        logger.debug(f"Successfully fetched repositories for: {username}")
        
        # Get comprehensive tech profile
        logger.debug(f"Fetching tech profile for: {username}")
        tech_profile = github.get_user_tech_profile(username)
        if not tech_profile:
            logger.error(f"Could not fetch tech profile for: {username}")
            return None
        logger.debug(f"Successfully fetched tech profile for: {username}")
        
        # Initialize the Gemini analyzer
        api_key = "AIzaSyCxstWuvZ3GlNev2eRVvflbE9M5okpVLNA"
        analyzer = create_analyzer(api_key)
        logger.debug("Initialized Gemini analyzer")
        
        # Prepare user skills data
        user_skills_data = {
            "languages": tech_profile.get("languages", []),
            "frameworks": tech_profile.get("frameworks", []),
            "tools": tech_profile.get("tools", []),
            "domains": tech_profile.get("domains", [])
        }
        logger.debug(f"Prepared user skills data: {user_skills_data}")
        
        # Load issues from github_issues.json
        try:
            logger.debug("Loading issues from github_issues.json")
            with open("github_issues.json", "r", encoding="utf-8") as f:
                all_issues = json.load(f)
            logger.debug(f"Successfully loaded {len(all_issues)} repositories' issues")
        except FileNotFoundError:
            logger.error("github_issues.json not found")
            return None
        except json.JSONDecodeError:
            logger.error("Invalid JSON format in github_issues.json")
            return None
        
        # Analyze each issue and find matches using enhanced tech profile
        issue_matches = []
        logger.debug("Starting issue analysis")
        
        for repo_name, issues in all_issues.items():
            logger.debug(f"Analyzing issues for repository: {repo_name}")
            for issue in issues:
                try:
                    # Create a simplified issue object for analysis
                    simplified_issue = {
                        'title': issue.get('title', ''),
                        'body': issue.get('bodyText', ''),
                        'labels': issue.get('labels', {}).get('nodes', []),
                        'number': issue.get('number', 0),
                        'url': issue.get('url', ''),
                        'createdAt': issue.get('createdAt', '')
                    }
                    
                    # Analyze issue requirements
                    issue_requirements = analyzer.analyze_issue(simplified_issue)
                    if not issue_requirements:
                        logger.warning(f"Could not analyze issue {simplified_issue['number']} in {repo_name}")
                        continue
                    
                    # Compare skills using enhanced tech profile
                    skill_match = analyzer.compare_skills(tech_profile, issue_requirements)
                    if not skill_match:
                        continue
                    
                    # Calculate score out of 10
                    match_score = calculate_score_out_of_10(skill_match.get("match_percentage", 0))
                    
                    # Only include issues with a match score above threshold
                    if match_score < 3.0:  # Minimum threshold of 3/10
                        continue
                    
                    # Add to matches list with issue details
                    issue_matches.append({
                        "repo_name": repo_name,
                        "issue_title": simplified_issue['title'],
                        "issue_description": simplified_issue['body'],
                        "labels": [label.get('name', '') for label in simplified_issue['labels']],
                        "created_at": simplified_issue['createdAt'],
                        "match_percentage": skill_match.get("match_percentage", 0),
                        "match_score": match_score,
                        "match_level": skill_match.get("match_level", "unknown"),
                        "matching_skills": skill_match.get("matching_skills", []),
                        "missing_skills": skill_match.get("missing_skills", []),
                        "required_skills": {
                            "languages": issue_requirements.get("required_languages", []),
                            "frameworks": issue_requirements.get("required_frameworks", []),
                            "domain_knowledge": issue_requirements.get("required_domain_knowledge", []),
                            "experience_level": issue_requirements.get("experience_level", "unknown")
                        }
                    })
                except Exception as e:
                    logger.warning(f"Error processing issue: {str(e)}")
                    continue
        
        if not issue_matches:
            logger.warning("No matching issues found")
            return None
        
        # Sort issues by multiple criteria to ensure consistent ordering
        issue_matches.sort(key=lambda x: (
            -x["match_percentage"],
            -len(x["matching_skills"]),
            x["repo_name"]
        ))
        
        # Get top 5 matches
        top_matches = issue_matches[:5]
        logger.debug(f"Found {len(top_matches)} matching issues")
        
        # Prepare the final data structure
        result = {
            "user_profile": {
                "skills": {
                    "languages": user_skills_data["languages"],
                    "frameworks": user_skills_data["frameworks"],
                    "tools": user_skills_data["tools"],
                    "domains": user_skills_data["domains"]
                }
            },
            "recommended_issues": top_matches
        }
        
        logger.debug("Successfully completed analysis")
        return result
        
    except Exception as e:
        logger.error(f"Error in analyze_github_user: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def main():
    # Get GitHub username from user
    username = input("Enter GitHub username: ")
    
    # Analyze the user
    result = analyze_github_user(username)
    
    if result:
        print("\nData for Frontend:")
        print(json.dumps(result, indent=2))
    else:
        print("Error: Could not analyze user profile")

if __name__ == "__main__":
    main() 