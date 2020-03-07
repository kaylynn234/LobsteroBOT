import sys
import random
import aiohttp
import discord
import asyncio
import praw

from html import unescape
from discord.ext.menus import MenuPages
from discord.ext import commands
from lobstero.utils import embeds, text, db
from lobstero.models import menus, handlers
from lobstero import lobstero_config 

lc = lobstero_config.LobsteroCredentials()

root_directory = sys.path[0] + "/"


shop_item_values = {
    # name lower: buy value, sell value, buy amount
    # use None to prevent item purchase/ selling
    "token of love & friendship": (None, 1, 1),
    "shoe": (10, 2, 1),
    "ancient pair of glasses": (10, 2, 1),
    "red trout": (5, 3, 1),
    "exemplary tuna": (7, 5, 1),
    "agile cod": (13, 10, 1),
    "odd-looking salmon": (20, 15, 1),
    "peculiar barramundi": (60, 40, 1),
    "weird carp": (120, 100, 1),
    "ultimate catch": (1000, 300, 1),
    "stock market token": (50, 3, 10)
}


class Cog(commands.Cog, name="Economy & Games"):
    """Ever wanted to earn and gamble away insignificant pieces of cheese? Now's your chance!
Game, economy and gambling commands reside in this module.
You can sell things, buy things and gift them to people.

Roll the dice. Lose it all - only to win it back ten-fold.
As a Lobstero Cheese Economy Member, your lows are the lowest, but at your high you become a self-propelled demi-god of cheese.
If you're not willing to risk it, you'll never experience the ecstasy of true RNG."""

    def __init__(self, bot):
        self.bot = bot
        self.task = self.bot.loop.create_task(self.aiohttp_init())
        self.bot.chs = "<a:cheese:533544087484366848>"

        if not hasattr(self.bot, "reddit_client"):
            if lc.auth.reddit_client_ID == "None" or lc.auth.reddit_client_secret == "None":
                self.bot.reddit_client = False

            else:
                self.bot.reddit_client = praw.Reddit(
                    client_id=lc.auth.reddit_client_ID,
                    client_secret=lc.auth.reddit_client_secret,
                    user_agent='python:LobsteroBOT:v1.0.0 (by /u/lobstero_economy_bot)')

                # anyone who wants to use anything else can suffer

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
    async def balance(self, ctx, who: discord.Member = None):
        """Shows the cheese balance of you or someone else."""

        who = ctx.author if who is None else who
        bal = db.economy_check(who.id)
        if bal == 0:
            await embeds.simple_embed("Looks like this person doesn't have any cheese. ", ctx)
        else:
            embed = discord.Embed(title=" ", color=16202876)
            embed.add_field(
                name=f"User {who}'s balance.", value=f"{bal} <a:cheese:533544087484366848>")
            embed.set_thumbnail(url=(
                "https://arnweb.blob.core.windows.net/cache/1/b/6/3/d/7"
                "/1b63d7cb7717896aa0fe806c17dba9a57476b2ce.jpg"))

            await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @commands.guild_only()
    @handlers.blueprints_or()
    async def guess(self, ctx):
        """Test your luck and see if you can guess a random card for some cheese.
This command took a fair chunk of inspiration from crimsoBOT. Thanks crimsoBOT."""

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
                db.economy_manipulate(ctx.author.id, 20)
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
                db.economy_manipulate(ctx.author.id, 20)
            else:
                res = "Your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_2[cardlist[item]])

            await sentembed.edit(embed=newembed)

        if msg.content == "3":
            if not db.economy_check(ctx.author.id) >= 20:
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

            db.economy_manipulate(ctx.author.id, -20)

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
                db.economy_manipulate(ctx.author.id, 100)
            else:
                res = "Your guess was incorrect. Better luck next time!"

            newembed = discord.Embed(
                title="Guess the card!", color=16202876,
                description=f"And the answer is... {cardlist[item].capitalize()}! \n{res}")
            newembed.set_thumbnail(url=text.cardurls_3)

            await sentembed.edit(embed=newembed)

        if msg.content == "4":
            if not db.economy_check(ctx.author.id) >= 50:
                await sentembed.edit(embed=embeds.eco_broke)
                return

            msg2 = await self.handle_confirmation(ctx, sentembed)
            if not msg2:
                return

            db.economy_manipulate(ctx.author.id, -50)
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
    @handlers.blueprints_or()
    async def guess_prices(self, ctx):
        """Shows the prices for cheese guessing."""

        embed = discord.Embed(title="Card guessing prices", color=16202876)
        embed.add_field(
            name="Guess the card's suit",
            value=f"**Cost to play**: 0 {self.bot.chs} **Payout**: 20 {self.bot.chs}")
        embed.add_field(
            name="Guess the card's type",
            value=f"**Cost to play**: 0 {self.bot.chs} **Payout**: 20 {self.bot.chs}")
        embed.add_field(
            name="Guess the number on the card",
            value=f"**Cost to play**: 20 {self.bot.chs}. **Payout**: 100 {self.bot.chs}")
        embed.add_field(
            name="Guess the exact card",
            value=f"**Cost to play**: 50 {self.bot.chs} **Payout**: 1234 {self.bot.chs}")

        return await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def bigbrain(self, ctx):
        """Engage in a fun game of Big Brain Trivia™!"""

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
            db.economy_manipulate(ctx.message.author.id, payout)
            await embeds.simple_embed(
                f"Your answer is correct! You earned {payout} cheese for winning.", ctx)
        else:
            await embeds.simple_embed(
                f"Your answer is sadly incorrect! The correct answer was {correct}", ctx)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def flip(self, ctx):
        """Flip a coin and test your luck. That's it."""

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
        """Shows a leaderboard for cheese values.
Who's the richest of them all?"""

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
    @handlers.blueprints_or()
    async def inventory(self, ctx, who: discord.Member = None):
        """Shows the lobstero inventory of yourself or someone else."""

        who = ctx.author if who is None else who
        inv = db.find_inventory(who.id)
        strpairs = [f"**{list(x.keys())[0]}**: {list(x.values())[0]}" for x in inv]
        if not strpairs:
            embed = discord.Embed(
                title=f"Inventory for {who}",
                description="Absolutely nothing!", color=16202876)
            return await ctx.send(embed=embed)

        source = menus.ListEmbedMenuClean(strpairs, f"Inventory for {who}", 15, True)
        menu = MenuPages(source, timeout=30, clear_reactions_after=True)

        await menu.start(ctx)

    @commands.command(aliases=["give"])
    @commands.guild_only()
    @commands.is_owner()
    async def grant(self, ctx, who: discord.Member, *, item):
        """Divinely grants items to somebody. Owner-exclusive."""

        split = item.split(" ")
        amount = int(split[-1])
        thing = " ".join(split[0:-1])
        db.grant_item(who.id, thing, amount)
        await embeds.simple_embed("Item granted!", ctx)

    @commands.command(aliases=["take"])
    @commands.guild_only()
    @commands.is_owner()
    async def rescind(self, ctx, who: discord.Member, *, item):
        """What can be given can also be taken away. Owner-exclusive."""

        split = item.split(" ")
        amount = int(split[-1])
        thing = " ".join(split[0:-1])
        res = db.remove_item(who.id, thing, amount)
        await embeds.simple_embed(
            "Item rescinded." if res else "Not enough of that item to do that.", ctx)

    @commands.command()
    @commands.guild_only()
    @handlers.blueprints_or()
    async def pay(self, ctx, who: discord.Member, *, item):
        """Pays an amount of any item you own to somebody."""

        split = item.split(" ")
        amount = int(split[-1])
        thing = " ".join(split[0:-1])
        res = db.remove_item(ctx.author.id, thing, amount)
        if res:
            db.grant_item(who.id, thing, amount)

        await ctx.simple_embed(
            "Payment successful!" if res else "You don't have enough of that item to do that!")

    @commands.group(invoke_without_command=True, ignore_extra=False)
    @commands.guild_only()
    @handlers.blueprints_or()
    async def shop(self, ctx):
        """A base command for the shop and all related commands.
Use the commands here to buy or sell things.

*Psst!* Buying stock market tokens gives you access to the illusive Cheese Market - but you didn't hear it from me."""

        displayable = []

        for item, info in shop_item_values.items():
            cur = []
            if info[0]:
                cur.append(f"**{info[2]}**x can be bought for {info[0]} {self.bot.chs}")
            else:
                cur.append("Cannot be purchased!")

            if info[1]:
                cur.append(f"Can be sold for {info[1]} {self.bot.chs} each.")
            else:
                cur.append("Cannot be sold!")

            displayable.append((item.capitalize(), "\n".join(cur)))

        source = menus.TupleEmbedMenu(displayable, "Available items", 3, footer=True, inline=True)
        pages = MenuPages(source, clear_reactions_after=True)

        await pages.start(ctx)

    @shop.command(name="buy")
    @commands.guild_only()
    @handlers.blueprints_or()
    async def shop_buy(self, ctx, item):
        """Buy an item from the shop."""

        split = item.split(" ")
        try:
            amount = int(split[-1])
            thing = " ".join(split[0:-1])
        except ValueError:
            amount = 1
            thing = " ".join(split)

        item_in_shop = shop_item_values.get(thing.lower(), False)
        current_balance = db.economy_check(ctx.author.id)
        if not item_in_shop:
            return await ctx.simple_embed("That item isn't available in the shop!")
        if item_in_shop[0] is None:
            return await ctx.simple_embed("That item can't be purchased!")
        if amount * item_in_shop[0] > current_balance:
            return await ctx.simple_embed("You can't afford that!")

        to_pay = amount * item_in_shop[0]
        r = random.randint(1, 200)

        if r == 200:
            await ctx.simple_embed(
                "An obscure glitch in the shop's payment suite keeps your account untouched.")
            to_pay = 0
        elif r == 199:
            await ctx.simple_embed(
                "For some reason, money is transferred to your account instead of taken from it.")
            to_pay *= -1
        elif r == 198:
            await ctx.simple_embed(
                "The cashier is kind, and makes sure you only pay for half of your order.")
            to_pay = int(to_pay / 2)
        elif r == 197:
            await ctx.simple_embed(
                "The cashier lets you have a little extra for free.")
            amount = int(amount * 1.25)

        db.grant_item(ctx.author.id, thing, amount)
        db.economy_manipulate(ctx.author.id, to_pay * -1)
        desc = [
            f"Purchase: {amount * item_in_shop[2]}x {thing.capitalize()}",
            f"Balance before transaction: {current_balance} {self.bot.chs}",
            f"Transaction total: {abs(to_pay)}",
            f"Balance after transaction: {db.economy_check(ctx.author.id)} {self.bot.chs}"
        ]

        embed = discord.Embed(
            title=f"Receipt for {ctx.author}",
            description="\n".join(desc), color=16202876)

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Cog(bot))
