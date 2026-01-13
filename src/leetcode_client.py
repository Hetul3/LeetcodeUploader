import requests
import os
from typing import List, Dict, Optional

class LeetCodeClient:
    BASE_URL = "https://leetcode.com/graphql"
    
    def __init__(self, session_cookie: str, csrf_token: str):
        self.session = requests.Session()
        self.session.cookies.set("LEETCODE_SESSION", session_cookie)
        self.session.cookies.set("csrftoken", csrf_token)
        self.headers = {
            "Content-Type": "application/json",
            "Referer": "https://leetcode.com/",
            "x-csrftoken": csrf_token,
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def _query(self, query: str, variables: Dict = None) -> Dict:
        response = self.session.post(
            self.BASE_URL,
            json={"query": query, "variables": variables or {}},
            headers=self.headers
        )
        response.raise_for_status()
        data = response.json()
        if "errors" in data:
            raise Exception(f"GraphQL Errors: {data['errors']}")
        return data["data"]

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
        return self._query(query)["userStatus"]

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
        return self._query(query, {"username": username, "limit": limit})["recentAcSubmissionList"]

    def get_submission_details(self, submission_id: str) -> Dict:
        query = """
        query submissionDetails($submissionId: Int!) {
          submissionDetails(submissionId: $submissionId) {
            runtime
            runtimeDisplay
            memory
            memoryDisplay
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
        return self._query(query, {"submissionId": int(submission_id)})["submissionDetails"]

    def get_question_details(self, title_slug: str) -> Dict:
        query = """
        query questionData($titleSlug: String!) {
          question(titleSlug: $titleSlug) {
            questionId
            questionFrontendId
            title
            difficulty
            content
            topicTags {
              name
            }
          }
        }
        """
        return self._query(query, {"titleSlug": title_slug})["question"]
