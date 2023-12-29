import aiohttp
import discord
import re

from html import unescape
import constants
import contextlib
from utils._formatting import iso_to_discord_timestamp
from utils._stackoverflow import StackOverflow


class CommitSelectMenu(discord.ui.Select):
    def __init__(self, commits, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.commits = commits
        self.last_message = None

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

            embed = discord.Embed(
                title=f"{commit_message[:253]}...", color=constants.COLORS["green"]
            )
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


class StackOverflowSelectMenu(discord.ui.Select):
    def __init__(self, results, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.results = results
        self.last_message = None
        self.sf_client = StackOverflow()

    def parse_body(self, body: str) -> str:
        body = unescape(body)

        body = body.replace(
            '<pre class="lang-py prettyprint-override">', "```python\n"
        ).replace("</pre>", "```")

        body = re.sub(r"<code>(.*?)</code>", r"`\1`", body)
        body = re.sub(r'<a href="(.*?)"[^>]*>(.*?)</a>', r"[`\2`](\1)", body)
        body = re.sub(r"<.*?>", "", body)
        return body

    async def callback(self, interaction: discord.Interaction):
        if self.last_message:
            with contextlib.suppress(discord.NotFound):
                await self.last_message.delete_original_response()

        if selected_result := next(
            (
                result
                for result in self.results
                if str(result["question_id"]) == self.values[0]
            ),
            None,
        ):
            embed = discord.Embed(
                title=selected_result["title"],
                url=selected_result["link"],
                color=constants.COLORS["orange"],
            )

            question_body = await self.sf_client.get_question_body(
                selected_result["question_id"]
            )

            if question_body:
                embed.description = self.parse_body(question_body[:600])
                if len(question_body) > 600:
                    embed.description += "..."

            embed.set_author(
                name=selected_result["owner"]["display_name"]
                + f"(• {selected_result['owner']['reputation']})",
                icon_url=selected_result["owner"]["profile_image"],
                url=selected_result["owner"]["link"],
            )

            embed.add_field(
                name="Answers",
                value=str(selected_result["answer_count"]),
                inline=True,
            )
            embed.add_field(
                name="Score", value=str(selected_result["score"]), inline=True
            )

            embed.add_field(
                name="Tags",
                value=", ".join(selected_result["tags"]),
                inline=False,
            )

            embed.add_field(
                name="Views",
                value=str(selected_result["view_count"]),
                inline=True,
            )

            embed.add_field(
                name="Last Activity",
                value=iso_to_discord_timestamp(selected_result["last_activity_date"]),
                inline=True,
            )

            embed.add_field(
                name="Creation Date",
                value=iso_to_discord_timestamp(selected_result["creation_date"]),
                inline=True,
            )

            open_in_stackoverflow = discord.ui.Button(
                label="Open in StackOverflow",
                url=selected_result["link"],
                style=discord.ButtonStyle.link,
            )
            view = discord.ui.View()
            view.add_item(open_in_stackoverflow)

            # Send the embed to the channel
            self.last_message = await interaction.response.send_message(
                embed=embed, view=view, ephemeral=True
            )

    # Add options to the select menu
    def add_options_from_results(self):
        for result in self.results:
            self.add_option(
                label=unescape(
                    result["title"][:100]
                ),  # Truncate if too long for select option
                description=f"Score: {result['score']} | Answers: {result['answer_count']}",
                value=str(result["question_id"]),
            )
