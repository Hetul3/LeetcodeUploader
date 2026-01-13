import os
import sys
import argparse
from dotenv import load_dotenv
from src.leetcode_client import LeetCodeClient
from src.github_client import GitHubClient
from src.sync_engine import SyncEngine

def main():
    load_dotenv()
    
    # Credentials
    lc_session = os.getenv("LEETCODE_SESSION")
    lc_csrf = os.getenv("LEETCODE_CSRF_TOKEN")
    lc_username = os.getenv("LEETCODE_USERNAME")
    
    gh_token = os.getenv("GITHUB_TOKEN")
    gh_repo = os.getenv("GITHUB_REPO")
    
    if not all([lc_session, lc_csrf, lc_username, gh_token, gh_repo]):
        print("❌ Error: Missing configuration in .env. Please check your variables.")
        sys.exit(1)
        
    # Initialize Clients
    lc_client = LeetCodeClient(lc_session, lc_csrf)
    gh_client = GitHubClient(gh_token, gh_repo)
    engine = SyncEngine(lc_client, gh_client)
    
    # CLI Parser
    parser = argparse.ArgumentParser(description="LeetCode solution synchronization tool.")
    subparsers = parser.add_subparsers(dest="command", help="Commands to run")
    
    # Init command
    subparsers.add_parser("init", help="Initialize the repository structure (Easy, Medium, Hard)")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize latest submissions")
    sync_parser.add_argument("--limit", type=int, default=20, help="Number of recent submissions to fetch")
    
    args = parser.parse_args()
    
    if args.command == "init":
        engine.initialize_repo()
    elif args.command == "sync":
        # Initial call to check auth
        status = lc_client.get_user_status()
        if not status['isSignedIn']:
            print("❌ Error: Not signed in to LeetCode. Check your cookies.")
            return
            
        print(f"🔄 Starting sync for user {lc_username}...")
        engine.sync(lc_username, limit=args.limit)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
