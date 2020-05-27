"""All the moderation."""

import discord
from discord import utils
from ..models import menus
from . import db, misc


class Holder():
    """Fuck you."""


async def confirm(self, ctx, users, description, reason):
    """Confirms moderation decisions."""
    table = db.give_table()

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
        return (m.clicked, m.message)

    return (True, None)


async def log(self, ctx, reason, users, later, later_plural, msg):
    """Logs stuff."""
    completed = discord.Embed(color=16202876, title=later_plural if len(users) > 1 else later)
    warned = ", ".join([member.mention for member in users])
    completed.description = f"Punishment submitted."
    completed.add_field(name="Affected members", value=warned, inline=False)
    completed.add_field(name="Reason", value=reason, inline=False)
    if db.is_logging_enabled(ctx.guild.id) is False:
        completed.set_footer(text="You can configure a logging channel using the <channels command")

    if msg:
        await msg.edit(embed=completed)
    else:
        await ctx.send(embed=completed)

    mchannels = db.find_settings_channels(ctx.guild.id, "moderation")
    mchannels = filter(None, map(lambda k: self.bot.get_channel(k["channel"]), mchannels))

    logging = discord.Embed(color=16202876, title=later_plural if len(users) > 1 else later)
    warned = ", ".join([member.mention for member in users])
    logging.description = f"Punishment submitted."
    logging.add_field(name="Affected members", value=warned, inline=False)
    logging.add_field(name="Reason", value=reason, inline=False)

    for channel in mchannels:
        try:
            await channel.send(embed=logging)
        except discord.errors.Forbidden:
            pass


async def return_mute_role(ctx):
    """Returns the server's mute role.
    Created automatically if there isn't one."""
    if not isinstance(ctx, discord.ext.commands.Context):
        n_ctx = Holder()
        setattr(n_ctx, "guild", ctx)
        ctx = n_ctx

    r_n = db.settings_value_for_guild(ctx.guild.id)
    if r_n:
        if "mute_role_id" in list(r_n.keys()):
            mute_role_name = r_n["mute_role"]
        else:
            mute_role_name = "Muted"
    else:
        mute_role_name = "Muted"

    mute_role = utils.get(ctx.guild.roles, name=mute_role_name)
    if not mute_role:
        new_text = discord.PermissionOverwrite(send_messages=False)
        new_voice = discord.PermissionOverwrite(speak=False)

        mute_role = await ctx.guild.create_role(
            name=mute_role_name, reason="A mute role did not already exist.")
        top_role = ctx.guild.me.roles[-1]
        await mute_role.edit(position=top_role.position - 1)

        for channel in ctx.guild.channels:
            permissions = channel.permissions_for(ctx.guild.me)
            current = channel.overwrites

            if permissions.manage_channels or permissions.administrator:
                current[mute_role] = new_text if str(channel.type) == "text" else new_voice
                await channel.edit(overwrites=current)

    return mute_role


async def return_deafen_role(ctx):
    """Returns the server's deafen role.
    Created automatically if there isn't one."""
    if not isinstance(ctx, discord.ext.commands.Context):
        n_ctx = Holder()
        setattr(n_ctx, "guild", ctx)
        ctx = n_ctx

    r_n = db.settings_value_for_guild(ctx.guild.id)
    if r_n:
        if "deafen_role_id" in list(r_n.keys()):
            deafen_role_name = r_n["deafen_role"]
        else:
            deafen_role_name = "Deafened"
    else:
        deafen_role_name = "Deafened"

    deafen_role = utils.get(ctx.guild.roles, name=deafen_role_name)
    if not deafen_role:
        new_text = discord.PermissionOverwrite(read_messages=False)
        new_voice = discord.PermissionOverwrite(connect=False)

        deafen_role = await ctx.guild.create_role(
            name=deafen_role_name, reason="A deafen role did not already exist.")
        top_role = ctx.guild.me.roles[-1]
        await deafen_role.edit(position=top_role.position - 1)

        for channel in ctx.guild.channels:
            permissions = channel.permissions_for(ctx.guild.me)
            current = channel.overwrites

            if permissions.manage_channels or permissions.administrator:
                current[deafen_role] = new_text if str(channel.type) == "text" else new_voice
                await channel.edit(overwrites=current)

    return deafen_role


async def handle_mute(ctx, user):
    """Easy abstract way of handling mutes."""
    mute_role = await return_mute_role(ctx)
    await user.add_roles(mute_role)


async def handle_deafen(ctx, user):
    """Easy abstract way of handling deafens."""
    deafen_role = await return_deafen_role(ctx)
    await user.add_roles(deafen_role)


async def handle_kick(ctx, user):
    """Easy abstract way of handling kicks."""
    failed = False
    try:
        await user.kick(reason="Moderation action. Use <records to view.")
    except discord.errors.Forbidden:
        failed = True
    if failed:
        embed = discord.Embed(title="Punishment not completed!", color=16202876)
        embed.description = (
            f"{str(user)} could not be kicked. "
            "They have a higher role than the bot.")
        return await ctx.send(embed=embed)


async def handle_ban(ctx, user):
    """Easy abstract way of handling bans."""
    failed = False
    try:
        await user.ban(reason="Moderation action. Use <records to view.")
    except discord.errors.Forbidden:
        failed = True
    if failed:
        embed = discord.Embed(title="Punishment not completed!", color=16202876)
        embed.description = (
            f"{str(user)} could not be banned. "
            "They have a higher role than the bot.")
        return await ctx.send(embed=embed)


async def handle_softban(ctx, user):
    """Easy abstract way of handling less agro bans."""
    failed = False
    try:
        await user.ban(reason="Moderation action. Use <records to view.", delete_message_days=7)
        await user.unban()
    except discord.errors.Forbidden:
        failed = True
    if failed:
        embed = discord.Embed(title="Punishment not completed!", color=16202876)
        embed.description = (
            f"{str(user)} could not be softbanned. "
            "They have a higher role than the bot.")
        return await ctx.send(embed=embed)


async def handle_unmute(bot, guildid, memberid):
    """Easy abstract way of... You get the point."""
    guild = bot.get_guild(int(guildid))
    if not guild:
        return

    user = guild.get_member(int(memberid))
    mute_role = await return_mute_role(guild)
    await user.remove_roles(mute_role)


async def handle_undeafen(bot, guildid, memberid):
    """I'm only doing this because my linter wants me to."""
    guild = bot.get_guild(int(guildid))
    if not guild:
        return

    user = guild.get_member(int(memberid))
    deafen_role = await return_deafen_role(guild)
    await user.remove_roles(deafen_role)


async def handle_unban(bot, guildid, memberid):
    """I am incredibly depressed."""
    guild = bot.get_guild(int(guildid))
    if not guild:
        return

    user = bot.fetch_member(int(memberid))
    await guild.unban(user)
