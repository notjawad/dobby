import aiohttp
import discord

import constants
import contextlib
from utils.formatting import iso_to_discord_timestamp


class CommitSelectMenu(discord.ui.Select):
    def __init__(self, commits, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commits = commits  # Store the commits passed to the constructor
        self.last_message = None  # Store the last message sent by this menu

    async def get_commit(self, url: str):
        async with (aiohttp.ClientSession() as session, session.get(url) as resp):
            return "Invalid commit." if resp.status != 200 else await resp.json()

    async def callback(self, interaction: discord.Interaction):
        # Delete the previous message if it exists
        if self.last_message:
            with contextlib.suppress(discord.NotFound):
                await self.last_message.delete_original_response()

        # Find the selected commit from the list of commits
        if selected_commit := next(
            (
                commit
                for commit in self.commits
                if commit["sha"].startswith(self.values[0])
            ),
            None,
        ):
            commit_data = selected_commit["commit"]
            commit_message, author_info, commit_url = (
                commit_data["message"].split("\n")[0],
                commit_data["author"],
                selected_commit["url"],
            )

            embed = discord.Embed(title=commit_message, color=constants.COLORS["green"])
            embed.add_field(
                name="Commit message:", value=commit_data["message"], inline=False
            )
            commit_ts = iso_to_discord_timestamp(author_info["date"])

            embed.add_field(
                name="Info:",
                value=f"Committed by [`{author_info['name']}`]({selected_commit['author']['html_url']}) - {commit_ts}\n",
                inline=False,
            )

            stats = await self.get_commit(commit_url)
            if stats != "Invalid commit.":
                stats = stats["stats"]
                embed.add_field(
                    name="Changes:",
                    value=f"{stats['total']} changes: ✨ {stats['additions']} additions & 🗑️ {stats['deletions']} deletions",
                    inline=False,
                )

            embed.set_footer(text=f"SHA: {selected_commit['sha']}")
            embed.set_author(
                name=selected_commit["author"]["login"],
                icon_url=selected_commit["author"]["avatar_url"],
                url=selected_commit["author"]["html_url"],
            )

            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="View on GitHub",
                    url=selected_commit["html_url"],
                    style=discord.ButtonStyle.link,
                )
            )

            self.last_message = await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )
