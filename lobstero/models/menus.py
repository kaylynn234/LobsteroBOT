"""I heard you liked ext.menus  """

import asyncio

import pendulum
import discord
from discord.ext import menus 
from lobstero.models import games


class ListEmbedMenu(menus.ListPageSource):
    """A simple menu class for paginating lists nicely."""
    def __init__(self, data, title, per_page: int = 10, footer=None):
        super().__init__(data, per_page=per_page)
        self.title = title
        self.footer = footer

    async def format_page(self, menu, entries):
        embed = discord.Embed(
            title=self.title,
            color=16202876,
            description="\n".join([f"``{x}``" for x in entries]))

        if self.footer:
            embed.set_footer(text=f"This is page {menu.current_page + 1}")

        return embed


class ListEmbedMenuClean(menus.ListPageSource):
    """A simple menu class for paginating lists with formatting."""
    def __init__(self, data, title, per_page: int = 10, footer=None):
        super().__init__(data, per_page=per_page)
        self.title = title
        self.footer = footer

    async def format_page(self, menu, entries):
        embed = discord.Embed(
            title=self.title,
            color=16202876,
            description="\n".join(entries))

        if self.footer:
            embed.set_footer(text=f"This is page {menu.current_page + 1}")

        return embed


class TupleEmbedMenu(menus.ListPageSource):
    """A simple menu class for paginating tuples nicely."""
    def __init__(self, data, title, per_page: int = 10, desc=None, footer=None):
        super().__init__(data, per_page=per_page)
        self.title = title
        self.desc = desc
        self.footer = footer

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=16202876)
        embed.description = self.desc

        for item in entries:
            embed.add_field(name=item[0], value=item[1], inline=False)

        if self.footer:
            embed.set_footer(text=f"This is page {menu.current_page + 1}")

        return embed


class Infractionmenu(menus.ListPageSource):
    """A not-so-simple menu class for paginating specific moderation data."""
    def __init__(self, data, title, per_page: int = 10, bot=None, desc=None):
        super().__init__(data, per_page=per_page)
        self.title = title
        self.desc = desc
        self._bot = bot

    async def format_page(self, menu, entries):
        embed = discord.Embed(title=self.title, color=16202876)
        embed.description = self.desc

        def r_username(id_):
            u = self._bot.get_user(int(id_))
            return str(u) if u else str(id_)

        for item in entries:
            data = {x[0]: x[1] for x in item}
            a = pendulum.parse(data["date_raw"])
            res = "".join([
                data["operation"].capitalize(),
                " for user ",
                r_username(data["user"]),
                f"; {a.humanize()}"])

            embed.add_field(
                name="Punishment ID #" + str(data["id"]),
                value=f"~~{res}~~" if data["redacted"] == "True" else res,
                inline=False)

        return embed


class MaizeMenu(menus.Menu):
    """A big fat menu class that entirely handles a maize maze game. Almost."""

    def __init__(self):
        """Does the things."""
        super().__init__(timeout=30, clear_reactions_after=True)
        self.maze = games.maize_array()
        self.tries = 3
        self.movements = 0

    def format_desc(self, title="A game of Maize Maze has begun!", footer=None, preserve_instructions=True, preserve_maze=True):
        """Formats the embed description properly."""

        m = f"**{title}** "
        if preserve_instructions:
            m += """Use the ⬅ ⬆ ➡ ⬇ reactions below to move botto. 
                Use the ⏹️ reaction to quit. Good luck!"""
        if preserve_maze:
            m += f"\n\n{self.maze.join()}"
        if footer:
            m += f"\n\n{footer}"

        return m

    async def send_initial_message(self, ctx, channel):
        """Sends the message that becomes the host for a maize maze game"""
        mazebed = discord.Embed(title="Maize maze!", description=self.format_desc(), color=16202876)
        return await ctx.send(embed=mazebed)

    @menus.button("⬅")
    async def on_left(self, _):
        """Called when someone wants botto to go left."""
        if await self.process_total_movements():
            await self.process_direction("left")
        else:
            self.stop()
            del self

    @menus.button("➡")
    async def on_right(self, _):
        """Called when someone wants botto to go right."""
        if await self.process_total_movements():
            await self.process_direction("right")
        else:
            self.stop()
            del self

    @menus.button("⬆")
    async def on_up(self, _):
        """Called when someone wants botto to go up."""
        if await self.process_total_movements():
            await self.process_direction("up")
        else:
            self.stop()
            del self

    @menus.button("⬇")
    async def on_down(self, _):
        """Called when someone wants botto to go down."""
        if await self.process_total_movements():
            await self.process_direction("down")
        else:
            self.stop()
            del self

    @menus.button('\N{BLACK SQUARE FOR STOP}\ufe0f')
    async def on_stop(self, _):
        """Stops the game."""
        mazetext = self.format_desc("Botto is dead and you are entirely responsible.", "Know this. Feel guilt. It was your unwilling that killed him.", False, False)
        mazebed = discord.Embed(title="Maize maze!", description=mazetext, color=16202876)
        await self.message.edit(embed=mazebed)

        self.stop()
        del self

    async def process_total_movements(self):
        """Makes sure the maize gods aren't too far behind."""
        self.movements += 1

        if self.movements > 20:
            mazetext = self.format_desc(
                "Botto is dead and you are entirely responsible.",
                "The Maize Gods were not far away, and you were not fast enough. The end has come.",
                False, False)

            mazebed = discord.Embed(title="Maize maze!", description=mazetext, color=16202876)
            await self.message.edit(embed=mazebed)

            return False
        return True

    async def process_direction(self, direction):
        """Processes where botto goes."""
        botto_x, botto_y = self.maze.botto_pos()
        tile = None

        if direction == "up":
            tile = self.maze.get_point(botto_x, botto_y - 1)
            offset = [0, -1]

        if direction == "right":
            tile = self.maze.get_point(botto_x + 1, botto_y)
            offset = [1, 0]

        if direction == "down":
            tile = self.maze.get_point(botto_x, botto_y + 1)
            offset = [0, 1]

        if direction == "left":
            tile = self.maze.get_point(botto_x - 1, botto_y)
            offset = [-1, 0]

        if "botto" in str(tile) or "maize_maize" in str(tile):
            self.tries -= 1

            if self.tries > 0:
                mazetext = self.format_desc(
                    "Botto cannot move there!",
                    (f"Botto has {self.tries} flesh remaining before the Maize Gods reach him."))
                mazebed = discord.Embed(title="Maize maze!", description=mazetext, color=16202876)

                await self.message.edit(embed=mazebed)
            else:
                mazetext = self.format_desc(
                    "Botto is dead and you are entirely responsible.",
                    "His body was found covered in ears of maize. Cause of death? Slaughter.",
                    False, False)

                mazebed = discord.Embed(title="Maize maze!", description=mazetext, color=16202876)
                await self.message.edit(embed=mazebed)
                self.stop()
                del self

        elif "blank" in str(tile) or "end" in str(tile) or "death" in str(tile):
            self.maze.set_point(
                botto_x, botto_y,
                "<:maize_blank:646810168977391629>")

            self.maze.set_point(
                botto_x + offset[0], botto_y + offset[1],
                "<:maize_botto:646810169556336650>")

            mazebed = discord.Embed(
                title="Maize maze!",
                description=self.format_desc("The game of Maize Maze continues."), color=16202876)

            await self.message.edit(embed=mazebed)

            if "deat" in str(tile):
                await asyncio.sleep(2)

                mazetext = self.format_desc(
                    "Botto is dead and you are entirely responsible.",
                    "Sit with this truth and weep.",
                    False, False)

                mazebed = discord.Embed(title="Maize maze!", description=mazetext, color=16202876)
                await self.message.edit(embed=mazebed)
                self.stop()
                del self

            elif "end" in str(tile):
                await asyncio.sleep(2)

                mazetext = self.format_desc(
                    "Botto has been saved from the Maize Gods!", 
                    "You win!\n\n(Saved from the Maize Gods for a little while, at least.)",
                    False, False)

                mazebed = discord.Embed(title="Maize maze!", description=mazetext, color=16202876)
                await self.message.edit(embed=mazebed)
                self.stop()
                del self

            elif "blank" not in str(tile):
                await self.message.edit(content=(
                    "Congratulations, you found the unfindable embed!"
                    "Now time wil collapse. \n\n(This shouldn't be possible. Tell Kaylynn.)"))


class ConfirmationMenu(menus.Menu):
    """Makes sure of things."""
    
    def __init__(self, embed):
        super().__init__(timeout=20, clear_reactions_after=True)    
        self.embed = embed
        self.clicked = False
        self.is_running = True

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed)

    @menus.button('\N{WHITE HEAVY CHECK MARK}')
    async def action_allowed(self, payload):
        self.clicked = True
        self.is_running = False
        self.stop()

    @menus.button('\N{CROSS MARK}')
    async def action_denied(self, payload):
        new = self.message.embeds[0]
        new.clear_fields()
        new.description = None
        await self.message.edit(embed=new.set_footer(text="This action was cancelled."))
        self.is_running = False
        self.stop()
