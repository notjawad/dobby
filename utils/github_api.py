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
            else:
                self.logger.error(
                    f"Failed to fetch PR details for {repo}#{pr_number}: {response.status}"
                )
                return None

    async def fetch_pr_comments(self, repo: str, pr_number: int) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}/pulls/{pr_number}/comments"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                self.logger.error(
                    f"Failed to fetch PR comments for {repo}#{pr_number}: {response.status}"
                )
                return None

    async def fetch_issue_details(self, repo: str, issue_number: int) -> dict:
        url = f"{self.BASE_URL}/repos/{repo}/issues/{issue_number}"
        async with self.session.get(url) as response:
            if response.status == 200:
                return await response.json()
            else:
                self.logger.error(
                    f"Failed to fetch issue details for {repo}#{issue_number}: {response.status}"
                )
                return None

    async def close(self):
        """Close the aiohttp session."""
        await self.session.close()
