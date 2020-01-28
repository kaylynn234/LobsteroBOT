"""Provides a set of tools for handling errors."""

import traceback
import sys
import pendulum

import discord

from collections import Counter
from typing import Type
from urllib3.exceptions import InsecureRequestWarning

from discord.ext import commands
from lobstero.utils import embeds, strings, misc


class LobsterHandler():
    """A crabby solution to error handling.
    Allows logging of errors, as well as some special things.
    Namely error tracking. See how many total things have gone wrong!"""

    def __init__(self):
        self.session_errors = {
            "handled": Counter(),
            "swallowed": Counter(),
            "raised": Counter()}

    async def handle(self, ctx: Type[commands.Context], error: Exception) -> None:
        """Handles an exception given context and the exception itself.
        Logging is handled for you, and statistics are automatically updated."""

        handled, message = None, None
        error_name = strings.pascalcase(type(error).__name__)

        if isinstance(error, (commands.CommandNotFound, InsecureRequestWarning)):
            handled = True
            # We can swallow these safely. They do nothing helpful and pollute the console.

        if isinstance(error, commands.MissingPermissions):
            handled, message = embeds.errorbed(
                f"You are missing required permissions\n\n{strings.blockjoin(error.missing_perms)}")

        if isinstance(error, commands.errors.MissingRequiredArgument):
            handled, message = embeds.errorbed(
                f"Missing required argumen ``{error.param.name}``")

        if isinstance(error, commands.errors.TooManyArguments):
            handled, message = embeds.errorbed(
                "Too many arguments provided")

        if isinstance(error, commands.errors.BotMissingPermissions):
            handled, message = embeds.errorbed(
                f"I am missing required permissions\n\n{strings.blockjoin(error.missing_perms)}")

        if isinstance(error, commands.errors.NotOwner):
            handled, message = embeds.errorbed(
                "You are not the bot owner.")

        if isinstance(error, OverflowError):
            handled, message = embeds.errorbed(
                "What the fuck no why would you even do that jesus christ")

        if isinstance(error, commands.errors.CommandOnCooldown):
            handled, message = embeds.errorbed(
                "This command is on cooldown! You can use it again in {:.2f}s!"
                .format(error.retry_after))

        if isinstance(error, discord.errors.Forbidden) or isinstance(error, discord.Forbidden):
            handled = True
            # Nothing we can do about this one.

        if isinstance(error, AttributeError):
            handled = True
            # Nothing we can do about this one. My code is just shit.

        if isinstance(error, commands.errors.MaxConcurrencyReached):
            handled, message = embeds.errorbed(
                "This command is already in use!")

        if isinstance(error, commands.errors.BadArgument):
            handled, message = embeds.errorbed(
                "Bad argument provided! Check your capitalisation and spelling.")

        if handled and message:
            misc.utclog(ctx, (
                f"Handled {error_name} in {ctx.guild or '(No guild)'} "
                f"channel {ctx.channel or '(No channel)'} "
                f"from member \"{ctx.author or '(No author, somehow)'}\" "))
            self.session_errors["handled"][error_name] += 1
        elif handled and not message:
            self.session_errors["swallowed"][error_name] += 1
        else:
            misc.utclog(ctx, f"Exception occurred and was not handled: {error_name}: Raising")
            self.session_errors["raised"][error_name] += 1

        if message:
            try:
                await ctx.send(embed=message, delete_after=10)
            except discord.Forbidden:
                misc.utclog(ctx, f"Exception {error_name} handled, but message was not sent.")

        if not handled:
            raise error


class GreedyMention(commands.Converter):
    """Argument handler to take a bunch of mentions."""

    async def convert(self, ctx, argument):
        if isinstance(argument, str):
            if " " in argument:
                split = [x for x in argument.split(" ") if x != ""]
                valid = []
                for string in split:
                    cond1 = (string.startswith("<@") and string.endswith(">"))
                    cond2 = (string.startswith("<@!") and string.endswith(">"))
                    if cond1 or cond2:
                        try:
                            member = await commands.MemberConverter().convert(ctx, string)
                            valid.append(member)
                        except commands.BadArgument:
                            condensed = list(set(valid))
                            return [condensed, argument[argument.find(string):]]
                    else:
                        condensed = list(set(valid)) 
                        return [condensed, argument[argument.find(string):]]

                condensed = list(set(valid)) 
                return [condensed, None]

            else:
                try:
                    member = await commands.MemberConverter().convert(ctx, argument)
                    return [[member], None] 
                except commands.BadArgument:
                    return [[], argument]

        else:
            raise commands.BadArgument(message=f"Expected str instance, got {type(argument)}")
