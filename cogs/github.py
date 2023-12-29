import discord
import logging

from discord.ext import commands
from utils import _embeds
from utils._github import GitHubAPI
from utils._ui import CommitSelectMenu


class Github(commands.Cog):
    def __init__(self, bot_: discord.Bot):
        self.bot = bot_
        self.logger = logging.getLogger("dobby")
        self.github_api = GitHubAPI()

    _git = discord.commands.SlashCommandGroup(
        name="git",
        description="GitHub related commands.",
    )

    @_git.command(
        name="pr",
        description="Get information about a pull request.",
    )
    async def get_pr(
        self,
        ctx: discord.ApplicationContext,
        repo: discord.Option(
            str,
            "The repository to get the pull request from (e.g. owner/repo)",
            required=True,
        ),
        pr_number: discord.Option(int, "The pull request number", required=True),
        show_comments: discord.Option(bool, "Whether to show comments", required=False),
    ) -> None:
        if "/" not in repo:
            return await ctx.respond(
                "Invalid repository name. Please use the format owner/repo.",
                ephemeral=True,
            )
        pr = await self.github_api.fetch_pr(repo, pr_number)

        if not pr:
            return await ctx.respond(
                f"Failed to fetch PR details for {repo}#{pr_number}.", ephemeral=True
            )

        comments = await self.github_api.fetch_pr_comments(repo, pr_number)

        embed = _embeds.construct_pr_embed(pr, show_comments, comments[:3])

        open_in_github = discord.ui.Button(
            label="Open in GitHub",
            url=pr["html_url"],
            style=discord.ButtonStyle.link,
        )

        view = discord.ui.View()
        view.add_item(open_in_github)

        await ctx.respond(embed=embed, view=view)

    @_git.command(
        name="commits",
        description="Get the latest commits for a repository.",
    )
    async def _commits(
        self,
        ctx: discord.ApplicationContext,
        repo: discord.Option(
            str,
            "The repository to get the latest commits for. (e.g. uni-bot/uni)",
            required=True,
        ),
    ) -> None:
        if repo.count("/") != 1:
            return await ctx.respond(
                "Invalid repository format. The format should be owner/repo.",
                ephemeral=True,
            )

        commits = await self.github_api.fetch_latest_commits(repo)

        if isinstance(commits, str):
            return await ctx.respond(commits)

        embed = _embeds.construct_commits_embed(repo, commits)

        select_menu = CommitSelectMenu(
            commits,
            placeholder="Select a commit to view more information.",
            min_values=1,
            max_values=1,
        )

        for commit in commits:
            sha = commit["sha"][:7]
            select_menu.add_option(
                label=f"{sha} - {commit['commit']['author']['name']}",
                value=sha,
                description=commit["commit"]["message"].split("\n")[0][:100],
            )

        view = discord.ui.View()
        view.add_item(select_menu)

        await ctx.respond(
            embed=embed,
            view=view,
        )

    @_git.command(
        name="loc",
        description="Line of code breakdown for a repository.",
    )
    async def _loc(
        self,
        ctx: discord.ApplicationContext,
        repo: discord.Option(
            str,
            "The repository to get the line of code breakdown for. (e.g. uni-bot/uni)",
            required=True,
        ),
    ) -> None:
        if repo.count("/") != 1:
            return await ctx.respond(
                "Invalid repository format. The format should be owner/repo.",
            )

        await ctx.defer()

        data = await self.github_api.fetch_lines_of_code(repo)

        if not data:
            return await ctx.respond(
                f"Failed to fetch lines of code for **{repo}**. Does the repository exist?",
                ephemeral=True,
            )

        embed = _embeds.construct_loc_embed(repo, data)
        await ctx.respond(embed=embed)

    @_git.command(
        name="files",
        description="Get the files of a repository.",
    )
    async def _files(
        self,
        ctx: discord.ApplicationContext,
        repo: discord.Option(
            str,
            "The repository to get the files for. (e.g. uni-bot/uni)",
            required=True,
        ),
    ) -> None:
        if repo.count("/") != 1:
            return await ctx.respond(
                "Invalid repository format. The format should be owner/repo.",
                ephemeral=True,
            )

        await ctx.defer()

        files = await self.github_api.fetch_repo_files(repo)
        if not files:
            return await ctx.respond(
                f"Failed to fetch files for **{repo}**. Does the repository exist?",
                ephemeral=True,
            )

        embed = _embeds.construct_repo_files_embed(repo, files)

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(label="View on GitHub", url=f"https://github.com/{repo}")
        )

        await ctx.respond(embed=embed, view=view)

    @_git.command(
        name="issue",
        description="Get information about an issue.",
    )
    async def _issue(
        self,
        ctx: discord.ApplicationContext,
        repo: discord.Option(
            str,
            "The repository to get the issue from (e.g. owner/repo)",
            required=True,
        ),
        issue_number: discord.Option(int, "The issue number", required=True),
    ) -> None:
        if "/" not in repo:
            return await ctx.respond(
                "Invalid repository name. Please use the format owner/repo.",
                ephemeral=True,
            )
        issue = await self.github_api.fetch_issue_details(repo, issue_number)

        if not issue:
            return await ctx.respond(
                f"Failed to fetch issue details for {repo}#{issue_number}.",
                ephemeral=True,
            )

        embed = _embeds.construct_issue_embed(issue)

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Open in GitHub", url=issue["html_url"]))

        await ctx.respond(embed=embed, view=view)

    @_git.command(
        name="search",
        description="Search for a repository.",
    )
    async def _search(
        self,
        ctx: discord.ApplicationContext,
        query: discord.Option(
            str,
            "The query to search for.",
            required=True,
        ),
    ) -> None:
        await ctx.defer()

        results = await self.github_api.search_repos(query)

        if not results:
            return await ctx.respond(
                f"Failed to fetch search results for **{query}**.", ephemeral=True
            )

        embed = _embeds.construct_repo_embed(results["items"][0])

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="View on GitHub",
                url=results["items"][0]["html_url"],
            )
        )

        await ctx.respond(embed=embed, view=view)

    @_git.command(
        name="profile",
        description="Get information about a GitHub profile.",
    )
    async def _profile(
        self,
        ctx: discord.ApplicationContext,
        username: discord.Option(
            str,
            "The username to get the profile for.",
            required=True,
        ),
    ) -> None:
        await ctx.defer()

        profile = await self.github_api.fetch_profile(username)
        repos = await self.github_api.get_user_repos(username)

        if not profile:
            return await ctx.respond(
                f"Failed to fetch profile for **{username}**.", ephemeral=True
            )

        embed = _embeds.construct_profile_embed(profile, repos)

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="View on GitHub",
                url=profile["html_url"],
            )
        )

        await ctx.respond(embed=embed, view=view)

    @_git.command(
        name="repo",
        description="Get information about a repository.",
    )
    async def _repo(
        self,
        ctx: discord.ApplicationContext,
        repo: discord.Option(
            str,
            "The repository to get the information for (e.g. owner/repo)",
            required=True,
        ),
    ) -> None:
        if "/" not in repo:
            return await ctx.respond(
                "Invalid repository name. Please use the format owner/repo.",
                ephemeral=True,
            )
        repo = await self.github_api.fetch_repo(repo)

        if not repo:
            return await ctx.respond(
                f"Failed to fetch repo details for {repo}.", ephemeral=True
            )

        embed = _embeds.construct_repo_embed(repo)

        view = discord.ui.View()
        view.add_item(
            discord.ui.Button(
                label="View on GitHub",
                url=repo["html_url"],
            )
        )

        await ctx.respond(embed=embed, view=view)


def setup(bot_: discord.Bot):
    bot_.add_cog(Github(bot_))
