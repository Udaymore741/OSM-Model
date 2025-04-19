import json
from gemini_analyzer import create_analyzer
from github_fetcher import GitHubFetcher
import sys

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

def main():
    # Initialize the GitHub fetcher
    github = GitHubFetcher()
    
    # Get GitHub username from user
    username = input("Enter GitHub username: ")
    
    # Fetch comprehensive user profile and repositories
    print(f"\nFetching comprehensive data for user {username}...")
    user_data = github.get_user_profile(username)
    if not user_data:
        print("Error: Could not fetch user profile")
        return
    
    # Fetch repositories with enhanced data
    repositories = github.get_user_repositories(username)
    if not repositories:
        print("Error: Could not fetch user repositories")
        return
    
    # Get comprehensive tech profile
    tech_profile = github.get_user_tech_profile(username)
    
    # Initialize the Gemini analyzer
    api_key = "AIzaSyCxstWuvZ3GlNev2eRVvflbE9M5okpVLNA"
    analyzer = create_analyzer(api_key)
    
    try:
        # Prepare user skills data
        user_skills_data = {
            "languages": tech_profile.get("languages", []),
            "frameworks": tech_profile.get("frameworks", []),
            "tools": tech_profile.get("tools", []),
            "domains": tech_profile.get("domains", [])
        }
        
        # Display user skills and languages
        print("\nUser Profile Data:")
        print(json.dumps({
            "skills": {
                "languages": user_skills_data["languages"],
                "frameworks": user_skills_data["frameworks"],
                "tools": user_skills_data["tools"],
                "domains": user_skills_data["domains"]
            }
        }, indent=2))
        
        # Load issues from github_issues.json
        try:
            with open("github_issues.json", "r", encoding="utf-8") as f:
                all_issues = json.load(f)
        except FileNotFoundError:
            print("Error: github_issues.json not found. Please run fetch_issues.py first.")
            return
        except json.JSONDecodeError:
            print("Error: Invalid JSON format in github_issues.json")
            return
        
        # Analyze each issue and find matches using enhanced tech profile
        issue_matches = []
        
        for repo_name, issues in all_issues.items():
            for issue in issues:
                try:
                    # Create a simplified issue object for analysis
                    simplified_issue = {
                        'title': issue.get('title', ''),
                        'body': issue.get('bodyText', ''),
                        'labels': [label['name'] for label in issue.get('labels', {}).get('nodes', [])],
                        'number': issue.get('number', 0),
                        'url': issue.get('url', ''),
                        'createdAt': issue.get('createdAt', '')
                    }
                    
                    # Analyze issue requirements
                    issue_requirements = analyzer.analyze_issue(simplified_issue)
                    
                    if not issue_requirements:
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
                        "labels": simplified_issue['labels'],
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
                    # print(f"Warning: Skipping issue due to error: {str(e)}")
                    continue
        
        if not issue_matches:
            print("No matching issues found.")
            return
        
        # Sort issues by multiple criteria to ensure consistent ordering
        issue_matches.sort(key=lambda x: (
            -x["match_percentage"],
            -len(x["matching_skills"]),
            x["repo_name"]
        ))
        
        # Get top 5 matches
        top_matches = issue_matches[:5]
        
        # Prepare the final data structure
        output_data = {
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
        
        # Print the data in a format that can be easily consumed by the frontend
        print("\nData for Frontend:")
        print(json.dumps(output_data, indent=2))
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 