import os
import sys
from dotenv import load_dotenv
from src.github_client import GitHubClient

def main():
    load_dotenv()
    
    token = os.getenv("GITHUB_TOKEN")
    repo = os.getenv("GITHUB_REPO")
    
    if not token or not repo:
        print("Error: Missing GITHUB_TOKEN or GITHUB_REPO in .env")
        sys.exit(1)
        
    client = GitHubClient(token, repo)
    
    test_path = "sync_test/ping.md"
    test_content = "# Test Success\nThis file was uploaded via the LeetCode Uploader tool."
    test_message = "feat: test github connectivity"
    
    try:
        print(f"--- Testing GitHub API on {repo} ---")
        success = client.create_or_update_file(test_path, test_content, test_message)
        
        if success:
            print(f"✅ Success! File '{test_path}' uploaded to your repo.")
            print(f"Check it here: https://github.com/{repo}/blob/main/{test_path}")
        else:
            print("❌ Failed to upload. Check your token permissions or repository name.")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
