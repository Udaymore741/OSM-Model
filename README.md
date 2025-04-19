# GitHub Issue Recommender

This system analyzes GitHub user profiles and repository issues to recommend issues that match the user's skills.

## Features

- Analyzes user's GitHub profile and repositories to extract skills
- Processes repository issues to identify required skills
- Uses NLP to extract technical skills from issue descriptions and labels
- Matches user skills with issue requirements using TF-IDF and cosine similarity
- Provides skill matching scores and missing skills information

## Setup

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Download the required NLTK data:
```bash
python -m nltk.downloader stopwords
```

3. Download the spaCy model:
```bash
python -m spacy download en_core_web_sm
```

4. Create a `.env` file in the project root with your GitHub token:
```
GITHUB_TOKEN=your_github_token_here
```

## Usage

1. Import and initialize the IssueRecommender:
```python
from app import IssueRecommender

recommender = IssueRecommender()
```

2. Get recommended issues for a user:
```python
username = "github_username"
repo_owner = "repository_owner"
repo_name = "repository_name"

recommended_issues = recommender.get_recommended_issues(username, repo_owner, repo_name)
```

3. The system will return a list of recommended issues with:
   - Issue details
   - Match score
   - Required skills
   - User's matching skills

## Example Output

```python
{
    'issue': {
        'title': 'Fix authentication bug',
        'body': 'The login system needs to be updated...',
        'labels': ['bug', 'security']
    },
    'match_score': 0.85,
    'required_skills': ['python', 'authentication', 'security'],
    'user_skills': ['python', 'javascript', 'security']
}
```

## Notes

- The system uses NLP to extract skills from various sources including repository descriptions, issue titles, and labels
- The match score is calculated using TF-IDF and cosine similarity
- Issues with a match score above 0.5 are recommended by default
- The system can identify both matching skills and missing skills for each issue 