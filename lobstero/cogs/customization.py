import random
import asyncio
import sys
import json
import inspect

import discord
import validators

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


class Cog(commands.Cog, name="Server customization and settings"):
    """A module that provides commands for managing Lobstero and your server.
Welcome messages, command blueprints, custom reactions and assignable roles can configured in this module.
This module is also used for the configuration of general server settings."""
    def __init__(self, bot):
        self.bot = bot

    async def handle_confirmation(self, ctx):
        try:
            msg = await self.bot.wait_for(
                'message', timeout=30.0,
                check=lambda message: message.author == ctx.author)
            return msg
        except asyncio.futures.TimeoutError:
            await ctx.send(embed=embeds.bp_not_fast_enough)

    @commands.command(aliases=["valueset", "changesetting", "valset"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def settings(self, ctx, value=None, changeto=None):
        """Allows or deny specific features of Lobstero on this server.
Use <settings to see editable settings and their uses.
Use ``<settings (setting) (value)`` to change a value.
Valid usage would be something along the lines of ``<settings respond_on_mention True``"""

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
        """A base command for all welcome messages.
If no subcommand is used, displays a list of all welcome messages on this server."""

        data = db.all_welcome_messages_for_guild(str(ctx.guild.id))
        messages = [x["message"] for x in data]
        source = menus.ListEmbedMenu(messages, "Welcome messages for this server", 10, True)
        menu = MenuPages(source, timeout=30, clear_reactions_after=True)

        await menu.start(ctx)

    @wm.command(name="add", aliases=["create"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def wm_add(self, ctx, *, message=None):
        """Adds a welcome message to this server.
Messages are sent in the channel that is set using ``<channels set ``.
Example usage is ``<wm add this is a cool welcome message! hi %u!``

%u will be replaced with the username of the new user.
%+u will be replaced with the username and discriminator of the new user.
%@u will be replaced with a mention of the new user.

Emoji, mentions of specific users, specific channels, and specific roles will function normally."""

        if message is not None:
            db.edit_settings_value(ctx.guild.id, "welcome_messages", True)
            db.add_welcome_message(str(ctx.guild.id), message)
            await ctx.simple_embed("Welcome message added!")
        else:
            await ctx.simple_embed("Please provide the message that you wish to add as a welcome message.")

    @wm.command(name="delete", aliases=["remove"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def wm_del(self, ctx, *, message):
        """Removes a welcome message from this server by content. """

        res = db.remove_welcome_message(str(ctx.guild.id), message)
        if res:
            await ctx.simple_embed("Matching welcome messages deleted.")
        else:
            await ctx.simple_embed("Could not find a matching welcome message!")

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @handlers.blueprints_or()
    async def channels(self, ctx):
        """A base command for managing the channels that Lobstero uses to function.
Use this command without a subcommand to display currently set values.
``<channels set`` is probably the subcommand you want to use."""

        channels = db.find_settings_channels(ctx.guild.id)
        mapped_channels = map(lambda k: (self.bot.get_channel(k["channel"]), k["type"]), channels)
        name_types = {c[0].name if c[0] else "(Inaccessible/ deleted)": c[1] for c in mapped_channels}
        sorted_channels = sorted(list(name_types.items()), key=lambda t: (t[1], t[0]))
        flattened_channels = [f"` {i[1]} channel`: {i[0]}" for i in sorted_channels]

        pages = menus.ListEmbedMenu(flattened_channels, "Showing currently set channels", footer=True)
        menu = MenuPages(pages, clear_reactions_after=True)

        await menu.start(ctx)

    @channels.command(name="set")
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def channels_set(self, ctx, channeltype, *, channel):
        """Allows you set the channels that are used for various Lobstero features.
The following channel types exist:

``welcoming`` - This is where welcome messages will be sent.
``archives`` - This is where pinned messages are sent when <archive is used. **You can only have one of these.**
``moderation`` - This is where moderation logging goes.
``conversation`` - This is where Lobstero will respond automatically if a message is sent.

For example, the following would add #general as a conversation channel:

``<channels set conversation general``.
When specifying a channel, the channel mention, channel ID or channel name can be used."""

        valid = ["welcoming", "archives", "conversation", "moderation"]
        if channeltype.lower() not in valid:
            return await ctx.simple_embed("That's not a valid channel type!")

        print("ye")
        c = commands.TextChannelConverter()
        try:
            found_channel = await c.convert(ctx, channel)
        except commands.BadArgument:
            return await ctx.simple_embed("That doesn't seem like a valid channel.")

        print("ye")
        if found_channel.guild.id != ctx.guild.id:
            return await ctx.simple_embed("That channel isn't on this server.")

        print("ye")
        res = db.add_settings_channel(ctx.guild.id, found_channel.id, channeltype.lower())
        print("poog0-wkgw")
        if res:
            await ctx.simple_embed("Channel added!")
        else:
            await ctx.simple_embed("You've reached the maximum channels of that type!")
        print("ye2")

    @channels.command(name="remove", aliases=["delete"])
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def channels_remove(self, ctx, channeltype, *, channel=None):
        """Removes a channel from the list of configured channels.
The following channel types exist:

``welcoming`` - This is where welcome messages will be sent.
``archives`` - This is where pinned messages are sent when <archive is used. **You can only have one of these.**
``moderation`` - This is where moderation logging goes.
``conversation`` - This is where Lobstero will respond automatically if a message is sent.

For example, the following would remove #general as a conversation channel:

``<channels remove conversation general``.
When specifying a channel, the channel mention, channel ID or channel name can be used."""

        valid = ["welcoming", "archives", "conversation", "moderation"]
        if channeltype.lower() not in valid:
            return await ctx.simple_embed("That's not a valid channel type!")

        c = commands.TextChannelConverter()
        try:
            found_channel = await c.convert(ctx, channel)
        except commands.BadArgument:
            return await ctx.simple_embed("That doesn't seem like a valid channel.")

        if found_channel.guild.id != ctx.guild.id:
            return await ctx.simple_embed("That channel isn't on this server.")

        db.remove_settings_channel(ctx.guild.id, channel.id, channeltype.lower())
        await ctx.simple_embed("Channel removed.")

    @channels.command(name="wipe")
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def channels_wipe(self, ctx, channeltype):
        """Wipes all of a channel type from the list of configured channels.
The following channel types exist:

``welcoming`` - This is where welcome messages will be sent.
``archives`` - This is where pinned messages are sent when <archive is used. **You can only have one of these.**
``moderation`` - This is where moderation logging goes.
``conversation`` - This is where Lobstero will respond automatically if a message is sent.
"""

        valid = ["welcoming", "archives", "conversation", "moderation"]
        if channeltype.lower() not in valid:
            return await ctx.simple_embed("That's not a valid channel type!")

        db.wipe_settings_channel(ctx.guild.id, channeltype.lower())
        await ctx.simple_embed("Channel removed.")

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

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @commands.guild_only()
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

    @blueprints.command(name="id")
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

    @blueprints.command(name="remove", aliases=["delete", "destroy"])
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

    @blueprints.command(name="wipe", aliases=["scrub"])
    @commands.has_permissions(manage_messages=True)
    async def blueprints_wipe(self, ctx, command=None):
        """<blueprints wipe (command)

Deletes all blueprints for a command.
        """
        if command is None:
            return await embeds.simple_embed("That doesn't seem like a valid command.", ctx)
        command = self.bot.get_command(command)
        if not command:
            return await embeds.simple_embed("That doesn't seem like a valid command.", ctx)

        current_blueprints = db.blueprints_for(str(ctx.guild.id), command.qualified_name)
        if not current_blueprints:
            return await embeds.simple_embed("There are no blueprints for this command.", ctx)

        await embeds.simple_embed(f"{len(current_blueprints)} blueprint(s) removed.", ctx)
        db.clear_blueprints_for(str(ctx.guild.id), command.qualified_name)

    @blueprints.command(name="make", aliases=["create", "add"])
    @commands.has_permissions(manage_messages=True)
    async def blueprints_add(self, ctx, *, command=None):
        """<blueprints add (command)

Walks you through adding a blueprint to a command."""
        if command is None:
            return await embeds.simple_embed("That doesn't seem like a valid command.", ctx)

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
                attrs = [
                    x for x in dir(example_perms) if x[0] != "_" and
                    not inspect.ismethod(getattr(example_perms, x)) and
                    not inspect.isfunction(getattr(example_perms, x))][2:]

                permstr = strings.bblockjoin(attrs)
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
                except commands.CommandError:
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
                except commands.CommandError:
                    return await ctx.send(embed=embeds.bp_wrong_value)

        # add the blueprint to the database
        db.add_blueprint(str(ctx.guild.id), command.qualified_name, bp_numbered[m.selected_b], value, m2.choice)

        # tell the user we didn't die in the process
        embed = discord.Embed(color=16202876, title="Blueprints")
        embed.description = "Blueprint successfully added!"
        await m.message.edit(embed=embed)

    @commands.group(invoke_without_command=True, ignore_extra=False, aliases=["customreacts", "reactions"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def cr(self, ctx):
        """A base command for managing custom reactions.
If no subcommand is used, lists all custom reactions on this server."""
        reactions = db.return_server_reacts_list(str(ctx.guild.id))

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

    async def process_add(self, ctx, trigger, response, base):
        try:
            msg = await self.bot.wait_for('message', timeout=10, check=lambda message: message.author == ctx.author)
        except asyncio.futures.TimeoutError:
            return await base.edit(embed=embeds.cr_timeout)

        if msg.content.lower() not in ["full", "partial"]:
            return await base.edit(embed=embeds.cr_formatted_incorrectly)
        else:
            db.remove_reaction(str(ctx.guild.id), trigger)
            rtype = "full" if "full" in msg.content.lower() else "partial"
            db.add_reaction(str(ctx.guild.id), trigger, response, rtype)
            embed = discord.Embed(title="Reaction added!", color=16202876)
            return await base.edit(embed=embed)

    @cr.command(name="add")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def cr_add(self, ctx, trigger, *, response):
        """Add a custom reaction."""
        if not db.find_matching_response(str(ctx.guild.id), trigger):
            base = await ctx.send(embed=embeds.cr_triggertype)
            await self.process_add(ctx, trigger, response, base)
        else:
            base = await ctx.send(embed=embeds.cr_confirmation)
            try:
                msg = await self.bot.wait_for('message', timeout=10, check=lambda message: message.author == ctx.author)

            except asyncio.futures.TimeoutError:
                return await base.edit(embed=embeds.cr_timeout)

            if not msg.content.lower() in ["overwrite", "add"]:
                return await base.edit(embed=embeds.cr_formatted_incorrectly)

            if msg.content.lower() == "overwrite":
                await base.edit(embed=embeds.cr_triggertype)
                await self.process_add(ctx, trigger, response, base)
            else:
                db.add_reaction(str(ctx.guild.id), trigger, response, )
                embed = discord.Embed(title="Reaction added!", color=16202876)
                return await base.edit(embed=embed)

    @cr.command(name="del", aliases=["delete", "remove"])
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def cr_del(self, ctx, *, trigger):
        """Deletes a custom reaction by trigger."""
        if db.find_matching_response(str(ctx.guild.id), trigger):
            db.remove_reaction(str(ctx.guild.id), trigger)
            await ctx.simple_embed("Reaction removed.")
        else:
            await ctx.simple_embed("There isn't a custom reaction with that trigger!")

    @cr.command(name="deny")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def cr_deny(self, ctx):
        """Deny the current channel access to custom reactions."""
        if not db.is_denied(str(ctx.guild.id), str(ctx.channel.id)):
            db.add_new_deny_channel(ctx.guild.id, str(ctx.channel.id))
            await ctx.simple_embed("Custom reactions are now denied in this channel.")
        else:
            await ctx.simple_embed("Custom reactions are already denied in this channel!")

    @cr.command(name="allow")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def cr_allow(self, ctx):
        """Allow the current channel access to custom reactions."""
        if db.is_denied(str(ctx.guild.id), str(ctx.channel.id)):
            db.remove_deny_channel(ctx.guild.id, str(ctx.channel.id))
            await ctx.simple_embed("Custom reactions are now allowed in this channel.")

        else:
            await ctx.simple_embed("Custom reactions are already allowed in this channel!")

    @cr.command(name="info")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def cr_info(self, ctx, *, trigger):
        """View info on a custom reaction with the provided trigger."""
        reactions = db.return_server_reacts_list(str(ctx.guild.id))
        if not reactions:
            return await ctx.send(embed=embeds.cr_none_present)

        if not db.find_matching_response(str(ctx.guild.id), trigger):
            return await ctx.send(embed=embeds.cr_no_trigger)

        reaction = db.raw_find_matching_response(str(ctx.guild.id), trigger)
        responses = json.loads(reaction["response"])
        mtype = reaction["type"]
        desc = f"**Trigger type**: {mtype}\n**Total responses**: {str(len(responses))}"
        embed = discord.Embed(title="Reaction info", description=desc, color=16202876)

        for index, x in enumerate(responses):
            embed.add_field(name=f"Response {str(index + 1)}", value=strings.clip(x), inline=False)

        return await ctx.send(embed=embed)

    @cr.command(name="search")
    @commands.guild_only()
    @handlers.blueprints_or(commands.has_permissions(manage_messages=True))
    async def cr_search(self, ctx, *, query=None):
        """Search for a custom reaction based on a query."""
        fetched = []
        reactions = db.return_server_reacts_list(str(ctx.guild.id))
        if not reactions:
            return await ctx.send(embed=embeds.cr_none_present)

        for x in reactions:
            response = [y.lower() for y in json.loads(x["response"])]
            if query.lower() in response or query.lower() in x["trigger"]:
                fetched.append(x["trigger"])

        if not fetched:
            desc = "No reactions matched your search query."
        else:
            desc = f"The following reactions matched your search query:\n\n{strings.bblockjoin(fetched)}"

        embed = discord.Embed(title="Search results", description=desc, color=16202876)
        return await ctx.send(embed=embed)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):
        """Called every message. Handles reactions."""
        if message.author.bot is False and message.guild:
            if db.is_denied(str(message.guild.id), str(message.channel.id)):
                return

            if message.content is None or message.content == "":
                return

            reacts = db.return_server_reacts_list(message.guild.id)
            for reaction in reacts:
                is_partial = (
                    reaction["type"] == "partial" and
                    reaction["trigger"].lower() in message.content.lower())

                is_full = message.content.lower() == reaction["trigger"].lower()
                if is_full or is_partial:
                    response = random.choice(json.loads(reaction["response"]))

                    if response.startswith(r"%r "):
                        for x in response.split(r"%r ", )[-1].split(" "):
                            return await message.add_reaction(x)

                    is_image = any([
                        response.lower().endswith(".png"), response.lower().endswith(".jpg"),
                        response.lower().endswith(".jpeg"), response.lower().endswith(".webp"),
                        response.lower().endswith(".bmp"), response.lower().endswith(".apng"),
                        response.lower().endswith(".gif")])

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

    @commands.Cog.listener()
    async def on_member_join(self, member):

        table = db.give_table()
        if member.guild.id not in table:
            th = misc.populate({})
        else:
            th = misc.populate(table[member.guild.id])

        if th["welcome_messages"] is True:
            wchannels = db.find_settings_channels(member.guild.id, "welcoming")
            wchannels = filter(None, map(lambda k: self.bot.get_channel(k["channel"]), wchannels))
            wchannels = filter(lambda c: c.guild.id == member.guild.id)

            welcomemessagelist = db.all_welcome_messages_for_guild(str(member.guild.id))
            welcmessage = random.choice([x["message"] for x in welcomemessagelist])
            welcmessage = welcmessage.replace(r"%u", member.name).replace(r"%+u", str(member))
            welcmessage = welcmessage.replace(r"%@u", member.mention)

            for channel in wchannels:
                try:
                    await channel.send(welcmessage)
                except discord.errors.Forbidden:
                    pass


def setup(bot):
    bot.add_cog(Cog(bot))
