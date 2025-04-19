from flask import Flask, request, jsonify
from main import analyze_github_user
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

@app.route('/analyze', methods=['GET'])
def analyze_user():
    # Get username from query parameter
    username = request.args.get('username')
    
    if not username:
        return jsonify({
            "error": "Username parameter is required",
            "status": "error"
        }), 400
    
    try:
        # Call the analysis function
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
        return jsonify({
            "error": str(e),
            "status": "error"
        }), 500

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True) 