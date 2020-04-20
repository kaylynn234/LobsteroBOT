import functools
import inspect
import random
import sys
import io
import time

import numpy
import cv2
import numpy as np
import discord
import PIL
import aiohttp

from itertools import chain

from scipy.io import wavfile
from unittest import mock
from io import BytesIO
from lobstero import lobstero_config
from lobstero.utils import strings
from lobstero.models import handlers
from lobstero.external import asciify, kromo, halftone
from urllib.parse import urlsplit
from PIL import ImageFilter, ImageFont, Image, ImageDraw, ImageEnhance
from discord.ext import commands
from jishaku.functools import executor_function
from jishaku.codeblocks import codeblock_converter

root_directory = sys.path[0] + "/"
lc = lobstero_config.LobsteroCredentials()


class ImageScriptException(Exception):
    """The base error for all Imagescript-related errors.
    You should never see this. Hopefully."""


class UnknownOperationException(ImageScriptException):
    """An UnknownOperationException error is raised when you attempt to do something that Lobstero doesn't understand.
    For example, the Imagescript code ``blurr();`` would produce this error, as there is no ``blurr`` operation.

    Check your spelling!
    The Imagescript manual has more in-depth information on the basics."""


class BadInputException(ImageScriptException):
    """A BadInputException error is raised when you try to perform an operation with the wrong kind of data.
    It can be raised if:
    - The image you provide is too small.
    - You use an argument with a word or letter instead of a number.
    - You try to use an argument that an operation does not support.

    For example:
    - the Imagescript code ``blur(amount: hello world);`` would produce this error, because the ``amount`` argument should be a number.
    - the Imagescript code ``blur(strength: 10);`` would produce this error, because the ``blur`` operation has no ``strength`` argument.

    Double-check what you're doing!"""


class TooMuchToDoException(ImageScriptException):
    """A TooMuchToDoException error should be fairly self-explanatory.
    Try doing less things at once!"""


class BadSyntaxException(ImageScriptException):
    """A BadSyntaxException error is raised when Lobstero doesn't understand the code you try to run.
    This can be raised if:
    - You put too many brackets in your code.
    - You forget a semicolon between operations.

    Double-check what you're doing!
    The Imagescript manual has more in-depth information on the basics."""


class MissingBracketsException(BadSyntaxException):
    """A MissingBracketsException error is raised when your code has no brackets.
    Brackets are needed after each operation - this is so that potential arguments can be specified within them.
    You still need a pair of brackets after an operation, even if the operation takes no arguments.

    Double-check what you're doing!"""


class MissingColonException(BadSyntaxException):
    """A MissingColonException error should be fairly self-explanatory.
    When giving arguments to an operation, make sure that they're arranged in ``argument: value`` pairs.

    Double-check what you're doing!
    The Imagescript manual has more in-depth information on the basics."""


class MissingSemicolonException(BadSyntaxException):
    """A MissingBracketsException error is raised when your code has no semicolons.
    A semicolon is needed after each operation - this is to concisely break them up so that they aren't clustered together.

    Double-check what you're doing!
    The Imagescript manual has more in-depth information on the basics."""


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
    """Edit images. Almost all commands in this module will take an ``Image`` parameter.

You can either:
- attach the image to the message you send the command in
- @mention a user to use their profile picture
- use a custom emoji
- or pass it using a URL when using the command
If you don't do any of that, Lobstero will search the previous few messages for an image."""
    def __init__(self, bot):
        self.bot = bot
        self.session = bot.session

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
                em = list(chain(*strings.split_count(url)))

                if em:
                    escape = "-".join([f"{ord(e):X}" for e in em]).lower()
                    constructed = await self.package(
                        f"{root_directory}data/static/emojis/{escape}.png", False)

                c = commands.PartialEmojiConverter()
                try:
                    em = list(chain(*strings.split_count(url)))
                    if not em:
                        e = await c.convert(p_ctx, url)
                except commands.BadArgument:  # Emoji lookup failed, assume it's a URL and pray
                    constructed = await self.package(url)
                else:  # Emoji lookup was a success
                    if em:
                        escape = "-".join([f"{ord(e):X}" for e in em]).lower()
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

    async def save_and_send(self, p_ctx, output, name, elapsed=None, *args, **kwargs):
        # Saves an Image into a BytesIO buffer and sends it.
        # Extra args/ kwargs are passed to save.
        file_f = name.split('.')[1]
        buffer = BytesIO()
        output.save(buffer, file_f, *args, **kwargs)
        buffer.seek(0)

        constructed_file = discord.File(fp=buffer, filename=name)
        embed = discord.Embed(color=16202876)
        embed.set_image(url=f"attachment://{name}")
        embed.description = elapsed

        await p_ctx.send(file=constructed_file, embed=embed)

    async def save_for_next_step(self, p_ctx, output, name, *args, **kwargs):
        # Saves an Image into a BytesIO buffer. This is an intermediary thing.
        # Extra args/ kwargs are passed to save.
        file_name, file_f = name.split('.')
        buffer = BytesIO()
        output.save(buffer, file_f, *args, **kwargs)
        buffer.seek(0)

        f_obj = mock.Mock()
        f_obj.data, f_obj.name, f_obj.ext = buffer, file_name, file_f

        return f_obj

    async def process_single(self, op, ctx, url):
        result = await self.processfile(ctx, url)
        if result is None:
            return

        to_do = getattr(self, f"image_do_{op}")

        # ugly, will fix later
        try:
            processed = list(await to_do(result))
        except ImageScriptException as e:
            return await ctx.send(str(e))

        if len(processed) == 2:
            processed.append({})

        await self.save_and_send(ctx, processed[0], processed[1], **processed[2])

    async def imagescript_run(self, ctx, input_code, provided_image):
        if not input_code:
            raise ImageScriptException("No code to run!")

        if ";" not in input_code:
            raise MissingSemicolonException("Missing semicolon!")

        start = time.time()
        current_image = provided_image
        chunked_code = input_code.strip("\r\n\u200b.}{][").split(";")
        cleaned_chunks = list(filter(None, chunked_code))

        if len(cleaned_chunks) > 15:
            raise TooMuchToDoException(f"Only 15 operations are allowed at once. You tried to do {len(cleaned_chunks)}")

        for current_step, chunk in enumerate(cleaned_chunks, start=1):
            if not ("(" in chunk or ")" in chunk):
                raise MissingBracketsException("No brackets present!", current_step)

            try:
                function_body, function_args = chunk.strip(") ").split("(")
            except ValueError:
                raise BadSyntaxException("Too many brackets for one operation!", current_step)

            op_to_run = getattr(self, f"image_do_{function_body}", None)
            if op_to_run is None:
                raise UnknownOperationException(f"Operation {function_body} does not exist!", current_step)

            if function_args.strip():
                try:
                    arguments = {arg.split(":")[0]: arg.split(":")[1] for arg in function_args.split(",")}
                except (ValueError, IndexError):
                    raise MissingColonException("No colon to denote argument value!", current_step)
            else:
                arguments = {}

            try:
                arguments = {key: int(value) for key, value in arguments.items()}
            except ValueError:
                raise BadInputException("Argument must be a number, not a word or letter!", current_step)

            try:
                results = await op_to_run(current_image, **arguments)
            except TypeError:
                raise BadInputException(f"Provided arguments are not valid for operation {function_body}", current_step)

            processed = list(results)
            if len(processed) == 2:
                processed.append({})

            if current_step != len(cleaned_chunks):
                current_image = await self.save_for_next_step(ctx, processed[0], processed[1], **processed[2])
            else:
                completion = time.time()
                time_taken = f"Completed {len(cleaned_chunks)} operation(s) in {round(completion - start, 2)} seconds."
                await self.save_and_send(ctx, processed[0], processed[1], elapsed=time_taken, **processed[2])

    @executor_function
    def image_do_blur(self, result, amount=10):
        myimage = Image.open(result.data)
        im = myimage.convert("RGBA")
        output = im.filter(ImageFilter.GaussianBlur(amount))

        return output, "blur.png"

    @executor_function
    def image_do_gay(self, result):
        simage = Image.open(result.data)
        gim = Image.open(f"{root_directory}lobstero/data/static/gay.jpg").convert("RGBA")
        im = simage.convert("RGBA")

        width, height = im.size
        gim_p = gim.resize((width, height), Image.NEAREST)
        output = Image.blend(im, gim_p, 0.5)

        return output, "gay.png"

    @executor_function
    def image_do_fry(self, result, amount=2):
        simage = Image.open(result.data)
        im = simage.convert("RGBA")
        output = im.filter(ImageFilter.UnsharpMask(radius=10, percent=450, threshold=amount))

        return output, "fry.png"

    @executor_function
    def image_do_nom(self, result):
        d_im = Image.open(result.data).convert("RGBA")

        c_owobase = Image.open(f"{root_directory}lobstero/data/static/blobowo.png").convert("RGBA")
        c_owotop = Image.open(f"{root_directory}lobstero/data/static/owoverlay.png").convert("RGBA")

        wpercent = (420 / float(d_im.size[0]))
        hsize = int((float(d_im.size[1]) * float(wpercent)))
        pd_im = d_im.resize((420, hsize), Image.ANTIALIAS)

        width, height = pd_im.size
        offset = (216, 528, 216 + int(width), 528 + int(height))
        offset2 = (0, 0, 1024, 1024)

        c_owobase.paste(pd_im, offset, pd_im)
        c_owobase.paste(c_owotop, offset2, c_owotop)

        return c_owobase, "nom.png"

    @executor_function
    def image_do_bless(self, result):
        im = Image.open(result.data).convert("RGBA")
        c_im = im.resize((1024, 1024), PIL.Image.ANTIALIAS)
        c_blesstop = Image.open(f"{root_directory}lobstero/data/static/bless.png").convert("RGBA")

        c_im.paste(c_blesstop, (0, 0, 1024, 1024), c_blesstop)

        return c_im, "bless.png"

    @executor_function
    def image_do_asciify(self, result):
        opened = Image.open(result.data).convert("RGBA")
        colorlist = [
            "blue", "green", "red", "orange", "greenyellow", "lawngreen", "hotpink",
            "mediumturquoise", "mistyrose", "orangered"]

        bglist = ["black", "black"]
        asciified = asciify.asciiart(
            opened, 0.2, 1.5, ..., str(random.choice(colorlist)),
            str(random.choice(colorlist)), str(random.choice(bglist)))

        return asciified, "ascii.png"

    @executor_function
    def image_do_xokify(self, result):
        im = Image.open(result.data).convert("RGBA")
        c_im = im.resize((1024, 1024), PIL.Image.ANTIALIAS)
        converter = ImageEnhance.Color(c_im)
        c_mask = Image.open(f"{root_directory}lobstero/data/static/xok_mask.png").convert("RGBA")
        c_xok = Image.open(f"{root_directory}lobstero/data/static/xok.png").convert("RGBA")

        converted = converter.enhance(1.75)
        blended = Image.blend(c_xok, converted, 0.3)
        masked = Image.new('RGBA', (1024, 1024))
        masked.paste(blended, (0, 0, 1024, 1024), c_mask)

        return masked, "xok.png"

    @executor_function
    def image_do_jpeg(self, result, quality=1):
        d_im = Image.open(result.data).convert("CMYK")
        d_im.thumbnail((200, 200))

        return d_im, "jpegify.jpeg", {"quality": quality}

    @executor_function
    def image_do_chromatic(self, result, strength=2):
        d_im = Image.open(result.data).convert("RGB")
        d_im.thumbnail((1024, 1024))
        if (d_im.size[0] % 2 == 0):
            d_im = d_im.crop((0, 0, d_im.size[0] - 1, d_im.size[1]))
            d_im.load()
        if (d_im.size[1] % 2 == 0):
            d_im = d_im.crop((0, 0, d_im.size[0], d_im.size[1] - 1))
            d_im.load()

        final_im = kromo.add_chromatic(d_im, strength=strength, no_blur=True)

        return final_im, "chromatic.png"

    @executor_function
    def image_do_halftone(self, result):
        im = Image.open(result.data)
        h = halftone.Halftone()
        output = h.make(im, style='grayscale', angles=[45], sample=16)

        return output, "halftone.png"

    def addzero(self, num):
        if len(str(num)) < 2:
            return "00" + str(num)
        if len(str(num)) < 3:
            return "0" + str(num)

        return str(num)

    def package_for_opencv(self, wheel, degrees, ban, ban_mask, banhandler):
        whl = wheel.rotate(degrees)
        whl.paste(ban, None, ban)
        out = banhandler.generate_frame(ban_mask)
        out.paste(whl, (63, 63), whl)

        buffer = BytesIO()
        out.save(buffer, "png")
        buffer.seek(0)

        imgstr = buffer.read()
        nparr = np.fromstring(imgstr, np.uint8)
        converted = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        return converted

    def produce_video(self, frames):
        writer = cv2.VideoWriter(
            f"{root_directory}lobstero/data/generated/wheelofban.webm",
            cv2.VideoWriter_fourcc(*"VP90"), 30, (640, 640))

        for frame in frames:
            writer.write(frame)

        writer.release()

    def smooth_resize(self, img, basewidth=1000, method=Image.LANCZOS):
        wpercent = (basewidth / float(img.size[0]))
        hsize = int((float(img.size[1]) * float(wpercent)))

        return img.resize((basewidth, hsize), method)

    @executor_function
    def image_do_mosaic(self, result):
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
        output = Image.blend(canvas, overlay, 0.3)

        return output, "mosaic.png"

    @executor_function
    def image_do_quilt(self, result, squares="random"):
        im = Image.open(result.data).convert("RGBA")
        im.thumbnail((4000, 4000))
        width, height = im.size
        if width <= 50 or height <= 50:
            raise BadInputException("Image too small!")

        if squares == "random":
            divisor = random.choice([2, 4, 5, 10])
        else:
            if squares not in [2, 4, 5, 10]:
                raise BadInputException(f"Squares value must be either 2, 4, 5 or 10. {squares} provided.")
            divisor = squares

        new_im = im.resize((round(width, -1), round(height, -1)))
        width, height = new_im.size
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        width, height = int(width / divisor), int(height / divisor)
        positions = []

        for x in range(0, width * divisor, width):
            for y in range(0, height * divisor, height):
                dimensions = (x, y, x + width, y + height)
                positions.append(new_im.crop(dimensions))

        random.shuffle(positions)
        counter = 0
        for x in range(0, width * divisor, width):
            for y in range(0, height * divisor, height):
                canvas.paste(positions[counter], (x, y))
                counter += 1

        return canvas, "quilt.png"

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
                draw.text((topTextPositionX + x_p, topTextPositionY + y_p), topString, (0, 0, 0), font=font)
                draw.text((bottomTextPositionX + x_p, bottomTextPositionY + y_p), topString, (0, 0, 0), font=font)

        draw.text(topTextPosition, topString, (255, 255, 255), font=font)
        draw.text(bottomTextPosition, bottomString, (255, 255, 255), font=font)

        return img

    @executor_function
    def image_do_triangulate(self, result):
        im = Image.open(result.data).convert("RGBA")
        if im.size[0] < 20 or im.size[1] < 20:
            raise BadInputException("Image too small!")

        im.thumbnail((20, 20))
        width, height = im.size
        canvas = Image.new("RGBA", (width * 20, height * 20), (0, 0, 0, 0))
        arr = numpy.array(im)
        draw = ImageDraw.Draw(canvas)

        every_first = arr[::1, ::1]
        every_second = arr[1::1, 1::1]

        for row_index, (row1, row2) in enumerate(zip(every_first, every_second)):
            for column_index, (color1, color2) in enumerate(zip(row1, row2)):
                color1 = tuple(color1)  # fuck numpy
                color2 = tuple(color2)  # PIL too

                draw.polygon(
                    (
                        (row_index * 20, column_index * 20 + 20),  # bottom left
                        (row_index * 20, column_index * 20),  # top left
                        (row_index * 20 + 20, column_index * 20)  # top right
                    ),
                    fill=color1)

                draw.polygon(
                    (
                        (row_index * 20, column_index * 20 + 20),  # bottom left
                        (row_index * 20 + 20, column_index * 20 + 20),  # bottom right
                        (row_index * 20 + 20, column_index * 20)  # top right
                    ),
                    fill=color2)

        output = canvas.rotate(-90).transpose(Image.FLIP_LEFT_RIGHT)
        return output, "triangulate.png"

    @executor_function
    def image_do_stringify(self, result):
        im = Image.open(result.data).convert("L")
        if im.size[0] < 20 or im.size[1] < 20:
            raise BadInputException("Image too small!")

        im.thumbnail((20, 20))
        brightest = int((sorted(numpy.array(im).flatten(), reverse=True)[0] / 255) * 100)
        width, height = im.size
        canvas = Image.new("L", (width * 99, height * 100))
        arr = numpy.flipud(numpy.rot90(numpy.array(im)))
        draw = ImageDraw.Draw(canvas)

        every_first = arr[::1, ::1]
        every_second = arr[1::1, ::1]

        for row_index, (row1, row2) in enumerate(zip(every_first, every_second)):
            for column_index, (color1, color2) in enumerate(zip(row1, row2)):
                height1 = (int((color1 / 255) * 100) * 100) / brightest
                height2 = (int((color2 / 255) * 100) * 100) / brightest

                for offset in range(3):
                    draw.line(
                        (
                            (row_index * 100, column_index * 100 + height1 + offset),
                            (row_index * 100 + 100, column_index * 100 + height2 + offset)
                        ),
                        fill="white", width=4, joint="curve")

        return canvas, "stringify.png"

    @executor_function
    def image_do_glitch(self, result, max_times=40):
        im = Image.open(result.data).convert("RGB")
        for _ in range(random.randint(20, max_times)):
            random_slice_y = random.randint(1, im.size[1] - 1)
            sliced = im.crop((0, random_slice_y, im.size[0], random_slice_y + 1))
            starting_position = random.randint(1, im.size[1] - 1)

            for i in range(random.randint(12, 20)):
                im.paste(sliced, (0, starting_position + i))

        return im, "glitch.png"

    @executor_function
    def image_do_tunnelvision(self, result):
        im = Image.open(result.data).convert("RGB")
        for i, _ in enumerate(range(random.randint(30, 60))):
            m = float(f"0.{100 - i}")
            new_x = int(im.size[0] * m)
            new_y = int(im.size[1] * m)

            to_stamp = im.resize((new_x, new_y))
            position = (
                int(im.size[0] / 2 - to_stamp.size[0] / 2) + random.randint(-3, 3),
                int(im.size[1] / 2 - to_stamp.size[1] / 2) + random.randint(-3, 3)
            )

            im.paste(to_stamp, position)

        return im, "tunnel.png"

    @commands.command()
    @handlers.blueprints_or()
    async def tunnelvision(self, ctx, url=None):
        """Far away!"""

        await self.process_single("tunnelvision", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def glitch(self, ctx, url=None):
        """Ruin an image"""

        await self.process_single("glitch", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def triangulate(self, ctx, url=None):
        """Fits an image into a cool-looking pattern"""

        await self.process_single("triangulate", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def stringify(self, ctx, url=None):
        """Make an image look like a joy division album cover"""

        await self.process_single("stringify", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def quilt(self, ctx, url=None):
        """Jumbled squares."""

        await self.process_single("quilt", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def mosaic(self, ctx, url=None):
        """Sqaure dance!"""

        await self.process_single("mosaic", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def halftone(self, ctx, url=None):
        """Fancy depressive dots."""

        await self.process_single("halftone", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def chromatic(self, ctx, url=None):
        """Fancy lens things!"""

        await self.process_single("chromatic", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def xokify(self, ctx, url=None):
        """xok"""

        await self.process_single("xokify", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def jpeg(self, ctx, url=None):
        """Ever wanted to make an image look terrible?"""

        await self.process_single("jpeg", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def blur(self, ctx, url=None):
        """Blur an image. Everyone has to start somewhwere."""

        await self.process_single("blur", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def fry(self, ctx, url=None):
        """Deep-frying, except not really."""

        await self.process_single("fry", ctx, url)

    @commands.command(name="asciify")
    @handlers.blueprints_or()
    async def asciify_command(self, ctx, url=None):
        """Turn an image into some spicy dots."""

        await self.process_single("asciify", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def gay(self, ctx, url=None):
        """Unleash the powers of homosexuality on any image."""

        await self.process_single("gay", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def bless(self, ctx, url=None):
        """🛐🛐🛐"""

        await self.process_single("bless", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def nom(self, ctx, url=None):
        """Eating is a fun and enjoyable activity."""

        await self.process_single("nom", ctx, url)

    @commands.command()
    @handlers.blueprints_or()
    async def shitpost(self, ctx, url=None):
        """It's humour from the future!"""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        markov = await self.bot.markov_generator.generate()
        meme = self.make_meme(markov, markov, result.data)

        await self.save_and_send(ctx, meme, "shitpost.png")

    @commands.command()
    @handlers.blueprints_or()
    async def audioimage(self, ctx, url=None):
        """Turn an image into audio."""

        result = await self.processfile(ctx, url)
        if result is None:
            return

        im = Image.open(result.data).convert("L")
        im.thumbnail((200, 200))
        buffer = BytesIO()
        arr = numpy.array(im, dtype=numpy.int8)
        new = []
        for i in range(arr.shape[1]):
            try:
                new.extend(list(arr[i]))
            except IndexError:
                break
                # in theory this /should/ be fine, but there's some strangeness with PIL / numpy / my code
                # that breaks the last item if the file is of a certain type, not sure why
                # shit's wack yo

        to_write = numpy.array(new, dtype=numpy.int8)
        wavfile.write(buffer, 10000, to_write)
        constructed_file = discord.File(fp=buffer, filename="audioimage.wav")

        await ctx.send(file=constructed_file)

    @commands.command()
    @handlers.blueprints_or()
    async def wheelofban(self, ctx):
        """Spin the wheel of ban!"""

        waiting = discord.Embed(title="Spinning the wheel...", color=16202876)
        snt = await ctx.send(embed=waiting)

        banhandler = ban_conglomerate()
        wheel = Image.open(f"{root_directory}lobstero/data/static/wheel_of_ban.png")
        wheel = wheel.convert("RGBA").resize((512, 512), Image.ANTIALIAS)
        ban = Image.open(f"{root_directory}lobstero/data/static/ban_spin_top.png")
        ban = ban.convert("RGBA").resize((512, 512), Image.ANTIALIAS)
        ban_mask = Image.open(f"{root_directory}lobstero/data/static/transparentban.png").convert("RGBA")
        degrees, to_spin, frameid = 0, 9.9, 0
        frames = []  # what could possibly go wrong

        for _ in range(random.randint(25, 175)):
            frameid += 1
            degrees += to_spin
            frames.append(self.package_for_opencv(wheel, degrees, ban, ban_mask, banhandler))

        for _ in range(70):
            frameid += 1
            to_spin = to_spin * 0.95
            degrees += to_spin
            frames.append(self.package_for_opencv(wheel, degrees, ban, ban_mask, banhandler))

        for _ in range(20):
            frameid += 1
            frames.append(self.package_for_opencv(wheel, degrees, ban, ban_mask, banhandler))

        to_run = functools.partial(self.produce_video, frames)
        await self.bot.loop.run_in_executor(None, to_run)

        done = discord.Embed(title="Judgement comes!", color=16202876)
        await ctx.send(file=discord.File(f"{root_directory}lobstero/data/generated/wheelofban.webm"))
        await snt.edit(embed=done)

    @commands.command()
    @handlers.blueprints_or()
    async def imagescript(self, ctx, *, url_and_code):
        """Runs code for Lobstero's Imagescript scripting language.
        At the moment, this is very poorly documented and still a WIP. It will be expanded upon later."""
        url = None
        code = url_and_code
        image = None

        if " " in url_and_code:
            split = url_and_code.split()
            if ";" not in split[0]:
                url = split[0]
                code = " ".join(split[1:])

        try:
            image = await self.processfile(ctx, url)
        except (commands.BadArgument, IndexError):  # conversion failed
            code = url_and_code
            await ctx.simple_embed(f"No images matching \"{url}\" were found.")

        if image is None:
            return

        cleaned = codeblock_converter(code)

        try:
            await self.imagescript_run(ctx, cleaned.content, image)
        except ImageScriptException as e:
            embed = discord.Embed(color=16202876, title="Something went wrong")
            embed.description = f"```{type(e).__name__}: {e.args[0]}```\n"
            if len(e.args) > 1:  # TODO: not this
                embed.description += f"This happened during line/ operation {e.args[1]}.\n"

            embed.description += inspect.getdoc(e)
            await ctx.send(embed=embed)

    @commands.command(aliases=["tti", "t2i", "texttoimage"], enabled=False)
    @commands.cooldown(3, 60, commands.BucketType.user)
    @handlers.blueprints_or()
    async def text2image(self, ctx, *, text):
        """Turn some text into an image with the power of AI."""
        data = {"text": text}
        headers = {"api-key": lc.auth.deepai_key}
        async with self.session.post("https://api.deepai.org/api/text2img", data=data, headers=headers) as resp:
            response_json = await resp.json()

        if response_json.get("output_url", None):
            embed = discord.Embed(color=16202876)
            embed.set_image(url=response_json["output_url"])
            await ctx.send(embed=embed)
        else:
            await ctx.simple_embed("The AI gave no result! This is probably an issue with it, and not you. Slow down!")


def setup(bot):
    bot.add_cog(Cog(bot))
