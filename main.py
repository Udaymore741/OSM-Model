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
    
    # Display comprehensive user profile
    display_user_profile(user_data)
    
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
        # Display comprehensive tech profile
        print("\nTechnology Profile:")
        print("Languages:", format_skill_list(tech_profile.get("languages", [])))
        print("Frameworks:", format_skill_list(tech_profile.get("frameworks", [])))
        print("Tools:", format_skill_list(tech_profile.get("tools", [])))
        print("Domains:", format_skill_list(tech_profile.get("domains", [])))
        
        # Enhanced repository analysis
        print("\nRepository Analysis:")
        for repo in repositories:
            print(f"\n{repo['name']}:")
            print("Language Statistics:")
            if repo.get('language_stats'):
                total_bytes = sum(repo['language_stats'].values())
                for lang, bytes_count in repo['language_stats'].items():
                    percentage = (bytes_count / total_bytes * 100) if total_bytes > 0 else 0
                    print(f"- {lang}: {percentage:.1f}%")
            else:
                print("- No language statistics available")
            
            print("\nDetected Technologies:")
            if repo.get('detected_tech_stack'):
                for tech, files in repo['detected_tech_stack'].items():
                    print(f"- {tech}")
            else:
                print("- No technologies detected")
        
        # Fetch and analyze React repository issues
        print("\nFetching React repository issues...")
        react_issues = github.get_repository_issues("facebook", "react", state="open", per_page=20)
        
        if not react_issues:
            print("Error: Could not fetch React repository issues")
            return
            
        # Analyze each issue and find matches using enhanced tech profile
        print("\nAnalyzing issues and finding matches...")
        issue_matches = []
        
        for issue in react_issues:
            try:
                # Create a simplified issue object for analysis
                simplified_issue = {
                    'title': issue.get('title', ''),
                    'body': issue.get('body', ''),
                    'labels': issue.get('labels', []),
                    'number': issue.get('number', 0)
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
                
                # Construct issue URL
                issue_url = f"https://github.com/facebook/react/issues/{simplified_issue['number']}"
                
                # Add to matches list with issue details
                issue_matches.append({
                    "issue_number": simplified_issue['number'],
                    "title": simplified_issue['title'],
                    "url": issue_url,
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
                print(f"Warning: Skipping issue due to error: {str(e)}")
                continue
        
        if not issue_matches:
            print("No matching issues found.")
            return
        
        # Sort issues by match percentage and get top 5
        issue_matches.sort(key=lambda x: x["match_percentage"], reverse=True)
        top_matches = issue_matches[:5]
        
        # Display top 5 matching issues
        print("\nTop 5 Matching Issues:")
        for idx, match in enumerate(top_matches, 1):
            print(f"\n{idx}. Issue #{match['issue_number']}: {match['title']}")
            print(f"   URL: {match['url']}")
            print(f"   Match Score: {match['match_score']}/10 ({match['match_percentage']}%)")
            print(f"   Match Level: {match['match_level']}")
            print("\n   Required Skills:")
            print(f"   - Languages: {format_skill_list(match['required_skills']['languages'])}")
            print(f"   - Frameworks: {format_skill_list(match['required_skills']['frameworks'])}")
            print(f"   - Domain Knowledge: {format_skill_list(match['required_skills']['domain_knowledge'])}")
            print(f"   - Experience Level: {match['required_skills']['experience_level']}")
            print("\n   Your Skills:")
            print(f"   - Matching: {format_skill_list(match['matching_skills'])}")
            print(f"   - Missing: {format_skill_list(match['missing_skills'])}")
        
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 