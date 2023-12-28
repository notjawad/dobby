import discord
import traceback
import os
import asyncio
import constants


from discord.ext import commands, tasks
from dotenv import load_dotenv
from log_config import setup_logging


load_dotenv()
setup_logging()


class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=".l ",
            intents=discord.Intents.all(),
            activity=discord.Game(name=""),
        )
        self.status_cycle.start()

        extensions_dir = "cogs"
        for filename in os.listdir(extensions_dir):
            if filename.endswith(".py"):
                extension = f"{extensions_dir}.{filename[:-3]}"
                try:
                    self.load_extension(extension)
                except Exception as e:
                    print(f"Failed to load extension {extension}.")
                    traceback.print_exc()

        self.remove_command("help")

    async def on_ready(self):
        print(f"Logged in as {self.user} ({self.user.id})")

    @tasks.loop(minutes=10)
    async def status_cycle(self):
        await self.wait_until_ready()

        for status in constants.BOT_STATUSES:
            await self.change_presence(activity=discord.Game(name=status))
            await asyncio.sleep(600)


bot = Bot()
bot.run(
    os.getenv("bot_token"),
)
