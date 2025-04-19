import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# GitHub token (should be in .env file)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    raise ValueError("Please set your GITHUB_TOKEN in the .env file")

# Repository list (up to 100)
repos = [
#     # easy
    "firstcontributions/first-contributions",
    "EddieHubCommunity/LinkFree",
    "public-apis/public-apis",
    "freeCodeCamp/freeCodeCamp",
    "mdn/content",
    "30-seconds/30-seconds-of-code",
    "sindresorhus/awesome",
    "MunGell/awesome-for-beginners",
#     # MERN
  "amazingandyyy/mern",
  "burakorkmez/mern-github-app",
  "abhishekrajput-web/GymMaster",
  "khushi2706/Blog-App-using-MERN-stack",
  "prajapati-sumit/mern-stack",

#   # Data Analytics
  "shsarv/Data-Analytics-Projects-in-python",
  "milaan9/93_Python_Data_Analytics_Projects",
  "dipeshdulal/netflix-data-analysis",
  "guipsamora/pandas_exercises",
  "owid/covid-19-data",

#   # Java
  "TheAlgorithms/Java",
  "iluwatar/java-design-patterns",
  "ityouknow/spring-boot-examples",
  "akullpp/awesome-java",
  "eugenp/tutorials",

#   #React
  "reactjs/reactjs.org",
  "ibaslogic/react-tutorial",
  "react-boilerplate/react-boilerplate",
  "briancodex/react-ecommerce-store",
  "creativetimofficial/argon-dashboard-react",

  # Node.js
  "nodejs/node",
  "expressjs/express",
  "sahat/hackathon-starter",
  "bradtraversy/chatcord",
  "madhums/node-express-mongoose",

#   #MongoDB
  "mongodb/node-mongodb-native",
  "Automattic/mongoose",
  "MongoDBUniversity/MongoDB-for-Developers",
  "Academind/mern-course",
  "nileshsingh5/mongodb-practice",

#   # AI
  "openai/gpt-2",
  "karpathy/nanoGPT",
  "openai/whisper",
  "openai/gym",
  "minimaxir/textgenrnn",

#   # ML
  "scikit-learn/scikit-learn",
  "tensorflow/tensorflow",
  "keras-team/keras",
  "fastai/fastai",
  "pytorch/pytorch",

#   # Blockchain
  "ChainSafe/web3.js",
  "ethereum/go-ethereum",
  "OpenZeppelin/openzeppelin-contracts",
  "Hyperledger/fabric",
  "trufflesuite/truffle",

  # DevOps
  "kelseyhightower/kubernetes-the-hard-way",
  "helm/helm",
  "ansible/ansible",
  "hashicorp/terraform",
  "prometheus/prometheus",

#   # Dart
  "dart-lang/sdk",
  "dart-lang/samples",
  "dart-lang/http",
  "flutter/plugins",
  "dart-lang/ffi",

#   # Flutter
  "flutter/flutter",
  "FilledStacks/flutter-tutorials",
  "flutter/samples",
  "bizz84/layout-demo-flutter",
  "abuanwar072/Flutter-Responsive-Admin-Panel-or-Dashboard",

#   # Android
  "android/sunflower",
  "googlesamples/android-architecture-components",
  "PhilJay/MPAndroidChart",
  "codepath/android_guides",
  "firebase/quickstart-android",

#   # Kotlin
  "JetBrains/kotlin",
  "Kotlin/kotlinx.coroutines",
  "Kotlin/anko",
  "android/architecture-samples",
  "Kotlin/kotlinx.serialization",

  # PHP
  "laravel/laravel",
  "symfony/symfony",
  "fzaninotto/Faker",
  "monicahq/monica",
  "slimphp/Slim",

#   # HTML
  "30-seconds/30-seconds-of-html",
  "phuocng/html-dom",
  "mdn/learning-area",
  "kognise/water.css",
  "oxalorg/sakura",

  # CSS
  "30-seconds/30-seconds-of-css",
  "necolas/normalize.css",
  "animate-css/animate.css",
  "tailwindlabs/tailwindcss",
  "daneden/animate.css",

  # JavaScript
  "30-seconds/30-seconds-of-code",
#   "microverseinc/awesome-javascript",
  "getify/You-Dont-Know-JS",
  "airbnb/javascript",
  "ryanmcdermott/clean-code-javascript",

  # Python
  "TheAlgorithms/Python",
  "keras-team/keras",
  "psf/requests",
  "python/cpython",
  "pallets/flask",

  # C#
  "dotnet/aspnetcore",
  "mono/mono",
  "aspnetboilerplate/aspnetboilerplate",
  "ShareX/ShareX",
  "Unity-Technologies/UnityCsReference",

  # React Native
  "facebook/react-native",
  "expo/expo",
  "jondot/awesome-react-native",
  "react-native-elements/react-native-elements",
  "infinitered/ignite",

#   # Web3
  "ChainSafe/web3.js",
  "web3/web3.py",
  "MetaMask/metamask-extension",
  "scaffold-eth/scaffold-eth",
  "ethers-io/ethers.js"
    
    
]

# GitHub GraphQL endpoint
url = "https://api.github.com/graphql"

# Headers with auth
headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Content-Type": "application/json"
}

# Build GraphQL query dynamically
def build_query(repo_list):
    query_parts = []
    for i, repo in enumerate(repo_list):
        try:
            owner, name = repo.split("/")
            if not owner or not name:
                print(f"Warning: Skipping invalid repository format: {repo}")
                continue
                
            alias = f"repo{i}"
            query = f'''
            {alias}: repository(owner: "{owner}", name: "{name}") {{
                issues(first: 5, states: OPEN, orderBy: {{field: CREATED_AT, direction: DESC}}) {{
                    nodes {{
                        title
                        url
                        bodyText
                        createdAt
                        number
                        labels(first: 5) {{
                            nodes {{
                                name
                            }}
                        }}
                        author {{
                            login
                        }}
                    }}
                }}
            }}'''
            query_parts.append(query)
        except ValueError:
            print(f"Warning: Skipping invalid repository format: {repo}")
            continue
            
    if not query_parts:
        raise ValueError("No valid repositories found in the list")
        
    full_query = "query {\n" + "\n".join(query_parts) + "\n}"
    return full_query

# Chunking to stay under query limits (25 repos per batch is safe)
def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def fetch_issues():
    # Final issue store
    all_issues = {}
    
    try:
        # Process in chunks
        for batch in chunked(repos, 25):
            try:
                graphql_query = build_query(batch)
                response = requests.post(url, headers=headers, json={"query": graphql_query})
                response.raise_for_status()  # Raise an exception for bad status codes
                data = response.json()

                if "errors" in data:
                    print("GraphQL Errors:", json.dumps(data["errors"], indent=2))
                    continue

                if "data" in data:
                    for key, repo_data in data["data"].items():
                        try:
                            repo_index = int(key.replace("repo", ""))
                            repo_name = repos[repo_index]
                            if repo_data and "issues" in repo_data:
                                all_issues[repo_name] = repo_data["issues"]["nodes"]
                        except (IndexError, ValueError) as e:
                            print(f"Warning: Error processing repository data: {str(e)}")
                            continue

            except requests.exceptions.RequestException as e:
                print(f"Warning: Error processing batch: {str(e)}")
                continue

        # Dump all issues to a file
        with open("github_issues.json", "w", encoding="utf-8") as f:
            json.dump(all_issues, f, indent=2, ensure_ascii=False)

        print("✅ Issues successfully saved to github_issues.json")
        print(f"📊 Fetched issues from {len(all_issues)} repositories")

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        raise

if __name__ == "__main__":
    fetch_issues() 