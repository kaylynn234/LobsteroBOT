"""
help
"""

# imports imports imports
import os
import sys
import logging

from discord.ext import commands
from .lobstero.bot import LobsteroBOT
from .lobstero import lobstero_config

lc = lobstero_config.LobsteroCredentials()
root_directory = f"{sys.path[0]}/LobsteroBOT/".replace("\\", "/")
os.chdir(root_directory)

# loop = asyncio.ProactorEventLoop()
logging.basicConfig(level=logging.INFO)
bot = LobsteroBOT(case_insensitive=lc.config.case_insensitive, owner_ids=set(lc.config.owner_id))

# venvs don't like ext.menus, this is mostly not needed but just in case
try:
    from discord.ext import menus
    print(f"Looks like ext.menus is already installed at {menus.__name__}! Great work.")
except ImportError:
    print("Ext.menus is not installed! Installing now - make sure you have curl on path.")
    write_to = commands.__file__.replace("commands", "menus")
    url = "https://raw.githubusercontent.com/Rapptz/discord-ext-menus/master/discord/ext/menus/__init__.py"
    os.mkdir(write_to.replace("__init__.py", ""))
    os.system(f"curl {url} --output {write_to}")
    from discord.ext import menus


@bot.command()
@commands.is_owner()
async def reload(ctx):
    """Reloads all modules."""

    status = await ctx.send("Attempting to reload modules...")
    try:
        for task in bot.background_tasks:
            try:
                task.cancel()
            except RuntimeError:
                pass

        bot.handle_extensions(lc.config.cogs_to_load, True)
        for task in bot.background_tasks:
            try:
                task.start()
            except RuntimeError:
                pass

        await status.edit(content="~~Attempting to reload modules...~~\nModules reloaded successfully.")
    except Exception:
        await status.edit(content=(
            "~~Attempting to reload modules...~~\nErrors occurred while reloading. Check console output for details."
            )
        )

        raise


while True:
    bot.handle_extensions(lc.config.cogs_to_load, None)
    bot.run(lc.auth.token)
