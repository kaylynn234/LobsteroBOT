import os
import sys
import pickle
import requests
import discord
import humanize
import dateparser
import pendulum

from lobstero.utils import embeds, db, strings, misc
from lobstero.models import menus, handlers
from discord.ext.menus import MenuPages
from datetime import timedelta
from natural import date
from io import open as iopen
from py_expression_eval import Parser
from discord.ext import commands, tasks
from PIL import Image, ImageDraw, ImageFont, ImageOps

afks = []
whitelist = [487374098864013352, 369883232767836161]
root_directory = sys.path[0] + "/"


class afkh:

    def __init__(self, user, reason):
        self.user, self.reason, = user, reason.replace("*", "")
        self.time = pendulum.now("Atlantic/Reykjavik")

    def print(self):
        delta = pendulum.now("Atlantic/Reykjavik") - self.time
        return f"*{self.user.name} is AFK*: {self.reason} - {humanize.naturaltime(delta)}"


class Cog(commands.Cog, name="Utilities"):
    """A bunch of utility-related commands.
Think avatars, emoji, and so on.
Also features commands for setting AFk statuses and similar."""
    def __init__(self, bot):
        self.bot = bot
        self.bot.afks = []
        self.check_reminders.start()

    def cog_unload(self):
        self.check_reminders.cancel()

    @commands.command(aliases=["e", "emote"])
    @handlers.blueprints_or()
    async def emoji(self, ctx, emoji: str):
        """Grabs a large version of an emoji."""

        em = strings.split_count(emoji)
        embed_mesg = discord.Embed(title="Emoji", color=16202876)
        if em:
            escape = f"{ord(em[0]):X}"
            filename = f"{root_directory}data/static/emojis/{escape}.png"
            to_send = discord.File(filename, filename=f"{escape}.png")
            embed_mesg.set_image(url=f"attachment://{escape}.png")
            return await ctx.send(file=to_send, embed=embed_mesg)

        emo_id = emoji.split(":")[2].split(">")[0]
        if not emoji.startswith("<a:"):
            emourl = f"https://cdn.discordapp.com/emojis/{emo_id}.png?v=1"
        else:
            emourl = f"https://cdn.discordapp.com/emojis/{emo_id}.gif?v=1"
        embed_mesg.set_image(url=emourl)
        await ctx.send(embed=embed_mesg)

    @commands.command(aliases=["a", "pfp"])
    @handlers.blueprints_or()
    async def avatar(self, ctx, user: str = None):
        """Grabs the avatar of a member. Will send yours if no arguments are prvoided."""

        if user is None:
            member = ctx.message.mentions[0]
        else:
            member = ctx.author
        embed_mesg = discord.Embed(title="Profile picture for " + str(member) + ".", color=16202876)
        embed_mesg.set_image(url=member.avatar_url_as(static_format="png", size=2048))
        await ctx.send(embed=embed_mesg)

    @commands.command()
    @handlers.blueprints_or()
    async def afk(self, ctx, *, reason="afk"):
        """Set an afk status so that people know why you're not in chat."""
        await ctx.send(f"I set your AFK - {reason}")
        data = afkh(ctx.author, reason)
        self.bot.afks.append(data)

    @commands.command()
    @handlers.blueprints_or()
    async def afkmessage(self, ctx, *, message="Welcome back. I removed your afk."):
        """Set a custom message for when you return from being AFK. 
Use the command without an argument to reset it."""

        if message == "Welcome back. I removed your afk.":
            await embeds.simple_embed("AFK message reset.", ctx)
            db.afk_message_set(ctx.author.id, message)
        else:
            if len(message) > 160:
                await embeds.simple_embed((
                    "AFK messages have a maximum character limit of 160."
                    f"You provided {len(message)} charcters."), ctx)
            else:
                db.afk_message_set(ctx.author.id, message)
                await embeds.simple_embed("AFK message changed!", ctx)

    @commands.command(aliases=["p", "pong"])
    @handlers.blueprints_or()
    async def ping(self, ctx):
        """Shows the bot's connection to discord."""
        racket = "<:pong:521111731364429834>" 
        await ctx.send(f"{racket} **Pong!** Took {round(self.bot.latency * 1000, 2)} ms.")

    @commands.command()
    @commands.cooldown(1, 300, commands.BucketType.member)
    @handlers.blueprints_or()
    async def clear(self, ctx):
        """Clear recent messages sent by the bot."""

        messagelist = [m async for m in ctx.channel.history(limit=10) if m.author == ctx.guild.me]
        await ctx.channel.delete_messages(messagelist)

    @commands.command(enabled=False)
    @handlers.blueprints_or()
    async def profile(self, ctx, *, user: discord.Member = None):
        """View the lobstero profile of a user - including earned badges, hugs given, and role colour."""

        if user is None:
            user = ctx.message.author
        
        bglayer = Image.new("RGBA", (630, 270), (255, 255, 255, 255))
        file_url = user.avatar_url_as(format="png", size=128)

        i = requests.get(file_url)
        with iopen(root_directory + "data/downloaded" + str(user.id) + ".png", 'wb') as mfile:
            mfile.write(i.content)
        
        userpfp = Image.open(root_directory + "image_downloads/profile" + str(user.id) + ".png")
        fitted = ImageOps.fit(userpfp, (68, 68), Image.ANTIALIAS, 0)
        fitted = fitted.convert("RGBA")

        bglayer.paste(fitted, (30, 28), fitted)

        sharptext = Image.new("RGBA", (1100, 150), (255, 255, 255, 0))
        draw = ImageDraw.Draw(sharptext)
        font = ImageFont.truetype(root_directory + "data/regular.otf", 50)

        draw.text((0, 0), f"{user.name}#{user.discriminator}", (0, 0, 0, 255), font=font)

        sharptext.save("C:/Users/kaylynn/Pictures/PDN monstrosities/exported_h.png")

        sharptext = sharptext.resize((int(sharptext.width / 2), int(sharptext.height / 2)))

        template = Image.open("C:/Users/kaylynn/Pictures/PDN monstrosities/lobstero_profile_detail.png")
        template = template.convert("RGBA")
        template.paste(sharptext, (116, 43), sharptext)

        bglayer.paste(template, mask=template)

        draw = ImageDraw.Draw(bglayer)
        font = ImageFont.truetype(root_directory + "data/regular.otf", 35)

        if os.path.isfile(root_directory + "data/hugstats/" + str(user.id) + ".pickle"):
            with open(root_directory + "data/hugstats/" + str(user.id) + ".pickle", "rb") as f:
                hugcounter = pickle.load(f)
        else:
            hugcounter = 0

        draw.text((135, 172), str(hugcounter), (0, 0, 0, 255), font=font)

        locked = Image.open(f"{root_directory}data/images/hugs/locked.png").convert("RGBA").resize((30, 30), Image.ANTIALIAS)
        wood = Image.open(f"{root_directory}data/images/hugs/wood.png").convert("RGBA").resize((30, 30), Image.ANTIALIAS)
        bronze = Image.open(f"{root_directory}data/images/hugs/bronze.png").convert("RGBA").resize((30, 30), Image.ANTIALIAS)
        silver = Image.open(f"{root_directory}data/images/hugs/silver.png").convert("RGBA").resize((30, 30), Image.ANTIALIAS)
        gold = Image.open(f"{root_directory}data/images/hugs/gold.png").convert("RGBA").resize((30, 30), Image.ANTIALIAS)
        diamond = Image.open(f"{root_directory}data/images/hugs/diamond.png").convert("RGBA").resize((30, 30), Image.ANTIALIAS)

        badgestr = [locked, locked, locked, locked, locked]
        if hugcounter >= 10:
            badgestr = [wood, locked, locked, locked, locked]
        if hugcounter >= 100:
            badgestr = [wood, bronze, locked, locked, locked]
        if hugcounter >= 500:
            badgestr = [wood, bronze, silver, locked, locked]
        if hugcounter >= 1750:
            badgestr = [wood, bronze, silver, gold, locked]
        if hugcounter >= 4000:
            badgestr = [wood, bronze, silver, gold, diamond]

        for index, x in enumerate(badgestr):

            bglayer.paste(x, (362 + 7 + 7 + (37 * index), 151 + 7), x)

        h = str(user.color).replace("#", "")
        rgbt = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        draw = ImageDraw.Draw(bglayer)
        draw.ellipse((362 + 7 + 7, 151 + 44, 392 + 7 + 7, 151 + 74), fill=rgbt)

        bglayer.save(f"{root_directory}image_downloads/profile_result/{str(user.id)}.png")
        to_send = discord.File(f"{root_directory}image_downloads/profile_result/{str(user.id)}.png")
        await ctx.send(file=to_send)

    @commands.command(aliases=["w", "wi", "who", "userinfo"])
    @handlers.blueprints_or()
    async def whois(self, ctx, *, user: discord.User = None):
        """Shows some simple information about a user.
If no parameters are provided, shows details for you instead."""

        embed = discord.Embed(title="Details about " + user.name, color=16202876)
        embed.add_field(name="Account created", value=str(user.created_at), inline=True)
        embed.add_field(name="Avatar URL", value=str(user.avatar_url), inline=True)
        embed.add_field(name="Username", value=user.name, inline=True)
        embed.add_field(name="ID", value=str(user.id), inline=True)
        embed.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=embed)

    @commands.group()
    @commands.guild_only()
    async def tag(self, ctx, *, tagname=None):
        """Finds details about the provided tag."""

        if tagname is None:
            return await embeds.simple_embed("Please specify a tag to find the value of.", ctx)
        value = db.return_tag(ctx.guild.id, tagname.lower())
        if value is None:
            return await embeds.simple_embed("There is no tag for that value.", ctx)
        embed = discord.Embed(
            title=f"Tag value for {tagname.capitalize()}.",
            description=strings.capitalize_start(value, ". "), color=16202876)

        await ctx.send(embed=embed)

    @tag.command(name="add")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def addtag(self, ctx, tagname=None, *, tagvalue=None):
        """Adds a tag for this server. Make sure you quote arguments that are multiple words."""

        if tagvalue is None:
            return await embeds.simple_embed("Please specify a tag name and a tag value.", ctx)
        db.set_tag(ctx.guild.id, tagname, tagvalue)
        await embeds.simple_embed("Tag added!", ctx)

    @tag.command(name="remove")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def removetag(self, ctx, tagname=None):
        """Removes a tag from this server by name.
Make sure you quote arguments that are multiple words."""

        if tagname is None:
            return await embeds.simple_embed("Please specify a tag name.", ctx.guild.id)
        db.delete_tag(ctx.guild.id, tagname)
        await embeds.simple_embed("Tag removed.", ctx.channel.id)

    @tag.command(name="list")
    @commands.guild_only()
    @handlers.blueprints_or()
    async def taglist(self, ctx):
        """Lists all tags on this server."""

        results = db.return_all_tags(ctx.guild.id)
        if not results:
            return await embeds.simple_embed("There are no tags on this server!", ctx.channel.id)
        source = menus.ListEmbedMenu(results, "Showing all tags for this server", 5, True)
        menu = MenuPages(source, timeout=30)
        await menu.start(ctx)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def math(self, ctx, *, equation):
        """Does math for you."""

        parser = Parser()

        try:
            expr = parser.parse(equation)
        except Exception:
            embed = discord.Embed(
                title="The expression you provided appears to be formatted incorrectly.",
                color=16202876)
            return await ctx.send(embed=embed)

        embed = discord.Embed(
            title="Your expression evaluates to the following:",
            description=f"``{expr.simplify({}).toString()}``", color=16202876)

        return await ctx.send(embed=embed)

    @commands.command(aliases=["reminder", "remind"])
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @handlers.blueprints_or()
    async def remindme(self, ctx, *, when=None):
        """Schedules a reminder for you. Valid usage is similar to below:
<remindme stop procrastinating in 20m

Valid usage can also include the following:
<remindme do something important in 12 hours, 13 minutes and 1 second"""

        if when:
            if " in " in when:
                date = f'in {when.split(" in ")[-1]}'
                reason = " in ".join(when.split(" in ")[0:-1])
                decoded = dateparser.parse(date, settings={'TIMEZONE': 'UTC'})
                if decoded:
                    passed = pendulum.parse(str(decoded))
                    db.add_reminder(
                        ctx.author.id, reason, passed,
                        str(pendulum.now("Atlantic/Reykjavik")))  # utc + 0

                    await embeds.simple_embed(
                        f"Got it! I'll remind you in {passed.diff_for_humans(absolute=True)}.", ctx)
                else:
                    await embeds.simple_embed("That doesn't seem like a valid date!", ctx)
            else:
                await embeds.simple_embed("No date was provided!", ctx)
        else:
            await embeds.simple_embed("I can't remind you about nothing.", ctx)

    @tasks.loop(seconds=10)
    async def check_reminders(self):
        res = await db.return_all_expiring_reminders()
        if not res:
            return

        for item in res:
            expires_at = pendulum.parse(item["expiry"])
            set_at = pendulum.parse(item["issued"])
            rn = pendulum.now("Atlantic/Reykjavik")  # utc+0
            if rn > expires_at:
                user = self.bot.get_user(int(item["user"]))
                if user:
                    embed = discord.Embed(
                        title=f"Reminder from {set_at.diff_for_humans()}", color=16202876)
                    embed.description = item["reason"]
                    try:
                        await user.send(embed=embed)
                    except discord.errors.Forbidden:
                        pass
                db.negate_reminder(item["id"])
    
    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):

        for member in self.bot.afks:
            if member.user == message.author:
                result = db.return_afk_message(message.author.id)
                readable = date.delta(
                    pendulum.now("Atlantic/Reykjavik"), member.time, justnow=timedelta(seconds=0))[0]
                elapsed = f"\n(*Away for {readable}*)"
                if result is None:
                    await message.channel.send(
                        "Welcome back. I removed your afk." + elapsed, delete_after=10)
                else:
                    await message.channel.send(result + elapsed, delete_after=10)
                self.bot.afks.remove(member)
                return

            if member.user.mention in message.content and not message.author.bot:
                await message.channel.send(member.print(), delete_after=10)


def setup(bot):
    """Adds the goddamn cog"""
    bot.add_cog(Cog(bot))
