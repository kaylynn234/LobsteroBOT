"""Owner commands and all that.
You get the point."""

import sys

from typing import Union

import discord

from discord.ext import commands
from discord.ext.menus import MenuPages
from lobstero.utils import db, embeds, strings
from lobstero.models import menus

root_directory = sys.path[0] + "/"


class Cog(commands.Cog, name="Bot Owner"):
    """Owner stuff."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def respond(self, ctx, userid: int, *, message):
        """<respond (userid) (message)

Sends a message to a user (specified by ID) in DMs. 
        """
        user = self.bot.get_user(userid)
        try:
            await user.send(embed=discord.Embed(
                title="Response from bot developer",
                description=message,
                color=16202876))

            await ctx.send("Message sent!")
        except discord.errors.Forbidden:
            await ctx.send("Message not sent.")

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def blacklist(self, ctx, *, who: Union[discord.User, discord.TextChannel, discord.Guild]):
        """<blacklist {User, Guild, Channel}

Denies the specified object access to bot functionality.
        """
        if isinstance(who, discord.User):
            blocktype = "user"
        elif isinstance(who, discord.TextChannel):
            blocktype = "channel"
        elif isinstance(who, discord.Guild):
            blocktype = "guild"
        else:
            print("I'm not sure how we got here")
            return

        db.blacklist_add(str(who.id), blocktype)
        await embeds.simple_embed("User blacklisted", ctx)

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def whitelist(self, ctx, *, who: Union[discord.User, discord.TextChannel, discord.Guild]):
        """<whitelist {User, Guild, Channel}

Allows the specified object access to bot functionality.
        """
        if isinstance(who, discord.User):
            blocktype = "user"
        elif isinstance(who, discord.TextChannel):
            blocktype = "channel"
        elif isinstance(who, discord.Guild):
            blocktype = "guild"
        else:
            print("I'm not sure how we got here")
            return

        db.blacklist_remove(str(who.id), blocktype)
        await embeds.simple_embed("User removed from blacklist", ctx)

    def file_len(self, fname) -> int:
        """Opens a file, returning its length in lines"""
        with open(fname, encoding="utf-8", errors="ignore") as f:
            for i, l in enumerate(f):
                pass
        return i + 1

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @commands.guild_only()
    @commands.is_owner()
    async def serverinfo(self, ctx):
        """Provides a set of information about connected servers."""
        guilds = len(self.bot.guilds)
        members = len(list(self.bot.get_all_members()))
        channels = len(list(self.bot.get_all_channels()))
        avg_m = int(members / guilds)
        avg_c = int(channels / guilds)

        embed = discord.Embed(color=16202876, title="Server information", description=f"""
        Connected to {str(guilds)} servers.
        {str(members)} members are visible.
        {str(channels)} channels are visible.
        On average, each server has {avg_m} members and {avg_c} channels.""")
        await ctx.send(embed=embed)

    @serverinfo.command(name="show")
    @commands.guild_only()
    @commands.is_owner()
    async def serverinfo_page(self, ctx):
        """Shows a list of servers."""
        data = [f"[{guild.id}] {guild.name}" for guild in self.bot.guilds]
        menu = menus.ListEmbedMenu(data, "Showing all servers", 10, True)
        pages = MenuPages(source=menu)
        await pages.start(ctx)

    @serverinfo.command(name="details")
    @commands.guild_only()
    @commands.is_owner()
    async def serverinfo_details(self, ctx, guildid: int = None):
        """Shows details about a specific server."""
        guild = self.bot.get_guild(guildid)

        if guild is None:
            return await embeds.simple_embed("Invalid server!", ctx)

        channel_names = [f"[{str(channel.id)}]: " + channel.name for channel in guild.channels]
        channels = strings.blockjoin(channel_names)
        large = "a large guild" if guild.large else "not a large guild"

        servert = f"""
        Server name: {guild.name}.
        Server region: {str(guild.region)}.
        
        This server has {str(len(guild.voice_channels))} voice channels.
        This server has {str(len(guild.roles))} roles.
        This server has {str(guild.member_count)} members.
        This server has {str(len(guild.channels))} channels.
        
        This server is {large}.
        This server is owned by {str(guild.owner)}, and was created at {str(guild.created_at)}.
        My nickname on this server is {guild.me.nick if guild.me.nick else self.bot.user.name}.

        """
        embed = discord.Embed(color=16202876, title="Server information", description=servert)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon_url)
        if guild.banner:
            embed.set_image(url=guild.banner_url)
        if len(channels) < 1000:
            embed.add_field(name="Channels", value=channels)
        else:
            embed.add_field(name="Channels", value="There are too many channels to display.")
        await ctx.send(embed=embed)

    @serverinfo.command(name="channels")
    @commands.guild_only()
    @commands.is_owner()
    async def serverinfo_channels(self, ctx, guildid: int = None):
        """Shows a list of channels on a server.."""
        guild = self.bot.get_guild(guildid)

        if guild is None:
            return await embeds.simple_embed("Invalid server!", ctx)

        data = [f"``{chn.type}``: [{chn.id}] {chn.name}" for chn in guild.channels]
        menu = menus.ListEmbedMenu(data, "Showing all channels on this guild", 8, True)
        pages = MenuPages(source=menu)
        await pages.start(ctx)

    @serverinfo.command(name="members")
    @commands.guild_only()
    @commands.is_owner()
    async def serverinfo_members(self, ctx, guildid: int = None):
        """Shows a list of members in a server."""
        guild = self.bot.get_guild(guildid)

        if guild is None:
            return await embeds.simple_embed("Invalid server!", ctx)

        data = [f"{member} | Bot: {member.bot}" for member in guild.members]
        menu = menus.ListEmbedMenu(data, "Showing all members in this guild", 8, True)
        pages = MenuPages(source=menu)
        await pages.start(ctx)

    @serverinfo.command(name="peek")
    @commands.guild_only()
    @commands.is_owner()
    async def serverinfo_peek(self, ctx, channelid: int = None):
        """Looks through recent messages in a channel."""
        channel = self.bot.get_channel(channelid)

        if channel is None:
            return await embeds.simple_embed("Invalid channel!", ctx)

        try:
            messages = await channel.history(limit=10).flatten()
        except discord.errors.Forbidden:
            return await embeds.simple_embed("Cannot peek channel!", ctx)
        messages.reverse()
        for message in messages:
            attachments = "\n".join([attachment.url for attachment in message.attachments])
            await ctx.send((
                f"{str(message.author)}:\n{str(message.content)}"
                f"\n\nHas attachments: {attachments}"))

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def querydb(self, ctx, *, text):
        await ctx.send(f"{db.query_db(text)}")


def setup(bot):
    """Fuck you flake8"""
    bot.add_cog(Cog(bot))
