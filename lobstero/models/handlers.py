"""Provides a set of tools for handling errors."""

import traceback
import io

import discord

from collections import Counter
from typing import Type
from urllib3.exceptions import InsecureRequestWarning

from discord.ext import commands
from lobstero.models.exceptions import BlueprintFailure
from lobstero.utils import embeds, strings, misc, db
from lobstero import lobstero_config

lc = lobstero_config.LobsteroCredentials()


class LobsterHandler():
    """A crabby solution to error handling.
    Allows logging of errors, as well as some special things.
    Namely error tracking. See how many total things have gone wrong!"""

    def __init__(self, bot):
        self.session_errors = {
            "handled": Counter(),
            "swallowed": Counter(),
            "raised": Counter()}
        self.bot = bot

    async def format_tb_and_send(self, additional=None):
        f = io.StringIO()
        traceback.print_exc(8, f)  # Prints to a stream
        to_be_formatted = f.getvalue()
        sendable = [f"```python\n{x}```" for x in misc.chunks(to_be_formatted, 1980)]

        for userid in lc.config.owner_id:
            destination = await self.bot.fetch_user(userid)
            try:
                for to_send in sendable:
                    await destination.send(to_send)
                if additional:
                    await destination.send(additional)
            except Exception as exc:
                print(f"Exception: {exc}")  # Can't be helped

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
                f"Missing required argument ``{error.param.name}``")

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

        if isinstance(error, discord.errors.Forbidden):
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

        if isinstance(error, commands.errors.DisabledCommand):
            handled, message = embeds.errorbed(
                "This command is currently disabled.")

        if isinstance(error, BlueprintFailure):
            handled, message = embeds.errorbed(
                error.description)

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
            try:
                raise error
            except Exception:
                await self.format_tb_and_send(additional=str((dir(error), error.args)))

            raise error  # Raise again, now that it's been logged on discord.


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


def blueprint_check(ctx):
    """A preliminary check that enables blueprint functionality.."""
    res = db.blueprints_for(str(ctx.guild.id), ctx.command.qualified_name)
    if res is None:
        return False

    successful, failed = [], []
    for check in res:
        if check["criteria_type"] == "has_any_role":
            if bool(ctx.author.roles) is check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)
        elif check["criteria_type"] == "has_role":
            role = check["criteria_value"] in [str(x.id) for x in ctx.author.roles]
            if role is check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)
        elif check["criteria_type"] == "has_permissions":
            perms = ctx.author.permissions_in(ctx.channel)
            can_run = getattr(perms, check["criteria_value"], False)
            if can_run is check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)
        elif check["criteria_type"] == "has_strict_permissions":
            perms = ctx.author.permissions
            can_run = getattr(perms, check["criteria_value"], False)
            if can_run is check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)
        elif check["criteria_type"] == "is_specific_user":
            can_run = str(ctx.author.id) == check["criteria_value"]
            if can_run == check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)
        elif check["criteria_type"] == "is_guild_owner":
            can_run = str(ctx.author.id) == str(ctx.guild.owner.id)
            if str(ctx.author.id) == check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)

    if failed:
        raise BlueprintFailure(ctx.bot, successful, failed)
    else:
        return True


def blueprints_or(c=None):
    """A check to make blueprints work."""

    async def predicate(ctx):
        blueprinted = blueprint_check().predicate
        blueprints_passed = await blueprinted(ctx)
        # this can raise an error, which will propogate if it does

        # test the non-blueprint check
        if c is not None:
            try:
                pred = c.predicate
            except AttributeError:
                raise TypeError('%r must be wrapped by commands.check decorator' % c) from None
        else:
            return True

        passed_result = await pred(ctx)
        await ctx.send(pred)
        
        # if blueprints_passed is False there were no blueprints for the command
        # if it's True, the blueprint passed
        if passed_result or blueprints_passed:
            return True
        
        await ctx.send("we shouldn't be here")

    return commands.check(predicate)
