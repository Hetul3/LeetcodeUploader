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
    # Priority 1: Check for .env in current working directory
    local_env = os.path.join(os.getcwd(), ".env")
    if os.path.exists(local_env):
        load_dotenv(local_env)
        env_used = local_env
    else:
        # Priority 2: Check for .env in global config dir
        if not os.path.exists(CONFIG_DIR):
            os.makedirs(CONFIG_DIR)
        load_dotenv(ENV_PATH)
        env_used = ENV_PATH
        
    creds = {
        "LEETCODE_SESSION": (os.getenv("LEETCODE_SESSION") or "").strip().strip('"').strip("'"),
        "LEETCODE_CSRF_TOKEN": (os.getenv("LEETCODE_CSRF_TOKEN") or "").strip().strip('"').strip("'"),
        "LEETCODE_USERNAME": (os.getenv("LEETCODE_USERNAME") or "").strip().strip('"').strip("'"),
        "GITHUB_TOKEN": (os.getenv("GITHUB_TOKEN") or "").strip().strip('"').strip("'"),
        "GITHUB_REPO": (os.getenv("GITHUB_REPO") or "").strip().strip('"').strip("'")
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
    
    # Identify which env file we're using
    local_env = os.path.join(os.getcwd(), ".env")
    current_env = local_env if os.path.exists(local_env) else ENV_PATH
    
    print(f"📄 Using Config: {current_env}")
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
        error_msg = str(e)
        print(f"\n❌ Error: {error_msg}")
        
        lower_msg = error_msg.lower()
        if "session" in lower_msg or "authentication failed" in lower_msg or "csrf" in lower_msg:
            print("\n" + "!" * 50)
            print("🔑 HOW TO REFRESH YOUR LEETCODE SESSION:")
            print("1. Log in to LeetCode in your web browser.")
            print("2. Right-click anywhere and select 'Inspect' (or press F12).")
            print("3. Go to the 'Application' tab (Chrome/Edge) or 'Storage' tab (Firefox).")
            print("4. Click on 'Cookies' in the left sidebar and select 'https://leetcode.com'.")
            print("5. Copy the values for:")
            print("   - LEETCODE_SESSION")
            print("   - csrftoken")
            print("\n6. Run these commands:")
            print("   leetcode-sync config LEETCODE_SESSION <your_session>")
            print("   leetcode-sync config LEETCODE_CSRF_TOKEN <your_csrftoken>")
            print("!" * 50 + "\n")
        
        sys.exit(1)

if __name__ == "__main__":
    main()
