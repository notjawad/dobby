import discord
import logging
import constants

from discord.ext import commands
from utils.formatting import build_pr_embed
from utils.github_api import GitHubAPI
from utils.ui import CommitSelectMenu


class Github(commands.Cog):
    def __init__(self, bot_: discord.Bot):
        self.bot = bot_
        self.logger = logging.getLogger("lambda")
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
        show_comments: discord.Option(bool, "Whether to show comments", default=False),
    ) -> None:
        if "/" not in repo:
            return await ctx.respond(
                "Invalid repository name. Please use the format **owner/repo**.",
                ephemeral=True,
            )
        pr = await self.github_api.fetch_pr(repo, pr_number)

        if not pr:
            return await ctx.respond(
                f"Failed to fetch PR details for {repo}#{pr_number}.", ephemeral=True
            )

        comments = await self.github_api.fetch_pr_comments(repo, pr_number)

        embed = build_pr_embed(pr, show_comments, comments[:3])

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
                "Invalid repository format. The format should be **owner/repo**."
            )

        commits = await self.github_api.fetch_latest_commits(repo)

        if isinstance(commits, str):
            return await ctx.respond(commits)

        description = []

        for commit in commits:
            sha = commit["sha"][:7]
            message = commit["commit"]["message"].split("\n")[0]

            if len(message) > 50:
                message = f"{message[:50]}..."
            description.append(
                f"{constants.EMOJIS['check']} [`{sha}`]({commit['html_url']}) {message.replace('`', '')}"
            )

        embed = discord.Embed(
            title=f"{constants.EMOJIS['github']} Latest commits in `{repo}`",
            description="\n".join(description),
            color=constants.COLORS["green"],
            url=f"https://github.com/{repo}",
        )

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
                "Invalid repository format. The format should be **owner/repo**."
            )

        await ctx.defer()

        data = await self.github_api.fetch_lines_of_code(repo)

        embed = discord.Embed(
            title=f"Lines of Code in `{repo}`",
            color=constants.COLORS["green"],
            url=f"https://github.com/{repo}",
        )

        total_lines = sum(item["lines"] for item in data)
        total_files = sum(item["files"] for item in data)
        code_breakdown = "\n".join(
            f"{language}: {linesOfCode}"
            for language, linesOfCode in (
                (item["language"], item["linesOfCode"]) for item in data
            )
            if language != "Total"
        )

        embed.description = (
            f"A total of **{total_lines}** lines of code in **{total_files}** files."
        )
        embed.add_field(
            name="Language Breakdown:",
            value=f"```{code_breakdown}```",
            inline=False,
        )

        await ctx.respond(embed=embed)


def setup(bot_: discord.Bot):
    bot_.add_cog(Github(bot_))
