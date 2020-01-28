"""Docstring to appease linter.
This is mainly just help commands."""

import collections
import discord

from discord.ext import commands, tasks
from lobstero.utils import strings
from lobstero import lobstero_config

status_position = collections.deque([0, 1, 2, 3])
lc = lobstero_config.LobsteroCredentials()

class Cog(commands.Cog, name="Miscellaneous"):
    """The commands that don't really fit anywhere."""

    def __init__(self, bot):
        self.bot = bot
        self.status_change.start()

    def cog_unload(self):
        self.status_change.cancel()

    @tasks.loop(seconds=45)
    async def status_change(self):
        """A loop that changes playing status every so often"""

        if not self.bot.is_closed():
            global status_position
            membercount = str(len(list(self.bot.get_all_members())))
            activity1 = discord.Activity(
                type=discord.ActivityType.watching,
                name="all " + str(membercount) + " of you.")
            activity2 = discord.Activity(
                type=discord.ActivityType.playing,
                name="mind games on " + str(len(list(self.bot.guilds))) + " servers.")
            activity3 = discord.Activity(
                type=discord.ActivityType.listening,
                name=str(len(list(self.bot.get_all_channels()))) + " channels.")
            activity4 = discord.Activity(
                type=discord.ActivityType.streaming,
                name='a message of hope. Have a good day!')

            activity_list = [activity1, activity2, activity3, activity4]
            await self.bot.change_presence(activity=activity_list[status_position[0]])

            status_position.rotate(1)

    @commands.command()
    async def search(self, ctx, *, text="aaaaaaaaaaaqdqdqfdqwfqwerfgeqrfgqwr3gfqerf"):
        """<search (query)

Searches for a command matching the supplied query.
If no query is given when using the command, it returns nothing."""

        results = []
        for x in self.bot.commands:
            if text.lower() in str(x.help).lower() or text.lower() in str(x.qualifed_name).lower():
                try:
                    if await x.can_run(ctx):
                        results.append(x)
                except commands.CheckFailure:
                    pass

        if not results:
            embed = discord.Embed(
                title="Search results",
                description=(
                    "No results were found that matched your query. "
                    "Try different keywords, or see <help for more information."),
                color=16202876)

            return await ctx.send(embed=embed)
        else:
            commandstring = strings.blockjoin([x.name for x in results])

        embed = discord.Embed(
            title="Search results",
            description=(
                "The following commands were found that matched your search:"
                f"\n\n{commandstring}"),
            color=16202876)

        return await ctx.send(embed=embed)

    async def runnable(self, cogobj, ctx):
        """An asynchronous iterator for runnable commands."""

        for command in cogobj.walk_commands():
            try:
                await command.can_run(ctx)
                yield command
            except commands.CheckFailure:
                pass

    async def canruncog(self, cogobj, ctx):
        """Will it work?"""

        return [x async for x in self.runnable(cogobj, ctx) if not x.root_parent]

    def gname(self, obj):
        """Less hideous naming. Probably useless."""

        if isinstance(obj, commands.Group):
            return obj.qualified_name
        else:
            return obj.name

    async def help_by_command_name(self, name, ctx):
        """Exactly what it says on the tin."""

        scommands = list(self.bot.walk_commands())
        for command in scommands:
            if name.lower() in [command.qualified_name] + command.aliases:
                try:
                    await command.can_run(ctx)
                except commands.CheckFailure:
                    return None

                if command.aliases:
                    aliases = f"the following aliases:\n{strings.blockjoin(command.aliases)}" 
                else:
                    aliases = "no aliases."

                if isinstance(command, commands.Group):
                    subcommands = (
                        f"This command has {str(len(command.commands))} subcommands."
                        f"These are:\n{strings.blockjoin([x.name for x in command.commands])}")
                else:
                    subcommands = "This command has no subcommands."

                cd = getattr(command._buckets._cooldown, 'per', None)
                cooldown = f"a {str(cd)} second" if cd else "no"

                module = "This command is not in any modules"
                if command.cog:
                    module = f"This command is in the ``{command.cog.qualified_name}`` module"

                descstr = (
                    f"Showing help for command ``{command.name.capitalize()}``.\n{module}, "
                    f"and has {aliases}\nThis command has {cooldown} cooldown.\n{subcommands}")

                embed = discord.Embed(title=f"Help", description=descstr, color=16202876)
                embed.add_field(name="Details", value=command.help)

                return embed

        return None

    async def help_by_cog_name(self, name, ctx):
        """I've been working on this one file for hours I just want my linter to shut up."""

        cogcommands = {
            cogobj: await self.canruncog(cogobj, ctx)
            for cogname, cogobj
            in self.bot.cogs.items()}

        for cog, commandlist in cogcommands.items():
            if cog.qualified_name.lower() == name.lower():
                if commandlist:
                    availstr = "``" + "``, ``".join([self.gname(x) for x in commandlist]) + "``."
                    embed = discord.Embed(
                        title=f"Help",
                        description=(
                            f"Showing help for module ``{cog.qualified_name}``. "
                            f"This module contains {str(len(commandlist))} commands. "
                            f"These are:\n{availstr}"),
                        color=16202876)
                    embed.add_field(name="Details", value=cog.description)

                    return embed
                else:
                    return None

    async def help_for_all_commands(self, ctx):
        """Very perplexing."""

        embed = discord.Embed(
            title=f"Help",
            description=f"Showing available commands for each module.",
            color=16202876)

        cogcommands = {
            cogobj: await self.canruncog(cogobj, ctx)
            for cogname, cogobj
            in self.bot.cogs.items()}

        for cog, commandlist in cogcommands.items():
            if commandlist:
                availstr = strings.blockjoin([self.gname(x) for x in commandlist])
                embed.add_field(name=cog.qualified_name, value=availstr, inline=False)

        return embed

    async def help_for_all_modules(self, ctx):
        """I wonder."""

        blocked = 0
        embed = discord.Embed(
            title=f"Help",
            description=f"Showing available modules.",
            color=16202876)

        cogcommands = {
            cogobj: await self.canruncog(cogobj, ctx)
            for cogname, cogobj
            in self.bot.cogs.items()}

        for cog, commandlist in cogcommands.items():
            if commandlist:
                embed.add_field(
                    name=cog.qualified_name,
                    value=f"Contains {str(len(commandlist))} commands.",
                    inline=False)
            else:
                blocked += 1

        if blocked > 0:
            embed.add_field(
                name="Blocked modules",
                value=(
                    f"{str(blocked)} modules have been hidden because you "
                    "do not have the permissions required to use them."),
                inline=False)

        return embed

    async def help_not_valid(self, name):
        """Hmmm."""

        embed = discord.Embed(
            title=f"Help",
            description=(
                f"A command, module or help filter that matched ``{name}`` could not be found. "
                f"Try using ``<search {name}`` to find a related command. Otherwise, use "
                "``<help modules`` to view all modules, ``<help commands`` to view all commands, "
                "``<help (module name)`` to view help on a specific module, or ``<help"
                "(command name)`` to view help on a specific command."),
            color=16202876)
        return embed

    async def help_queryless(self, ctx):
        """What could it be?"""

        modulen, commandn = 0, 0
        embed = discord.Embed(
            title=f"Help",
            description=f"Showing available modules.",
            color=16202876)

        cogcommands = {
            cogobj: await self.canruncog(cogobj, ctx)
            for cogname, cogobj
            in self.bot.cogs.items()}

        for _, commandlist in cogcommands.items():
            if commandlist:
                modulen += 1
                commandn += len(commandlist)

        embed = discord.Embed(
            title=f"Help",
            description=(
                f"Currently, you can use {str(commandn)} commands across {str(modulen)} modules. "
                "Use ``<help modules`` to view all modules, ``<help commands`` to view "
                "all commands, ``<help (module name)`` to view help on a specific module, or "
                "``<help (command name)`` to view help on a specific command."),
            color=16202876)

        return embed

    @commands.command()
    @commands.guild_only()
    async def help(self, ctx, *, query=None):
        """<help (query)

Finds help based on the query given. Query can be blank, or it can be a command name/ module name.
All arguments are optional.
        """

        if not query:
            return await ctx.send(embed=await self.help_queryless(ctx))
        if query.lower() == "modules":
            await ctx.send(embed=await self.help_for_all_modules(ctx))
        elif query.lower() == "commands":
            await ctx.send(embed=await self.help_for_all_commands(ctx))
        else:
            embed = await self.help_by_cog_name(query.lower(), ctx)
            if embed:
                return await ctx.send(embed=embed)
            embed = await self.help_by_command_name(query.lower(), ctx)
            if embed:
                return await ctx.send(embed=embed)

            return await ctx.send(embed=await self.help_not_valid(query))

    @commands.command(aliases=["invite"])
    async def info(self, ctx):
        """<info
Contains an invite link to add the bot to your server.
Also has a link to join Lobstero's support server."""
        embed = discord.Embed(
            color=16202876,
            description=(
                f"Lobstero is a badly programmed discord bot developed by Kaylynn#4444. "
                f"This instance of Lobstero is owned by {lc.config.owner_name}. "
                "Find the bot on GitHub at https://github.com/kaylynn234/LobsteroBOT"))
        embed.add_field(name="Lobstero's support server", value=lc.config.support_server_url)
        appinfo = await self.bot.application_info()
        _id = appinfo.id
        embed.add_field(
            name="Invite Lobstero to your server",
            value=f"https://discordapp.com/api/oauth2/authorize?client_id={_id}&scope=bot")
        embed.set_footer(text=f"Connected on {(len(self.bot.guilds))} servers.")
        await ctx.send(embed=embed)


def setup(bot):
    """Help"""
    bot.add_cog(Cog(bot))
