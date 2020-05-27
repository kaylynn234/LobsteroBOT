"""Provides a set of tools for handling things.
Mainly to do with the commands extension."""

from discord.ext import commands
from ..utils import db
from ...lobstero import lobstero_config
from ..models.exceptions import BlueprintFailure

lc = lobstero_config.LobsteroCredentials()


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


async def blueprint_check(ctx):
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
            if can_run is check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)
        elif check["criteria_type"] == "is_guild_owner":
            can_run = str(ctx.author.id) == str(ctx.guild.owner.id)
            if can_run is check["criteria_requires"]:
                successful.append(check)
            else:
                failed.append(check)

    if failed:
        raise BlueprintFailure(ctx, successful, failed)
    else:
        return True


def blueprints_or(c=None):
    """A check to make blueprints work."""

    async def predicate(ctx):
        blueprints_passed = await blueprint_check(ctx)
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

        # if blueprints_passed is False there were no blueprints for the command
        # if it's True, the blueprint passed
        if passed_result or blueprints_passed:
            return True

    return commands.check(predicate)
