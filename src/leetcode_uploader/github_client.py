import requests
import base64
from typing import Optional

class GitHubClient:
    BASE_URL = "https://api.github.com"
    
    def __init__(self, token: str, repo_full_name: str):
        """
        :param token: GitHub Personal Access Token
        :param repo_full_name: e.g. "username/repo"
        """
        self.token = token
        self.repo = repo_full_name
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def _handle_response(self, response: requests.Response):
        if response.status_code == 401:
            raise Exception("GitHub Authentication Failed: Invalid GITHUB_TOKEN.")
        if response.status_code == 404:
            raise Exception(f"GitHub Repository Not Found: {self.repo}. Check your GITHUB_REPO name.")
        response.raise_for_status()

    def get_file_sha(self, path: str) -> Optional[str]:
        """Check if a file exists and return its SHA (needed for updates)."""
        url = f"{self.BASE_URL}/repos/{self.repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json().get("sha")
        if response.status_code == 404:
            return None
        self._handle_response(response)
        return None

    def get_file_content(self, path: str) -> Optional[str]:
        """Fetch the content of a file from GitHub and decode it."""
        url = f"{self.BASE_URL}/repos/{self.repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            content_base64 = response.json().get("content", "")
            if content_base64:
                return base64.b64decode(content_base64).decode("utf-8")
        return None

    def create_or_update_file(self, path: str, content: str, commit_message: str) -> bool:
        """Uploads a file to GitHub. Encodes content to base64 automatically."""
        sha = self.get_file_sha(path)
        url = f"{self.BASE_URL}/repos/{self.repo}/contents/{path}"
        
        # GitHub API requires content to be base64 encoded
        encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")
        
        data = {
            "message": commit_message,
            "content": encoded_content
        }
        
        if sha:
            data["sha"] = sha  # Required for updating existing files
        
        response = requests.put(url, json=data, headers=self.headers)
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"GitHub Error: {response.json()}")
            return False
