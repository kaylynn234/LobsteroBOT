import random
import os
import urllib
import urllib.request
import urllib.parse
import re
import sys
import functools
import aiohttp
import discord
import imgkit
import spotipy
import matplotlib.pyplot as plotter

from io import BytesIO
from spotipy.oauth2 import SpotifyClientCredentials
from discord.ext import commands
from discord.ext.menus import MenuPages
from PIL import Image
from nltk.corpus import wordnet as wn
from collections import Counter
from lobstero.utils import misc, db, strings, text, embeds
from lobstero.models import games, menus
from lobstero import lobstero_config 

lc = lobstero_config.LobsteroCredentials()
root_directory = f"{sys.path[0]}/".replace("\\", "/")
nouns = {x.name().split('.', 1)[0] for x in wn.all_synsets('n')}
verbs = {x.name().split('.', 1)[0] for x in wn.all_synsets('v')}
mazes = {}

if lc.config.wkhtmltoimage_path != "None":
    config = imgkit.config(wkhtmltoimage=lc.config.wkhtmltoimage_path)

unogames = games.uno_game_collector()


def rverb():
    return random.sample(verbs, 1)[0]


def rnoun():
    return random.sample(verbs, 1)[0]


fishchances = (
    ["shoe" for _ in range(50)] +
    ["glasses" for _ in range(50)] +
    ["fish1" for _ in range(200)] +
    ["fish2" for _ in range(175)] +
    ["fish3" for _ in range(125)] +
    ["fish4" for _ in range(100)] +
    ["fish5" for _ in range(75)] +
    ["fish6" for _ in range(50)] +
    ["fish7" for _ in range(10)])


class Cog(commands.Cog, name="Fun"):
    """Commands to (hopefully) brighten your day."""

    def __init__(self, bot):
        self.bot = bot
        self.task = self.bot.loop.create_task(self.aiohttp_init())

    async def aiohttp_init(self):
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.task.cancel()
        self.session.close()

    @commands.command(enabled=(lc.auth.cat_api_kay != "None"))
    async def cat(self, ctx):
        """images of the felines"""
        url = f"https://api.thecatapi.com/v1/images/search?api_key={lc.auth.cat_api_kay}"
        async with self.session.get(url) as resp:
            data = await resp.json()

        embed = discord.Embed(title="Random cat image", color=16202876)
        embed.set_image(url=data[0]["url"])
        await ctx.send(embed=embed)

    @commands.command()
    async def dog(self, ctx):
        """images of the canines"""
        url = "https://dog.ceo/api/breeds/image/random"
        async with self.session.get(url) as resp:
            data = await resp.json()

        embed = discord.Embed(title="Random dog image", color=16202876)
        embed.set_image(url=data["message"])
        await ctx.send(embed=embed)

    @commands.command()
    async def fox(self, ctx):
        """Sends a random fox picture. """
        url = "https://randomfox.ca/floof/"
        async with self.session.get(url) as resp:
            data = await resp.json()

        embed = discord.Embed(title="Random fox image", color=16202876)
        embed.set_image(url=data["image"])
        await ctx.send(embed=embed)

    @commands.command(aliases=["luggi", "sadcat"])
    async def cursedcat(self, ctx, number: int = None):
        """<cursedcat (number)

Sends either a specific or random cursed cat. All parameters are optional.
Nobody knows where they came from originally.
Thanks Luggi."""

        cat_filenames = [x for x in os.listdir(root_directory + "data/cursedcats/")]

        if number is None:
            cat_num = int(random.randint(0, len(cat_filenames) - 1))
        else:
            cat_num = misc.clamp(number, 0, len(cat_filenames - 1))

        embed = discord.Embed(title=f"Cursed cat image #{cat_num + 1}", color=16202876)
        filename = f"{root_directory}data/static/cursedcats/{cat_filenames[cat_num]}"
        to_send = discord.File("some_file_path", filename=cat_filenames[cat_num])
        embed.set_image(url=f"attachment://{filename}")
        await ctx.send(file=to_send, embed=embed)

    @commands.command()
    @commands.guild_only()
    async def dice(self, ctx, sides: int):
        """Usage: <dice (number)

Rolls a dice with sides ``number``. All parameters are required.
It's not every day you experience the rolling of the dice.
        """
        numero = random.randint(1, sides)
        await ctx.send("🎲 **You rolled ** ``" + str(numero) + "``.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    @commands.guild_only()
    async def say(self, ctx, *, mesgg: str):
        """<say (text)

Make the bot say something haha funni for you.
All parameters are required."""
        await ctx.send(mesgg)
        await ctx.message.delete()

    @commands.command()
    @commands.guild_only()
    async def garkov(self, ctx):
        """<garkov

Markov but garfield. No parameters are required."""
        if lc.config.wkhtmltoimage_path != "None":
            conf = {"config": config}
        else:
            conf = {}
            options = {"options": {"xvfb": ""}}

        to_run = functools.partial(
            imgkit.from_url, "http://joshmillard.com/garkov/",
            f"{root_directory}/lobstero/data/downloaded/garkovraw.png", **conf, **options)

        await self.bot.loop.run_in_executor(None, to_run)

        saved = Image.open(f"{root_directory}/lobstero/data/downloaded/garkovraw.png")
        finished = saved.crop((206, 447, 818, 662))

        buffer = BytesIO()
        finished.save(buffer, "png")
        buffer.seek(0)
        img = discord.File(fp=buffer, filename="garkov.png")

        embed = discord.Embed(color=16202876)
        embed.set_image(url="attachment://garkov.png")
        await ctx.send(file=img, embed=embed)

    @commands.command()
    @commands.guild_only()
    async def conglomerate(self, ctx):
        """<conglomerate

Randomized text madness. No parameters are required.
        """
        wordlist, num, endstr = [], random.randint(6, 18), ""
        async for message in ctx.channel.history(limit=250):
            if message.clean_content != "":
                wordlist.append(message.clean_content)
        for i in range(num):
            endstr += " " + random.choice(random.choice(wordlist).split())
        await ctx.send(endstr)

    @commands.command(aliases=["g"])
    @commands.guild_only()
    async def gnome(self, ctx, *, member=None):
        """I'm gnot a gnoblin, I'm gnot a gnelf...
Usage: <gnome @mention"""

        if member is None:
            embed = discord.Embed(
                title=f"{ctx.author.name} tries to gnome the abyss",
                description="... But fails miserably. \n\nYou can't gnome gnothingness.",
                color=16202876).set_footer(text="In space, nobody can hear you in space.")

            return await ctx.send(embed=embed)

        if not ctx.message.mentions:
            embed = discord.Embed(
                title=f"{ctx.author.name} tries to gnome the ungnome",
                description="... Nothing happens.",
                color=16202876).set_footer(text="Try mentioning somebody to gnome.")

            return await ctx.send(embed=embed)

        if ctx.message.mentions and ctx.message.mentions[0] == ctx.author:
            embed = discord.Embed(
                title=f"{ctx.author.name} tries to gnome themselves",
                description="... But it doesn't work.",
                color=16202876).set_footer(text="Try gnoming somebody else.")

            return await ctx.send(embed=embed)

        if len(ctx.message.mentions) > 1:
            embed = discord.Embed(
                title=f"{ctx.author.name} tries to gnome multiple people",
                description="... But they receive nothing for their efforts.",
                color=16202876)
            embed.set_footer(text="You can only gnome one person at a time. Slow and painful.")

            return await ctx.send(embed=embed)

        gnomecount = db.add_gnome(ctx.message.mentions[0].id, 1)
        gnome_filenames = [x for x in os.listdir(root_directory + "lobstero/data/static/gnomes/")]
        gnome_index = random.randint(1, len(gnome_filenames))
        gnomefile = discord.File(
            f"{root_directory}lobstero/data/static/gnomes/{gnome_filenames[gnome_index]}",
            filename=gnome_filenames[gnome_index])

        gnomebed = discord.Embed(
            title=ctx.author.name + " gnomes " + ctx.message.mentions[0].name,
            description=(
                f"{ctx.message.mentions[0].name.capitalize()} has been gnomed {gnomecount} "
                f"times now. This is gnome {gnome_index}."),
            color=16202876)
        gnomebed.set_image(url=f"attachment://{gnome_filenames[gnome_index]}")

        await ctx.send(file=gnomefile, embed=gnomebed)

    @commands.command(aliases=["h", "huggy", "shareamethneedlewith"])
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    async def hug(self, ctx, *, user=None):
        """<hug (@mentions)

Show somebody love an affection. Use mentions to specify who you want to hug.
Up to 6 people can be hugged at once.
        """
        mentionlist = [x for x in ctx.message.mentions if x != ctx.author]
        embed = discord.Embed(color=16202876)

        if len(mentionlist) > 6:
            embed.description = f"{ctx.author.mention}! You can't hug that many people at once!"
            return await ctx.send(embed=embed)

        if mentionlist:
            outstr = [f"{ctx.message.author.mention} hugs {mentionlist[0].mention}"]
            if len(mentionlist) == 2:
                outstr.append(f" and {mentionlist[1].mention}!")
            elif len(mentionlist) > 2:
                outstr.append(", ".join([""] + [x.mention for x in mentionlist[1:-1]]))
                outstr.append(f" and {mentionlist[-1].mention}!")

            embed.description = "".join(outstr)
            await ctx.send(embed=embed)

            db.grant_item(str(ctx.author.id), "Token of love & friendship", len(mentionlist))
            for member in mentionlist:
                db.grant_item(str(member.id), "Token of love & friendship", 1)
        else:
            embed.description = f"{ctx.author.mention} hugs ``ṫ̫̼h̉̃ͤe̵̡̊ v̴̹̅o̢͙̎iͭ͢͡d̬̽̕``"
            ctx.command.reset_cooldown(ctx)
            return await ctx.send(embed=embed)

    @commands.command(aliases=["mh", "megahuggy"])
    @commands.cooldown(1, 600, commands.BucketType.user)
    @commands.guild_only()
    async def megahug(self, ctx, *, user=None):
        """<megahug (@mention)

It's like hugging somebody four times at once!
You can only hug one person this tightly.
        """
        mentionlist = [x for x in ctx.message.mentions]
        embed = discord.Embed(color=16202876)
        if len(mentionlist) == 1 and mentionlist[0] == ctx.author:
            ctx.command.reset_cooldown(ctx)
            embed.description = "Don't even try."

        if len(mentionlist) == 1:
            embed.description = (
                f"{ctx.message.author.mention} hugs {mentionlist[0].mention} "
                "four times more tightly than usual")
            db.grant_item(ctx.author.id, "Token of love & friendship", 4)
            db.grant_item(mentionlist[0].id, "Token of love & friendship", 1)
        elif len(mentionlist) > 1:
            embed.description = "You can't hug more than one person that tightly!"
            ctx.command.reset_cooldown(ctx)
        elif len(mentionlist) == 0 or user is None:
            embed.description = (
                f"{ctx.author.mention} hugs ``ṫ̫̼h̉̃ͤe̵̡̊ v̴̹̅o̢͙̎iͭ͢͡d̬̽̕`` "
                "as hard as they can. Nothing really happens.")
            ctx.command.reset_cooldown(ctx)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def haiku(self, ctx):
        """<haiku

This is most definitely poetry. No parameters required.
Spits out a haiku."""
        async with self.session.get("http://randomhaiku.com/") as resp:
            pagecontent = await resp.text()
        pagecontent = strings.str_between(pagecontent, "<poem>", "</poem>")
        pagecontent = pagecontent.replace("<line>", "")
        pagecontent = pagecontent.replace("</line>", "\n")
        await ctx.send(str(pagecontent))

    @commands.command()
    @commands.guild_only()
    async def dadjoke(self, ctx):
        """<dadjoke

Gives you a tidbit of "humour." This was a terrible idea.
        """
        url = 'https://icanhazdadjoke.com/'
        headers = {'Accept': 'text/plain'}
        async with self.session.get(url, headers=headers) as resp:
            pagecontent = await resp.text()
        await ctx.send(pagecontent)

    @commands.command()
    @commands.guild_only()
    async def corpus(self, ctx, *, text: str = None):
        """Cephalon lobstero
Usage: <corpus some text here"""
        newtext = ""
        for x in list(text):
            strpos = 0
            counter = -1
            letter = str(x)
            for y in """abcdefghijklymnopqrstuvwxyz""":
                counter += 1
                if str(y).lower() == str(x).lower():
                    letter = "apykeppkipkkyypokqpyputj yz"[counter]
            newtext += letter
            strpos += 1
        await ctx.send(newtext)

    @commands.command()
    @commands.guild_only()
    async def love(self, ctx, person1: str = None, person2: str = None):
        """Calculates chance of love between two people.
Usage: <love person1 "person with name longer then 1 word" """
        if person2:
            p_1, p_2 = urllib.parse.quote_plus(person1), urllib.parse.quote_plus(person2)
            url = "https://www.lovecalculator.com/love.php?name1=" + str(p_1) + "&name2=" + str(p_2)
            async with self.session.get(url) as resp:
                pagecontent = await resp.text()

            result = strings.str_between(pagecontent, '"result__score"', "%")
            result = result.replace(" ", "").replace("\n", "")
            await ctx.send("".join([
                "<a:heartbeat:544335833004507159> There is a **", str(result)[1:],
                "%** chance of a successful relationship between **", str(person1),
                "** and **" + str(person2) + "**. <a:heartbeat:544335833004507159>"]))
        else:
            await ctx.send("Something's missing...")

    @commands.command()
    @commands.guild_only()
    async def inspire(self, ctx):
        """Inspirobot is very inspiring.
Usage: <inspire"""
        url = "https://inspirobot.me/api?generate=true"
        async with self.session.get(url) as resp:
            pagecontent = await resp.text()
        embed = discord.Embed(title='Random "Inspiring" quote.', color=16202876)
        embed.set_image(url=pagecontent)
        await ctx.send(embed=embed)

    @commands.command(enabled=(lc.auth.spotify_client_id != "None"))
    @commands.guild_only()
    async def suggestmusic(self, ctx):
        """Music from Kaylynn's spotify library.
Usage: <suggestmusic"""
        client_credentials_manager = SpotifyClientCredentials(
            lc.auth.spotify_client_id, lc.auth.spotify_client_secret)

        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        username = lc.config.spotify_user_uri
        playlist_id = lc.config.spotify_playlist_uri
        results = sp.user_playlist(
            username, playlist_id,
            fields="tracks.items(track(name,album(artists, name, images)))")

        resultlist = []
        for x in results['tracks']['items']:
            resultlist.append([
                x['track']['name'], x['track']['album']['name'],
                x['track']['album']['images'][0]['url'],
                x['track']['album']['artists'][0]["name"]])

        y = random.choice(resultlist)
        embed = discord.Embed(title="Suggested song", color=16202876)
        embed.add_field(name="Artist", value=y[3], inline=True)
        embed.add_field(name="Track name", value=y[0], inline=True)
        embed.add_field(name="Album", value=y[1], inline=False)
        embed.set_thumbnail(url=y[2])
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def activitygraph(self, ctx):
        """It's educational!
Usage: <activitygraph"""
        messagelist = [str(x.author) async for x in ctx.channel.history(limit=250)]

        counted_messages = Counter(messagelist)
        main_people = counted_messages.most_common(5)
        everyone_else = sum(counted_messages.values()) - sum([v[1] for v in main_people])
        main_people.append(("Other users", everyone_else))
        data, labels = [], []

        for x in main_people:
            labels.append(x[0])
            data.append(x[1])

        fig, axes = plotter.subplots()
        axes.pie(data, labels=labels, autopct='%1.2f', startangle=0)
        axes.axis('equal')
        plotter.savefig(root_directory + 'lobstero/data/generated/activity_data.png')

        image = discord.File(
            f"{root_directory}lobstero/data/generated/activity_data.png", filename="activity_data.png")

        embed = discord.Embed(
            title="Recent activity",
            description="User activity in the last 250 messages is shown below.", color=16202876)

        embed.set_image(url="attachment://activity_data.png")
        await ctx.send(file=image, embed=embed)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_message(self, message):
        should_continue = 0

        if message.guild is None:
            return

        if "lobstero " in message.content.lower() and "play " in message.content.lower():
            should_continue = 1
        if message.guild.id == 177192169516302336:
            should_continue = 0

        table = db.give_table()
        if message.guild.id not in table:
            th = misc.populate({})
        else:
            th = misc.populate(table[message.guild.id])

        if should_continue and th["random_messages"]:
            ytquery = strings.slicer(message.content.lower(), "play").replace("play ", "")
            query_string = urllib.parse.urlencode({"search_query": ytquery})
            async with self.session.get(f"https://www.youtube.com/results?{query_string}") as resp:
                pagecontent = await resp.text()

            search_results = re.findall(r'href=\"\/watch\?v=(.{11})', pagecontent)
            await message.channel.send(f"https://www.youtube.com/watch?v={search_results[0]}")

    @commands.command()
    @commands.guild_only()
    async def lmgtfy(self, ctx, *, query):
        val = urllib.parse.quote_plus(query)
        embed = discord.Embed(
            title='Search result:', description=f"https://lmgtfy.com/?qtype=search&q={val}",
            color=16202876)

        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def fortune(self, ctx):
        """Fortune cookies, with (of course) a twist."""
        async with self.session.get("http://yerkee.com/api/fortune") as resp:
            pagecontent = await resp.text()

        val = strings.str_between(pagecontent, '{"fortune":"', '"}')
        newval = []
        for x in val.split(" "):
            if x.lower() in nouns:
                newval.append(random.choice(["Lobsteric", "Lobstero", "Lobster"]))
            else:
                newval.append(x)
        desc = " ".join(newval).capitalize()
        embed = discord.Embed(
            description=desc.replace(r"\n\t\t--", "").replace(r"\n", "").replace(r"\t", ""),
            color=16202876)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def punchline(self, ctx):
        """Creates a /funny/ surreal meme."""

        templates = [
            f"Do not {rverb()} for they will {rverb()}. They will know if you {rverb()}.",
            f"Remember to {rverb()} your {rnoun()}, or else they will {rverb()}.",
            f"Be wary of {rnoun()}, because they {rverb()}.",
            f"It is the time to {rverb()}, for the {rnoun()} has returned.",
            f"Who has {rverb()} my {rnoun()}?",
            f"Ah yes, enslaved {rnoun()}.",
            f"Do you ever wonder where {rnoun()} comes from? They {rverb()} it."]

        result = random.choice(templates)
        embed = discord.Embed(description=result.replace("_", " "), color=16202876)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def fish(self, ctx):
        """<fish

Throw out a line and take a fish. No parameters are required.
Use <inventory to see the fish you own."""

        if db.economy_check(ctx.author.id) < 11:
            embed = discord.Embed(
                description="You don't have enough <a:cheese:533544087484366848> to fish!")
            return await ctx.send(embed=embed, color=16202876)

        result = random.choice(fishchances)

        db.economy_manipulate(ctx.author.id, -10)
        db.grant_item(ctx.author.id, text.fish_names[result], 1)

        embedtext = [
            f"You found a {text.fishdict[result]}!\n\n"
            f"Find it in your inventory under the name \"{text.fish_names[result]}\"\n"]
        embed = discord.Embed(description="".join(embedtext), color=16202876)
        embed.set_footer(text="You paid 10 cheese for casting.")
        return await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def shareatag(self, ctx):
        """Find out who shares a tag with you."""
        discrim = ctx.author.discriminator
        shared = [str(x) for x in self.bot.users if x.discriminator == discrim]

        menu = menus.ListEmbedMenu(shared, "Users that share your tag", 10)
        pages = MenuPages(source=menu)
        await pages.start(ctx)

    @commands.command()
    @commands.guild_only()
    @commands.max_concurrency(1, commands.BucketType.guild)
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def maizemaze(self, ctx):
        mazes[ctx.author] = menus.MaizeMenu()
        await mazes[ctx.author].start(ctx)

    @commands.command(aliases=["gn", "bedtime"])
    @commands.cooldown(1, 300, commands.BucketType.user)
    @commands.guild_only()
    async def goodnight(self, ctx, *, user: discord.User):
        await embeds.simple_embed("User bedtime'd.", ctx.message.channel.id)
        embed = discord.Embed(title="It is bed o'clock", color=16202876)
        embed.set_image(url=text.bedtime_url)
        embed.set_footer(text="You best be sleeping.")
        await user.send(embed=embed)

    @commands.command(name="88x31", aliases=["31x88"])
    @commands.guild_only()
    async def buttoncmd(self, ctx):
        """
        <88x31

        Gets a random 88x31 button from https://cyber.dabamos.de/88x31/. No parameters are required.
        """
        async with self.session.get("https://cyber.dabamos.de/88x31/") as resp:
            data = await resp.text()
        found = re.findall('<img.*?src="(.*?)"[^\>]+>', data)
        chosen = random.choice(found)
        embed = discord.Embed(title="88x31", color=16202876)
        embed.set_image(url=f"https://cyber.dabamos.de/88x31/{chosen}")

        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Cog(bot))
