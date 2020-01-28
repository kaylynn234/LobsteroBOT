import random
import discord
import asyncio
from discord.ext import commands

from discord.ext import menus

ritualtext = """
**The Wielder**: I call upon the Divine Jury to commune, and present the Prayer.

(Crowd stands)

**Divine Jury**: Our Lobstero who art in Lobstero Hell, hallowed be thy name. Thy server come. Thy will be done on earth as it is in Lobstero Hell. Give
us this day our daily cheese, and forgive us our mentions, as we forgive those who mention us, and lead us not into bannation, but deliver us from rulebreaking.

For thine is the server, and the power, and the glory, for ever and ever.

**All**: Amen.

(Crowd is seated)

**Divine Jury**: The Prayer has been spoken.
The Ritual will now commence. 

(Crowd stands)

**Divine Jury**: Who would *dare* break the rules?

**All**: {val1} dares!

**Divine Jury**: Then they shall suffer, shall they not?

**All**: {val1} will suffer! And they will not resist.

**Divine Jury**: Thus it will be done.

(crowd is seated)

**Divine Jury**: And now, the beginning of the final rite. 

Lord Lobstero, grant us a ban, and allow us to channel it.

(Divine Jury prays)

**Divine Jury**: The ban has been granted.

With all due might, I give this gift of benevolent power to {val2}, The Wielder. 

May they use it well.

(The Divine Jury steps to the right)

**Divine Jury**: Come, Wielder! 
Dispense the just fury of a thousand suns!

(The Wielder steps forward)

**The Wielder**:"""

class EmbedMenu(menus.ListPageSource):
    def __init__(self, data, title, per_page:int=10):
        super().__init__(data, per_page=per_page)
        self.title = title

    async def format_page(self, menu, entries):
        # offset = menu.current_page * self.per_page
        is_dict = isinstance(entries, dict)
        if is_dict:
            embed = discord.Embed(title=self.title, color=16202876)
            for key, value in entries.items():
                embed.add_field(name=key, value=value, inline=False)
        else: # presume iterable
            embed = discord.Embed(title=self.title, color=16202876, description = "\n".join([f"``{x}``" for x in entries]))
        
        return embed

class Cog(commands.Cog, name = "testing"):
    """Why are you here"""
    def __init__(self, client):
        self.client = client

    @commands.command()
    @commands.is_owner()
    async def menu_test(self, ctx, num: int = 20):
        """fvevggv"""
        pages = menus.MenuPages(source=EmbedMenu(range(1, num), "example", 10), clear_reactions_after=True)
        await pages.start(ctx)

    @commands.command()
    async def test_guess(self, ctx):
        number = random.randint(1, 100)
        numguesses = 3
        print(number)
        
        ranges = None
        for i in range(0, 101, 25): # start, stop, step; "i" will be 0, 25, 50 and 75
            if i <= number <= i + 25: # if number is between i and i plus 25
                ranges = [i, i+25] # ranges = i and i plus 25

        # ranges should never, ever be none but we can check anyway

        if not ranges:
            print("something broke")

        await ctx.send(f"i've picked a random number between {ranges[0]} and {ranges[1]}. you have 3 guesses and 10 seconds per guess. go!")
        for _ in range(4): # we don't need the value here, so we can just make it _. this is just to make sure the code doesn't do anything it shouldn't and runs a finite amount of times

            try:
                guess = await self.client.wait_for('message', timeout=10.0, check=lambda message: message.author == ctx.author) # wait for the message 

                if guess.content: # make sure the message contains text
                    if guess.content.isnumeric(): # make sure the text is a number
                        
                        if int(guess.content) == number: # you got it
                            return await ctx.send("you win!")

                        elif int(guess.content) != number:
                            if numguesses != 1:
                                await ctx.send(f"you didn't answer correctly! you have {str(numguesses - 1)} guesses remaining...")
                            else:
                                return await ctx.send("you didn't answer correctly and are completely out of guesses. better luck next time!")
                        else:
                            guess = None # answer incorrect
                    else: # format incorrect, probably normal text
                        if numguesses != 1:
                            await ctx.send(f"you need to enter a number. you have {str(numguesses - 1)} guesses remaining...")
                        else:
                            return await ctx.send("you need to enter a number, you silly goose. you're out of guesses, better luck next time!")

                else: 
                    if numguesses != 1:
                        await ctx.send(f"you need to enter a number! you have {str(numguesses - 1)} guesses remaining")
                    else:
                        return await ctx.send("you need to enter a number, you silly goose. you're out of guesses, better luck next time!")
            except asyncio.futures.TimeoutError:
                guess = None
                if numguesses != 1:
                    await ctx.send(f"you didn't answer in time. you have {str(numguesses - 1)} guesses remaining")
                else:
                    await ctx.send("you didn't answer in time and are completely out of guesses, you lose!")
                
            numguesses -= 1 # lower numguesses by 1

    @commands.command()
    async def nuclear(self, ctx):
        embed = discord.Embed(title="Nuclear", description="1. Nuclear Defense\n2. Launch Codes")
        await ctx.send(embed=embed)
        try:
            my_input = await self.client.wait_for('message', check=lambda message: message.author == ctx.author) #this looks for a response and makes sure that it is from the person who used the command, "ctx.author"
            if my_input.content:
                if my_input.content.isnumeric(): #self explanatory
                    if int(my_input.content) == 1: #if the answer is 1   
                        embed = discord.Embed(title="`NUCLEAR DEFENCE HAS BEEN ENABLED.`")
                        await ctx.send(embed=embed) #sends it in an embed
                    elif int(my_input.content) == 2:
                        embed = discord.Embed(title="`LAUNCH CODES`")
                        embed.description = str(random.randint(10000, 30000)) #random.randint(10000, 30000) picks a random number betwen 10,000 and 30,000
                        await ctx.send(embed=embed)
                    else: 
                        await ctx.send("you need to enter either 1 or 2.")
                else:
                  await ctx.send("you need to enter a number.")

        except asyncio.futures.TimeoutError:
            await ctx.send("time's up")
        except:
            print("something else went wrong")
    
    @commands.command(aliases=["ritual"])
    @commands.guild_only()
    @commands.has_permissions(manage_messages=True)
    async def theritual(self, ctx, *, user: discord.User = None):
        """<theritual (user)

Divination.
        """

        val = ritualtext.format(val1=user.mention, val2=ctx.author.mention)
        embed = discord.Embed(description=val, color=16202876)
        await ctx.send(embed=embed)

        try:
            msg = await self.client.wait_for('message', timeout=10.0, check=lambda message: message.author == ctx.author)
        except:
            msg = None

        if msg != None:
            if "ban" in msg.content.lower():
                embed = discord.Embed(title=f"User {str(user)} MEGA HECKING BANNED.", color=16202876)
                embed.add_field(name="Executed by staff member:", value=str(ctx.author), inline=False)
                embed.add_field(name="With reason:", value="Divine justice.", inline=False)

                await ctx.send(embed=embed)

    @commands.command()
    async def reactoo(self, ctx):
        first = True
        embed=discord.Embed(title = "Pick a choice", color=0x00f900)
        embed.add_field(name="Choice 1", value="Say nothing", inline=False)
        embed.add_field(name="Choice 2", value="What", inline=False)
        embed.add_field(name="Choice 3", value="Ignore", inline=False)
        embed.add_field(name="Choice 4", value="Cancel & Quit", inline=False)
        embed.set_footer(text="Choices")
        if first:
            sent = await ctx.channel.send(embed=embed)
        else:
            await sent.edit(embed=embed)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "❌"]
        for emoji in emojis:
            await sent.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.message.author and str(reaction.emoji) in emojis

        reaction = await self.client.wait_for('reaction_add', check=check)
        await sent.clear_reactions()

        if reaction[0].emoji == "1️⃣":
            embed=discord.Embed(title="test 1", color=0x00f900)
            await ctx.send(embed=embed)
        elif reaction[0].emoji == "2️⃣":
            embed=discord.Embed(title="test 2", color=0x00f900)
            await ctx.send(embed=embed)
        elif reaction[0].emoji == "3️⃣":
            embed=discord.Embed(title="test 3", color=0x00f900)
            await ctx.send(embed=embed)
        elif reaction[0].emoji == "❌":
            await sent.delete()
            await ctx.message.delete()
        
def setup(client):
    client.add_cog(Cog(client))