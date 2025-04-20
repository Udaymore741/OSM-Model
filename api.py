from flask import Flask, request, jsonify
from flask_cors import CORS
from main import analyze_github_user
from github_fetcher import GitHubFetcher
import os
from dotenv import load_dotenv
import logging
import traceback
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Verify GitHub token is set
if not os.getenv('GITHUB_TOKEN'):
    logger.error("GITHUB_TOKEN environment variable is not set")
    raise ValueError("GITHUB_TOKEN environment variable is not set")

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize GitHub fetcher
github = GitHubFetcher()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "version": "1.0.0"
    })

@app.route('/api/profile/<username>', methods=['GET'])
def get_user_profile(username: str) -> Dict[str, Any]:
    """Get comprehensive user profile"""
    try:
        logger.info(f"Fetching profile for user: {username}")
        
        # Fetch user data
        user_data = github.get_user_profile(username)
        if not user_data:
            return jsonify({
                "error": "User not found",
                "status": "error"
            }), 404
            
        # Fetch repositories
        repositories = github.get_user_repositories(username)
        
        # Get tech profile
        tech_profile = github.get_user_tech_profile(username)
        
        # Prepare response
        profile_data = {
            "basic_info": {
                "username": username,
                "name": user_data.get('name'),
                "bio": user_data.get('bio'),
                "location": user_data.get('location'),
                "company": user_data.get('company'),
                "avatar_url": user_data.get('avatar_url'),
                "followers": user_data.get('followers'),
                "following": user_data.get('following'),
                "created_at": user_data.get('created_at')
            },
            "skills": {
                "languages": tech_profile.get("languages", []),
                "frameworks": tech_profile.get("frameworks", []),
                "tools": tech_profile.get("tools", []),
                "domains": tech_profile.get("domains", [])
            },
            "repositories": {
                "total": len(repositories) if repositories else 0,
                "pinned": user_data.get('pinned_repositories', []),
                "recent": repositories[:5] if repositories else []
            },
            "activity": {
                "recent_events": user_data.get('recent_events', [])[:5],
                "gists": user_data.get('gists', [])[:3]
            }
        }
        
        return jsonify({
            "data": profile_data,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error fetching profile: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Error fetching profile: {str(e)}",
            "status": "error"
        }), 500

@app.route('/api/analyze', methods=['GET'])
def analyze_user() -> Dict[str, Any]:
    """Analyze user profile and get recommendations"""
    try:
        username = request.args.get('username')
        if not username:
            return jsonify({
                "error": "Username parameter is required",
                "status": "error"
            }), 400
            
        logger.info(f"Starting analysis for user: {username}")
        
        result = analyze_github_user(username)
        if not result:
            return jsonify({
                "error": "Could not analyze user profile",
                "status": "error"
            }), 404
            
        return jsonify({
            "data": result,
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error in analysis: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Error in analysis: {str(e)}",
            "status": "error"
        }), 500

@app.route('/api/skills/<username>', methods=['GET'])
def get_user_skills(username: str) -> Dict[str, Any]:
    """Get detailed user skills analysis"""
    try:
        logger.info(f"Fetching skills for user: {username}")
        
        tech_profile = github.get_user_tech_profile(username)
        if not tech_profile:
            return jsonify({
                "error": "Could not fetch user skills",
                "status": "error"
            }), 404
            
        return jsonify({
            "data": {
                "languages": tech_profile.get("languages", []),
                "frameworks": tech_profile.get("frameworks", []),
                "tools": tech_profile.get("tools", []),
                "domains": tech_profile.get("domains", [])
            },
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error fetching skills: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Error fetching skills: {str(e)}",
            "status": "error"
        }), 500

@app.route('/api/repositories/<username>', methods=['GET'])
def get_user_repositories(username: str) -> Dict[str, Any]:
    """Get user repositories"""
    try:
        logger.info(f"Fetching repositories for user: {username}")
        
        repositories = github.get_user_repositories(username)
        if not repositories:
            return jsonify({
                "error": "Could not fetch repositories",
                "status": "error"
            }), 404
            
        return jsonify({
            "data": {
                "total": len(repositories),
                "repositories": repositories
            },
            "status": "success"
        })
        
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"Error fetching repositories: {str(e)}",
            "status": "error"
        }), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting API server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 