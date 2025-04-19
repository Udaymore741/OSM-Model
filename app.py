import os
from dotenv import load_dotenv
from github_api import GitHubAPI
from nlp_processor import NLPProcessor
from skill_matcher import SkillMatcher

class IssueRecommender:
    def __init__(self):
        load_dotenv()
        self.github_api = GitHubAPI()
        self.nlp_processor = NLPProcessor()
        self.skill_matcher = SkillMatcher()

    def analyze_user_profile(self, username):
        """Analyze user's GitHub profile and repositories to extract skills"""
        user_data = self.github_api.get_user_data(username)
        repositories = self.github_api.get_user_repositories(username)
        user_skills = self.nlp_processor.extract_skills_from_repos(repositories)
        return user_skills

    def analyze_repository_issues(self, repo_owner, repo_name):
        """Analyze issues in a repository and extract required skills"""
        issues = self.github_api.get_repository_issues(repo_owner, repo_name)
        issues_with_skills = []
        
        for issue in issues:
            issue_skills = self.nlp_processor.extract_skills_from_issue(issue)
            issues_with_skills.append({
                'issue': issue,
                'required_skills': issue_skills
            })
        
        return issues_with_skills

    def get_recommended_issues(self, username, repo_owner, repo_name):
        """Get issues that match user's skills"""
        user_skills = self.analyze_user_profile(username)
        issues_with_skills = self.analyze_repository_issues(repo_owner, repo_name)
        
        recommended_issues = []
        for issue_data in issues_with_skills:
            match_score = self.skill_matcher.calculate_match_score(
                user_skills,
                issue_data['required_skills']
            )
            
            if match_score > 0.5:  # Threshold for recommendation
                recommended_issues.append({
                    'issue': issue_data['issue'],
                    'match_score': match_score,
                    'required_skills': issue_data['required_skills'],
                    'user_skills': user_skills
                })
        
        return sorted(recommended_issues, key=lambda x: x['match_score'], reverse=True)

if __name__ == "__main__":
    recommender = IssueRecommender()
    
    # Example usage
    username = "example_user"
    repo_owner = "example_org"
    repo_name = "example_repo"
    
    recommended_issues = recommender.get_recommended_issues(username, repo_owner, repo_name)
    
    for issue in recommended_issues:
        print(f"Issue: {issue['issue']['title']}")
        print(f"Match Score: {issue['match_score']}")
        print(f"Required Skills: {issue['required_skills']}")
        print(f"User Skills: {issue['user_skills']}")
        print("-" * 50) 