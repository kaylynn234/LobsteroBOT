import os
import functools
import random
import sys
import glob
import io
import discord
import PIL
import aiohttp

from unittest import mock
from io import BytesIO
from lobstero import lobstero_config
from lobstero.utils import strings
from lobstero.external import asciify, kromo, halftone
from urllib.parse import urlsplit
from PIL import ImageFilter, ImageFont, Image, ImageDraw, ImageEnhance
from discord.ext import commands

root_directory = sys.path[0] + "/"
lc = lobstero_config.LobsteroCredentials()


class ban_loc():

    def __init__(self):
        self.x, self.y = random.randint(1, 512), random.randint(1, 512)
        self.vectorx, self.vectory = 0, 0
        self.speed = random.randint(4, 9)

        while self.vectorx == 0 and self.vectory == 0:
            self.vectorx, self.vectory = random.randint(-1, 1), random.randint(-1, 1)

    def update_frame(self):
        self.x += (self.vectorx * self.speed) 
        self.y += (self.vectory * self.speed)


class ban_conglomerate():

    def __init__(self):
        self.bans = [ban_loc() for _ in range(random.randint(9, 12))]
        self.frames = 0

    def generate_frame(self, banimg):
        img = Image.new("RGBA", (640, 640), (54, 57, 63, 255))

        for x in self.bans:
            img.paste(banimg, (x.x, x.y), banimg)
            x.update_frame()

        if self.frames == 10:
            self.bans.append(ban_loc())
            self.frames = -1

        self.frames += 1

        return img


class Cog(commands.Cog, name="Editing"):
    """Edit images. All commands in this module will take an ``Image`` parameter.

You can either:
- attach the image to the message you send the command in
- @mention a user to use their profile picture
- use a custom emoji
- or pass it using a URL when using the command
If you don't do any of that, Lobstero will search the previous few messages for an image."""
    def __init__(self, bot):
        self.bot = bot
        self.task = self.bot.loop.create_task(self.aiohttp_init())

    async def aiohttp_init(self):
        self.session = aiohttp.ClientSession()

    def cog_unload(self):
        self.task.cancel()
        self.session.close()

    def is_image(self, url):
        finalurl = None
        if str(url).lower().endswith(".png") or str(url).lower().endswith(".jpg"):
            finalurl = url.lower()
        elif str(url).lower().endswith(".jpeg"):
            finalurl = f"{url[:-4]}jpg"
        return finalurl

    async def package(self, file_loc, download=True):
        """Packages a local or downloaded file into an object."""
        try:
            file_name = urlsplit(file_loc)[2].split('/')[-1]
            file_ext = file_name.split(".", 1)[1]
        except KeyError:
            return None  # Not a well-formed url
        f = io.BytesIO()

        if download:
            try:
                async with self.session.get(file_loc) as resp:
                    f.write(await resp.read())
            except (OSError, ValueError):
                return None
        else:
            try:
                b = open(file_loc, "rb")
                f.write(b.read())
            except (OSError, ValueError):
                return None

        # This should (hopefully) never fail
        f_obj = mock.Mock()
        f_obj.data, f_obj.name, f_obj.ext = f, file_name, file_ext

        return f_obj

    async def processfile(self, p_ctx, url):
        constructed = None
        if url:
            value = None
            c = commands.MemberConverter()
            try:
                m = await c.convert(p_ctx, url)
            except commands.BadArgument:  # Member lookup failed, assume emoji
                em = strings.split_count(url)
                if em:
                    escape = f"{ord(em[0]):X}"
                    constructed = await self.package(
                        f"{root_directory}data/static/emojis/{escape}.png", False)

                c = commands.PartialEmojiConverter()
                try:
                    found_emoji = strings.split_count(url)
                    if not found_emoji:
                        e = await c.convert(p_ctx, url)
                except commands.BadArgument:  # Emoji lookup failed, assume it's a URL and pray
                    constructed = await self.package(url)
                else:  # Emoji lookup was a success
                    if found_emoji:
                        escape = "-".join([f"{ord(e):X}" for e in found_emoji])
                        filename = f"{root_directory}lobstero/data/static/emojis/{escape}.png"
                        constructed = await self.package(filename, False)
                    else:
                        constructed = await self.package(str(e.url))

            else:  # Member conversion was a success, get an avatar url and download it
                value = m.avatar_url_as(static_format="png", size=2048)
                constructed = await self.package(str(value))

        elif url is None:
            if p_ctx.message.attachments:
                constructed = await self.package(p_ctx.message.attachments[0].url)

        if constructed is None:
            for message in await p_ctx.channel.history(limit=25).flatten():
                if not constructed:
                    if message.embeds and message.embeds[0].image:
                        constructed = await self.package(message.embeds[0].image.url)
                    if message.attachments:
                        await self.package(message.attachments[0].url)
                else:
                    break

        if constructed is None:  # No luck despite all this.
            embed = discord.Embed(title="No images were found.", color=16202876)
            await p_ctx.send(embed=embed)
            return None

        constructed.data.seek(0)  # just to be safe
        return constructed

    async def save_and_send(self, p_ctx, output, name, *args, **kwargs):
        # Saves an Image into a BytesIO buffer and sends it.
        # Extra args/ kwargs are passed to send.
        file_f = name.split('.')[1]
        buffer = BytesIO()        
        output.save(buffer, file_f, *args, **kwargs)
        buffer.seek(0)

        constructed_file = discord.File(fp=buffer, filename=name)
        embed = discord.Embed(color=16202876)
        embed.set_image(url=f"attachment://{name}")

        await p_ctx.send(file=constructed_file, embed=embed)

    @commands.command()
    async def blur(self, ctx, url=None):
        """Blur an image. Everyone has to start somewhwere."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        myimage = Image.open(result.data)
        im = myimage.convert("RGBA")
        output = im.filter(ImageFilter.GaussianBlur(10))

        await self.save_and_send(ctx, output, "blur.png")

    @commands.command()
    async def gay(self, ctx, url=None):
        """Unleash the powers of homosexuality on any image."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        gimage = await self.package(f"{root_directory}lobstero/data/static/gay.jpg", False)
        simage = Image.open(result.data)
        gim = Image.open(gimage.data).convert("RGBA")
        im = simage.convert("RGBA")

        width, height = im.size
        gim_p = gim.resize((width, height), Image.NEAREST)
        output = Image.blend(im, gim_p, 0.5)

        await self.save_and_send(ctx, output, "gay.png")

    @commands.command()
    async def fry(self, ctx, url=None):
        """Deep-frying, except not really."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        simage = Image.open(result.data)
        im = simage.convert("RGBA")
        output = im.filter(ImageFilter.UnsharpMask(radius=10, percent=450, threshold=2))

        await self.save_and_send(ctx, output, "gay.png")

    @commands.command()
    async def nom(self, ctx, url=None):
        """Eating is a fun and enjoyable activity."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        d_im = Image.open(result.data).convert("RGBA")
        owobase = await self.package(f"{root_directory}lobstero/data/static/blobowo.png", False)
        owotop = await self.package(f"{root_directory}lobstero/data/static/owoverlay.png", False)
        c_owobase = Image.open(owobase.data).convert("RGBA")
        c_owotop = Image.open(owotop.data).convert("RGBA")

        wpercent = (420 / float(d_im.size[0]))
        hsize = int((float(d_im.size[1]) * float(wpercent)))
        pd_im = d_im.resize((420, hsize), Image.ANTIALIAS)

        width, height = pd_im.size
        offset = (216, 528, 216 + int(width), 528 + int(height))
        offset2 = (0, 0, 1024, 1024)

        c_owobase.paste(pd_im, offset, pd_im)
        c_owobase.paste(c_owotop, offset2, c_owotop)

        await self.save_and_send(ctx, c_owobase, "nom.png")

    @commands.command()
    async def bless(self, ctx, url=None):
        """🛐🛐🛐"""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        blesstop = await self.package(f"{root_directory}lobstero/data/static/bless.png", False)
        im = Image.open(result.data).convert("RGBA")
        c_im = im.resize((1024, 1024), PIL.Image.ANTIALIAS)
        c_blesstop = Image.open(blesstop.data).convert("RGBA")

        c_im.paste(c_blesstop, (0, 0, 1024, 1024), c_blesstop)

        await self.save_and_send(ctx, c_im, "bless.png")

    @commands.command(name="asciify")
    async def asciify_command(self, ctx, url=None):
        """Turn an image into some spicy dots."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        opened = Image.open(result.data).convert("RGBA")
        colorlist = [
            "blue", "green", "red", "orange", "greenyellow", "lawngreen", "hotpink",
            "mediumturquoise", "mistyrose", "orangered"]

        bglist = ["black", "black"]
        asciified = asciify.asciiart(
            opened, 0.2, 1.5, ..., str(random.choice(colorlist)), 
            str(random.choice(colorlist)), str(random.choice(bglist)))

        await self.save_and_send(ctx, asciified, "ascii.png")

    @commands.command()
    async def xokify(self, ctx, url=None):
        """xok"""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        im = Image.open(result.data).convert("RGBA")
        c_im = im.resize((1024, 1024), PIL.Image.ANTIALIAS)
        converter = ImageEnhance.Color(c_im)
        mask = await self.package(f"{root_directory}lobstero/data/static/xok_mask.png", False)
        xok = await self.package(f"{root_directory}lobstero/data/static/xok.png", False)
        c_mask = Image.open(mask.data).convert("RGBA")
        c_xok = Image.open(xok.data).convert("RGBA")

        converted = converter.enhance(1.75)
        blended = Image.blend(c_xok, converted, 0.3)
        masked = Image.new('RGBA', (1024, 1024))
        masked.paste(blended, (0, 0, 1024, 1024), c_mask)

        await self.save_and_send(ctx, masked, "xokify.png")

    @commands.command()
    async def jpeg(self, ctx, url=None):
        """Ever wanted to make an image look terrible?"""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        d_im = Image.open(result.data).convert("CMYK")
        d_im.thumbnail((200, 200))
        await self.save_and_send(ctx, d_im, "jpegify.jpeg", quality=1)

    @commands.command()
    async def chromatic(self, ctx, url=None):
        """Fancy lens things!"""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        d_im = Image.open(result.data).convert("RGB")
        d_im.thumbnail((1024, 1024))
        if (d_im.size[0] % 2 == 0):
            d_im = d_im.crop((0, 0, d_im.size[0] - 1, d_im.size[1]))
            d_im.load()
        if (d_im.size[1] % 2 == 0):
            d_im = d_im.crop((0, 0, d_im.size[0], d_im.size[1] - 1))
            d_im.load()

        to_run = functools.partial(kromo.add_chromatic, d_im, strength=2, no_blur=True)
        final_im = await self.bot.loop.run_in_executor(None, to_run)

        await self.save_and_send(ctx, final_im, "chromatic.png")

    @commands.command()
    async def halftone(self, ctx, url=None):
        """Fancy depressive dots."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        im = Image.open(result.data)
        h = halftone.Halftone()
        output = h.make(im, style='grayscale', angles=[45], sample=16)
        await self.save_and_send(ctx, output, "halftone.png")

    def addzero(self, num):
        if len(str(num)) < 2:
            return "00" + str(num)
        if len(str(num)) < 3:
            return "0" + str(num)
        return str(num)

    @commands.command(enabled=False)
    async def wheelofban(self, ctx):
        """Spin the wheel of ban!"""

        waiting = discord.Embed(title="Spinning the wheel...", color=16202876)
        snt = await ctx.send(embed=waiting)
        files = glob.glob(f"{root_directory}image_downloads/wheel/*.png")

        banhandler = ban_conglomerate()

        for x in files:
            os.remove(x)

        wheel = Image.open(f"{root_directory}lobstero/data/static/wheel_of_ban.png").convert("RGBA").resize((512, 512), Image.ANTIALIAS)
        ban = Image.open(f"{root_directory}lobstero/data/static/ban_spin_top.png").convert("RGBA").resize((512, 512), Image.ANTIALIAS)
        ban_mask = Image.open(f"{root_directory}lobstero/data/static/transparentban.png").convert("RGBA")
        degrees, to_spin, frameid = 0, 9.9, 0

        for _ in range(random.randint(25, 175)):
            frameid += 1
            degrees += to_spin
            whl = wheel.rotate(degrees)
            whl.paste(ban, None, ban)
            out = banhandler.generate_frame(ban_mask)
            out.paste(whl, (63, 63), whl)
            out.save(f"{root_directory}image_downloads/wheel/img{self.addzero(frameid)}.png")
        for _ in range(70):

            frameid += 1
            to_spin = to_spin * 0.95
            degrees += to_spin
            whl = wheel.rotate(degrees)
            whl.paste(ban, None, ban)
            out = banhandler.generate_frame(ban_mask)
            out.paste(whl, (63, 63), whl)
            out.save(f"{root_directory}image_downloads/wheel/img{self.addzero(frameid)}.png")
        for _ in range(20):
            frameid += 1
            whl = wheel.rotate(degrees)
            whl.paste(ban, None, ban)
            out = banhandler.generate_frame(ban_mask)
            out.paste(whl, (63, 63), whl)
            out.save(f"{root_directory}image_downloads/wheel/img{self.addzero(frameid)}.png")
        
        files = glob.glob(f"{root_directory}image_downloads/wheel/*.png")

        with open(f"{root_directory}image_downloads/wheel/fileoutputs.txt", "w+") as writef:
            for x in files:
                path = "file '" + "img" + x.split("\img")[1] + "'\n"
                writef.write(path)

        os.system(r"C:\ffmpeg\bin\ffmpeg.exe" + r""" -y -r 30 -f concat -safe 0 -i """ + '"' + f"{root_directory}data/static/fileoutputs.txt" + '"' """ -c:v libx264 -vf "fps=30,format=yuv420p" """ + '"' +  root_directory + 'image_downloads/wheel/result.mp4"')

        done = discord.Embed(title="Judgement comes!", color=16202876)

        await ctx.send(file=discord.File(f"{root_directory}image_downloads/wheel/result.mp4"))
        await snt.edit(embed=done)

    def smooth_resize(self, img, basewidth=1000, method=Image.LANCZOS):
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        return img.resize((basewidth, hsize), method)

    @commands.command()
    async def mosaic(self, ctx, url=None):
        """Sqaure dance!"""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        d_im = Image.open(result.data).convert("RGBA")
        base = self.smooth_resize(d_im, 100, Image.NEAREST)
        c_base = base.convert("L").convert("RGBA")
        c_base = self.smooth_resize(d_im, int(base.size[0] / 8), Image.NEAREST)
        overlay = self.smooth_resize(base, base.size[0] * 10, Image.NEAREST)
        canvas = Image.new("RGBA", (overlay.size[0], overlay.size[1]))

        for w_pos in range(0, overlay.size[0] + 1, c_base.size[0]):
            for h_pos in range(0, overlay.size[1] + 1, c_base.size[1]):
                canvas.paste(c_base, (w_pos, h_pos), c_base)

        canvas = canvas.convert("L").convert("RGBA")
        final = Image.blend(canvas, overlay, 0.3)

        await self.save_and_send(ctx, final, "mosaic.png")

    @commands.command()
    async def quilt(self, ctx, url=None):
        """Jumbled squares."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        im = Image.open(result.data).convert("RGBA")
        im.thumbnail((4000, 4000))
        width, height = im.size
        new_im = im.resize((round(width, -1), round(height, -1)))
        width, height = new_im.size
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        width, height = int(width / 10), int(height / 10)
        positions = []

        for x in range(0, width * 10, width):
            for y in range(0, height * 10, height):
                dimensions = (x, y, x + width, y + height)
                positions.append(new_im.crop(dimensions))

        random.shuffle(positions)
        counter = 0
        for x in range(0, width * 10, width):
            for y in range(0, height * 10, height):
                canvas.paste(positions[counter], (x, y))
                counter += 1

        await self.save_and_send(ctx, canvas, "quilt.png")

    def make_meme(self, topString, bottomString, filename):

        img = Image.open(filename).convert("RGBA")

        wpercent = (2048/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((2048, hsize), Image.ANTIALIAS)

        imageSize = img.size    

        # find biggest font size that works
        fontSize = int(imageSize[1]/5)
        font = ImageFont.truetype(f"{root_directory}lobstero/data/static/impact.ttf", fontSize)
        topTextSize = font.getsize(topString)
        bottomTextSize = font.getsize(bottomString)
        while topTextSize[0] > imageSize[0]-20 or bottomTextSize[0] > imageSize[0]-20:
            fontSize = fontSize - 1
            font = ImageFont.truetype(f"{root_directory}lobstero/data/static/impact.ttf", fontSize)
            topTextSize = font.getsize(topString)
            bottomTextSize = font.getsize(bottomString)

        # find top centered position for top text
        topTextPositionX = (imageSize[0]/2) - (topTextSize[0]/2)
        topTextPositionY = 0
        topTextPosition = (topTextPositionX, topTextPositionY)

        # find bottom centered position for bottom text
        bottomTextPositionX = (imageSize[0]/2) - (bottomTextSize[0]/2)
        bottomTextPositionY = imageSize[1] - bottomTextSize[1]
        bottomTextPosition = (bottomTextPositionX, bottomTextPositionY)

        draw = ImageDraw.Draw(img)
        for x_p in range(-15, 15, 5):
            for y_p in range(-15, 15, 5):
                draw.text((topTextPositionX + x_p, topTextPositionY + y_p), topString, (0,0,0), font=font)
                draw.text((bottomTextPositionX + x_p, bottomTextPositionY + y_p), topString, (0,0,0), font=font)

        draw.text(topTextPosition, topString, (255, 255, 255), font=font)
        draw.text(bottomTextPosition, bottomString, (255, 255, 255), font=font)

        return img

    @commands.command()
    async def shitpost(self, ctx, url=None):
        """It's humour from the future!"""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        markov = await self.bot.markov_generator.generate()
        meme = self.make_meme(markov, markov, result.data)

        await self.save_and_send(ctx, meme, "shitpost.png")


def setup(bot):
    bot.add_cog(Cog(bot))
