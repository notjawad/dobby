import discord
import constants
import aiohttp
import psutil
import platform
import datetime
import inspect
import json, os

from discord.ext import commands
from utils import _formatting, _github
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
        self.github_api = _github.GitHubAPI()
        self.start_time = datetime.datetime.now(datetime.timezone.utc)
        self.cache_file = "source_cache.json"
        self._load_cache()

    def _load_cache(self):
        # Load the cache from a file, if it exists; otherwise, initialize an empty cache.
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "r") as f:
                self.cache = json.load(f)
        else:
            self.cache = {}

    def _save_cache(self):
        # Save the current cache to a file.
        with open(self.cache_file, "w") as f:
            json.dump(self.cache, f)

    async def paste(self, content: str, command_name: str) -> str:
        # First, check if the command's source is already cached.
        if command_name in self.cache:
            return self.cache[command_name]

        # If not cached, create a new paste and update the cache.
        async with aiohttp.ClientSession() as session:
            async with session.post("https://paste.rs/", data=content) as resp:
                if resp.status == 201:
                    paste_url = await resp.text()
                    # Update cache and save it
                    self.cache[command_name] = paste_url
                    self._save_cache()
                    return paste_url
                else:
                    return None

    @discord.slash_command(
        name="about", description="Get some useful (or not) information about the bot."
    )
    async def about(self, ctx: discord.ApplicationContext):
        async with aiohttp.ClientSession() as session:
            commit = await self.github_api.fetch_latest_commits(constants.BOT_REPO)
            commit = commit[0]

        uptime = str(
            datetime.datetime.now(datetime.timezone.utc) - self.start_time
        ).split(".")[0]

        version = f"[`{commit['sha'][:7]}`]({commit['html_url']}) - {_formatting.iso_to_discord_timestamp(commit['commit']['author']['date'])}"

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

    @discord.slash_command(
        name="source", description="Get the source code for a command."
    )
    async def command_source(
        self,
        ctx: discord.ApplicationCommand,
        command_name: discord.Option(
            str, description="The command to get the source code for.", required=True
        ),
    ):
        commands = list(self.bot.walk_application_commands())

        full_name = [
            f"{command.parent.name} {command.name}" if command.parent else command.name
            for command in commands
        ]

        if command_name not in full_name:
            return await ctx.respond(f"Command **{command_name}** not found.")

        command = commands[full_name.index(command_name)]
        self.command_name = command.qualified_name
        source = inspect.getsource(command.callback)

        source = inspect.cleandoc(source)
        self.source = source

        source = source[:800]

        # Get the beginning line number and the ending line number.
        begin = inspect.getsourcelines(command.callback)[1]
        end = begin + source.count("\n")

        embed = discord.Embed(
            description=f"```py\n{source}\n```",
            color=constants.COLORS["white"],
        )
        embed.add_field(
            name="Description",
            value=command.description or "No description.",
        )
        embed.add_field(
            name="Usage",
            value=f"```/{command.qualified_name} { ' '.join([f'<{opt.name}>' for opt in command.options]) }```",
            inline=False,
        )

        full_source_button = discord.ui.Button(
            label="Full Source",
            style=discord.ButtonStyle.green,
            custom_id="full_source",
            emoji="🔎",
        )
        full_source_button.callback = self._callback_full_source

        view = discord.ui.View()
        view.add_item(full_source_button)

        await ctx.respond(embed=embed, view=view)

    async def _callback_full_source(self, interaction: discord.Interaction):
        paste_url = await self.paste(self.source, self.command_name)

        if not paste_url:
            return await interaction.response.send_message(
                "Failed to paste source code.", ephemeral=True
            )

        await interaction.response.send_message(
            paste_url,
            ephemeral=True,
        )


def setup(bot: commands.Bot):
    bot.add_cog(Info(bot))
