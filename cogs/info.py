import discord
import constants
import aiohttp
import psutil
import platform
import datetime

from discord.ext import commands
from utils import formatting, github_api
from dataclasses import dataclass


@dataclass
class BotInfo:
    latency: str
    version: str
    uptime: str
    python: str
    memory_usage: str
    server_count: int


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.github_api = github_api.GitHubAPI()
        self.start_time = datetime.datetime.now(datetime.timezone.utc)

    @discord.slash_command(
        name="about", description="Get some useful (or not) information about the bot."
    )
    async def about(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            commit = await self.github_api.fetch_latest_commits(constants.BOT_REPO)[0]

        uptime = str(
            datetime.datetime.now(datetime.timezone.utc) - self.start_time
        ).split(".")[0]

        version = f"[`{commit['sha'][:7]}`]({commit['url']}) - {formatting.iso_to_discord_timestamp(commit['commit']['author']['date'])}"

        process = psutil.Process()
        memory_usage = f"{process.memory_info().rss / 1024**2:.2f} / {psutil.virtual_memory().total / 1024**2:.2f} MB"

        bot_info = BotInfo(
            latency=f"{round(self.bot.latency * 1000)}ms",
            version=version,
            uptime=uptime,
            python=platform.python_version(),
            memory_usage=memory_usage,
            server_count=len(self.bot.guilds),
        )

        embed = discord.Embed(
            description=constants.BOT_DESCRIPTION, color=constants.COLORS["green"]
        )
        for field, value in bot_info.__dict__.items():
            embed.add_field(name=field.title().replace("_", " "), value=value)
        embed.set_thumbnail(url=self.bot.user.avatar.url)

        await ctx.respond(embed=embed)


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
