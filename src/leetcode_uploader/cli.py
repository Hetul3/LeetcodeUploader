import os
import sys
import argparse
from dotenv import load_dotenv, set_key
from .leetcode_client import LeetCodeClient
from .github_client import GitHubClient
from .sync_engine import SyncEngine

ENV_PATH = ".env"

def check_credentials():
    """Checks for all required env variables and returns them."""
    load_dotenv()
    creds = {
        "LEETCODE_SESSION": os.getenv("LEETCODE_SESSION"),
        "LEETCODE_CSRF_TOKEN": os.getenv("LEETCODE_CSRF_TOKEN"),
        "LEETCODE_USERNAME": os.getenv("LEETCODE_USERNAME"),
        "GITHUB_TOKEN": os.getenv("GITHUB_TOKEN"),
        "GITHUB_REPO": os.getenv("GITHUB_REPO")
    }
    
    missing = [k for k, v in creds.items() if not v]
    return creds, missing

def handle_config(args):
    """Handles the 'config' command to set env variables."""
    key = args.key.upper()
    value = args.value
    
    valid_keys = [
        "LEETCODE_SESSION", "LEETCODE_CSRF_TOKEN", "LEETCODE_USERNAME",
        "GITHUB_TOKEN", "GITHUB_REPO", "PREFERRED_LANGUAGE"
    ]
    
    if key not in valid_keys:
        print(f"❌ Invalid key: {key}")
        print(f"Valid keys are: {', '.join(valid_keys)}")
        return

    # Ensure .env exists
    if not os.path.exists(ENV_PATH):
        open(ENV_PATH, 'a').close()

    set_key(ENV_PATH, key, value)
    print(f"✅ Updated {key} in {ENV_PATH}")

def main():
    parser = argparse.ArgumentParser(description="LeetCode solution synchronization tool.")
    subparsers = parser.add_subparsers(dest="command")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize latest submissions")
    sync_parser.add_argument("--limit", type=int, default=20, help="Number of recent submissions to fetch")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Set configuration variables")
    config_parser.add_argument("key", help="The setting to change (e.g. GITHUB_REPO)")
    config_parser.add_argument("value", help="The new value for the setting")
    
    args = parser.parse_args()
    
    if args.command == "config":
        handle_config(args)
        return

    # For other commands, verify credentials first
    creds, missing = check_credentials()
    
    if missing:
        print("❌ Error: Missing configuration variables in .env:")
        for m in missing:
            print(f"  - {m}")
        print("\nUse the config command to set them, e.g.:")
        print(f"  python3 main.py config {missing[0]} your_value_here")
        sys.exit(1)

    try:
        # Initialize Clients
        lc_client = LeetCodeClient(creds["LEETCODE_SESSION"], creds["LEETCODE_CSRF_TOKEN"])
        gh_client = GitHubClient(creds["GITHUB_TOKEN"], creds["GITHUB_REPO"])
        engine = SyncEngine(lc_client, gh_client)

        if args.command == "sync":
            print(f"🔄 Starting sync for user {creds['LEETCODE_USERNAME']}...")
            engine.sync(creds['LEETCODE_USERNAME'], limit=args.limit)
        else:
            parser.print_help()
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if "Authentication Failed" in str(e) or "Session Expired" in str(e):
            print("\nPlease update your credentials using 'python3 main.py config KEY VALUE'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
