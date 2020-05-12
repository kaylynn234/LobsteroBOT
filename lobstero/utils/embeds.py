"""Makes embeds for specific purposes less of a pain in the ass.
You're welcome."""

from typing import Type

import discord


def errorbed(text: str) -> Type[discord.Embed]:
    """Formats an embed for command errors """
    return discord.Embed(title="You can't use this command!", description=text, color=16202876)


async def simple_embed(em_title: str, chn_location) -> Type[discord.Embed]:
    """Sends an embed given a title and location."""
    sm_embed = discord.Embed(title=em_title, color=16202876)
    await chn_location.channel.send(embed=sm_embed)
    # I really should be using a custom context for this but I don't care

cr_triggertype = discord.Embed(
    title="How should this reaction trigger?",
    description=(
        "If the reaction should only trigger when the message exactly matches the "
        "trigger, respond with ``full``. If the reaction should trigger when the "
        "message contains the trigger at all, respond with ``partial``."),
    color=16202876)

cr_timeout = discord.Embed(
    title="Timed out.",
    description="You didn't answer in time. No changes were committed.",
    color=16202876)

cr_formatted_incorrectly = discord.Embed(
    title="Incorrect response!",
    description="Your response was formatted incorrectly. No changes were committed.",
    color=16202876)

cr_confirmation = discord.Embed(
    title="There is already a custom reaction matching that trigger!",
    description=(
        "Respond with ``overwrite`` to overwrite it, or ``add`` to "
        "add it as another possible response. Custom reactions with multiple "
        "responses will respond with one at random when they are triggered."),
    color=16202876)

cr_none_present = discord.Embed(
    title="There are no custom reactions on this server!",
    color=16202876)

cr_no_trigger = discord.Embed(
    title="There is no custom reaction with this trigger!",
    color=16202876)


def embed_generator(title: str, description: str = None, fields: list = None):
    """Generates an embed suitable for using in ctx.send"""
    embed = discord.Embed(title=title, color=16202876)

    if description:
        embed.description = description
    if fields:
        for x in fields:
            embed.add_field(name=x[0], value=x[1], inline=x[2])

    return embed


chs = "<a:cheese:533544087484366848>"


eco_not_fast_enough = discord.Embed(
    title="Guess the card!", color=16202876, 
    description="Whoops, looks like you didn't respond in time. Game's over!")


eco_broke = discord.Embed(
    title="Guess the card!", color=16202876,
    description=f"Aww, looks like you don't have enough {chs} to play. Sorry!")

settings_embed = discord.Embed(title="Values available to change:", color=16202876)
settings_embed.add_field(
    name="respond_on_mention",
    value=(
        "Changes whether Lobstero will respond when mentioned."
        "Can be either ``True`` or ``False``."), inline=False)
settings_embed.add_field(
    name="random_messages", value=(
        "Changes whether Lobstero will occasionally send a random "
        "message. Can be either ``True`` or ``False``."), inline=False)
settings_embed.add_field(
    name="random_reactions", value=(
        "Changes whether Lobstero will randomly react to messages. "
        "Can be either ``True`` or ``False``."), inline=False)
settings_embed.add_field(
    name="welcome_messages", value=(
        "Changes whether welcome messages will be used on this server. "
        "Can be either ``True`` or ``False``."), inline=False)
settings_embed.add_field(
    name="moderation_confirmation", value=(
        "Changes whether moderation commands will require confirmation to use. "
        "**This is a very dangerous setting to change.** "
        "Can be either ``True`` or ``False``."), inline=False)
settings_embed.add_field(
    name="indexed_reactions", value=(
        "For reactions with more than 1 response, enabling this will make "
        "``(reaction trigger) (number)`` send the reaction's ``(number)`` "
        "response. Can be either ``True`` or ``False``."), inline=False)

bp_not_fast_enough = discord.Embed(
    title="Blueprints", color=16202876,
    description="Timed out. No changes were made.")

bp_wrong_value = discord.Embed(
    title="Blueprints", color=16202876,
    description="That's not a valid response! No changes were made.")
