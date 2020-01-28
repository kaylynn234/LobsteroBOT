import sys
import random
import aiohttp
import discord
import asyncio

from discord.ext.menus import MenuPages
from discord.ext import commands
from lobstero.utils import embeds, text, db
from lobstero.models import menus

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
    async def balance(self, ctx):
        if ctx.message.mentions:
            user = ctx.message.mentions[0]
        else:
            user = ctx.message.author

        bal = db.economy_check(user.id)
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
    async def guess(self, ctx, arg=None):
        """<guess

Test your luck and see if you can guess a random card for some cheese.
No parameters are required.
To see the costs and outcomes of playing, use <guess prices.
This command took a fair chunk of inspiration from crimsoBOT. Thanks crimsoBOT.
        """
        chs = "<a:cheese:533544087484366848>"
        if str(arg).lower() == "prices":
            embed = discord.Embed(title="Card guessing prices", color=16202876)
            embed.add_field(
                name="Guess the card's suit",
                value=f"**Cost to play**: 0 {chs} **Payout**: 25 {chs}")
            embed.add_field(
                name="Guess the card's type",
                value=f"**Cost to play**: 10 {chs} **Payout**: 50 {chs}")
            embed.add_field(
                name="Guess the number on the card",
                value=f"**Cost to play**: 50 {chs}. **Payout**: 500 {chs}")
            embed.add_field(
                name="Guess the exact card",
                value=f"**Cost to play**: 200 {chs} **Payout**: 5000 {chs}")
            return await ctx.send(embed=embed)

        embed = discord.Embed(title="Guess the card!", color=16202876, description=text.guess_what)
        sentembed = await ctx.send(embed=embed)

        msg = await self.handle_confirmation(ctx, sentembed)
        if not msg:
            return

        if msg.content == "5":
            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description="Well, thanks for the interest. See ya next time!")
            await sentembed.edit(embed=newembed)

        if msg.content == "1":
            await sentembed.edit(embed=discord.Embed(
                title="Guess the card!", color=16202876,
                description=(
                    "Well then! What suit is the card gonna be? It can be either ``hearts``, "
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
                db.economy_manipulate(ctx.author.id, 75)
            else:
                res = "Aw shucks, your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_1[cardlist[item]])

            await sentembed.edit(embed=newembed)

        if msg.content == "2":
            if not db.economy_check(ctx.author.id) >= 10:
                await sentembed.edit(embed=embeds.eco_broke)
                return

            await sentembed.edit(embed=discord.Embed(
                title="Guess the card!", color=16202876,
                description=(
                    "Alrighty! What type is the card gonna be? It can be either a ``king``, "
                    "``queen``, ``jack``, ``ace`` or a ``number``. You have 10 seconds to answer. "
                    "Get to it!")))

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            db.economy_manipulate(ctx.author.id, -10)
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
                db.economy_manipulate(ctx.author.id, 150)
            else:
                res = "Aw shucks, your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_2[cardlist[item]])

            await sentembed.edit(embed=newembed)

        if msg.content == "3":
            if not db.economy_check(ctx.author.id) >= 50:
                await sentembed.edit(embed=embeds.eco_broke)
                return

            await sentembed.edit(embed=discord.Embed(
                title="Guess the card!", color=16202876,
                description=(
                    "Hey, okay! What number do ya reckon is gonna be on the card? It can be "
                    "either a number from ``2``, ``3``, ``4``, etc (up to 10), or ``none``. "
                    "You have 10 seconds to answer. Hop to it, friend!")))

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            db.economy_manipulate(ctx.author.id, -50)

            cardlist = []
            for _ in range(12):
                cardlist.append("none")
            for _ in range(4):
                for i in range(10):
                    cardlist.append(str(i))

            random.shuffle(cardlist)
            item = random.randint(0, 51)

            if cardlist[item] == msg2.content.lower():
                res = "Congratulations! You're correct!"
                db.economy_manipulate(ctx.author.id, 5000)
            else:
                res = "Aw shucks, your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_3)

            await sentembed.edit(embed=newembed)

        if msg.content == "4":
            if not db.economy_check(ctx.author.id) >= 200:
                await sentembed.edit(embed=embeds.eco_broke)
                return

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            db.economy_manipulate(ctx.author.id, -200)
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
                db.economy_manipulate(ctx.author.id, 5000)
            else:
                res = "Aw shucks, your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_4)

            await sentembed.edit(embed=newembed)

    @guess.command(name="prices")
    async def guess_prices(self, ctx):
        chs = "<a:cheese:533544087484366848>"
        embed = discord.Embed(title="Card guessing prices", color=16202876)
        embed.add_field(
            name="Guess the card's suit",
            value=f"**Cost to play**: 0 {chs} **Payout**: 25 {chs}")
        embed.add_field(
            name="Guess the card's type",
            value=f"**Cost to play**: 10 {chs} **Payout**: 50 {chs}")
        embed.add_field(
            name="Guess the number on the card",
            value=f"**Cost to play**: 50 {chs}. **Payout**: 500 {chs}")
        embed.add_field(
            name="Guess the exact card",
            value=f"**Cost to play**: 200 {chs} **Payout**: 5000 {chs}")

        return await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def bigbrain(self, ctx):
        """<bigbrain

Engage in a fun game of Big Brain Trivia™!
This command has no arguments.
        """
        url = "https://opentdb.com/api.php?amount=1&type=boolean"
        async with self.session.get(url) as resp:
            data = await resp.json()

        embed = discord.Embed(title="Big Brain Trivia™!", color=16202876)
        correct = data["results"]["correct_answer"]
        dif = data["results"]["difficulty"].capitalize()

        embed.add_field(
            name="Category:", value=data["results"]["category"], inline=True)
        embed.add_field(
            name="Difficulty:", value=dif, inline=True)
        embed.add_field(
            name="Question:", value=data["results"]["question"], inline=False)
        embed.set_footer(text="True or False?")

        if dif == "Easy":
            timeg, payout = 6, 50
        if dif == "Medium":
            timeg, payout = 10, 100
        if dif == "Hard":
            timeg, payout = 14, 200

        embed.add_field(name="Time to answer:", value=f"{timeg} seconds.", inline=False)
        await ctx.send(embed=embed)

        try:
            msg = await self.bot.wait_for(
                'message', check=lambda message: message.author == ctx.author, timeout=timeg)
        except asyncio.futures.TimeoutError:
            return await embeds.simple_embed(
                f"You didn't answer in time! The correct answer was {correct}.", ctx)

        if msg.content.lower() == correct.lower():
            db.economy_manipulate(ctx.message.author.id, payout)
            await embeds.simple_embed(
                f"Your answer is correct! You earned {payout} cheese for winning.", ctx)
        else:
            await embeds.simple_embed(
                f"Your answer is sadly incorrect! The correct answer was {correct}", ctx)

    @commands.command()
    @commands.guild_only()
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
    async def cheeseboard(self, ctx):
        """<cheeseboard

Shows a leaderboard for cheese values. No arguments are required.
Who's the richest of them all?
        """
        richlist = db.return_all_balances()
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
    async def inventory(self, ctx, user: discord.Member = None):
        """<inventory [user]

Views the lobstero inventory of yourself or a given user.
        """
        user = ctx.author if user is None else user
        inv = db.find_inventory(user.id)
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
        db.grant_item(user.id, thing, amount)
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
        res = db.remove_item(user.id, thing, amount)
        await embeds.simple_embed(
            "Item rescinded." if res else "Not enough of that item to do that.", ctx)

    @commands.command()
    @commands.guild_only()
    async def pay(self, ctx, user: discord.Member, *, sobject):
        """<grant (user) (object) (amount)

Pays an amount of any item you own to somebody.
All parameters are required.
User should be a user ID, user mention, user nickname or username. Amount should be a number.
        """

        split = sobject.split(" ")
        amount = int(split[-1])
        thing = " ".join(split[0:-1])
        res = db.remove_item(ctx.author.id, thing, amount)
        if res:
            db.grant_item(user.id, thing, amount)
        await embeds.simple_embed(
            "Payment successful!" if res else "You don't have enough of that item to do that!", ctx)


def setup(bot):
    bot.add_cog(Cog(bot))
