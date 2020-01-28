import discord, os, sys
import crabtools
from discord.utils import get
from discord.ext import commands
import quest_text as qt_

root_directory = sys.path[0] + "/"

class recipe_holder():
    pass

class recipes():

    def __init__(self):
        self.recipes = []
    
    def add_recipe(self, takes, gives, level = 1):
        if not isinstance(takes, list):
            takes = [takes]
        if not isinstance(gives, list):
            gives = [gives]

        r = recipe_holder
        r.takes, gives = takes, gives

        self.recipes.append(r)

u_, c_ = recipes(), recipes()

# define upgrade / repair recipes

u_.add_recipe(["ripped backpack", "sewing kit"], gives="hurridly stitched backpack")
u_.add_recipe(["hurridly stitched backpack", "tailor's needle", "woven fabric", "refined string"], gives="pristine backpack")
        
# define crafting recipes

c_.add_recipe(["large rock", "small rock"], gives=["primitive blade", "large rock"]) # primitive knife blade
c_.add_recipe(["large rock", "large rock"], gives=["stone workbench", "large rock"]) # stone workbench
c_.add_recipe(["stone workbench", "small rock"], gives=["sharpened primitive blade", "stone workbench"], level = 2) # better primitive knife blade



class Cog(commands.Cog, name = "Games & Questing"): 
    """It's basically FFXIV!"""
    def __init__(self, client):
        self.client = client

    async def simple_embed(self, em_title: str, chn_location: int):
        sm_embed = discord.Embed(title=em_title, color=16202876)
        chn = self.client.get_channel(chn_location)
        await chn.send(embed=sm_embed)

    def str_between(self, s: str, first: str, last: str):
        start = s.index(first) + len(first)
        end = s.index(last, start)
        try: return s[start:end]
        except: return None

    @commands.command(aliases=["inv"])
    @commands.guild_only()
    async def inventory(self, ctx, user: discord.Member = None):
        """<inventory [user]

Views the lobstero inventory of yourself or a given user. User is an optional parameter, and should be a user ID, user mention, user nickname or username if specified.
        """
        user = ctx.author if user == None else user
        inv = crabtools.find_inventory(user.id)
        strpairs = [f"**{list(x.keys())[0]}** : {list(x.values())[0]}" for x in inv]
        embed = discord.Embed(title=f"Inventory for {str(user)}", description = "Absolutely nothing!" if len(strpairs) == 0 else "\n".join(strpairs), color=16202876)
        await ctx.send(embed=embed)

        loc = crabtools.retrieve_location(ctx.author.id)
        if loc == "undergrowth_b":
            embed = discord.Embed(title=f"The Undergrowth", description = qt_.ug_1a, color=16202876)
            await ctx.send(embed=embed)
            crabtools.set_location(ctx.author.id, "undergrowth_c")
    
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
        crabtools.grant_item(user.id, thing, amount)
        await self.simple_embed("Item granted!", ctx.channel.id)
    
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
        res = crabtools.remove_item(user.id, thing, amount)
        await self.simple_embed("Item rescinded." if res else "Not enough of that item to do that.", ctx.channel.id)

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
        res = crabtools.remove_item(ctx.author.id, thing, amount)
        if res:
            crabtools.grant_item(user.id, thing, amount)
        await self.simple_embed("Payment successful!" if res else "You don't have enough of that item to do that!", ctx.channel.id)
    
    @commands.group(invoke_without_command=True)
    @commands.guild_only()
    @commands.is_owner()
    async def quest(self, ctx):
        """<quest

Begins the Quest activity. No parameters are required.
        """
        crabtools.set_location(ctx.author.id, "undergrowth")
        loc = crabtools.retrieve_location(ctx.author.id)
        if not "undergrowth" in loc:
            return await self.simple_embed("You've already begun your quest! Use <quest whereami for more information on your surroundings.", ctx.channel.id)

        embed = discord.Embed(title = "The Undergrowth", description = qt_.ug_0, color=16202876)
        await ctx.send(embed=embed)

        crabtools.set_location(ctx.author.id, "undergrowth_a")

    @quest.command()
    @commands.guild_only()
    @commands.is_owner()
    async def rummage(self, ctx):
        """<quest rummage

Rummages through where you are in an attempt to find something. No parameters are required.
        """
        loc = crabtools.retrieve_location(ctx.author.id)
        embed = discord.Embed(title = "You can't use that here!", color=16202876)
        if loc == "undergrowth_a":
            embed = discord.Embed(title = "The Undergrowth", description = qt_.ug_0a, color=16202876)
            crabtools.grant_item(ctx.author.id, "diminished aid kit", 1)
            crabtools.grant_item(ctx.author.id, "woven bandages", 3)

            crabtools.set_location(ctx.author.id, "undergrowth_b")
        if loc == "undergrowth_c":
            embed = discord.Embed(title = "The Undergrowth", description = qt_.ug_1c, color=16202876)
            crabtools.grant_item(ctx.author.id, "Mysterious Ring", 1)
            crabtools.grant_item(ctx.author.id, "Crimson letter", 1)
            crabtools.grant_item(ctx.author.id, "Sewing Kit", 1)

            crabtools.set_location(ctx.author.id, "undergrowth_d")

        await ctx.send(embed=embed)
    
    @quest.command()
    @commands.guild_only()
    @commands.is_owner()
    async def use(self, ctx, *, item: str = None):
        """<quest use (item)

Uses an item, if possible.
        """
        loc = crabtools.retrieve_location(ctx.author.id)
        embed = discord.Embed(title = "You can't use that item! Try another, or wait until you're in a situation where it seems sensible.", color=16202876)
        if loc == "undergrowth_c" and item.lower() == "woven bandages":
            embed = discord.Embed(title = "The Undergrowth", description = qt_.ug_1b, color=16202876)
            if crabtools.remove_item(ctx.author.id, "woven bandages", 1):
                crabtools.set_location(ctx.author.id, "undergrowth_c")
            else:
                return await self.simple_embed("You don't have enough of that item to use it!", ctx.channel.id)

        await ctx.send(embed=embed)




def setup(client):
    client.add_cog(Cog(client))