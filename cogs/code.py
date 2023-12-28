import discord
import logging
import yaml
import difflib
import aiohttp

from discord.ext import commands
from utils import _embeds, _tio

with open("default_langs.yml") as default_langs_file:
    default_langs = yaml.safe_load(default_langs_file)

with open("languages.txt") as languages_file:
    languages = languages_file.read().splitlines()


def too_long(string):
    return len(string) > 2000


class Code(commands.Cog):
    def __init__(self, bot_: discord.Bot):
        self.bot = bot_
        self.logger = logging.getLogger("dobby")

    async def paste(self, content: str) -> str:
        async with aiohttp.ClientSession() as session:
            async with session.post("https://paste.rs/", data=content) as resp:
                return await resp.text() if resp.status == 201 else None

    @commands.command(
        name="eval",
        description="Evaluate code.",
    )
    async def eval_(self, ctx: commands.Context, *, code: str) -> None:
        if not code.startswith("```"):
            return await ctx.reply(
                "Invalid code block. Please use the format ```language\ncode```"
            )

        lang = code.split("\n")[0].replace("```", "")
        code = "\n".join(code.split("\n")[1:-1]).rstrip()

        if lang not in languages:
            closest_langs = difflib.get_close_matches(lang, languages, n=3)

            return await ctx.reply(embed=_embeds.invalid_language(lang, closest_langs))

        emoji_lang = lang

        if lang in default_langs:
            lang = default_langs[lang]

        tio = _tio.Tio(lang, code)
        result = await tio.send()

        if too_long(result):
            url = await self.paste(result)
            if url:
                return await ctx.reply(f"Output was too long. {url}")
            else:
                return await ctx.reply("Output was too long and failed to paste.")

        metrics = tio.parse_metrics(result)
        embed = _embeds.create_eval_embed(emoji_lang, ctx.message, result, metrics)
        await ctx.reply(embed=embed, allowed_mentions=discord.AllowedMentions.none())


def setup(bot_: discord.Bot):
    bot_.add_cog(Code(bot_))
