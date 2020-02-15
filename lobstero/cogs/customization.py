import random
import asyncio
import sys
import json
import discord

from discord.ext.menus import MenuPages
from lobstero.utils import db, embeds, misc, text, strings
from lobstero.models import menus, handlers
from discord.ext import commands

root_directory = sys.path[0] + "/"
valid_bp_responses = [
    "has_any_role", "has_role", "has_permissions", "has_strict_permissions",
    "is_specific_user", "is_guild_owner"]

acceptable = [
    "respond_on_mention", "random_messages",
    "random_reactions", "welcome_messages",
    "moderation_confirmation", "indexed_reactions"]

bp_numbered = {i: x for i, x in enumerate(valid_bp_responses, 1)}


class Cog(commands.Cog, name="Settings and server customization"):
    """A module that provides commands for managing your server's Lobstero settings."""
    def __init__(self, bot):
        self.bot = bot

    async def handle_confirmation(self, ctx):
        try:
            msg = await self.bot.wait_for(
                'message', timeout=30.0,
                check=lambda message: message.author == ctx.author)
            return msg
        except asyncio.futures.TimeoutError:
            await ctx.send(embeds.bp_not_fast_enough)


    @commands.command(aliases=["valueset", "changesetting", "valset"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def settings(self, ctx, value=None, changeto=None):
        """<settings (setting) (value)

Allows or deny specific features of Lobstero on this server.
Use <settings to see editable settings and their uses.
Use ``<settings (setting) (value)`` to change a value.
Valid usage would be something along the lines of ``<settings respond_on_mention True``
        """
        if value and changeto:
            if value.lower() in acceptable and str(changeto).lower() in ["true", "false"]:
                newval = True if changeto.lower() == "true" else False
                db.edit_settings_value(ctx.guild.id, value.lower(), newval)
                await embeds.simple_embed("Value updated.", ctx)
            else:
                await embeds.simple_embed("That value is not valid!", ctx)
        else:
            await ctx.send(embed=embeds.settings_embed)

    @commands.group(invoke_without_command=True, ignore_extra=False, aliases=["welcomemessages", "wmessages"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def wm(self, ctx):
        """A base command for all welcome messages."""
        pass

    @wm.command(name="add", aliases=["create"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def wm_add(self, ctx, *, message=None):
        """<wm add (message)

Adds a welcome message to this server.
Messages are sent in the channel that is set using ``<channels set ``.
Example usage is ``<wm add this is a cool welcome message! hi %u!``

%u will be replaced with the username of the new user.
%+u will be replaced with the username and discriminator of the new user.
%@u will be replaced with a mention of the new user.

Emoji, mentions of specific users, specific channels, and specific roles will function normally.
        """
        if message is not None:
            db.edit_settings_value(ctx.guild.id, "welcome_messages", True)
            db.add_welcome_message(str(ctx.guild.id), message)
            await embeds.simple_embed("Welcome message added!", ctx.message.channel.id)
        else:
            await embeds.simple_embed(
                "Please provide the message that you wish to add as a welcome message.", ctx)

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @handlers.blueprints_or()
    async def channels(self, ctx):
        """<channels

Provides tools to set the channels that Lobstero uses to function.
Use ``<channels`` alone to display currently set values.
``<channels set`` is probably the subcommand you want to use.
"""
        current = db.settings_value_for_guild(ctx.guild.id)
        wm, pa, ml = "None", "None", "None"
        if "wmessagechannel" in current:
            if str(current["wmessagechannel"]) != "None":
                wm = str(self.bot.get_channel(int(current["wmessagechannel"])).name)
        if "archivechannel" in current:
            if str(current["archivechannel"]) != "None":
                pa = str(self.bot.get_channel(int(current["archivechannel"])).name)
        if "moderationlogs" in current:
            if str(current["moderationlogs"]) != "None":
                loaded = json.loads(current["moderationlogs"])
                [print(x) for x in loaded]
                listed = [str(self.bot.get_channel(int(x)).name) for x in loaded]
                ml = ", ".join(listed)

        embed = discord.Embed(title="Showing currently set channels", color=16202876)
        embed.description = f"welcome_messages: ``{wm}``\narchives: ``{pa}``\nmoderation: ``{ml}``"

        await ctx.send(embed=embed)

    @channels.command(name="set")
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def channels_set(self, ctx, name=None):
        """<channels set (value)

Allows you set the channels that are used for various Lobstero features.
Use this command (with the value you want to change as an argument) in any channel to set the channel for that value.
For example, using the below would set the pin archive channel to the channel it was used in:

    <channels set archives

Multiple values exist, and each does something different.
Usable values:

    ``welcome_messages`` - This is the channel where welcome messages will be sent.
    ``archives`` - This is where pinned messages are sent when <archive is used.
    ``moderation`` - This is where moderation logging goes. Use this in multiple channels to toggle each one as a logging channel.
        """
        if not name:
            await embeds.simple_embed("No value was chosen to set!", ctx)

        if name.lower() == "welcome_messages":
            db.edit_settings_value(ctx.guild.id, "wmessagechannel", ctx.channel.id)
            await embeds.simple_embed("Welcome message channel set successfully!", ctx)
        if name.lower() == "archives":
            db.edit_settings_value(ctx.guild.id, "archivechannel", ctx.channel.id)
            await embeds.simple_embed("Pin archive channel set successfully!", ctx)
        if name.lower() == "moderation":
            current = db.settings_value_for_guild(ctx.guild.id)
            if not current:
                db.edit_settings_value(
                    ctx.guild.id, "moderationlogs", json.dumps([ctx.channel.id]))
                await embeds.simple_embed("Moderation logging channel set successfully!", ctx)

            elif current and "moderationlogs" not in current:
                db.edit_settings_value(
                    ctx.guild.id, "moderationlogs", json.dumps([ctx.channel.id]))
                await embeds.simple_embed("Moderation logging channel set successfully!", ctx)

            elif current and "moderationlogs" in current:
                try:
                    loaded = json.loads(current["moderationlogs"])
                except KeyError:
                    loaded = []

                if len(loaded) == 1:
                    if int(loaded[0]) == ctx.channel.id:
                        db.edit_settings_value(ctx.guild.id, "moderationlogs", None)
                        await embeds.simple_embed(
                            "Moderation logging channel successfully removed!", ctx)
                    else:
                        loaded.append(ctx.channel.id)
                        db.edit_settings_value(
                            ctx.guild.id, "moderationlogs", json.dumps(loaded))
                        await embeds.simple_embed(
                            "Moderation logging channel added successfully!", ctx)
                else:
                    if ctx.channel.id in [int(x) for x in loaded]:
                        loaded.remove(ctx.channel.id)
                        await embeds.simple_embed(
                            "Moderation logging channel successfully removed!", ctx)
                    else:
                        loaded.append(ctx.channel.id)
                        await embeds.simple_embed(
                            "Moderation logging channel added successfully!", ctx)

                    db.edit_settings_value(ctx.guild.id, "moderationlogs", json.dumps(loaded))

    @wm.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def wm_del(self, ctx, *, message):
        """Removes a welcome message from this server by index. """
        res = db.remove_welcome_message(str(ctx.guild.id), message)
        if res:
            await embeds.simple_embed("Matching welcome messages deleted.", ctx)
        else:
            await embeds.simple_embed("Could not find a matching welcome message!", ctx)

    @wm.command(name="list")
    @commands.guild_only()
    @handlers.blueprints_or()
    async def wm_list(self, ctx):
        """Lists all welcome messages on this server. """
        data = db.all_welcome_messages_for_guild(str(ctx.guild.id))
        messages = [x["message"] for x in data]
        source = menus.ListEmbedMenu(messages, "Welcome messages for this server", 10, True)
        menu = MenuPages(source, timeout=30, clear_reactions_after=True)

        await menu.start(ctx)

    @commands.command(aliases=["selfrole", "sr"])
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @handlers.blueprints_or()
    async def iam(self, ctx, *, wanted=None):
        """Add or remove self-assignable roles from yourself."""

        role = None
        for x in ctx.guild.roles:
            if role is None and wanted is not None:
                if wanted.isnumeric():
                    if x.id == int(wanted):
                        role = x
                if x.name.lower() == wanted.lower():
                    role = x

        if role is not None:
            roles = db.assignables_check(ctx.guild.id)
            roles = [int(x) for x in roles]
            if role.id in roles:
                await ctx.author.add_roles(role)
                await embeds.simple_embed("Role added successfully!", ctx)
            else:
                await embeds.simple_embed("This role is not self-assignable!", ctx)
        else:
            await embeds.simple_embed(
                "Please specify a self-assignable role when using this command!", ctx)

    @commands.command(aliases=["iamn", "notselfrole", "nsr"])
    @commands.bot_has_permissions(manage_roles=True)
    @commands.guild_only()
    @handlers.blueprints_or()
    async def iamnot(self, ctx, *, wanted=None):
        """Add or remove self-assignable roles from yourself."""

        role = None
        for x in ctx.guild.roles:
            if role is None and wanted is not None:
                if wanted.isnumeric():
                    if x.id == int(wanted):
                        role = x
                if x.name.lower() == wanted.lower():
                    role = x

        if role is not None:
            roles = db.assignables_check(ctx.guild.id)
            roles = [int(x) for x in roles]
            if role.id in roles:
                await ctx.author.remove_roles(role)
                await embeds.simple_embed("Role removed successfully!", ctx)
            else:
                await embeds.simple_embed("This role is not self-assignable!", ctx)
        else:
            await embeds.simple_embed(
                "Please specify a self-assignable role when using this command!", ctx)

    @commands.command(aliases=["addselfrole", "asar"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_roles=True))
    async def addassignable(self, ctx, *, wanted):
        """Adds a self-assignable role on this server."""

        role = None
        for x in ctx.guild.roles:
            if role is None and wanted is not None:
                if wanted.isnumeric():
                    if x.id == int(wanted):
                        role = x
                if x.name.lower() == wanted.lower():
                    role = x

        if role is not None:
            db.assignables_add(ctx.guild.id, role.id)
            await embeds.simple_embed("Successfully made this role self-assignable!", ctx)
        else:
            await embeds.simple_embed((
                "Please specify a role to make self-assignable "
                "when using this command!"), ctx)

    @commands.command(aliases=["removeselfrole", "rsar"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_roles=True))
    async def removeassignable(self, ctx, *, wanted: discord.Role = None):
        """Removes a self-assignable role from this server."""

        role = None
        for x in ctx.guild.roles:
            if role is None and wanted is not None:
                if x.id == int(wanted.id):
                    role = x
                if x.name.lower() == wanted.name.lower():
                    role = x

        if role is not None:
            db.assignables_remove(ctx.guild.id, role.id)
            await embeds.simple_embed("Successfully removed this self-assignable role!", ctx)
        else:
            await embeds.simple_embed(
                "Please specify a self-assignable role to remove when using this command!", ctx)

    @commands.command(aliases=["listselfrole", "lsar"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def listassignables(self, ctx, page: int = 1):
        """Lists all self-assignable roles on this server."""
        roles = db.assignables_check(ctx.guild.id)
        data = [str(ctx.guild.get_role(int(x))) for x in roles]
        source = menus.ListEmbedMenu(data, "Self-assignable roles for this server", 10, True)
        menu = MenuPages(source, timeout=30, clear_reactions_after=True)

        await menu.start(ctx)

    @commands.command(aliases=["setprefix", "prefix"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(administrator=True))
    async def changeprefix(self, ctx, *, new):
        db.add_prefix(ctx.guild.id, new)
        await embeds.simple_embed("Prefix updated!", ctx)

    @commands.Cog.listener()
    async def on_member_join(self, member):

        table = db.give_table()
        if member.guild.id not in table:
            th = misc.populate({})
        else:
            th = misc.populate(table[member.guild.id])

        if th["welcome_messages"] is True:
            try:
                th["wmessagechannel"]
            except KeyError:
                return

            welcomemessagelist = db.all_welcome_messages_for_guild(str(member.guild.id))
            welcmessage = random.choice([x["message"] for x in welcomemessagelist])

            welcmessage = str(welcmessage).replace(r"%u", member.name)
            welcmessage = str(welcmessage).replace(r"%+u", str(member))
            welcmessage = str(welcmessage).replace(r"%@u", member.mention)
            channel = self.bot.get_channel(th["wmessagechannel"])

            await channel.send(welcmessage)

    @commands.group(invoke_without_command=True, ignore_extra=False, enabled=False)
    @commands.guild_only()
    @commands.is_owner()
    async def blueprints(self, ctx):
        """<blueprints

The base command for all blueprints-related commands.
Blueprints are used to configure who can use what command.
No parameters are required. Displays a list of all blueprints if a subcommand is not used.
        """
        dbresults = sorted(db.blueprints_for_guild(ctx.guild.id), key=lambda x: x["command"])
        results = [
            f"Blueprint ID {x['id']}: **``{x['criteria_type']}``** for **``<{x['command']}``**"
            for x in dbresults]

        desc = (
            "Displaying all blueprints on this server - use the reactions below "
            "to navigate, or use a subcommand to see more detailed information. "
            "This menu will time out in 60 seconds. ")
        pages = menus.ListEmbedMenuClean(results, "Blueprints", 10, True, desc)
        m = MenuPages(source=pages, clear_reactions_after=True)
        await m.start(ctx)

    @blueprints.command(name="id", enabled=False)
    async def blueprints_id(self, ctx, id_=None):
        """<blueprints id

Displays specific details about a blueprint based on blueprint ID.
        """
        if not id_:
            return await embeds.simple_embed(text.bp_id_invalid, ctx)
        elif not id_.isnumeric():
            return await embeds.simple_embed(text.bp_not_number, ctx)
        res = db.blueprint_by_id(id_)
        if not res:
            return await embeds.simple_embed(text.bp_none_matching, ctx)
        if str(res["guildid"]) != str(ctx.guild.id):
            return await embeds.simple_embed(text.bp_on_other_guild, ctx)

        valstr = "succeed" if res["criteria_requires"] else "fail"
        typestr = f"The ``{res['criteria_type']}`` check must {valstr} for this command to run."
        embed = discord.Embed(color=16202876, title=f"Blueprint #{str(id_)}")
        embed.add_field(name="Command", value=f"<{res['command']}", inline=False)
        embed.add_field(name="Blueprint requirement", value=typestr, inline=False)
        embed.add_field(name="Internal blueprint value", value=res["criteria_value"], inline=False)

        await ctx.send(embed=embed)

    @blueprints.command(name="remove", aliases=["delete"], enabled=False)
    @commands.has_permissions(manage_messages=True)
    async def blueprints_remove(self, ctx, id_=None):
        """<blueprints remove (id)

Removes a blueprint by ID.
        """
        if not id_:
            return await embeds.simple_embed(text.bp_id_invalid, ctx)
        elif not id_.isnumeric():
            return await embeds.simple_embed(text.bp_not_number, ctx)
        res = db.blueprint_by_id(id_)
        if not res:
            return await embeds.simple_embed(text.bp_none_matching, ctx)
        if str(res["guildid"]) != str(ctx.guild.id):
            return await embeds.simple_embed(text.bp_on_other_guild, ctx)

        await embeds.simple_embed("Blueprint removed.", ctx)
        db.clear_blueprint(str(ctx.guild.id), id_)

    @blueprints.command(name="make", aliases=["create", "add"], enabled=False)
    @commands.has_permissions(manage_messages=True)
    async def blueprints_add(self, ctx, *, command=None):
        """<blueprints add (command)

Walks you through adding a blueprint to a command."""
        command = self.bot.get_command(command)
        if not command:
            return await embeds.simple_embed("That doesn't seem like a valid command.", ctx)

        current_blueprints = db.blueprints_for(str(ctx.guild.id), command.qualified_name)
        if current_blueprints and len(current_blueprints) >= 10:
            return await embeds.simple_embed("There's a maximum of 10 blueprints per command.", ctx)

        embed = discord.Embed(color=16202876, title=f"Blueprints")
        embed.description = text.bp_what_type

        # get the type of blueprint we want to add
        m = menus.BlueprintTypeMenu()
        await m.start(ctx, wait=True)
        if not m.selected_b:
            await ctx.send(embed=embeds.bp_not_fast_enough)

        # edit embed for trigger cond. choice
        embed = discord.Embed(color=16202876, title=f"Blueprints")
        embed.description = getattr(text, f"bp_{bp_numbered[m.selected_b]}")
        await m.message.edit(embed=embed)

        # start the confirmation menu
        m2 = menus.BlueprintConfirmationMenu()
        m2.message = m.message
        await m2.start(ctx, wait=True)
        if m2.choice is None:
            await ctx.send(embed=embeds.bp_not_fast_enough)

        embed = discord.Embed(color=16202876, title=f"Blueprints")
        value = None
        if m.selected_b not in [1, 6]:  # 1 & 6 do not need confirmation
            if m.selected_b == 2:
                embed.description = text.bp_role_prompt
            elif m.selected_b in [3, 4]:
                example_perms = discord.Permissions()
                attrs = [x for x in dir(example_perms) if x[0] != "_"][:2]
                permstr = strings.blockjoin(attrs)
                embed.description = text.bp_perm_prompt % permstr
            else:
                embed.description = text.bp_member_prompt

            # now we get what the blueprint val is
            await m.message.edit(embed=embed)
            res = await self.handle_confirmation(ctx)
            if not res:
                return

            # conversion logic
            if m.selected_b == 2:
                c = commands.RoleConverter()
                try:
                    prelim = await c.convert(ctx, res.content)
                    value = str(prelim.id)
                except commands.CommandError as e:
                    raise e
                    return await ctx.send(embed=embeds.bp_wrong_value)

            elif m.selected_b in [3, 4]:
                if res.content.lower() in attrs:
                    value = res.content.lower()
                else:
                    return await ctx.send(embed=embeds.bp_wrong_value)
            else:
                c = commands.MemberConverter()
                try:
                    prelim = await c.convert(ctx, res.content)
                    value = str(prelim.id)
                except commands.CommandError as e:
                    raise e
                    return await ctx.send(embed=embeds.bp_wrong_value)

        # add the blueprint to the database
        db.add_blueprint(
            str(ctx.guild.id), command.qualified_name, bp_numbered[m.selected_b], value, m2.choice)

        # tell the user we didn't die in the process
        embed = discord.Embed(color=16202876, title=f"Blueprints")
        embed.description = "Blueprint successfully added!"
        await m.message.edit(embed=embed)


def setup(bot):
    bot.add_cog(Cog(bot))
