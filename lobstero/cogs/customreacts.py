import random
import asyncio
import json
import sys

import validators
import discord

from discord.ext import commands
from discord.ext.menus import MenuPages
from lobstero.utils import embeds, db, strings
from lobstero.models import menus, handlers

root_directory = sys.path[0] + "/"


class Cog(commands.Cog, name="Custom Reactions"):
    """It's not spam, I swear."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def cradd(self, ctx, trigger, *, response):
        """Add a custom reaction."""
        if await db.aio.find_matching_response(str(ctx.guild.id), trigger):
            base = await ctx.send(embed=embeds.cr_confirmation)
            try:
                msg = await self.bot.wait_for(
                    'message',
                    timeout=10.0,
                    check=lambda message: message.author == ctx.author)

            except asyncio.futures.TimeoutError:
                return await base.edit(embed=embeds.cr_timeout)

            if not msg.content.lower() in ["overwrite", "add"]:
                return await base.edit(embed=embeds.cr_formatted_incorrectly)

            if msg.content.lower() == "overwrite":
                await base.edit(embed=embeds.cr_triggertype)

                try:
                    msg2 = await self.bot.wait_for(
                        'message',
                        timeout=10.0,
                        check=lambda message: message.author == ctx.author)

                except asyncio.futures.TimeoutError:
                    return await base.edit(embed=embeds.cr_timeout)

                if msg2.content.lower() in ["full", "partial"]:
                    await db.aio.remove_reaction(str(ctx.guild.id), trigger)
                    await db.aio.add_reaction(
                        str(ctx.guild.id),
                        trigger,
                        response,
                        "full" if "full" in msg2.content.lower() else "partial")

                    embed = discord.Embed(title="Reaction added!", color=16202876)
                    return await base.edit(embed=embed)
                else:
                    return await base.edit(embed=embeds.cr_formatted_incorrectly)
            else:
                await db.aio.add_reaction(str(ctx.guild.id), trigger, response, )
                embed = discord.Embed(title="Reaction added!", color=16202876)
                return await base.edit(embed=embed)

        else:
            base = await ctx.send(embed=embeds.cr_triggertype)

            try:
                msg2 = await self.bot.wait_for(
                    'message',
                    timeout=10.0,
                    check=lambda message: message.author == ctx.author)

            except asyncio.futures.TimeoutError:
                return await base.edit(embed=embeds.cr_timeout)

            if msg2.content.lower() in ["full", "partial"]:
                await db.aio.add_reaction(
                    str(ctx.guild.id),
                    trigger,
                    response,
                    "full" if "full" in msg2.content.lower() else "partial")

                embed = discord.Embed(title="Reaction added!", color=16202876)
                return await base.edit(embed=embed)
            else:
                return await base.edit(embed=embeds.cr_formatted_incorrectly)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def crdel(self, ctx, *, trigger):
        """Delete a custom reaction."""
        if await db.aio.find_matching_response(str(ctx.guild.id), trigger):
            await db.aio.remove_reaction(str(ctx.guild.id), trigger)
            embed = discord.Embed(title="Reaction removed.", color=16202876)
        else:
            embed = discord.Embed(
                title="There isn't a custom reaction with that trigger!",
                color=16202876)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def crdeny(self, ctx):
        """Deny the current channel access to custom reactions."""
        if not await db.aio.is_denied(str(ctx.guild.id), str(ctx.channel.id)):
            await db.aio.add_new_deny_channel(ctx.guild.id, str(ctx.channel.id))
            embed = discord.Embed(
                title="Custom reactions are now denied in this channel.",
                color=16202876)

        else:
            embed = discord.Embed(
                title="Custom reactions are already denied in this channel!",
                color=16202876)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def crallow(self, ctx):
        """Allow the current channel access to custom reactions."""
        if await db.aio.is_denied(str(ctx.guild.id), str(ctx.channel.id)):
            await db.aio.remove_deny_channel(ctx.guild.id, str(ctx.channel.id))
            embed = discord.Embed(
                title="Custom reactions are now allowed in this channel.",
                color=16202876)

        else:
            embed = discord.Embed(
                title="Custom reactions are already allowed in this channel!",
                color=16202876)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def crlist(self, ctx):
        """List all custom reactions on this server."""
        reactions = await db.aio.return_server_reacts_list(str(ctx.guild.id))

        if not reactions:
            return await ctx.send(embed=embeds.cr_none_present)

        s = {x["trigger"]: json.loads(x["response"]) for x in reactions}
        data = {
            trigger: (
                f"**1 response**: {responses[0]}"
                if len(responses) == 1
                else f"**{len(responses)} responses** - see ``<crinfo (trigger)`` for details.")
            for trigger, responses in s.items()}

        menu = menus.TupleEmbedMenu(
            list(data.items()), "Showing all custom reactions on this server",
            5, footer=True)

        pages = MenuPages(source=menu)
        await pages.start(ctx)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def crinfo(self, ctx, *, trigger):
        """Vuew info on a custom reaction with the provided trigger."""
        reactions = await db.aio.return_server_reacts_list(str(ctx.guild.id))
        if not reactions:
            return await ctx.send(embed=embeds.cr_none_present)

        if not await db.aio.find_matching_response(str(ctx.guild.id), trigger):
            return await ctx.send(embed=embeds.cr_no_trigger)

        reaction = await db.aio.raw_find_matching_response(str(ctx.guild.id), trigger)
        responses = json.loads(reaction["response"])
        mtype = reaction["type"]
        desc = f"**Trigger type**: {mtype}\n**Total responses**: {str(len(responses))}"
        embed = discord.Embed(title="Reaction info", description=desc, color=16202876)

        for index, x in enumerate(responses):
            embed.add_field(
                name=f"Response {str(index + 1)}",
                value=strings.clip(x),
                inline=False)

        return await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def crsearch(self, ctx, *, query=None):
        """Search for a custom reaction based on a query."""
        fetched = []
        reactions = await db.aio.return_server_reacts_list(str(ctx.guild.id))
        if not reactions:
            return await ctx.send(embed=embeds.cr_none_present)

        for x in reactions:
            response = [y.lower() for y in json.loads(x["response"])]
            if query.lower() in response or query.lower() in x["trigger"]:
                fetched.append(x["trigger"])

        if not fetched:
            desc = "No reactions matched your search query."
        else:
            desc = "".join([
                "The following reactions matched your search query:\n\n",
                strings.bblockjoin(fetched)])

        embed = discord.Embed(title="Search results", description=desc, color=16202876)
        return await ctx.send(embed=embed)

    @commands.Cog.listener()
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def on_message(self, message):
        """Called every message. Handles reactions."""
        if message.author.bot is False and message.guild:

            if await db.aio.is_denied(str(message.guild.id), str(message.channel.id)):
                return

            if message.content is None or message.content == "":
                return

            reacts = await db.aio.return_server_reacts_list(message.guild.id)
            for reaction in reacts:
                is_partial = (
                    reaction["type"] == "partial" and
                    reaction["trigger"].lower() in message.content.lower())

                is_full = message.content.lower() == reaction["trigger"].lower()
                if is_full is True or is_partial is True:
                    response = random.choice(json.loads(reaction["response"]))

                    if response.startswith(r"%r "):
                        for x in response.split(r"%r ", )[-1].split(" "):
                            print("x = '", x, "'")
                            return await message.add_reaction(x)

                    is_image = any([
                        response.lower().endswith(".png"), response.lower().endswith(".jpg"),
                        response.lower().endswith(".jpeg"), response.lower().endswith(".webp"),
                        response.lower().endswith(".bmp")])

                    if validators.url(response) and is_image:
                        embed = discord.Embed(title=reaction["trigger"], color=16202876)
                        embed.set_image(url=response)
                        return await message.channel.send(embed=embed)

                    if r"%@u" in response:
                        response = response.replace(r"%@u", message.author.mention)

                    if r"%u" in response:
                        response = response.replace(r"%u", message.author.name)

                    if r"%+u" in response:
                        response = response.replace(
                            r"%+u",
                            message.author.name + str(message.author.discriminator))

                    return await message.channel.send(response)


def setup(bot):
    """It does the thing which makes things happen."""
    bot.add_cog(Cog(bot))
