"""
help
"""

# imports imports imports
import os
import sys
import logging

from discord.ext import commands
from lobstero.bot import LobsteroBOT
from lobstero import lobstero_config

lc = lobstero_config.LobsteroCredentials()
root_directory = sys.path[0] + "/"
os.chdir(root_directory)

# loop = asyncio.ProactorEventLoop()
logging.basicConfig(level=logging.INFO)

bot = LobsteroBOT(
    case_insensitive=lc.config.case_insensitive,
    owner_ids=set(lc.config.owner_id))

try:
    from discord.ext import menus
    print(f"Looks like ext.menus is already installed at {menus.__name__}! Great work.")
except ImportError:
    print(f"Ext.menus is not installed! Installing now - make sure you have curl on path.")
    write_to = commands.__file__.replace("commands", "menus")
    url = (
        "https://raw.githubusercontent.com/Rapptz/discord-ext-menus/"
        "master/discord/ext/menus/__init__.py")
    os.mkdir(write_to.replace("__init__.py", ""))
    os.system(f"curl {url} --output {write_to}")


@bot.command()
@commands.is_owner()
async def reload(ctx):
    """<reload

Reloads all modules. No parameters are required.
    """

    status = await ctx.send("Attempting to reload modules...")
    try:
        bot.handle_extensions(lc.config.cogs_to_load, True)
        await status.edit(content=(
            "~~Attempting to reload modules...~~\n"
            "Modules reloaded successfully."))
    except Exception as error:
        await status.edit(content=(
            "~~Attempting to reload modules...~~\n"
            "Errors occurred while reloading. "
            "Check console output for details."))
        raise error

bot.handle_extensions(lc.config.cogs_to_load, None)
bot.run(lc.auth.token)

# everything has gone to shit!
# time to try and save it
backup = commands.Bot(command_prefix=commands.when_mentioned)
backup.load_extension("jishaku")


@backup.on_command_error
async def on_command_error(context, exception):
    if isinstance(exception, commands.CommandNotFound):
        await context.send("Lobstero is currently in maintenace mode. It will be functional again shortly.")


# all the jank
while bot.dead:
    try:
        backup.run(lc.auth.token)
    except:
        pass
