import sys
import functools

import discord
import humanize
import dateparser
import pendulum
import imgkit

from io import BytesIO
from datetime import timedelta

from ..utils import embeds, db, strings
from ..models import menus, handlers
from .. import lobstero_config 
from discord.ext.menus import MenuPages
from natural import date
from py_expression_eval import Parser
from discord.ext import commands, tasks
from PIL import Image

afks = []
whitelist = [487374098864013352, 369883232767836161]
root_directory = f"{sys.path[0]}/LobsteroBOT/".replace("\\", "/")
lc = lobstero_config.LobsteroCredentials()


if lc.config.wkhtmltoimage_path != "None":
    config = imgkit.config(wkhtmltoimage=lc.config.wkhtmltoimage_path)


class AfkHolder:

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
        self.bot.background_tasks.append(self.check_reminders)

    @commands.command(aliases=["e", "emote"])
    @handlers.blueprints_or()
    async def emoji(self, ctx, emoji: str):
        """Grabs a large version of an emoji."""

        em = strings.split_count(emoji)
        embed_mesg = discord.Embed(title="Emoji", color=16202876)
        if em:
            escape = "-".join([f"{ord(e):X}" for e in em]).lower()
            filename = f"{root_directory}lobstero/data/static/emojis/{escape}.png"
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
    async def avatar(self, ctx, user: discord.User = None):
        """Grabs the avatar of a member. Will send yours if no arguments are prvoided."""

        user = user or ctx.author
        embed_mesg = discord.Embed(title=f"Profile picture for {user}.", color=16202876)
        embed_mesg.set_image(url=user.avatar_url_as(static_format="png", size=2048))
        await ctx.send(embed=embed_mesg)

    @commands.command()
    @handlers.blueprints_or()
    async def afk(self, ctx, *, reason="afk"):
        """Set an afk status so that people know why you're not in chat."""
        c = commands.clean_content()
        scrubbed = await c.convert(ctx, reason)
        await ctx.send(f"I set your AFK - {scrubbed}")
        data = AfkHolder(ctx.author, reason)
        self.bot.afks.append(data)

    @commands.command()
    @handlers.blueprints_or()
    async def afkmessage(self, ctx, *, message="Welcome back. I removed your afk."):
        """Set a custom message for when you return from being AFK. 
Use the command without an argument to reset it."""

        if message == "Welcome back. I removed your afk.":
            await embeds.simple_embed("AFK message reset.", ctx)
            await db.afk_message_set(ctx.author.id, message)
        else:
            if len(message) > 160:
                await ctx.simple_embed(
                    f"AFK messages have a maximum character limit of 160. You provided {len(message)} charcters.")
            else:
                await db.afk_message_set(ctx.author.id, message)
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

    @commands.command()
    @handlers.blueprints_or()
    async def profile(self, ctx, *, user: discord.Member = None):
        """View the lobstero profile of a user.
If no user is specified, displays your profile."""

        if user is None:
            user = ctx.message.author

        if lc.config.wkhtmltoimage_path != "None":
            conf = {"config": config}
        else:
            conf = {}
            options = {"options": {"xvfb": ""}}

        with open(f"{root_directory}/lobstero/data/static/profile/profile.html", "r", encoding="utf-8") as profile_in:
            lobstero_profile = profile_in.read()

        locked = "https://cdn.discordapp.com/emojis/571264807119093769.png?v=1"
        wood = "https://cdn.discordapp.com/emojis/571264854376185867.png?v=1"
        bronze = "https://cdn.discordapp.com/emojis/571264868930420746.png?v=1"
        silver = "https://cdn.discordapp.com/emojis/571264858520289290.png?v=1"
        gold = "https://cdn.discordapp.com/emojis/571264849179443200.png?v=1"
        diamond = "https://cdn.discordapp.com/emojis/571264832565673984.png?v=1"

        inv = await db.find_inventory(str(user.id))
        filtered_inv = filter(lambda k: list(k.keys())[0] == "Token of love & friendship", inv)
        if not filtered_inv:
            hugcount = 0
        else:
            try:
                hugcount = int(list(list(filtered_inv)[0].values())[0])
            except IndexError:
                hugcount = 0

        badge_reqs = [10, 100, 500, 1750, 4000]
        badges = [locked, locked, locked, locked, locked]
        if hugcount >= 10:
            badges = [wood, locked, locked, locked, locked]
        if hugcount >= 100:
            badges = [wood, bronze, locked, locked, locked]
        if hugcount >= 500:
            badges = [wood, bronze, silver, locked, locked]
        if hugcount >= 1750:
            badges = [wood, bronze, silver, gold, locked]
        if hugcount >= 4000:
            badges = [wood, bronze, silver, gold, diamond]

        for i, url in enumerate(badges):
            lobstero_profile = lobstero_profile.replace(f"bdg_{i + 1}", url)

        unachieved_badges = list(filter(lambda k: k >= hugcount, badge_reqs))
        achieved = 5 - len(unachieved_badges)
        if unachieved_badges:
            if not hugcount:
                encouragement = "You should try hugging somebody!"
            else:
                encouragement = "There are still badges to be had!"
            until_next = f"{unachieved_badges[0] - hugcount} hugs until next badge. {encouragement}"
        else:
            until_next = "Looks like you've got all of the badges!"

        lobstero_profile = lobstero_profile.replace("name_and_tag", user.name)
        lobstero_profile = lobstero_profile.replace("hug_total", str(hugcount))
        lobstero_profile = lobstero_profile.replace("hg_s", str(achieved))
        lobstero_profile = lobstero_profile.replace("hg_l", "5")
        lobstero_profile = lobstero_profile.replace("until_next", until_next)
        lobstero_profile = lobstero_profile.replace("user_pfp", str(user.avatar_url_as(format="png", size=512)))
        with open(f"{root_directory}/lobstero/data/static/profile/profile_c.html", "w+", encoding="utf-8") as out:
            out.write(lobstero_profile)

        to_run = functools.partial(
            imgkit.from_file, f"{root_directory}/lobstero/data/static/profile/profile_c.html",
            f"{root_directory}/lobstero/data/downloaded/profileraw.png", **conf, **options)

        await self.bot.loop.run_in_executor(None, to_run)

        saved = Image.open(f"{root_directory}/lobstero/data/downloaded/profileraw.png")
        finished = saved.crop((0, 0, 1023, 481))

        buffer = BytesIO()
        finished.save(buffer, "png")
        buffer.seek(0)
        img = discord.File(fp=buffer, filename="profile.png")

        embed = discord.Embed(color=16202876)
        embed.set_image(url="attachment://profile.png")
        await ctx.send(file=img, embed=embed)

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
        value = await db.return_tag(ctx.guild.id, tagname.lower())
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
        await db.set_tag(ctx.guild.id, tagname, tagvalue)
        await embeds.simple_embed("Tag added!", ctx)

    @tag.command(name="remove")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def removetag(self, ctx, tagname=None):
        """Removes a tag from this server by name.
Make sure you quote arguments that are multiple words."""

        if tagname is None:
            return await embeds.simple_embed("Please specify a tag name.", ctx.guild.id)
        await db.delete_tag(ctx.guild.id, tagname)
        await embeds.simple_embed("Tag removed.", ctx.channel.id)

    @tag.command(name="list")
    @commands.guild_only()
    @handlers.blueprints_or()
    async def taglist(self, ctx):
        """Lists all tags on this server."""

        results = await db.return_all_tags(ctx.guild.id)
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

    @commands.group(invoke_without_command=True, ignore_extra=False, aliases=["reminder", "reminders"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def remind(self, ctx):
        """A base command for managing reminders. Displays a list of active reminders if no subcommand is used."""
        reminders = await db.find_reminders_for_user(ctx.author.id)
        if not reminders:
            return await ctx.simple_embed("Looks like you don't have any reminders to list.")

        rn = pendulum.now("Atlantic/Reykjavik")
        data = []

        for item in reminders:
            id_and_when = f"Reminder ID #{item['id']}: {humanize.naturaltime(rn - pendulum.parse(item['expiry']))}"
            if len(item["reason"]) > 120:
                clipped = item["reason"][:119] + "..."
            else:
                clipped = item["reason"][:119]
            data.append((id_and_when, clipped))

        menu = menus.TupleEmbedMenu(data, "Current reminders", 10, footer=True)
        pages = MenuPages(menu, clear_reactions_after=True)

        await pages.start(ctx)

    @remind.command(name="add")
    @commands.guild_only()
    @commands.cooldown(1, 60, commands.BucketType.user)
    @handlers.blueprints_or()
    async def remind_add(self, ctx, *, whatandwhen):
        """Schedules a reminder for you. Valid usage is similar to below:
<remind add stop procrastinating in 20m

Valid usage can also include the following:
<remind add do something important in 12 hours, 13 minutes and 1 second"""

        if " in " not in whatandwhen:
            await ctx.simple_embed("No date was provided!")
        else:
            date = f'in {whatandwhen.split(" in ")[-1]}'
            reason = " in ".join(whatandwhen.split(" in ")[0:-1])
            decoded = dateparser.parse(date, settings={'TIMEZONE': 'UTC'})
            if decoded:
                passed = pendulum.parse(str(decoded))
                await db.add_reminder(ctx.author.id, reason, passed, str(pendulum.now("Atlantic/Reykjavik")))  # utc + 0

                await ctx.simple_embed(f"Got it! I'll remind you in {passed.diff_for_humans(absolute=True)}.")
            else:
                await embeds.simple_embed("That doesn't seem like a valid date!", ctx)

    @remind.command(name="remove", aliases=["delete"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def remind_remove(self, ctx, *, reminderid):
        """Removes a currently active reminder by ID."""
        reminder = await db.find_reminder(int(reminderid))
        if not reminder:
            return await ctx.simple_embed("This reminder does not exist.")
        if int(reminder["user"]) != ctx.author.id:
            return await ctx.simple_embed("This reminder exists, but is not owned by you.")

        await db.negate_reminder(int(reminderid))
        await ctx.simple_embed("Reminder removed.")

    @remind.command(name="view", aliases=["id"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def remind_view(self, ctx, *, reminderid):
        """Shows details on a currently active reminder by ID."""
        reminder = await db.find_reminder(int(reminderid))
        if not reminder:
            return await ctx.simple_embed("This reminder does not exist.")
        if int(reminder["user"]) != ctx.author.id:
            return await ctx.simple_embed("This reminder exists, but is not owned by you.")

        embed = discord.Embed(title="Reminder information", color=16202876)
        if len(reminder["reason"]) > 1000:
            clipped = reminder["reason"][:1000] + "... (Content too large to display.)"
        else:
            clipped = reminder["reason"]

        expires_at = pendulum.parse(reminder["expiry"])
        set_at = pendulum.parse(reminder["issued"])
        rn = pendulum.now("Atlantic/Reykjavik")  # utc+0

        embed.add_field(name="Reminder text", value=clipped, inline=False)
        embed.add_field(name="Set at", value=humanize.naturaldate(set_at), inline=False)
        embed.add_field(name="Expires", value=humanize.naturaltime(expires_at - rn), inline=False)

        await ctx.send(embed=embed)

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
                user = self.bot.get_user(int(item["username"]))
                if user:
                    embed = discord.Embed(title=f"Reminder from {set_at.diff_for_humans()}", color=16202876)
                    embed.description = item["reason"]

                    try:
                        await user.send(embed=embed)
                    except discord.errors.Forbidden:
                        pass

                await db.negate_reminder(item["id"])

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):
        mentioned_afk_members = []
        context = await self.bot.get_context(message)

        for member in self.bot.afks:
            if member.user == message.author:
                result = await db.return_afk_message(message.author.id)
                readable = date.delta(
                    pendulum.now("Atlantic/Reykjavik"), member.time, justnow=timedelta(seconds=0))[0]

                self.bot.afks.remove(member)
                if context.command:
                    continue

                elapsed = f"\n(*Away for {readable}*)"
                if result is None:
                    await context.send(
                        f"Welcome back. I removed your afk.{elapsed}", delete_after=10)
                else:
                    await context.send(result + elapsed, delete_after=10)

            if member.user.mention in message.content and not message.author.bot:
                mentioned_afk_members.append(member)

        if mentioned_afk_members and not context.command:
            user_names = [member.user.name for member in mentioned_afk_members]
            if len(mentioned_afk_members) == 1:
                await message.channel.send(member.print(), delete_after=10)
            elif len(mentioned_afk_members) == 2:
                await message.channel.send(f"{user_names[0]} and {user_names[1]} are both AFK.")
            else:
                await message.channel.send(", ".join(user_names[:-1]) + f" and {user_names[-1]} are AFK.")


def setup(bot):
    """Adds the goddamn cog"""
    bot.add_cog(Cog(bot))
