import os
import sys
from dotenv import load_dotenv
from src.leetcode_client import LeetCodeClient

def main():
    load_dotenv()
    
    session = os.getenv("LEETCODE_SESSION")
    csrf = os.getenv("LEETCODE_CSRF_TOKEN")
    username = os.getenv("LEETCODE_USERNAME")
    
    if not all([session, csrf, username]):
        print("Error: Missing credentials in .env file.")
        print("Please copy .env.example to .env and fill in your details.")
        sys.exit(1)
        
    client = LeetCodeClient(session, csrf)
    
    try:
        print(f"--- Verifying status for {username} ---")
        status = client.get_user_status()
        print(f"Is Signed In: {status['isSignedIn']}")
        
        print("\n--- Fetching recent accepted submissions ---")
        recent = client.get_recent_accepted_submissions(username, limit=3)
        for sub in recent:
            print(f"- {sub['title']} (ID: {sub['id']}, Slug: {sub['titleSlug']})")
            
        if recent:
            last_sub_id = recent[0]['id']
            print(f"\n--- Fetching details for submission {last_sub_id} ---")
            details = client.get_submission_details(last_sub_id)
            print(f"Language: {details['lang']['verboseName']}")
            print(f"Runtime: {details['runtimeDisplay']}")
            print(f"Memory: {details['memoryDisplay']}")
            print(f"Code Preview: {details['code'][:50]}...")
            
            title_slug = details['question']['titleSlug']
            print(f"\n--- Fetching question details for {title_slug} ---")
            question = client.get_question_details(title_slug)
            print(f"Difficulty: {question['difficulty']}")
            print(f"ID: {question['questionFrontendId']}")
            
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
