import sys
import random
import aiohttp
import discord
import asyncio

from html import unescape
from discord.ext.menus import MenuPages
from discord.ext import commands
from lobstero.utils import embeds, text, db
from lobstero.models import menus, handlers

root_directory = sys.path[0] + "/"


class Cog(commands.Cog, name="Economy & Games"):
    """Ever wanted to earn and gamble away insignificant pieces of cheese? Now's your chance!."""

    def __init__(self, bot):
        self.bot = bot
        self.task = self.bot.loop.create_task(self.aiohttp_init())

    async def aiohttp_init(self):
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.task.cancel()
        self.session.close()

    async def handle_confirmation(self, ctx, sent):
        try:
            msg = await self.bot.wait_for(
                'message', timeout=10.0,
                check=lambda message: message.author == ctx.author)
            return msg
        except asyncio.futures.TimeoutError:
            await sent.edit(embed=embeds.eco_not_fast_enough)

    @commands.command(aliases=["$", "money", "check", "bal"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def balance(self, ctx):
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.author

        bal = await db.aio.economy_check(user.id)
        if bal == 0:
            await embeds.simple_embed("Looks like this person doesn't have any cheese. ", ctx)
        else:
            embed = discord.Embed(title=" ", color=16202876)
            embed.add_field(
                name=f"User {user}'s balance.", value=f"{bal} <a:cheese:533544087484366848>")
            embed.set_thumbnail(url=(
                "https://arnweb.blob.core.windows.net/cache/1/b/6/3/d/7"
                "/1b63d7cb7717896aa0fe806c17dba9a57476b2ce.jpg"))

            await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @commands.guild_only()
    @handlers.blueprints_or()
    async def guess(self, ctx):
        """<guess

Test your luck and see if you can guess a random card for some cheese.
No parameters are required.
To see the costs and outcomes of playing, use <guess prices.
This command took a fair chunk of inspiration from crimsoBOT. Thanks crimsoBOT.
        """
        chs = "<a:cheese:533544087484366848>"

        embed = discord.Embed(title="Guess the card!", color=16202876, description=text.guess_what)
        sentembed = await ctx.send(embed=embed)

        msg = await self.handle_confirmation(ctx, sentembed)
        if not msg:
            return

        if msg.content == "5":
            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description="Well, thanks for the interest. See you next time!")
            await sentembed.edit(embed=newembed)

        if msg.content == "1":
            await sentembed.edit(embed=discord.Embed(
                title="Guess the card!", color=16202876,
                description=(
                    "What suit will the card be? It can be either ``hearts``, "
                    "``diamonds``, ``spades`` or ``clubs``. You have 10 seconds to answer. Go!")))

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            cardlist = (
                ["hearts" for _ in range(13)] +
                ["clubs" for _ in range(13)] +
                ["spades" for _ in range(13)] +
                ["diamonds" for _ in range(13)])

            random.shuffle(cardlist)
            item = random.randint(0, 51)

            if cardlist[item] == msg2.content.lower():
                res = "Congratulations! You're correct!"
                await db.aio.economy_manipulate(ctx.author.id, 20)
            else:
                res = "Your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_1[cardlist[item]])

            await sentembed.edit(embed=newembed)

        if msg.content == "2":
            await sentembed.edit(embed=discord.Embed(
                title="Guess the card!", color=16202876,
                description=(
                    "What type will the card be? It can be either a ``king``, "
                    "``queen``, ``jack``, ``ace`` or a ``number``. You have 10 seconds to answer. ")
                ))

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            cardlist = (
                ["king" for _ in range(4)] +
                ["queen" for _ in range(4)] +
                ["jack" for _ in range(4)] +
                ["ace" for _ in range(4)] +
                ["number" for _ in range(36)])

            random.shuffle(cardlist)
            item = random.randint(0, 51)

            if cardlist[item] == msg2.content.lower():
                res = "Congratulations! You're correct!"
                await db.aio.economy_manipulate(ctx.author.id, 20)
            else:
                res = "Your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_2[cardlist[item]])

            await sentembed.edit(embed=newembed)

        if msg.content == "3":
            if not await db.aio.economy_check(ctx.author.id) >= 20:
                await sentembed.edit(embed=embeds.eco_broke)
                return

            await sentembed.edit(embed=discord.Embed(
                title="Guess the card!", color=16202876,
                description=(
                    "What number will be on the card? It can be "
                    "either a number from ``2``, ``3``, ``4``, etc (up to 10), or ``none``. "
                    "You have 10 seconds to answer.")))

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            await db.aio.economy_manipulate(ctx.author.id, -20)

            cardlist = []
            for _ in range(20):
                cardlist.append("none")
            for _ in range(4):
                for i in range(2, 10):
                    cardlist.append(str(i))

            random.shuffle(cardlist)
            item = random.randint(0, 51)

            if cardlist[item] == msg2.content.lower():
                res = "Congratulations! You're correct!"
                await db.aio.economy_manipulate(ctx.author.id, 100)
            else:
                res = "Your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_3)

            await sentembed.edit(embed=newembed)

        if msg.content == "4":
            if not await db.aio.economy_check(ctx.author.id) >= 50:
                await sentembed.edit(embed=embeds.eco_broke)
                return

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            await db.aio.economy_manipulate(ctx.author.id, -50)
            cardlist = []

            for letter in ["H", "D", "C", "S"]:
                for i in range(2, 10):
                    cardlist.append(f"{i}{letter}")
                cardlist.append(f"K{letter}")
                cardlist.append(f"Q{letter}")
                cardlist.append(f"J{letter}")
                cardlist.append(f"A{letter}")

            random.shuffle(cardlist)
            item = random.randint(0, 51)

            if cardlist[item].lower() == msg2.content.lower():
                res = "Congratulations! You're correct!"
                await db.aio.economy_manipulate(ctx.author.id, 5000)
            else:
                res = "Aw shucks, your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_4)

            await sentembed.edit(embed=newembed)

    @guess.command(name="prices")
    @handlers.blueprints_or()
    async def guess_prices(self, ctx):
        chs = "<a:cheese:533544087484366848>"
        embed = discord.Embed(title="Card guessing prices", color=16202876)
        embed.add_field(
            name="Guess the card's suit",
            value=f"**Cost to play**: 0 {chs} **Payout**: 20 {chs}")
        embed.add_field(
            name="Guess the card's type",
            value=f"**Cost to play**: 0 {chs} **Payout**: 20 {chs}")
        embed.add_field(
            name="Guess the number on the card",
            value=f"**Cost to play**: 20 {chs}. **Payout**: 100 {chs}")
        embed.add_field(
            name="Guess the exact card",
            value=f"**Cost to play**: 50 {chs} **Payout**: 1234 {chs}")

        return await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def bigbrain(self, ctx):
        """<bigbrain

Engage in a fun game of Big Brain Trivia™!
This command has no arguments.
        """
        url = "https://opentdb.com/api.php?amount=1&type=boolean"
        async with self.session.get(url) as resp:
            data = await resp.json()

        data["results"][0]["question"] = unescape(data["results"][0]["question"])
        embed = discord.Embed(title="Big Brain Trivia™!", color=16202876)
        correct = data["results"][0]["correct_answer"]
        dif = data["results"][0]["difficulty"].capitalize()

        embed.add_field(
            name="Category:", value=data["results"][0]["category"], inline=True)
        embed.add_field(
            name="Difficulty:", value=dif, inline=True)
        embed.add_field(
            name="Question:", value=data["results"][0]["question"], inline=False)
        embed.set_footer(text="True or False?")

        if dif == "Easy":
            timeg, payout = 6, 5
        if dif == "Medium":
            timeg, payout = 10, 10
        if dif == "Hard":
            timeg, payout = 14, 20

        embed.add_field(name="Time to answer:", value=f"{timeg} seconds.", inline=False)
        await ctx.send(embed=embed)

        try:
            msg = await self.bot.wait_for(
                'message', check=lambda message: message.author == ctx.author, timeout=timeg)
        except asyncio.futures.TimeoutError:
            return await embeds.simple_embed(
                f"You didn't answer in time! The correct answer was {correct}.", ctx)

        if msg.content.lower() == correct.lower():
            await db.aio.economy_manipulate(ctx.message.author.id, payout)
            await embeds.simple_embed(
                f"Your answer is correct! You earned {payout} cheese for winning.", ctx)
        else:
            await embeds.simple_embed(
                f"Your answer is sadly incorrect! The correct answer was {correct}", ctx)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def flip(self, ctx):
        """<fip

Flip a coin and test your luck. No arguments are required."""
        coinlist = (["heads" for _ in range(500)] + ["tails" for _ in range(500)])
        random.shuffle(coinlist)
        embed = discord.Embed(
            title="Coin Flipper.", color=16202876,
            description=f"And the answer is... \n**{random.choice(coinlist).capitalize()}**!")
        embed.set_thumbnail(url=(
            "https://cdn.discordapp.com/attachments/"
            "506665745229545472/589345676949848074/crabcoingem.png"))

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def cheeseboard(self, ctx):
        """<cheeseboard

Shows a leaderboard for cheese values. No arguments are required.
Who's the richest of them all?
        """
        richlist = await db.aio.return_all_balances()
        userlist, i = [], 0
        while len(userlist) != 7:
            user = self.bot.get_user(int(richlist[i][1]))
            if user is not None:
                if user.bot is False:
                    userlist.append([user, richlist[i][0]])
            i += 1
        embed = discord.Embed(title="Global Cheese Leaderboard", color=16202876)

        for y in range(7):
            embed.add_field(
                name=userlist[y][0].name,
                value=f"With a balance of {userlist[y][1]} <a:cheese:533544087484366848>",
                inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["inv"])
    @commands.guild_only()
    @handlers.blueprints_or()
    async def inventory(self, ctx, user: discord.Member = None):
        """<inventory [user]

Views the lobstero inventory of yourself or a given user.
        """
        user = ctx.author if user is None else user
        inv = await db.aio.find_inventory(user.id)
        strpairs = [f"**{list(x.keys())[0]}**: {list(x.values())[0]}" for x in inv]
        if not strpairs:
            embed = discord.Embed(
                title=f"Inventory for {user}",
                description="Absolutely nothing!", color=16202876)
            return await ctx.send(embed=embed)

        source = menus.ListEmbedMenuClean(strpairs, f"Inventory for {user}", 15, True)
        menu = MenuPages(source, timeout=30, clear_reactions_after=True)

        await menu.start(ctx)

    @commands.command(aliases=["give"])
    @commands.guild_only()
    @commands.is_owner()
    async def grant(self, ctx, user: discord.Member, *, sobject):
        """<grant (user) (object) (amount)

Divinely grants items to somebody. Owner-exclusive.
All parameters are required.
User should be a user ID, user mention, user nickname or username. Amount should be a number.
        """

        split = sobject.split(" ")
        amount = int(split[-1])
        thing = " ".join(split[0:-1])
        await db.aio.grant_item(user.id, thing, amount)
        await embeds.simple_embed("Item granted!", ctx)

    @commands.command(aliases=["take"])
    @commands.guild_only()
    @commands.is_owner()
    async def rescind(self, ctx, user: discord.Member, *, sobject):
        """<rescind (user) (object) (amount)

What can be given can also be taken away. Owner-exclusive.
All parameters are required.
User should be a user ID, user mention, user nickname or username. Amount should be a number.
        """

        split = sobject.split(" ")
        amount = int(split[-1])
        thing = " ".join(split[0:-1])
        res = await db.aio.remove_item(user.id, thing, amount)
        await embeds.simple_embed(
            "Item rescinded." if res else "Not enough of that item to do that.", ctx)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def pay(self, ctx, user: discord.Member, *, sobject):
        """<grant (user) (object) (amount)

Pays an amount of any item you own to somebody.
All parameters are required.
User should be a user ID, user mention, user nickname or username. Amount should be a number.
        """

        split = sobject.split(" ")
        amount = int(split[-1])
        thing = " ".join(split[0:-1])
        res = await db.aio.remove_item(ctx.author.id, thing, amount)
        if res:
            await db.aio.grant_item(user.id, thing, amount)
        await embeds.simple_embed(
            "Payment successful!" if res else "You don't have enough of that item to do that!", ctx)


def setup(bot):
    bot.add_cog(Cog(bot))
