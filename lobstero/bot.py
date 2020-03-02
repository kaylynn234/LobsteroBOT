"""The heart of Lobstero itself.
This is where the subclassed bot object lies."""

import logging
import random
import discord

from typing import Any, Type

from discord.ext import commands
from discord.ext.menus import MenuPages
from chattymarkov import ChattyMarkovAsync
from lobstero.utils import db, misc, text, embeds, strings
from lobstero.models import handlers, menus
from lobstero import lobstero_config

lc = lobstero_config.LobsteroCredentials()

config_types = {
    ("auth", "database_address"): str,
    ("auth", "cat_api_key"): str,
    ("auth", "spotify_client_id"): str,
    ("auth", "spotify_client_secret"): str,
    ("auth", "token"): str,
    ("config", "owner_name"): str,
    ("config", "owner_id"): list,
    ("config", "image_channel"): int,
    ("config", "home_channel"): int,
    ("config", "cogs_to_load"): list,
    ("config", "prefixes"): list,
    ("config", "case_insensitive"): bool,
    ("config", "spotify_playlist_uri"): str,
    ("config", "support_server_url"): str,
    ("config", "wkhtmltoimage_path"): str
}

failed = False
for value, required in config_types.items():
    try:
        received = getattr(getattr(lc, value[0]), value[1])
        assert isinstance(received, required)
    except AssertionError:
        logger = logging.getLogger(__name__)
        logger.fatal(
            "Config file configured incorrectly! Value %s does not match required type.", value[1])
        failed = True

if failed:
    logger.fatal("One or more config values was of the incorrect type. Execution cannot continue.")
    input("Press any key to exit.")
    exit(1)


class LobsteroCONTEXT(commands.Context):

    async def send(self, content=None, *, tts=False, embed=None, file=None, files=None, delete_after=None, nonce=None):
        try:
            return await super().send(
                content, tts=tts, embed=embed, file=file, files=files, delete_after=delete_after,
                nonce=nonce)

        except discord.errors.Forbidden:
            if self.guild:
                perms = self.guild.me.permissions_in(self.channel)
                if perms.send_messages:
                    await super().send((
                        "⚠️ **|** I tried to send an embed or file in this channel, "
                        "but was unable to due to a lack of permissions."), delete_after=5)

            raise

    async def simple_embed(self, content):
        """Sends an embed."""
        await embeds.simple_embed(content, self)


class LobsteroHELP(commands.HelpCommand):

    async def generate_cog_help(self, cog):
        usable_commands = []
        retrieved = cog.get_commands()  # normally i wouldn't, but we'll reuse this

        for command in cog.get_commands():
            try:
                usable = await command.can_run(self.context)
            except:  # fuck you flake8
                usable = False

            if usable:
                usable_commands.append(command)

        if not usable_commands:  # empty list
            return None

        embed = discord.Embed(title="Help", color=16202876)
        description = [
            f"```{cog.qualified_name}```",
            f"{cog.description}\n",
            "```Commands```",
            strings.blockjoin([command.name for command in usable_commands])
        ]

        if len(usable_commands) != len(retrieved):
            delta = len(retrieved) - len(usable_commands)
            if delta == 1:
                embed.set_footer(text=(
                    "1 command has been omitted because you lack the "
                    "permissions required to use it."))
            else:
                embed.set_footer(text=(
                    f"{delta} commands have been omitted because you lack the "
                    "permissions required to use them."))

        embed.description = "\n".join(description)
        return embed

    async def single_help(self, command):
        embed = discord.Embed(title="Help", color=16202876)
        description = [
            f"{self.context.prefix}{command.qualified_name} {command.signature}",
            "<*arg*> represents a required argument. [*arg*] represents an optional argument.",
            "**Do not actually use these symbols when using commands!**\n",
            f"{command.help or '*(No detailed help provided)*'}"
        ]

        if isinstance(command, commands.Group):
            description[0] += "(subcommand)"
            description[1] += " (*subcommand*) represents where a subcommand can be used."
            embed.add_field(
                name=f"{len(command.commands)} subcommand(s):",
                value=strings.blockjoin([c.name for c in command.commands]))

        if command.aliases:
            embed.add_field(
                name=f"{len(command.aliases)} alias(es):",
                value=strings.blockjoin(command.aliases))

        cd = getattr(command._buckets._cooldown, 'per', None)

        description[0] = f"```{description[0]}```"
        embed.description = "\n".join(description)
        if cd:
            embed.set_footer(text=f"This command has a {cd} second cooldown.")

        await self.context.send(embed=embed)

    async def send_command_help(self, command):
        await self.single_help(command)

    async def send_group_help(self, group):
        await self.single_help(group)

    async def send_cog_help(self, cog):
        to_send = await self.generate_cog_help(cog)
        if to_send:
            await self.context.send(embed=to_send)
        else:
            await self.context.simple_embed(
                "You do not have the permissions required to use this module.")

    async def send_bot_help(self, _):
        embed = discord.Embed(title="Help", color=16202876)

        cogs = sorted(self.context.bot.cogs.values(), key=lambda c: c.qualified_name)
        raw_pages = [await self.generate_cog_help(cog) for cog in cogs]
        cog_pages = [page for page in raw_pages if page is not None]

        description = [
            "From here, you can:",
            "_ _   • Use the reactions below to navigate between module help pages.",
            "_ _   • Use *<help (module)* to view help on a module.",
            "_ _   • Use *<help (command)* to view help on a command.\n",
            "You can also use *<info* to view more information about Lobstero."
        ]

        embed.description = "\n".join(description)

        pages = menus.HelpPagesMenu([embed] + cog_pages)
        menu = MenuPages(pages, timeout=90, clear_reactions_after=True)
        await menu.start(self.context)

    async def send_error_message(self, error):
        await self.context.simple_embed(error)


class LobsteroBOT(commands.AutoShardedBot):

    def __init__(self, **kwargs: Any):
        command_prefix = self.get_prefix
        self.log = logging.getLogger(__name__)  # type: Type[logging.Logger]
        self.first_run = True
        self.markov_generator = ChattyMarkovAsync(lc.auth.database_address)
        self.handler = handlers.LobsterHandler(self)

        super().__init__(command_prefix, help_command=LobsteroHELP(), **kwargs)

        self.load_extension("jishaku")
        self.restricted_channels = {  # will implement this in a db later, for now this'll work
            177192169516302336: (487287141047599106, 487288080764502016)
        }

    async def get_prefix(self, message) -> str:
        """Gets the prefix that should be used based on message context."""

        prefix_l = db.prefix_list()
        if str(message.guild.id) not in prefix_l:
            return lc.config.prefixes
        else:
            if prefix_l[str(message.guild.id)]["prefix"] == "<":
                return lc.config.prefixes
            else:
                return prefix_l[str(message.guild.id)]["prefix"]

    def handle_extensions(self, seq, loadtype=False, excluded=[]) -> None:
        """Deals with management of Lobstero's extensions."""

        for filename in seq:
            if filename not in excluded:
                f = f"lobstero.cogs.{filename}"
                if loadtype:
                    self.reload_extension(f)
                    pre = "RELOAD: "
                elif loadtype is False:
                    self.unload_extension(f)
                    pre = "UNLOAD: "
                else:
                    self.load_extension(f)
                    pre = "LOAD: "

                self.log.info("%sExtension file %s", pre, filename)
            else:
                self.log.info("SKIP: Extension file %s", filename)

    async def on_ready(self) -> None:
        """My linter wants me to add a docstring for this."""

        if self.first_run:
            self.first_run = False
            await self.markov_generator.connect()
            # self.handle_extensions(lc.config.cog_mapping, True)

        chn = self.get_channel(lc.config.home_channel)
        await chn.send("Bot online.")
        self.log.info("Bot online.")

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="you. <help | <info")

        await self.change_presence(activity=activity)

    async def handle_blacklist(self, ctx):
        """A check that runs once before every command execution.
        In our case, this checks if a user/server/channel is blacklisted.
        If they are, they get sent a spooky message, and the command isn't executed.
        """

        blacklisted = True in [
            db.is_not_blacklisted(str(ctx.author.id), "user"),
            db.is_not_blacklisted(str(ctx.guild.id), "guild"),
            db.is_not_blacklisted(str(ctx.channel.id), "channel")]

        if blacklisted is False:
            misc.utclog(ctx, f"{ctx.author} cannot use command {ctx.command.name}.")
            await ctx.send((
                f"**{ctx.author.name}**, {random.choice(text.quotelist)} "
                "Your access to bot functions has been disabled."), delete_after=10)
            await ctx.message.add_reaction("🚫")
        else:
            if ctx.valid:
                commandname = getattr(ctx.command, "name", None)
                misc.utclog(ctx, f"{ctx.author} is trying to use command {commandname}.")

        if ctx.guild.id == 177192169516302336:
            if ctx.message.channel.id in [487287141047599106, 487288080764502016]:
                blacklisted = True
            else:
                blacklisted = False

        return blacklisted

    async def on_message(self, message):
        """Called every message. Processes commands."""

        should_continue = False

        for server, channels in self.restricted_channels.items():
            if message.guild is not None and message.guild.id == server:
                if message.channel.id not in channels:
                    return

        if message.author.bot:
            return

        if message.guild:
            table = db.give_table()
            if message.guild.id not in table:
                th = misc.populate({})
            else:
                th = misc.populate(table[message.guild.id])

        else:
            owners = [self.get_user(id_) for id_ in lc.config.owner.owner_id]
            return await misc.handle_dm(owners, message)

        blacklists = (
            db.is_not_blacklisted(str(message.channel.id), "channel"),
            db.is_not_blacklisted(str(message.guild.id), "guild"))

        if False not in blacklists:
            if random.randint(1, 2000) == 2000 and th["random_reactions"]:
                await message.add_reaction(random.choice(text.emotes))

            elif random.randint(1, 4000) == 4000 and th["random_reactions"]:
                await message.add_reaction("\N{CHESTNUT}")
                await message.add_reaction("\N{ALARM CLOCK}")

            user_mentioned = (
                f"<@{message.guild.me.id}>" in message.content or
                f"<@!{message.guild.me.id}>" in message.content)

            if th["respond_on_mention"] and user_mentioned:
                should_continue = True

            elif random.randint(1, 567) == 567 and th["random_messages"]:
                should_continue = True

            elif message.channel.name == "crabversation":
                should_continue = True
        else:
            return

        c_ctx = await self.get_context(message)
        can_continue = await self.handle_blacklist(c_ctx)

        if can_continue and should_continue and not c_ctx.valid:
            await c_ctx.trigger_typing()
            markov = await self.markov_generator.generate()

            await c_ctx.send(markov)

        # Process commands
        ctx = await self.get_context(message, cls=LobsteroCONTEXT)
        await self.invoke(ctx)

    async def on_command_error(self, ctx, error) -> None:
        await self.handler.handle(ctx, error)

    async def on_error(self, event_method, *args, **kwargs):
        if str(event_method) == "on_command_error":
            return  # already handled

        msg = f"""**Additional notes:**
        Event: {event_method}
        Provided args: {", ".join([str(i) for i in args])}
        Provided kwargs: {", ".join([f"{x}: {y}" for x, y in kwargs])}
        """
        await self.handler.format_tb_and_send(additional=msg)
