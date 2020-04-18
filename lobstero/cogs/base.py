"""Docstring to appease linter.
This is mainly just help commands."""

import psutil
import collections

import discord

from discord.ext import commands, tasks
from github import Github
from lobstero.utils import strings
from lobstero.models import handlers
from lobstero import lobstero_config

status_position = collections.deque([0, 1, 2, 3])
lc = lobstero_config.LobsteroCredentials()
psutil.cpu_percent(interval=None, percpu=True)  # Returns a meaningless value on first call, ignore


class Cog(commands.Cog, name="Miscellaneous"):
    """The commands that don't really fit anywhere.
Most of these are more "meta" commands, and revolve around the bot itself.
Also features git-related commands."""

    def __init__(self, bot):
        self.bot = bot
        self.recent_commits = []

    @commands.command()
    async def search(self, ctx, *, text="aaaaaaaaaaaqdqdqfdqwfqwerfgeqrfgqwr3gfqerf"):
        """Searches for a command matching the supplied query.
If no query is given when using the command, it returns nothing."""

        results = []
        for x in self.bot.commands:
            if text.lower() in str(x.help).lower() or text.lower() in str(x.qualified_name).lower():
                try:
                    if await x.can_run(ctx):
                        results.append(x)
                except commands.CommandError:
                    pass

        if not results:
            embed = discord.Embed(
                title="Search results",
                description=(
                    "No results were found that matched your query. "
                    "Try different keywords, or see <help for more information."),
                color=16202876)

            return await ctx.send(embed=embed)
        else:
            command_string = strings.blockjoin([x.name for x in results])

        embed = discord.Embed(
            title="Search results",
            description=(
                "The following commands were found that matched your search:"
                f"\n\n{command_string}"),
            color=16202876)

        return await ctx.send(embed=embed)

    async def runnable(self, cogobj, ctx):
        """An asynchronous iterator for runnable commands."""

        for command in cogobj.walk_commands():
            try:
                await command.can_run(ctx)
                yield command
            except commands.CommandError:
                pass

    @commands.command(aliases=["invite"])
    async def info(self, ctx):
        """Contains an invite link to add the bot to your server, as well as other information about the bot."""

        embed = discord.Embed(
            color=16202876,
            description=(
                f"Lobstero is a badly programmed discord bot developed by Kaylynn#4444. "
                f"This instance of Lobstero is owned by {lc.config.owner_name}. "
                "Find the bot on GitHub at https://github.com/kaylynn234/LobsteroBOT"
                "\n\n**Recent updates**:\n"))

        appinfo = await self.bot.application_info()
        invite_url = f"https://discordapp.com/api/oauth2/authorize?client_id={appinfo.id}&scope=bot"

        embed.add_field(
            name="Lobstero's support server",
            value=f"[``Click here``]({lc.config.support_server_url})")

        embed.add_field(
            name="Invite Lobstero to your server",
            value=f"[``Click here``]({invite_url})")

        text = (
            f"If you're on mobile and can't use the links "
            f"below, use <{invite_url}> and <{lc.config.support_server_url}> instead.")

        embed.set_footer(text=f"Connected on {(len(self.bot.guilds))} servers.")
        await ctx.send(text, embed=embed)

    @commands.command()
    @commands.cooldown(1, 3600, commands.BucketType.user)
    @commands.guild_only()
    async def bugreport(self, ctx, problem, *, text):
        """Opens an issue on GitHub as a bug report. **THE TEXT YOU SUPPLY IS PUBLIC**.
Misuse of this command will result in a blacklist."""

        if self.manager:
            r = self.manager.get_repo(lc.config.github_repo)
            bug_report_label = r.get_label("bug")
            pending_review_label = r.get_label("pending review")
            r.create_issue(
                f"{str(ctx.author)}: {problem}", f"Submitted via discord:\n\n{text}",
                assignee="kaylynn234", labels=[bug_report_label, pending_review_label])

            return await ctx.send("Report submitted.")

        await ctx.send("Github is not configured on this instance!.")

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @commands.is_owner()
    @commands.guild_only()
    async def git(self, ctx):
        """A base command for repo interactions."""

        await ctx.send("Use a subcommand.")

    @git.command(name="lock")
    @commands.is_owner()
    @commands.guild_only()
    async def git_lock_issue(self, ctx, issue_n: int, *, reason):
        """Locks an issue on github by issue number and reason."""

        if self.manager:
            r = self.manager.get_repo(lc.config.github_repo)
            issue = r.get_issue(issue_n)
            issue.lock(reason)

            return await ctx.send("Issue closed.")

        await ctx.send("Github is not configured on this instance!.")

    @git.command(name="label")
    @commands.is_owner()
    @commands.guild_only()
    async def git_add_label(self, ctx, issue_n: int, *, label):
        """Adds a label to a github issue by issue name and label."""

        if self.manager:
            r = self.manager.get_repo(lc.config.github_repo)
            issue = r.get_issue(issue_n)
            current_labels = [x.name for x in issue.labels]
            issue.edit(labels=[label] + current_labels)

            return await ctx.send("Label added.")

        await ctx.send("Github is not configured on this instance!.")

    @git.command(name="unlabel")
    @commands.is_owner()
    @commands.guild_only()
    async def git_remove_label(self, ctx, issue_n: int, *, label):
        """Removes a label from a github issue by issue name and label."""

        if self.manager:
            r = self.manager.get_repo(lc.config.github_repo)
            issue = r.get_issue(issue_n)
            current_labels = [x.name for x in issue.labels]
            try:
                current_labels.remove(label)
            except ValueError:
                return await ctx.send("No label by this name for this issue.")
            issue.edit(labels=current_labels)

            return await ctx.send("Label removed.")

        await ctx.send("Github is not configured on this instance!.")

    @commands.command(aliases=["hwstats"])
    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.guild_only()
    @handlers.blueprints_or()
    async def hardwarestats(self, ctx):
        """Hardware information about Lobstero. Mostly useless."""

        core_count = psutil.cpu_count()
        thread_count = psutil.cpu_count(logical=False)
        packet_info = psutil.net_io_counters()
        running_processes = len(psutil.pids())

        core_info = "\n".join([
            f"Core {c_n + 1}: ``{c_p}``% usage"
            for c_n, c_p in enumerate(psutil.cpu_percent(interval=None, percpu=True))])

        embed = discord.Embed(
            title=f"System information for this machine",
            description=(
                f"This machine has {core_count} physical CPU core(s), and {thread_count} thread(s)."
                f"\n{core_info}\n\n{running_processes} processes are currently running.\n"
                f"⬆️ {packet_info.bytes_sent / 1048576:,.2f} "
                "megabytes of data have been sent since boot.\n"
                f"⬇️ {packet_info.bytes_recv / 1048576:,.2f} "
                "megabytes of data have been received since boot."),
            color=16202876)

        await ctx.send(embed=embed)


def setup(bot):
    """Help"""
    bot.add_cog(Cog(bot))
