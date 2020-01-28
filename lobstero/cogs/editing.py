import os
import random
import sys
import glob
import halftone
import discord
import kromo
import PIL
import asciify as acfy
import aiohttp

from io import BytesIO
from lobstero import lobstero_config
from lobstero.utils import strings
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
        if str(url).lower().endswith(".png"):
            finalurl = url.lower()
        if str(url).lower().endswith(".jpg"):
            finalurl = url.lower()
        if str(url).lower().endswith(".jpeg"):
            finalurl = f"{url[:-4]}jpg"
        return finalurl

    async def imgdownload(self, file_url):
        file_name = urlsplit(file_url)[2].split('/')[-1]
        file_ext = file_name.split(".", 1)[1]

        async with self.session.get(file_url) as resp:
            with open(f"{root_directory}data/downloaded/{file_name}", 'wb+') as f:
                f.write(await resp.read())

        return [f"{root_directory}data/downloaded/{file_name}", file_ext]

    async def processfile(self, p_ctx, url):
        filename = None
        if url is not None:
            if p_ctx.message.mentions:
                filename = await self.imgdownload(str(p_ctx.message.mentions[0].avatar_url))

            else:
                em = strings.split_count(url)
                if em:
                    escape = f"{ord(em[0]):X}"
                    filename = f"{root_directory}data/static/emojis/{escape}.png"

                elif url.startswith("<") and url.endswith(">"):
                    emo_id = url.split(":")[2].split(">")[0]
                    if not url.startswith("<a:"):
                        emourl = f"https:/cdn.discordapp.com/emojis/{emo_id}.png?v=1"
                    else:
                        emourl = f"https:/cdn.discordapp.com/emojis/{emo_id}.gif?v=1"
                    filename = await self.imgdownload(emourl)

                else:
                    filename = await self.imgdownload(url)

        elif url is None:
            if p_ctx.message.attachments:
                for x in p_ctx.message.attachments:
                    filename = await self.imgdownload(x.url)
        attachlist = []
        if filename is None:
            for message in await p_ctx.channel.history(limit=25).flatten():
                if message.embeds:
                    if not attachlist:
                        if message.embeds[0].image.url:
                            attachlist.append(message.embeds[0].image.url)
                if message.attachments:
                    if not attachlist:
                        attachlist.append(message.attachments[0].url)

        if attachlist:
            filename = await self.imgdownload(str(attachlist[0]))

        if filename is None:
            await p_ctx.send(embed=discord.Embed(title="No images were found.", color=16202876))
            return None
        else:
            return filename

    @commands.command()
    async def blur(self, ctx, url=None, amount=10):
        """Blur an image. Everyone has to start somewhwere."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        myimage = Image.open(str(result))
        im = myimage.convert("RGBA")
        output = im.filter(ImageFilter.GaussianBlur(int(amount)))
        output.save(f"{root_directory}data/downloaded/" + "blur_editoutput.png")

        buffer = BytesIO()
        output.save(buffer, "png")  # 'save' function for PIL, adapt as necessary
        buffer.seek(0)

        imgurl = await chn.send(file= discord.File(f"{root_directory}data/downloaded/" + "blur_editoutput.png"))
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
    
    @commands.command()
    async def gay(self, ctx, url = None):
        """Unleash the powers of homosexuality on any image."""
        result = await self.processfile(ctx, url)
        if result is None:
            return

        gimage = Image.open(root_directory + "data/images/gay.jpg")
        simage = Image.open(str(result))
        gim = gimage.convert("RGBA")
        im = simage.convert("RGBA")
        width, height = im.size
        gim_p = gim.resize((width, height), Image.NEAREST)
        result = Image.blend(im, gim_p, 0.5)
        result.save(f"{root_directory}data/downloaded/" + "gay_editoutput.png")
        imgurl = await chn.send(file= discord.File(f"{root_directory}data/downloaded/" + "gay_editoutput.png"))
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
    
    @commands.command()
    async def fry(self, ctx, url = None):
        """Deepfrying, except not really, and we forgot the oil. Mainly because it's not easily available in a python program. Heck."""
        result = await self.processfile(ctx, url)
        if result is None:
            return

        simage = Image.open(str(result))
        im = simage.convert("RGBA")
        result = im.filter(ImageFilter.UnsharpMask(radius = 10, percent = 450, threshold = 2))
        result.save(f"{root_directory}data/downloaded/" + "fry_editoutput.png")
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
    
    @commands.command()
    async def nom(self, ctx, url = None):
        """Eating is a fun and enjoyable activity."""
        prog = await ctx.send(embed=discord.Embed(title="Finding image... (1/4)", color=16202876))
        result = await self.processfile(ctx, url)
        if result is None:
            return

        size = 420, 420
        d_im = Image.open(str(result))
        pd_im = d_im.convert("RGBA")
        mywidth = 420
        wpercent = (mywidth/float(pd_im.size[0]))
        hsize = int((float(pd_im.size[1])*float(wpercent)))
        pd_im = pd_im.resize((mywidth,hsize), PIL.Image.ANTIALIAS)
        owobase = Image.open(root_directory + "data/images/blobowo.png")
        c_owobase = owobase.convert("RGBA")
        owotop = Image.open(root_directory + "data/images/owoverlay.png")
        c_owotop = owotop.convert("RGBA")
        width, height = pd_im.size
        offset = (216, 528, 216 + int(width), 528 + int(height))
        offset2 = (0, 0, 1024, 1024)
        c_owobase.paste(pd_im, offset, pd_im)
        c_owobase.paste(c_owotop, offset2, c_owotop)
        c_owobase.save(f"{root_directory}data/downloaded/" + "nom_editoutput.png")
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)

    @commands.command()
    async def bless(self, ctx, url = None):
        """🛐🛐🛐"""
        result = await self.processfile(ctx, url)
        if result is None:
            return

        im = Image.open(result)
        c_im = im.convert("RGBA")
        c_im = c_im.resize((1024,1024), PIL.Image.ANTIALIAS)
        blesstop = Image.open(root_directory + "data/images/bless.png")
        c_blesstop = blesstop.convert("RGBA")
        c_im.paste(c_blesstop, (0, 0, 1024, 1024), c_blesstop)
        c_im.save(f"{root_directory}data/downloaded/" + "bless_editoutput.png")
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
    
    @commands.command()
    async def asciify(self, ctx, url = None):
        """Turn an image into some spicy dots."""
        result = await self.processfile(ctx, url)
        if result is None:
            return

        colorlist = ["blue", "green", "red", "orange", "greenyellow", "lawngreen", "hotpink", "mediumturquoise", "mistyrose", "orangered"]
        bglist = ["black", "black"]
        acfy.asciiart(result, 0.2, 1.5, f"{root_directory}data/downloaded/" + "ascii_editoutput.png", str(random.choice(colorlist)), str(random.choice(colorlist)), str(random.choice(bglist)))
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)

    @commands.command()
    async def goblin(self, ctx, url = None):
        """Pull him out and BEAT HIM"""
        prog = await ctx.send(embed=discord.Embed(title="Finding image... (1/4)", color=16202876))
        result = await self.processfile(ctx, url)
        if result is None:
            return

        im = Image.open(result)
        c_im = im.convert("RGBA")
        c_im = c_im.resize((1024,1024), PIL.Image.ANTIALIAS)
        goblintop = Image.open(root_directory + "data/images/goblin.png")
        c_goblintop = goblintop.convert("RGBA")
        c_im.paste(c_goblintop, (0, 0, 1024, 1024), c_goblintop)
        c_im.save(f"{root_directory}data/downloaded/" + "goblin_editoutput.png")
        await prog.edit(embed=discord.Embed(title="Uploading... (3/4)", color=16202876))
        imgurl = await chn.send(file= discord.File(f"{root_directory}data/downloaded/" + "goblin_editoutput.png"))
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
        await prog.edit(embed=finalembed)
    
    @commands.command()
    async def xokify(self, ctx, url = None):
        """xok"""
        result = await self.processfile(ctx, url)
        if result is None:
            return

        im = Image.open(result)
        c_im = im.convert("RGBA")
        c_im = c_im.resize((1024,1024), PIL.Image.ANTIALIAS)
        converter = ImageEnhance.Color(c_im)
        img4455 = converter.enhance(1.75)
        mask = Image.open(root_directory + "data/images/xok_mask.png")
        c_mask = mask.convert("RGBA")
        xok = Image.open(root_directory + "data/images/xok.png")
        xok = xok.convert("RGBA")
        result = Image.blend(xok, img4455, 0.3)
        fuckpillow = Image.new('RGBA', (1024, 1024))
        fuckpillow.paste(result, (0, 0, 1024, 1024), c_mask)
        fuckpillow.save(root_directory + "image_downloads/xokify_editoutput.png")
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)

    @commands.command()
    async def jpeg(self, ctx, url = None):
        """Ever wanted to make an image look terrible?"""
        prog = await ctx.send(embed=discord.Embed(title="Finding image... (1/4)", color=16202876))
        result = await self.processfile(ctx, url)
        if result is None:
            return

        d_im = Image.open(str(result)).convert("CMYK")
        d_im.thumbnail((200, 200))
        d_im.save(root_directory + "image_downloads/jpeg_editoutput.jpg", format='JPEG', quality=1)
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
    
    @commands.command()
    async def chromatic(self, ctx, url = None):
        """Fancy lens things!"""
        result = await self.processfile(ctx, url)
        if result is None:
            return

        d_im = Image.open(str(result)).convert("RGB")
        d_im.thumbnail((1024, 1024))
        if (d_im.size[0] % 2 == 0):
            d_im = d_im.crop((0, 0, d_im.size[0] - 1, d_im.size[1]))
            d_im.load()
        if (d_im.size[1] % 2 == 0):
            d_im = d_im.crop((0, 0, d_im.size[0], d_im.size[1] - 1))
            d_im.load()
        final_im = kromo.add_chromatic(d_im, strength=4, no_blur=False)
        final_im.save(root_directory + "image_downloads/chromatic_editoutput.png")
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
    
    @commands.command()
    async def halftone(self, ctx, url = None):
        """Fancy depressive dots."""
        result = await self.processfile(ctx, url)
        if result is None:
            return

        h = halftone.Halftone(result)
        h.make(style='grayscale', angles= [45], sample = 16)
        imgurl = await chn.send(file= discord.File(result.split(".")[0] + "_halftoned." + result.split(".")[1]))
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
    
    def addzero(self, num):

        if len(str(num)) < 2:
            return "00" + str(num)
        if len(str(num)) < 3:
            return "0" + str(num)
        return str(num)

    @commands.command()
    async def wheelofban(self, ctx):
        """Spin the wheel of ban!"""
        waiting = discord.Embed(title="Spinning the wheel...", color=16202876)
        snt = await ctx.send(embed=waiting)
        files = glob.glob(f"{root_directory}image_downloads/wheel/*.png")

        banhandler = ban_conglomerate()

        for x in files:
            os.remove(x)

        wheel = Image.open(f"{root_directory}data/images/wheel_of_ban.png").convert("RGBA").resize((512, 512), Image.ANTIALIAS)
        ban = Image.open(f"{root_directory}data/images/ban_spin_top.png").convert("RGBA").resize((512, 512), Image.ANTIALIAS)
        ban_trans = Image.open(f"{root_directory}data/images/transparentban.png").convert("RGBA")
        degrees, to_spin, frameid = 0, 9.9, 0

        for _ in range(random.randint(25, 175)):
            frameid += 1
            degrees += to_spin
            whl = wheel.rotate(degrees)
            whl.paste(ban, None, ban)
            out = banhandler.generate_frame(ban_trans)
            out.paste(whl, (63, 63), whl)
            out.save(f"{root_directory}image_downloads/wheel/img{self.addzero(frameid)}.png")
        for _ in range(70):

            frameid += 1
            to_spin = to_spin * 0.95
            degrees += to_spin
            whl = wheel.rotate(degrees)
            whl.paste(ban, None, ban)
            out = banhandler.generate_frame(ban_trans)
            out.paste(whl, (63, 63), whl)
            out.save(f"{root_directory}image_downloads/wheel/img{self.addzero(frameid)}.png")
        for _ in range(20):
            frameid += 1
            whl = wheel.rotate(degrees)
            whl.paste(ban, None, ban)
            out = banhandler.generate_frame(ban_trans)
            out.paste(whl, (63, 63), whl)
            out.save(f"{root_directory}image_downloads/wheel/img{self.addzero(frameid)}.png")
        
        files = glob.glob(f"{root_directory}image_downloads/wheel/*.png")

        with open(f"{root_directory}image_downloads/wheel/fileoutputs.txt", "w+") as writef:
            for x in files:
                path = "file '" + "img" + x.split("\img")[1] + "'\n"
                writef.write(path)

        os.system(r"C:\ffmpeg\bin\ffmpeg.exe" + r""" -y -r 30 -f concat -safe 0 -i """ + '"' + f"{root_directory}image_downloads/wheel/fileoutputs.txt" + '"' """ -c:v libx264 -vf "fps=30,format=yuv420p" """ + '"' +  root_directory + 'image_downloads/wheel/result.mp4"')
        
        
        done = discord.Embed(title="Judgement comes!", color=16202876)

        await ctx.send(file=discord.File(f"{root_directory}image_downloads/wheel/result.mp4"))
        await snt.edit(embed=done)

    def smooth_resize(self, img, basewidth = 1000, method = Image.LANCZOS):
        wpercent = (basewidth/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        return img.resize((basewidth, hsize), method)

    @commands.command()
    async def mosaic(self, ctx, url = None):
        """Sqaure dance!"""
        prog = await ctx.send(embed=discord.Embed(title="Finding image... (1/4)", color=16202876))
        result = await self.processfile(ctx, url)
        if result is None:
            return

        await prog.edit(embed=discord.Embed(title="Processing... (2/4)", color=16202876))
        
        d_im = Image.open(str(result)).convert("RGBA")
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
        final.save(root_directory + "image_downloads/mosaic_editoutput.png")
        await prog.edit(embed=discord.Embed(title="Uploading... (3/4)", color=16202876))
        imgurl = await chn.send(file= discord.File(root_directory + "image_downloads/mosaic_editoutput.png"))
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
        await prog.edit(embed=finalembed)
    
    def make_meme(self, topString, bottomString, filename):

        img = Image.open(filename).convert("RGBA")
        
        wpercent = (2048/float(img.size[0]))
        hsize = int((float(img.size[1])*float(wpercent)))
        img = img.resize((2048,hsize), Image.ANTIALIAS)
        
        imageSize = img.size    

        # find biggest font size that works
        fontSize = int(imageSize[1]/5)
        font = ImageFont.truetype(f"{root_directory}data/fonts/impact.ttf", fontSize)
        topTextSize = font.getsize(topString)
        bottomTextSize = font.getsize(bottomString)
        while topTextSize[0] > imageSize[0]-20 or bottomTextSize[0] > imageSize[0]-20:
            fontSize = fontSize - 1
            font = ImageFont.truetype(f"{root_directory}data/fonts/impact.ttf", fontSize)
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

        draw.text(topTextPosition, topString, (255,255,255), font=font)
        draw.text(bottomTextPosition, bottomString, (255,255,255), font=font)

        img.save(f"{root_directory}image_downloads/shitpostgen_editoutput.png")

    @commands.command()
    async def shitpost(self, ctx, url = None):
        """It's humour from the future!"""
        prog = await ctx.send(embed=discord.Embed(title="Finding image... (1/4)", color=16202876))
        result = await self.processfile(ctx, url)
        if result is None:
            return

        await prog.edit(embed=discord.Embed(title="Processing... (2/4)", color=16202876))
        retrieved = self.client.get_cog("Miscellaneous").get_commands()
        mapped = {x.name : x for x in retrieved}
        c = mapped["invoked_markov"]
        t = await ctx.invoke(c)
        self.make_meme(t, t, result)
        await prog.edit(embed=discord.Embed(title="Uploading... (3/4)", color=16202876))
        imgurl = await chn.send(file= discord.File(root_directory + "image_downloads/shitpostgen_editoutput.png"))
        finalembed = discord.Embed(title="Complete! (4/4)", color=16202876)
        finalembed.set_image(url=imgurl.attachments[0].url)
        await prog.edit(embed=finalembed)

def setup(bot):
    bot.add_cog(Cog(bot))