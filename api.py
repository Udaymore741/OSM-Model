from flask import Flask, request, jsonify
from main import analyze_github_user
import os
from dotenv import load_dotenv
import logging
import traceback

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,
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

@app.route('/analyze', methods=['GET'])
def analyze_user():
    try:
        # Log all query parameters received
        logger.debug(f"Received request with parameters: {request.args}")
        
        # Get username from query parameter
        username = request.args.get('username')
        logger.debug(f"Extracted username: {username}")
        
        if not username:
            logger.error("No username provided in request")
            return jsonify({
                "error": "Username parameter is required. Please provide a username in the URL like: /analyze?username=YOUR_USERNAME",
                "status": "error"
            }), 400
        
        # Call the analysis function
        logger.debug(f"Starting analysis for user: {username}")
        try:
            result = analyze_github_user(username)
            logger.debug(f"Analysis result: {result}")
            
            if not result:
                logger.error(f"Analysis returned None for user: {username}")
                return jsonify({
                    "error": "Could not analyze user profile. Please check if the username exists and is accessible.",
                    "status": "error"
                }), 404
            
            logger.debug(f"Successfully analyzed user: {username}")
            return jsonify({
                "data": result,
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Error in analyze_github_user: {str(e)}")
            logger.error(traceback.format_exc())
            return jsonify({
                "error": f"Error analyzing profile: {str(e)}",
                "status": "error"
            }), 500
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({
            "error": f"An unexpected error occurred: {str(e)}",
            "status": "error"
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Starting Flask application on port {port}")
    app.run(host='0.0.0.0', port=port, debug=True) 