import os
import sys
import argparse
from dotenv import load_dotenv, set_key
from .leetcode_client import LeetCodeClient
from .github_client import GitHubClient
from .sync_engine import SyncEngine

VERSION = "1.1.0"
CONFIG_DIR = os.path.expanduser("~/.leetcode-uploader")
ENV_PATH = os.path.join(CONFIG_DIR, ".env")

def check_credentials():
    """Checks for all required env variables and returns them."""
    # Create config dir if it doesn't exist
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
        
    load_dotenv(ENV_PATH)
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

    # Ensure config dir exists
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)

    # Ensure .env exists
    if not os.path.exists(ENV_PATH):
        open(ENV_PATH, 'a').close()

    set_key(ENV_PATH, key, value)
    print(f"✅ Updated {key}")
    print(f"⚙️  Config location: {ENV_PATH}")

def handle_status(creds):
    """Shows the tool status, config location, and login info."""
    print(f"🚀 LeetCode Uploader v{VERSION}")
    print(f"📂 Config Directory: {CONFIG_DIR}")
    print(f"📄 Config File: {ENV_PATH}")
    print("-" * 30)
    
    try:
        lc_client = LeetCodeClient(creds["LEETCODE_SESSION"], creds["LEETCODE_CSRF_TOKEN"])
        status = lc_client.get_user_status()
        if status['isSignedIn']:
            print(f"✅ LeetCode: Signed in as {status['username']}")
        else:
            print("❌ LeetCode: Not signed in.")
    except Exception as e:
        print(f"❌ LeetCode Error: {str(e)}")
        
    print(f"✅ GitHub Repo: {creds['GITHUB_REPO'] or 'Not Set'}")
    print("-" * 30)
    print("\nTo uninstall, simply delete the binary and the config directory (~/.leetcode-uploader).")

def main():
    parser = argparse.ArgumentParser(description="LeetCode solution synchronization tool.")
    parser.add_argument("--version", action="version", version=f"%(prog)s {VERSION}")
    subparsers = parser.add_subparsers(dest="command")
    
    # Sync command
    sync_parser = subparsers.add_parser("sync", help="Synchronize latest submissions")
    sync_parser.add_argument("--limit", type=int, default=20, help="Number of recent submissions to fetch")
    
    # Config command
    config_parser = subparsers.add_parser("config", help="Set configuration variables")
    config_parser.add_argument("key", help="The setting to change (e.g. GITHUB_REPO)")
    config_parser.add_argument("value", help="The new value for the setting")

    # Status command
    subparsers.add_parser("status", help="Check tool status and configuration")
    
    args = parser.parse_args()
    
    if args.command == "config":
        handle_config(args)
        return

    # Check credentials for status and sync
    creds, missing = check_credentials()
    
    if args.command == "status":
        handle_status(creds)
        return
    
    if missing:
        print(f"❌ Error: Missing configuration variables.")
        for m in missing:
            print(f"  - {m}")
        print("\nUse the config command to set them, e.g.:")
        print(f"  leetcode-sync config {missing[0]} your_value_here")
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
            print("\nPlease update your credentials using 'leetcode-sync config KEY VALUE'.")
        sys.exit(1)

if __name__ == "__main__":
    main()
