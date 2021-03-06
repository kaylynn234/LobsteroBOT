"""Provides a set of utilities for various things.
Generally to do with logging/data manipulation"""

import math
import time

from typing import Type, Any, Sequence

import pendulum
import discord

from discord.ext import commands


def utclog(ctx: Type[commands.Context], message: str) -> None:
    """Logs to console with a timestamp.
    Uses the bot's logger.
    Handles unicode bullshit too."""

    try:
        ctx.bot.log.info("%s | %s", str(pendulum.now("Atlantic/Reykjavik")), message)
    except UnicodeDecodeError:
        ctx.bot.log.critical("%s | UnicodeDecodeError ocurred while printing.", str(pendulum.now("Atlantic/Reykjavik")))


def ordinal(n) -> str:
    """Creates an ordinal out of an int."""
    return "%d%s" % (n, "tsnrhtdd"[
        (math.floor(n/10) % 10 != 1)*(n % 10 < 4) * n % 10::4])


def populate(thing: Any) -> dict:
    """Populates a dictionary with mock settings values"""
    old = dict(thing)
    standard = {
        "respond_on_mention": True,
        "random_messages": False,
        "random_reactions": False,
        "welcome_messages": True,
        "moderation_confirmation": True}
    standard.update(old)
    return standard


async def handle_dm(owners, message, bot) -> None:
    """Handles a DM if one is received."""
    attachment_urls = None

    if message.attachments:
        attachment_urls = "\n".join([x.url for x in message.attachments])
    if "https://discord" in message.content.lower():
        appinfo = await bot.application_info()
        _id = appinfo.id
        await message.channel.send(embed=discord.Embed(
            title="Hol' up!", description=(
                "To invite Lobstero to your server, use this link: https://discordapp.com"
                f"/api/oauth2/authorize?client_id={_id}&scope=bot.\n\n"
                "You must be signed in to discord on your web browser and have "
                "manage server permissions in the server you wish to add the bot to.")))

    else:
        await message.channel.send(embed=discord.Embed(
            title="Hol' up!", description=(
                "All messages sent to Lobstero are monitored but are not public, "
                "and are only seen by the bot's owner.\n"
                "**Commands do not work in DMs**. If you want to know how to do something, "
                "use <help on any server.\n**If you want to send feedback, please use "
                "<feedback, as it's easier for the bot's developer to keep up with.** "
                "Or you can just send a DM to Lobstero, so do whatever. Your choice. ")))

    ownerembed = discord.Embed(
        title=f"DM from user {message.author.name}",
        description=f"{message.content or '(Message empty)'}")
    ownerembed.add_field(name="Attachments", value=f"{attachment_urls or 'No attachments'}")
    ownerembed.set_footer(text=str(message.author.id))

    for owner in owners:
        await owner.send(embed=ownerembed)


def chunks(l, n) -> list:
    """Splits a sequence into a list of lists with size n"""
    for i in range(0, len(l), n):
        yield l[i:i+n]


def clamp(x, minimum, maximum):
    """Fits a number into a range."""
    return max(minimum, min(x, maximum))


def calculate_investment_details(submission):
    age = pendulum.duration(seconds=time.time() - submission.created_utc)
    adjusted_score = submission.score * (submission.upvote_ratio / 100)
    asset_growth_score = round(adjusted_score / age.total_hours(), 3)
    asset_interactivity_score = ((age.total_hours() * (submission.upvote_ratio / 100)) / 72) * 100

    info = [
        f"This asset's ID is ``{submission.id}``. Save this value to invest in this asset!",
        "Basic asset information can be seen below:\n"
        f"**Growth score**: {asset_growth_score}",
        "*The growth score is a measure used to judge the growth of an asset.*",
        f"**Interactivity score**: {round(asset_interactivity_score, 3)}%",
        "*The interactivity score shows how happy the market is with this asset over time.*\n",
        "*For both values, higher is better*"
    ]

    embed = discord.Embed(
        title="Market browser",
        description="\n".join(info), color=16202876)

    embed.set_image(url=submission.url)

    return embed