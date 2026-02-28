import requests
import os
from typing import List, Dict, Optional

class LeetCodeClient:
    BASE_URL = "https://leetcode.com/graphql"
    
    def __init__(self, session_cookie: str, csrf_token: str):
        self.session = requests.Session()
        # Set cookies - using plural and removing leading dot for broader compatibility
        self.session.cookies.set("LEETCODE_SESSION", session_cookie, domain="leetcode.com")
        self.session.cookies.set("csrftoken", csrf_token, domain="leetcode.com")
        self.headers = {
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com/",
            "Origin": "https://leetcode.com",
            "x-csrftoken": csrf_token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _query(self, query: str, variables: Dict = None) -> Dict:
        try:
            response = self.session.post(
                self.BASE_URL,
                json={"query": query, "variables": variables or {}},
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 403:
                raise Exception("LeetCode Authentication Failed: LEETCODE_SESSION or CSRF_TOKEN is expired or invalid.")
                
            response.raise_for_status()
            data = response.json()
            
            if not data:
                raise Exception("Empty response from LeetCode API.")

            if "errors" in data:
                msg = str(data['errors'])
                if "not authenticated" in msg.lower() or "not signed in" in msg.lower():
                    raise Exception("LeetCode Session Expired: Please update your LEETCODE_SESSION and CSRF_TOKEN.")
                raise Exception(f"GraphQL Errors: {data['errors']}")
            
            if "data" not in data or data["data"] is None:
                raise Exception("LeetCode API returned no data. This usually means your session is invalid or the record is private.")
                
            return data["data"]
        except requests.exceptions.RequestException as e:
            raise Exception(f"Network error while connecting to LeetCode: {str(e)}")

    def get_user_status(self) -> Dict:
        query = """
        query userStatus {
          userStatus {
            username
            isSignedIn
            isAdmin
          }
        }
        """
        data = self._query(query)
        if not data or "userStatus" not in data:
            return {"isSignedIn": False, "username": None}
        return data["userStatus"]

    def get_recent_accepted_submissions(self, username: str, limit: int = 20) -> List[Dict]:
        query = """
        query recentAcSubmissions($username: String!, $limit: Int!) {
          recentAcSubmissionList(username: $username, limit: $limit) {
            id
            title
            titleSlug
            timestamp
          }
        }
        """
        data = self._query(query, {"username": username, "limit": limit})
        if not data or "recentAcSubmissionList" not in data or data["recentAcSubmissionList"] is None:
            return []
        return data["recentAcSubmissionList"]

    def get_submission_details(self, submission_id: str) -> Dict:
        query = """
        query submissionDetails($submissionId: Int!) {
          submissionDetails(submissionId: $submissionId) {
            runtime
            runtimeDisplay
            runtimePercentile
            memory
            memoryDisplay
            memoryPercentile
            code
            timestamp
            lang {
              name
              verboseName
            }
            question {
              questionId
              titleSlug
              title
              difficulty
            }
          }
        }
        """
        data = self._query(query, {"submissionId": int(submission_id)})
        
        if not data or "submissionDetails" not in data or data["submissionDetails"] is None:
            # If we get no data, check if it's because the session expired
            status = self.get_user_status()
            if not status.get('isSignedIn'):
                raise Exception("LeetCode Session Expired: Your session is no longer valid. Please update your LEETCODE_SESSION.")
            
            raise Exception(f"Unauthorized: Could not fetch details for submission {submission_id}. "
                            "This code might be private or belong to another user.")
            
        return data["submissionDetails"]

    def get_question_details(self, title_slug: str) -> Optional[Dict]:
        query = """
        query questionData($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            titleSlug
            difficulty
            content
            topicTags {
              name
            }
          }
        }
        """
        data = self._query(query, {"titleSlug": title_slug})
        if not data or "question" not in data:
            return None
        return data["question"]
