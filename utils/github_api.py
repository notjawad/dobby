import aiohttp
import logging


class GitHubAPI:
    BASE_URL = "https://api.github.com"

    def __init__(self):
        self.session = aiohttp.ClientSession()
        self.logger = logging.getLogger("lambda")

    async def fetch_pr(self, repo: str, pr_number: int) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}/pulls/{pr_number}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch PR details for {repo}#{pr_number}: {response.status}"
            )
            return None

    async def fetch_pr_comments(self, repo: str, pr_number: int) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}/pulls/{pr_number}/comments"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch PR comments for {repo}#{pr_number}: {response.status}"
            )
            return None

    async def fetch_issue_details(self, repo: str, issue_number: int) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}/issues/{issue_number}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch issue details for {repo}#{issue_number}: {response.status}"
            )
            return None

    async def fetch_latest_commits(self, repo: str) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}/commits"
        async with self.session.get(url) as response:
            if response.status == 200:
                return (await response.json())[:10]
            self.logger.error(
                f"Failed to fetch latest commit for {repo}: {response.status}"
            )
            return None

    async def fetch_lines_of_code(self, repo: str) -> dict:
        url = f"https://api.codetabs.com/v1/loc?github={repo}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch lines of code for {repo}: {response.status}"
            )
            return None

    async def fetch_repo_files(self, repo: str) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}/contents"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch repo files for {repo}: {response.status}"
            )
            return None

    async def search_repos(self, query: str) -> dict:
        url = f"{self.BASE_URL}/search/repositories?q={query}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(f"Failed to search for {query}: {response.status}")
            return None

    async def fetch_profile(self, username: str) -> dict:
        url = f"{self.BASE_URL}/users/{username}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch profile for {username}: {response.status}"
            )
            return None

    async def get_user_repos(self, username: str) -> dict:
        url = f"{self.BASE_URL}/users/{username}/repos"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch repos for {username}: {response.status}"
            )
            return None

    async def fetch_repo(self, repo: str) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            self.logger.error(
                f"Failed to fetch repo details for {repo}: {response.status}"
            )
            return None

    async def close(self):
        await self.session.close()
