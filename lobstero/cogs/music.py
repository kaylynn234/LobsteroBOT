import wavelink
from discord.ext import commands


class Cog(commands.Cog, name="Music"):
    """I heard you liked music."""

    def __init__(self, bot):
        self.bot = bot

        if not hasattr(bot, 'wavelink'):
            self.bot.wavelink = wavelink.Client(self.bot)

        self.bot.loop.create_task(self.start_nodes())

    async def start_nodes(self):
        await self.bot.wait_until_ready()

        await self.bot.wavelink.initiate_node(
            host="127.0.0.1", port=2333, rest_uri="http://127.0.0.1:2333",
            password="lobsterlink", identifier='TEST', region='us_central')
    
    # TODO: Make a menu-based "remote" command to control music
    # TODO: Make a check to decide whether the user can use a command based on vc member count
    # TODO: Add all of the commands lol (play, pause, skip, queue)
    # Pay spoecial attention to making skip not suck
    # TODO: Add MIDI play
    # TODO: Add play by file upload
    # TODO: Add management class and integrate with ctx (attach to bot, fetch on ctx init)
    # actually maybe don't, it sounds kinda bad
    # TODO: Allow looping (regardless) and shuffle (if playlists are present)
    # TODO: Allow volume change during play
    # TODO: Add an EQ of some sort
    # TODO: Allow handing the remote to someone else


def setup(bot):
    bot.add_cog(Cog(bot))