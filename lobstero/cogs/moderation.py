import re
import sys
import calendar
import collections
import asyncio
import validators
import discord
import demoji
import dateparser

import aiohttp
import pendulum
from lobstero.utils import db, embeds, text, misc, moderation
from lobstero.models import handlers, menus
from discord.ext import commands, tasks
from discord.ext.menus import MenuPages
from urllib.parse import urlsplit

root_directory = sys.path[0] + "/"
records_aliases = ["logs", "modlogs", "infractions", "record"]
m_aliases = ["moderation", "moderate", "mod"]


class Cog(commands.Cog, name="Moderation"):
    """For those whomst are powerful."""
    def __init__(self, bot):
        self.bot = bot
        self.check_for_updates.start()
        self.task = self.bot.loop.create_task(self.aiohttp_init())

    async def aiohttp_init(self):
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.task.cancel()
        self.session.close()
        self.check_for_updates.cancel()

    def r_username(self, id_):
        u = self.bot.get_user(int(id_))
        return str(u) if u else str(id_)

    async def imgdownload(self, file_url):
        file_name = urlsplit(file_url)[2].split('/')[-1]
        file_ext = file_name.split(".", 1)[1]

        async with self.session.get(file_url) as resp:
            with open(f"{root_directory}data/downloaded/{file_name}", 'wb+') as f:
                f.write(await resp.read())

        return [f"{root_directory}data/downloaded/{file_name}", file_ext]

    @commands.group(invoke_without_command=True, ignore_extra=False, aliases=records_aliases)
    @commands.guild_only()
    @commands.is_owner()
    async def records(self, ctx):
        """<records

Displays a list of all infractions on this server.
Multiple subcommands exist for more fine-grained viewing.
No parameters are required.
        """
        results = db.find_all_infractions(ctx.guild.id)
        data = [list(item.items()) for item in list(results)]
        desc = (
            "Displaying all recorded infractions on this server - use the reactions below "
            "to navigate, or use a subcommand to see more detailed information. "
            "This menu will time out in 60 seconds. ")
        pages = menus.Infractionmenu(data, "Infractions", 10, self.bot, desc)
        m = MenuPages(source=pages, clear_reactions_after=True)
        await m.start(ctx)

    @records.command(name="id")
    async def records_id(self, ctx, id_=None):
        """<records id

Displays specific details about an infraction based on case ID.
        """
        if not id_:
            return await embeds.simple_embed(text.mod_id_invalid, ctx)
        elif not id_.isnumeric():
            return await embeds.simple_embed(text.mod_not_number, ctx)
        res = db.find_specific_infraction(id_)
        if not res:
            return await embeds.simple_embed(text.mod_none_matching, ctx)
        if str(res["guild"]) != str(ctx.guild.id):
            return await embeds.simple_embed(text.mod_on_other_guild, ctx)

        a = pendulum.parse(res["date_raw"])
        embed = discord.Embed(color=16202876, title=f"Infraction #{str(id_)}")
        embed.description = (
            f"This operation was performed on {res['date']}; {res['date_raw']}; {a.humanize()}.")
        embed.add_field(name="Operation", value=res["operation"], inline=False)
        embed.add_field(name="Offender", value=self.r_username(res["user"]), inline=False)
        embed.add_field(name="Performed by", value=self.r_username(res["staff"]), inline=False)
        embed.add_field(name="Reason", value=res["reason"], inline=False)

        await ctx.send(embed=embed)

    @records.command(name="member", aliases=["user"])
    async def records_member(self, ctx, member=None):
        """<records member

Displays all infractions committed by a specific member.
        """
        user = None
        try:
            user = await commands.MemberConverter().convert(ctx, member)
        except commands.BadArgument:
            pass

        if not user:
            return await embeds.simple_embed(text.mod_member_invalid, ctx)
        results = db.find_all_member_infractions(ctx.guild.id, user.id)
        if not results:
            return await embeds.simple_embed(text.mod_none_assoc, ctx)

        data = [list(item.items()) for item in list(results)]
        desc = (
            "Displaying all recorded infractions for this member - use the reactions below "
            "to navigate. This menu will time out in 60 seconds. ")

        pages = menus.Infractionmenu(data, f"Infractions for {str(user)}", 60, self.bot, desc)
        m = MenuPages(source=pages, clear_reactions_after=True)
        await m.start(ctx)

    @records.command(name="summary", aliases=["viewall"])
    async def records_summary(self, ctx, member=None):
        """<records summary (member)

Shows a count-based summary of the infractions a member has committed.
Striked infractions are not counted. All parameters are required.
        """
        user = None
        try:
            user = await commands.MemberConverter().convert(ctx, member)
        except commands.BadArgument:
            pass

        if not user:
            return await embeds.simple_embed(text.mod_member_invalid, ctx.channel.id)
        results = db.find_all_member_infractions(ctx.guild.id, user.id)
        if not results:
            return await embeds.simple_embed(text.mod_none_assoc, ctx.channel.id)

        data = [list(item.items()) for item in list(results)]
        counts = collections.Counter([
            dict(item)["operation"]
            for item in data
            if dict(item)["redacted"] != "True"])

        embed = discord.Embed(color=16202876, title=f"Infraction summary for {str(user)}")
        for key, value in text.moderation_mapping.items():
            embed.add_field(
                name=value, value=f"{counts[key]} of this operation type recorded.", inline=False)

        await ctx.send(embed=embed)

    @records.command(name="strike")
    @commands.has_permissions(manage_messages=True)
    async def records_strike(self, ctx, id_=None):
        """<records strike (id)

Strikes a record. This causes it to not be counted in member summaries, and will make it appear crossed-out when navigating infractions.
        """
        if not id_:
            return await embeds.simple_embed(text.mod_id_invalid, ctx.channel.id)
        elif not id_.isnumeric():
            return await embeds.simple_embed(text.mod_not_number, ctx.channel.id)
        res = db.find_specific_infraction(id_)
        if not res:
            return await embeds.simple_embed(text.mod_none_matching, ctx.channel.id)
        if str(res["guild"]) != str(ctx.guild.id):
            return await embeds.simple_embed(text.mod_on_other_guild, ctx.channel.id)

        if res["redacted"] == "True":
            await embeds.simple_embed("Record unstriked.", ctx.channel.id)
            db.strike_infraction(res["operation"], res["guild"], res["user"], id_, "False")
        else:
            await embeds.simple_embed("Record striked.", ctx.channel.id)
            db.strike_infraction(res["operation"], res["guild"], res["user"], id_, "True")

    @records.command(name="close")
    @commands.has_permissions(manage_messages=True)
    async def records_close(self, ctx, id_=None):
        """<records close (id)

Close a record. This is not the same as striking a record!
Closing a record stops it from expiring.
        """
        if not id_:
            return await embeds.simple_embed(text.mod_id_invalid, ctx.channel.id)
        elif not id_.isnumeric():
            return await embeds.simple_embed(text.mod_not_number, ctx.channel.id)
        res = db.find_specific_infraction(id_)
        if not res:
            return await embeds.simple_embed(text.mod_none_matching, ctx.channel.id)
        if str(res["guild"]) != str(ctx.guild.id):
            return await embeds.simple_embed(text.mod_on_other_guild, ctx.channel.id)

        if res["expiry"] != "False":
            await embeds.simple_embed("Record closed.", ctx.channel.id)
            db.close_infraction(id_)
        else:
            await embeds.simple_embed("Record is already closed.", ctx.channel.id)

    @records.command(name="filter")
    async def records_filter(self, ctx, *args):
        """<records filter (pairs)

Shows infraction records for this server, but offers much more fine-grained control over what is displayed.
For example, the following will only show infractions that were performed by Kaylynn and affected Delta:

    <records filter staff Kaylynn#4444 member Delta

Available filters can be seen below:

    Member: A member username, nickname, mention or ID. Only infractions that affect this member will be shown.
    Staff: A member username, nickname, mention or ID for a staff member. Only punishments performed by this member will be shown.
    Operation: Text representing the punishment type you wish to filter. Only infractions of this punishment type will be shown.

The specific pairs that you pass are optional, but the command requires at least one pair to be present.
"""
        chunked = [x for x in misc.chunks(args, 2) if len(x) > 1]
        print(chunked)

        if not args:
            embed = discord.Embed(color=16202876, title="Available filters")
            embed.add_field(name="member", value=(
                "A member username, nickname, mention or ID. "
                "Only infractions that affect this member will be shown."))

            embed.add_field(name="staff", value=(
                "A member username, nickname, mention or ID for a staff member. "
                "Only punishments performed by this member will be shown."))

            embed.add_field(name="operation", value=(
                "Text representing the punishment type you wish to filter. "
                "Only infractions of this punishment type will be shown."))

            return await ctx.send(embed=embed)
        if not chunked:
            return await embeds.simple_embed((
                "Make sure to provide pairs of arguments when filtering records. "
                "Use <records filter to see a list of valid arguments."), ctx)

        results = db.find_all_infractions(ctx.guild.id)
        filtered = await self.fits_record_criteria(ctx, chunked, results)
        data = [list(item.items()) for item in list(filtered)]
        desc = (
            "Displaying all recorded infractions on this server - use the reactions below to "
            "navigate, or use a subcommand to see more detailed information. "
            "This menu will time out in 60 seconds. ")

        pages = menus.Infractionmenu(data, "Infractions", 60, self.bot, desc)
        m = MenuPages(source=pages, clear_reactions_after=True)
        await m.start(ctx)

    async def fits_record_criteria(self, ctx, pairs, records):
        valid = []
        for item in pairs:
            if item[0].lower() == "member":
                member = None
                try:
                    member = await commands.MemberConverter().convert(ctx, item[1])
                except commands.BadArgument:
                    pass
            if item[0].lower() == "staff":
                staff = None
                try:
                    staff = await commands.MemberConverter().convert(ctx, item[1])
                except commands.BadArgument:
                    pass
            if item[0].lower() == "operation":
                operation = None
                if str(item[1]).lower() in list(text.moderation_mapping.keys()):
                    operation = str(item[1]).lower()

        for rec in records:
            res = []
            for item in pairs:
                if item[0].lower() == "member":
                    res.append(str(member.id) == str(rec["user"]))
                if item[0].lower() == "staff":
                    res.append(str(staff.id) == str(rec["staff"]))
                if item[0].lower() == "operation":
                    res.append(operation == rec["operation"])

            if False not in res and True in res:
                valid.append(rec)

        return valid

    @commands.group(invoke_without_command=True, ignore_extra=False, aliases=m_aliases)
    @commands.guild_only()
    async def m(self, ctx):
        """A base command for all moderation actions."""
        embed = discord.Embed(color=16202876, title="Moderation")
        embed.description = text.mod_how_to
        await ctx.send(embed=embed)

    @m.command(name="warn")
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True)
    async def m_warn(self, ctx, *, arg: handlers.GreedyMention):
        """<m warn (users) (reason)

Warns a user (or users) and logs it to the channel (or channels) specified using ``<channels set moderation``.
        """
        r = await self.handle_confirmation_and_logging(
            ctx, arg, text.action_warn,
            "User warned",
            "Users warned")
        if r[0]:
            for user in r[1]:
                db.log_infraction("warn", ctx.guild.id, user.id, ctx.author.id, r[2])

    @m.command(name="mute")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        manage_roles=True)
    async def m_mute(self, ctx, *, arg: handlers.GreedyMention):
        """<m mute (users) (reason)

Mutes a user (or users) and logs it to the channel (or channels) specified using ``<channels set moderation``. A mute role is created and set up if it does not already exist.
        """
        r = await self.handle_confirmation_logging_and_expiry(
            ctx, arg, text.action_mute,
            "User muted",
            "Users muted")
        if r[0]:
            for user in r[1]:
                db.log_infraction("mute", ctx.guild.id, user.id, ctx.author.id, r[2], str(r[3]))
                await moderation.handle_mute(ctx, user)

    @m.command(name="deafen")
    @commands.guild_only()
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        manage_roles=True)
    async def m_deafen(self, ctx, *, arg: handlers.GreedyMention):
        """<m deafen (users) (reason)

Deafens a user (or users) and logs it to the channel (or channels) specified using ``<channels set moderation``. A deafen role is created and set up if it does not already exist.
        """
        r = await self.handle_confirmation_logging_and_expiry(
            ctx, arg, text.action_deafen, "User deafened", "Users deafened")
        if r[0]:
            for user in r[1]:
                db.log_infraction("deafen", ctx.guild.id, user.id, ctx.author.id, r[2], str(r[3]))
                await moderation.handle_deafen(ctx, user)

    @m.command(name="kick")
    @commands.guild_only()
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        kick_members=True)
    async def m_kick(self, ctx, *, arg: handlers.GreedyMention):
        """<m kick (users) (reason)

Kicks a user (or users) and logs it to the channel (or channels) specified using ``<channels set moderation``.
        """
        r = await self.handle_confirmation_and_logging(
            ctx, arg, text.action_kick, "User kicked", "Users kicked")
        if r[0]:
            for user in r[1]:
                db.log_infraction("kick", ctx.guild.id, user.id, ctx.author.id, r[2], str(r[3]))
                await moderation.handle_kick(ctx, user)

    @m.command(name="ban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        ban_members=True)
    async def m_ban(self, ctx, *, arg: handlers.GreedyMention):
        """<m ban (users) (reason)

Bans a user (or users) and logs it to the channel (or channels) specified using ``<channels set moderation``. No messages are deleted.
        """
        r = await self.handle_confirmation_logging_and_expiry(
            ctx, arg, text.action_ban, "User banned", "Users banned")
        if r[0]:
            for user in r[1]:
                db.log_infraction("ban", ctx.guild.id, user.id, ctx.author.id, r[2], str(r[3]))
                await moderation.handle_ban(ctx, user)

    @m.command(name="softban")
    @commands.guild_only()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(
        read_message_history=True,
        send_messages=True,
        embed_links=True,
        attach_files=True,
        ban_members=True)
    async def m_softban(self, ctx, *, arg: handlers.GreedyMention):
        """<m softban

Softbans a user (or users) and logs it to the channel (or channels) specified using ``<channels set moderation``. 7 days of messages are deleted and the affected members are immediately unbanned.
        """
        r = await self.handle_confirmation_and_logging(
            ctx, arg, text.action_softban, "User softbanned", "Users softbanned")
        if r[0]:
            for user in r[1]:
                db.log_infraction(
                    "softban", ctx.guild.id, user.id, ctx.author.id, r[2], str(r[3]))
                await moderation.handle_softban(ctx, user)

    async def handle_confirmation_and_logging(self, ctx, arg, description="No information provided.", later="Moderation action taken", later_plural="Moderation actions taken"):
        users, reason = arg
        if not users:
            return False
        table = db.give_table()
        m = None

        if int(ctx.guild.id) not in list(table.keys()):
            th = misc.populate({})
        else:
            th = misc.populate(table[ctx.guild.id])

        if th["moderation_confirmation"]:
            precautionary = discord.Embed(color=16202876, title="Operation summary")
            warned = ", ".join([member.mention for member in users])
            precautionary.description = description
            precautionary.add_field(name="Affected members", value=warned, inline=False)
            precautionary.add_field(name="Reason", value=reason, inline=False)
            precautionary.set_footer(
                text="You can disable this message by using the \"settings\" command.")

            m = menus.ConfirmationMenu(precautionary)
            await m.start(ctx, wait=True)

            if not m.clicked:
                return (False, users, reason, False)

        completed = discord.Embed(color=16202876, title=later_plural if len(users) > 1 else later)
        warned = ", ".join([member.mention for member in users])
        completed.description = f"Punishment submitted."
        completed.add_field(name="Affected members", value=warned, inline=False)
        completed.add_field(name="Reason", value=reason, inline=False)
        if db.is_logging_enabled(ctx.guild.id)[0] is False:
            completed.set_footer(
                text="You can configure a logging channel using the <channels command")

        if m:
            await m.message.edit(embed=completed)
        else:
            await ctx.send(embed=completed)

        logging = db.is_logging_enabled(ctx.guild.id)
        if logging[0]:
            for channel_id in logging[1]:
                logging = discord.Embed(
                    color=16202876, title=later_plural if len(users) > 1 else later)
                warned = ", ".join([member.mention for member in users])
                logging.description = f"Punishment submitted."
                logging.add_field(name="Affected members", value=warned, inline=False)
                logging.add_field(name="Reason", value=reason, inline=False)

                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(embed=logging)

        return (True, users, reason, False)

    async def handle_confirmation_logging_and_expiry(self, ctx, arg, description="No information provided.", later="Moderation action taken", later_plural="Moderation actions taken", op=None):
        users, reason = arg
        if not users:
            return False
        table = db.give_table()
        m = None

        if int(ctx.guild.id) not in list(table.keys()):
            th = misc.populate({})
        else:
            th = misc.populate(table[ctx.guild.id])

        if th["moderation_confirmation"]:
            precautionary = discord.Embed(color=16202876, title="Operation summary")
            warned = ", ".join([member.mention for member in users])
            precautionary.description = description
            precautionary.add_field(name="Affected members", value=warned, inline=False)
            precautionary.add_field(name="Reason", value=reason, inline=False)
            precautionary.set_footer(
                text="You can disable this message by using the \"settings\" command.")

            m = menus.ConfirmationMenu(precautionary)
            await m.start(ctx, wait=True)

            if not m.clicked:
                return (False, users, reason, False)

        expiry = discord.Embed(color=16202876, title="Set an expiry")
        expiry.description = text.mod_can_expire
        if m:
            await m.message.edit(embed=expiry)
        else:
            await ctx.send(embed=expiry)

        future, parsed = None, None
        try:
            future = await self.bot.wait_for(
                'message', timeout=10.0,
                check=lambda message: message.author == ctx.author)

        except asyncio.futures.TimeoutError:
            expiry_r = "Timed out."

        if future:
            if "in" not in future.content:
                future.content = f"in {future.content}"
            parsed = dateparser.parse(future.content, settings={'TIMEZONE': 'UTC'})
        if parsed:
            expires_at = pendulum.parse(parsed)
            rn = expires_at

            readable = rn.strftime((
                f"{calendar.day_name[rn.weekday()]} {misc.ordinal(rn.day)}"
                f"{calendar.month_name[rn.month]} %Y, %H:%M UTC"))

            await embeds.simple_embed(f"Got it. This punishment will expire on {readable}.", ctx)
        else:
            expires_at = False
            expiry_r = "Couldn't make sense of the provided date."
            await embeds.simple_embed(f"Got it. This punishment won't expire - {expiry_r}", ctx)

        completed = discord.Embed(color=16202876, title=later_plural if len(users) > 1 else later)
        warned = ", ".join([member.mention for member in users])
        completed.description = f"Punishment submitted."
        completed.add_field(name="Affected members", value=warned, inline=False)
        completed.add_field(name="Reason", value=reason, inline=False)
        if db.is_logging_enabled(ctx.guild.id)[0] is False:
            completed.set_footer(text="You can configure a logging channel using the <channels command")

        if m:
            await m.message.edit(embed=completed)
        else:
            await ctx.send(embed=completed)

        logging = db.is_logging_enabled(ctx.guild.id)
        if logging[0]:
            for channel_id in logging[1]:
                logging = discord.Embed(
                    color=16202876, title=later_plural if len(users) > 1 else later)
                warned = ", ".join([member.mention for member in users])
                logging.description = f"Punishment submitted."
                logging.add_field(name="Affected members", value=warned, inline=False)
                logging.add_field(name="Reason", value=reason, inline=False)

                channel = self.bot.get_channel(int(channel_id))
                if channel:
                    await channel.send(embed=logging)

        return (True, users, reason, expires_at)

    @tasks.loop(seconds=10)
    async def check_for_updates(self):
        res = await db.return_all_expiring_infractions()
        if res:
            for item in res:
                expires_at = pendulum.parse(item["date_raw"])
                rn = pendulum.now("Atlantic/Reykjavik")
                if rn > expires_at:
                    if item["operation"] == "mute":
                        try:
                            await moderation.handle_unmute(self.bot, item["guild"], item["user"])
                        except Exception as e:
                            print(e)
                    if item["operation"] == "deafen":
                        try:
                            await moderation.handle_undeafen(self.bot, item["guild"], item["user"])
                        except Exception as e:
                            print(e)
                    if item["operation"] == "ban":
                        try:
                            await moderation.handle_unban(self.bot, item["guild"], item["user"])
                        except Exception as e:
                            print(e)

                    db.close_infraction(item["id"])

    async def fits_criteria(self, message, pairs):
        res = []

        for item in pairs:

            if item[0].lower() == "has":
                if item[1].lower() == "embed":
                    res.append(len(message.embeds) > 0)
                elif item[1].lower() == "image":
                    images = [x for x in message.attachments if x.width]
                    res.append(len(images) > 0)
                elif item[1].lower() == "file":
                    files = [x for x in message.attachments if not x.width]
                    res.append(len(files) > 0)
                else:
                    raise commands.errors.BadArgument

            elif item[0].lower() == "from":
                res.append(message.author.id == item[1].id)
            elif item[0].lower() == "mentions":
                res.append(item[1].mentioned_in(message))

            elif item[0].lower() == "contains":
                if item[1].lower() == "mention":
                    res.append(len(message.mentions) > 0)
                elif item[1].lower() == "emoji":
                    emoji = re.findall(
                        r"<(?P<animated>a)?:(?P<name>[0-9a-zA-Z_]{2,32}):(?P<id>[0-9]{15,21})>",
                        message.content)

                    standard_emoji = list(demoji.findall(message.content).keys())
                    res.append(len(emoji + standard_emoji) > 0)
                elif item[1].lower() == "link":
                    urls = [validators.url(x) for x in message.content.split(" ")]
                    res.append(True in urls)
                else:
                    raise commands.errors.BadArgument

            elif item[0].lower() == "formatting":
                if item[1].lower() == "spoiler":
                    spoiler = re.findall(r"\|\|(.*?)\|\|", message.content)
                    res.append(len(spoiler) > 0)
                elif item[1].lower() == "bold":
                    bold = re.findall(r"\*\*(.*?)\*\*", message.content)
                    res.append(len(bold) > 0)
                elif item[1].lower() == "italic":
                    italic = re.findall(r"\*\*(.*?)\*\*", message.content)
                    res.append(len(italic) > 0)
                elif item[1].lower() == "underline":
                    underline = re.findall(r"__(.*?)__", message.content)
                    res.append(len(underline) > 0)
                elif item[1].lower() == "strikethrough":
                    strikethrough = re.findall(r"~~(.*?)~~", message.content)
                    res.append(len(strikethrough) > 0)
                elif item[1].lower() == "quote":
                    res.append("> " in message.content)
                else:
                    raise commands.errors.BadArgument

        return res

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def prune(self, ctx, *args):
        """<prune (pairs)

Prunes messages from the current channel. Use with no arguments to delete the 15 most recent messages.
Alternatively, pass pairs of arguments to delete messages matching certain criteria:

    <prune count 25 has image

The above will delete the most recent 25 messages in this channel that have images attached to them.
Valid criteria can be seen below:

    Count = Number. This is the amount of messages to delete.
    Has = Text. This is should be either "embed", "image" or "file". Only messages with one of these will be deleted.
    From = Text. This is a user ID, username, user mention or user nickname. Only messages sent by this member will be deleted.
    Mentions = Text. This is a user ID, username, user mention or user nickname. Only messages that mention this user will be deleted.
    Contains = Text. This should be either "mention", "emoji" or "link". Only messages that contain one of these will be deleted..
    Formatting = Text. This should be either "spoiler", "bold", "italic", "underline", "strikethrough" or "quote". Only messages that contain one of these will be deleted.

Multiple of the same criteria can be chained together for greater control over deletion:

    <prune count 25 has image contains emoji contains link

The above will delete the most recent 25 messages in this channel with images, emoji and links.
        """

        if len(args) == 1:
            if args[0].isnumeric:
                args = ["count", str(args[0])]

        chunked = [x for x in misc.chunks(args, 2) if len(x) > 1]

        type_mapping = {
            "count": int,  # number to delete
            "has": str,  # embed, image, file
            "from": commands.MemberConverter,
            "mentions": commands.MemberConverter,
            "contains": str,  # mention, emoji, link
            "formatting": str  # spoiler, bold, italic, underline, quote
        }

        filtered = [x for x in chunked if x[0].lower() in type_mapping]

        for index, pair in enumerate(filtered):
            new_type = type_mapping[pair[0].lower()]
            if new_type != commands.MemberConverter:
                filtered[index] = [pair[0], new_type(pair[1])]
            else:
                filtered[index] = [pair[0], await new_type().convert(ctx, pair[1])]

            if pair[0].lower() == "count":
                max_m = filtered[index][1]

        is_count = [True for x in filtered if x[0].lower() == "count"]
        if True not in is_count:
            max_m = 25

        messages = await ctx.channel.history(limit=275).flatten()

        filtered_messages = []

        for message in messages:
            if False not in await self.fits_criteria(message, filtered):
                filtered_messages.append(message)

            if len(filtered_messages) == abs(max_m) or len(filtered_messages) == 100:
                break
        try:
            await ctx.channel.delete_messages(filtered_messages)
            await embeds.simple_embed(
                "Messages deleted." if filtered_messages
                else "No matching messages were found!", ctx)
        except discord.errors.Forbidden:
            await embeds.simple_embed("Cannot delete messages more than 14 days old!", ctx)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 300, commands.BucketType.channel)
    @commands.has_permissions(manage_messages=True)
    async def archive(self, ctx):
        """<archive

Archives pins for the current channel. No parameters are required.
        """

        table = db.give_table()
        if ctx.guild.id not in table:
            return await embeds.simple_embed("There is no archive channel set on this server!", ctx)
        if "archivechannel" not in table[ctx.guild.id]:
            return await embeds.simple_embed("There is no archive channel set on this server!", ctx)

        channel = table[ctx.guild.id]["archivechannel"]

        embed_mesg = discord.Embed(
            title="<a:loading:521107731940376576> Archiving pins...", color=16202876)
        mesg = await ctx.send(embed=embed_mesg)

        pinchn = discord.utils.get(ctx.guild.channels, id=int(channel))
        for x in await ctx.message.channel.pins():

            embed = discord.Embed(color=16202876, title=f"#{x.channel.name}")
            if x.content:
                embed.description = x.content
            embed.set_author(name=x.author, url=x.jump_url, icon_url=x.author.avatar_url)
            await pinchn.send(embed=embed)

            for y in x.attachments:
                atturl = y.url
                fname = await self.imgdownload(str(atturl))
                await pinchn.send(file=discord.File(fname[0]))

            for embed in x.embeds:
                await pinchn.send(embed=embed)

            await x.unpin()

        embed2 = discord.Embed(title="✅ Pins archived!", color=16202876)
        await mesg.edit(embed=embed2)


def setup(bot):
    bot.add_cog(Cog(bot))
