import discord
import logging

from discord.ext import commands
from constants import *
from utils.formatting import build_pr_embed
from utils.github_api import GitHubAPI


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


def setup(bot_: discord.Bot):
    bot_.add_cog(Github(bot_))
