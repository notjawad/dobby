import discord
import constants

from discord.ext import commands
from utils import _stackoverflow
from utils._ui import StackOverflowSelectMenu
from utils._formatting import iso_to_discord_timestamp
from typing import Optional


class Tools(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sf_client = _stackoverflow.StackOverflow()

    sf_group = discord.commands.SlashCommandGroup(
        name="stackoverflow",
        description="Stack Overflow commands.",
    )

    @sf_group.command(
        name="search",
        description="Search Stack Overflow.",
    )
    async def sf_search(
        self,
        ctx: discord.ApplicationCommand,
        query: discord.Option(str, description="Search query.", required=True),
    ):
        results = await self.sf_client.search(query, 10)  # 10 results
        if not results["items"]:
            return await ctx.respond("No results found.")

        embed = discord.Embed(
            color=constants.COLORS["white"],
        )

        embed.description = "\n".join(
            [
                f"{constants.EMOJIS['check'] if result['is_answered'] else constants.EMOJIS['cross']} [`{result['question_id']}`]({result['link']}) {result['title']}"
                for result in results["items"]
            ]
        )

        select_menu = StackOverflowSelectMenu(results["items"])
        select_menu.add_options_from_results()
        view = discord.ui.View()
        view.add_item(select_menu)

        await ctx.respond(embed=embed, view=view)

    @sf_group.command(
        name="user",
        description="Get a Stack Overflow user.",
    )
    async def sf_user(
        self,
        ctx: discord.ApplicationCommand,
        username: discord.Option(
            str,
            description="The username to get the profile for.",
            required=True,
        ),
    ):
        user = await self.sf_client.get_user(username)

        if not user:
            return await ctx.respond("No user found with the provided ID.")

        embed = self.create_user_embed(user)
        view = self.create_stackoverflow_button(user["link"])

        await ctx.respond(embed=embed, view=view)

    def format_badges(self, badge_counts: dict) -> str:
        badges = {
            "🥇": badge_counts["gold"],
            "🥈": badge_counts["silver"],
            "🥉": badge_counts["bronze"],
        }

        return " ".join(
            f"{badge} {count}" for badge, count in badges.items() if count != 0
        )

    def create_stackoverflow_button(self, url: str) -> discord.ui.View:
        button = discord.ui.Button(
            label="Open in StackOverflow", url=url, style=discord.ButtonStyle.link
        )
        view = discord.ui.View()
        view.add_item(button)
        return view

    def create_user_embed(self, user: dict) -> discord.Embed:
        embed = discord.Embed(color=constants.COLORS["white"])
        embed.set_author(
            name=f"{user['display_name']} ({user['user_id']})",
            icon_url=user["profile_image"],
            url=user["link"],
        )

        description_lines = [
            f"🌎 {user['location']}" if user["location"] else "",
            f"🔗 {user['website_url']}" if user["website_url"] else "",
            "👔 Employee" if user["is_employee"] else "",
        ]

        embed.description = "\n".join(filter(None, description_lines))
        embed.add_field(
            name="Joined", value=iso_to_discord_timestamp(user["creation_date"])
        )
        embed.add_field(name="Reputation", value=user["reputation"])
        embed.add_field(name="Badges", value=self.format_badges(user["badge_counts"]))

        return embed


def setup(bot: commands.Bot):
    bot.add_cog(Tools(bot))
