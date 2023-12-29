import discord
import constants

from discord.ext import commands
from utils import _stackoverflow
from utils._ui import StackOverflowSelectMenu


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


def setup(bot: commands.Bot):
    bot.add_cog(Tools(bot))
