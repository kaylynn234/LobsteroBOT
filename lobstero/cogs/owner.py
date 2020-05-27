"""Owner commands and all that.
You get the point."""

import sys

import discord

from discord.ext import commands
from discord.ext.menus import MenuPages
from ..utils import embeds, strings
from ..models import menus

root_directory = sys.path[0] + "/"


class Cog(commands.Cog, name="Bot Owner"):
    """Owner related commands.
You shouldn't even see this. if you do, you know what it does."""
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def respond(self, ctx, userid: int, *, message):
        """Sends a message to a user in DMs."""

        user = self.bot.get_user(userid)
        try:
            await user.send(embed=discord.Embed(
                title="Response from bot developer",
                description=message,
                color=16202876))

            await ctx.send("Message sent!")
        except discord.errors.Forbidden:
            await ctx.send("Message not sent.")

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
        Connected to {guilds} servers.
        {members} members are visible.
        {channels} channels are visible.
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
        Server region: {guild.region}.

        This server has {len(guild.voice_channels)} voice channels.
        This server has {len(guild.roles)} roles.
        This server has {guild.member_count} members.
        This server has {len(guild.channels)} channels.

        This server is {large}.
        This server is owned by {guild.owner}, and was created at {guild.created_at}.
        My nickname on this server is {guild.me.nick or self.bot.user.name}.

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


def setup(bot):
    """Fuck you flake8"""
    bot.add_cog(Cog(bot))
