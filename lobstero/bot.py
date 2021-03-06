"""The heart of Lobstero itself.
This is where the subclassed bot object lies."""

import logging
import difflib
import random
import traceback
import sys

import aiohttp
import discord
import uwuify

from collections import defaultdict
from typing import Any, Type

from urllib3.exceptions import InsecureRequestWarning
from discord.ext import commands
from discord.ext.menus import MenuPages
from chattymarkov import ChattyMarkovAsync
from ..lobstero.utils import db, misc, text, embeds, strings
from ..lobstero.models import menus
from ..lobstero.models.exceptions import BlueprintFailure
from ..lobstero import lobstero_config

lc = lobstero_config.LobsteroCredentials()


class LobsteroCONTEXT(commands.Context):

    async def send(self, content=None, **kwargs):
        try:
            return await super().send(content, **kwargs)

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
        return await embeds.simple_embed(content, self)


class LobsteroHELP(commands.HelpCommand):

    def __init__(self):
        self.not_found = None
        super().__init__(command_attrs={
            "aliases": [
                "hlep", "hpel", "pehl", "phel", "pleh", "halp", "holp", "howolp", "huwulp",
                "hilp", "hulp", "hylp"]})

    async def check_and_jumble(self, embed):
        if self.context.invoked_with != "help":
            if self.context.invoked_with.lower() in ["halp", "holp", "hilp", "hulp"]:
                tr = str.maketrans(
                    "e" + "E",
                    self.context.invoked_with[1].lower() + self.context.invoked_with[1].upper())

                embed.description = embed.description.translate(tr)
                embed.title = embed.title.translate(tr)
            elif self.context.invoked_with in ["howolp", "huwulp"]:
                embed.description = uwuify.uwu_text(embed.description)
                embed.title = uwuify.uwu_text(embed.title)
            elif self.context.invoked_with == "pleh":
                embed.title = " ".join([w[len(w)::-1] for w in embed.title.split(" ")])
                embed.description = " ".join([w[len(w)::-1] for w in embed.description.split(" ")])
            elif self.context.invoked_with == "hylp":
                tr = str.maketrans("aeiou", "yyyyy")
                embed.title = embed.title.translate(tr)
                embed.description = embed.description.translate(tr)
            else:
                desc = list(embed.description)
                title = list(embed.title)
                random.shuffle(desc)
                random.shuffle(title)

                embed.description = "".join(desc)
                embed.title = "".join(title)

        return embed

    async def all_usable_commands(self):
        usable_commands = []

        for command in self.context.bot.commands:
            try:
                usable = await command.can_run(self.context)
            except:  # fuck you flake8
                usable = False

            if usable:
                usable_commands.append(command)

        return usable_commands

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
            f"```Commands ({len(usable_commands)} available)``` ",
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
        return await self.check_and_jumble(embed)

    async def single_help(self, command):
        embed = discord.Embed(title="Help", color=16202876)
        description = [
            f"{self.context.prefix}{command.qualified_name} {command.signature}",
            "<*arg*> represents a required argument. [*arg*] represents an optional argument.",
            "**Do not actually use these brackets when using commands!**\n",
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

        embed = await self.check_and_jumble(embed)

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
            "_ _   • Use the ❓ reaction to view Lobstero's FAQ.",
            "_ _   • Use *<help (module)* to view help on a module.",
            "_ _   • Use *<help (command)* to view help on a command.\n",
            "You can also use *<info* to view more information about Lobstero."
        ]

        embed.description = "\n".join(description)
        embed = await self.check_and_jumble(embed)

        pages = menus.HelpPagesMenu([embed] + cog_pages)
        menu = menus.HelpCustomizedMenuPages(pages, timeout=90)
        await menu.start(self.context, wait=True)

        if menu.go_to_faq:
            embeds = [discord.Embed(title=k, description=v, color=16202876) for k, v in text.faq_pages.items()]
            newpages = menus.EmbedMenu(embeds)
            newmenu = MenuPages(newpages, clear_reactions_after=True)
            newmenu.message = menu.message
            await newmenu.message.edit(embed=embeds[0])

            await newmenu.start(self.context)

    async def command_not_found(self, string):
        self.not_found = string
        return super().command_not_found(string)

    async def subcommand_not_found(self, command, string):
        r = super().subcommand_not_found(command, string)
        if "no subcommands." not in str(r):
            self.not_found = command.qualified_name

        return r

    async def send_error_message(self, error):
        usable = [c.qualified_name for c in await self.all_usable_commands()]
        if not self.not_found:
            command_matches = cog_matches = False
        else:
            usable_cogs = self.context.bot.cogs.keys()
            command_matches = difflib.get_close_matches(self.not_found, usable)
            cog_matches = difflib.get_close_matches(self.not_found, usable_cogs)

        if not (command_matches or cog_matches):
            return await self.context.simple_embed(error)

        embed = discord.Embed(title=error, color=16202876)
        lines = []
        if cog_matches:
            lines += ["The following modules might be what you're looking for: \n"]
            lines += [f"``{m}``" for m in cog_matches] + ["\n"]
        if command_matches:
            lines += ["Did you mean: \n"]
            lines += [f"``<{m}``" for m in command_matches]

        embed.description = "\n".join(lines)
        await self.context.send(embed=embed)


class LobsteroBOT(commands.AutoShardedBot):

    def __init__(self, **kwargs: Any):
        command_prefix = self.get_prefix
        self.prefix_cache = defaultdict(lambda: {"prefix": lc.config.prefixes})
        self.log = logging.getLogger(__name__)  # type: Type[logging.Logger]
        self.first_run = True
        self.markov_generator = ChattyMarkovAsync(lc.auth.database_address)
        self.session = aiohttp.ClientSession()
        self.background_tasks = []

        super().__init__(command_prefix, help_command=LobsteroHELP(), **kwargs)

        self.load_extension("jishaku")
        self.restricted_channels = {  # will implement this in a db later, for now this'll work
            177192169516302336: (487287141047599106, 487288080764502016)
        }

    async def get_prefix(self, message) -> str:
        """Gets the prefix that should be used based on message context."""

        return self.prefix_cache[str(message.guild.id)]["prefix"]

    def handle_extensions(self, seq, loadtype=False, excluded=[]) -> None:
        """Deals with management of Lobstero's extensions."""

        for filename in seq:
            if filename not in excluded:
                f = f"LobsteroBOT.lobstero.cogs.{filename}"
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
            await db.connect_to_db()
            try:
                await self.markov_generator.connect()
            except OSError:
                async def error_message():
                    return "Chat functionality is currently disabled."

                self.markov_generator.generate = error_message

            self._db_migrate = db.migrate
            self._db_obj = db.db

        for task in self.background_tasks:
            try:
                task.start()
            except RuntimeError:
                pass  # task is already running

        self.prefix_cache = await db.prefix_list()
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

        blacklisted = False
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

        if message.author.bot or message.author.id == self.user.id:
            return

        if message.guild:
            table = await db.give_table()
            if message.guild.id not in table:
                th = misc.populate({})
            else:
                th = misc.populate(table[message.guild.id])

        else:
            owners = [self.get_user(id_) for id_ in lc.config.owner_id]
            return await misc.handle_dm(owners, message, self)

        if random.randint(1, 2000) == 2000 and th["random_reactions"]:
            await message.add_reaction(random.choice(text.emotes))

        elif random.randint(1, 4000) == 4000 and th["random_reactions"]:
            await message.add_reaction("\N{CHESTNUT}")
            await message.add_reaction("\N{ALARM CLOCK}")

        user_mentioned = (
            f"<@{self.user.id}>" in message.content or
            f"<@!{self.user.id}>" in message.content)

        cchannels = await db.find_settings_channels(message.guild.id, "conversation")
        if th["respond_on_mention"] and user_mentioned:
            should_continue = True
        elif random.randint(1, 567) == 567 and th["random_messages"]:
            should_continue = True
        elif message.channel.name == "crabversation":
            should_continue = True
        elif message.channel.id in [int(c["channel"]) for c in cchannels]:
            should_continue = True

        c_ctx = await self.get_context(message)
        can_continue = await self.handle_blacklist(c_ctx)
        if can_continue and should_continue and not c_ctx.valid:
            await c_ctx.trigger_typing()
            markov = await self.markov_generator.generate()

            await c_ctx.send(markov)

        # Process commands
        ctx = await self.get_context(message, cls=LobsteroCONTEXT)
        await self.invoke(ctx)

    async def handle(self, location, error: Exception) -> bool:
        """Handles an exception given context and the exception itself."""

        cannot_send = (
            discord.errors.Forbidden, discord.ext.menus.CannotReadMessageHistory,
            discord.ext.menus.CannotEmbedLinks, discord.ext.menus.CannotSendMessages
        )

        if isinstance(error, cannot_send):
            return False  # nothing to be done

        error = getattr(error, "original", error)  # just in case
        response = None

        if isinstance(error, (commands.CommandNotFound, InsecureRequestWarning)):
            return False

        if isinstance(error, commands.MissingPermissions):
            response = embeds.errorbed(
                f"You're missing required permissions\n\n{strings.blockjoin(error.missing_perms)}"
            )

        if isinstance(error, commands.errors.MissingRequiredArgument):
            response = embeds.errorbed(f"Missing required argument ``{error.param.name}``")

        if isinstance(error, commands.errors.TooManyArguments):
            response = embeds.errorbed("Too many arguments provided")

        if isinstance(error, commands.errors.BotMissingPermissions):
            response = embeds.errorbed(
                f"I am missing required permissions\n\n{strings.blockjoin(error.missing_perms)}"
            )

        if isinstance(error, commands.errors.NotOwner):
            response = embeds.errorbed("You are not the bot owner.")

        if isinstance(error, OverflowError):
            response = embeds.errorbed("What the fuck no why would you even do that jesus christ")

        if isinstance(error, commands.errors.CommandOnCooldown):
            response = embeds.errorbed(
                "This command is on cooldown! You can use it again in {:.2f}s!".format(error.retry_after)
            )

        if isinstance(error, commands.errors.MaxConcurrencyReached):
            response = embeds.errorbed("This command is already in use!")

        if isinstance(error, commands.errors.BadArgument):
            response = embeds.errorbed("Bad argument provided! Check your capitalisation and spelling.")

        if isinstance(error, commands.errors.DisabledCommand):
            response = embeds.errorbed("This command is currently disabled.")

        if isinstance(error, discord.ext.menus.CannotAddReactions):
            response = embeds.errorbed("This command uses a reaction menu, but the bot cannot add reactions.")

        if isinstance(error, BlueprintFailure):
            response = embeds.errorbed(error.description)

        if response:
            try:
                await location.send(embed=response, delete_after=10)
            except:
                return False
        else:
            try:
                await location.send(
                    "You've found Arnold, the unreachable error message. Now time will collapse.\n"
                    "Normally I'd have something to tell you when something went wrong, but nope, not this time.\n"
                    "My best guess? The develeper sucks. I bet an important file is missing somewhere. Past that?\n"
                    "There's a chance permissions in this channel are borked, but if you're seeing this, they probably aren't.\n"
                    "Feel free to join the support server and harass the bot developer if it makes you feel better - that's ``<info`` if you didn't know.\n"
                    "Anyway, this specific issue should get fixed soon. Hopefully. Nobody really likes Arnold anyway.",
                    delete_after=5
                )
            except discord.errors.Forbidden:
                pass  # whoop-di-doo

        return True

    async def format_tb_and_send(self, exception, location=None, additional=None):
        to_be_formatted = "".join(
            [f"{additional}\n"] + traceback.format_exception(type(exception), exception, exception.__traceback__, 4)
        )

        if "discord.errors.Forbidden" in to_be_formatted:
            return  # we don't need to spam DMs with this nonsense.

        location_message = []
        if isinstance(location, (discord.Message, commands.Context)):
            location_message = [
                f"This happened in guild {location.guild.name} with ID {location.guild.id}.\n"
                f"The message was sent in channel {location.channel.name} with ID {location.channel.id}.\n"
                f"User {location.author} with ID {location.author.id} sent the message that caused this issue.\n"
                f"The command that caused this issue was "
                f"{getattr(getattr(location, 'command', None), 'qualified_name', None) or '(None)'}"]

        sendable = location_message + [f"```python\n{x}```" for x in misc.chunks(to_be_formatted, 1980)]
        for userid in lc.config.owner_id:
            destination = await self.fetch_user(userid)
            try:
                for to_send in sendable:
                    await destination.send(to_send)
            except Exception as exc:
                print(f"Exception: {exc}")  # Can't be helped

    async def on_error(self, event_method, *args, **kwargs):
        exception = kwargs.get("exception") or sys.exc_info()[1]
        context = None
        if args:
            context = args[0] if isinstance(args[0], (discord.Message, commands.Context)) else None
        if getattr(context, "command", False):
            context.command.reset_cooldown(context)

        if isinstance(context, commands.Context):
            context_location = context
        elif isinstance(context, discord.Message):
            if context.channel:
                context_location = context.channel
            else:
                return
        else:
            return

        handled = await self.handle(context_location, exception)
        if exception and handled is True:
            await self.format_tb_and_send(exception, context, event_method)

    async def on_command_error(self, context, error):
        await self.on_error("command", context, exception=error)
