"""All the bullshit for games."""

import random
import sys
import collections

from lobstero.utils import misc

root_directory = sys.path[0] + "/"


class uno_card():

    def __init__(self, ctype, colour, used):
        self.type, self.colour, self.used = ctype, colour, used
        self.used_special = None

    @property
    def filename(self):
        return f"{root_directory}data/uno/{self.type + self.colour}"

    @property
    def is_special(self):
        return self.type.lower() in ["drawfour", "drawtwo", "wild", "skip", "reverse"]

    def play(self):
        """Fancy setter. Expand later."""
        if self.used is False:
            self.used = True

    def similar_to(self, card):
        """Is a card similar enough to another to be played?"""
        if card.used_special == self.colour or card.colour == self.used_special:
            return True
        if card.colour == self.colour:
            return True
        if card.type == self.type:
            return True

        return False


class uno_player():

    def __init__(self, user):
        self.id, self.cards = user.id, collections.deque()

    @property
    def hand(self):
        return self.cards

    def remove(self, card: int):
        del self.cards[card]

    def add(self, card: uno_card):
        self.cards.append(card)

    @property
    def cards_in_hand(self):
        return len(self.cards)


class uno_game():

    def __init__(self, ctx, players):

        self.ctx = ctx
        self.players = [uno_player(x) for x in players]
        self.turn_direction = "right"
        self.pickup_pile, self.discard_pile = collections.deque(), collections.deque()

    def setup(self):
        pass

    @property
    def current_player(self):

        return self.players[0]

    def process_special(self, card):

        if card.type == "reverse":
            if self.turn_direction == "right":
                self.turn_direction = "left"

            else:
                self.turn_direction = "right"

        if card.type == "drawfour":
            pass


class uno_game_collector(dict):

    def __init__(self):
        self.__dict__ = self

    def new(self, ctx, players: list):
        self[ctx.guild.id] = uno_game(ctx, players)


class maize_array():

    def do_pathfinding(self):

        corn = "<:maize_maize:646810169661194270>"
        death = "<:maize_death:646810168897568770>"
        end = "<:maize_end:646810352067018762>"
        botto = "<:maize_botto:646810169556336650>"
        nothing = "<:maize_blank:646810168977391629>"

        self.list = [
            [[None], [None], [None], [None], [None], [None], [None], [None], [None]],
            [[None], [None], [None], [None], [None], [None], [None], [None], [None]],
            [[None], [None], [None], [None], [None], [None], [None], [None], [None]],
            [[None], [None], [None], [None], [None], [None], [None], [None], [None]],
            [[None], [None], [None], [None], [None], [None], [None], [None], [None]]
        ]

        def rand():
            l = [0, 1]
            if random.randint(1, 2) == 2:
                l[1] = -1

            random.shuffle(l)
            return l

        def is_valid(xpos, ypos):
            v = []
            if self.get_point(xpos, ypos) == nothing:

                v.append(
                    [(self.get_point(xpos + 1, ypos) is None), [xpos + 1, ypos]])
                v.append(
                    [(self.get_point(xpos - 1, ypos) is None), [xpos - 1, ypos]])
                v.append(
                    [(self.get_point(xpos, ypos + 1) is None), [xpos, ypos + 1]])
                v.append(
                    [(self.get_point(xpos, ypos - 1) is None), [xpos, ypos - 1]])

                for i in v:
                    if i[0] is True:
                        return i

                return (False, [0, 0])

            else:
                return (False, [0, 0])

        self.width, self.height = 9, 5

        self.path_x = random.randint(1, self.width - 2)
        self.path_y = random.randint(1, self.height - 2)
        self.dir = rand()

        for _ in range(random.randint(15, 20)):
            if random.randint(1, 4) == 4:
                self.dir = rand()

            if self.get_point(self.path_x + self.dir[0], self.path_y + self.dir[1]) is None:
                self.set_point(self.path_x + self.dir[0], self.path_y + self.dir[1], nothing)
                self.path_x, self.path_y = self.path_x + self.dir[0], self.path_y + self.dir[1]
            else:
                self.dir = rand()

        valid_locs = []

        for y_index, y in enumerate(self.list):
            for x_index, x in enumerate(y):
                valid = is_valid(x_index, y_index)
                if valid[0]:
                    valid_locs.append(valid[1])

        def random_pop(l):
            r = random.choice(l)
            i = l.index(r)
            return i

        end_pos = valid_locs.pop(random_pop(valid_locs))
        death_pos = valid_locs.pop(random_pop(valid_locs))
        botto_pos = valid_locs.pop(random_pop(valid_locs))

        self.set_point(end_pos[0], end_pos[1], end)
        self.set_point(death_pos[0], death_pos[1], death)
        self.set_point(botto_pos[0], botto_pos[1], botto)

        for y_index, y in enumerate(self.list):
            for x_index, x in enumerate(y):
                if x == [None]:
                    self.set_point(x_index, y_index, corn)

    def __init__(self):
        corn = "<:maize_maize:646810169661194270>"
        death = "<:maize_death:646810168897568770>"
        end = "<:maize_end:646810352067018762>"
        botto = "<:maize_botto:646810169556336650>"
        nothing = "<:maize_blank:646810168977391629>"

        self.list = [
            [[corn], [corn], [corn], [corn], [corn], [corn], [corn], [corn], [corn]],
            [[corn], [botto], [nothing], [nothing], [nothing], [nothing], [corn], [corn], [corn]],
            [[corn], [corn], [corn], [nothing], [corn], [nothing], [corn], [corn], [corn]],
            [[corn], [corn], [corn], [death], [corn], [nothing], [nothing], [nothing], [end]],
            [[corn], [corn], [corn], [corn], [corn], [corn], [corn], [corn], [corn]]
        ]

        if random.randint(1, 11) != 11:
            self.do_pathfinding()

        self.width, self.height = 9, 5

    def get_point(self, x, y):
        return self.list[misc.clamp(y, 0, self.height - 1)][misc.clamp(x, 0, self.width - 1)][0]

    def set_point(self, x, y, val):
        self.list[misc.clamp(y, 0, self.height - 1)][misc.clamp(x, 0, self.width - 1)][0] = val

    def botto_pos(self):
        for y_index, y in enumerate(self.list):
            for x_index, x in enumerate(y):
                if self.list[y_index][x_index][0] == "<:maize_botto:646810169556336650>":
                    return [x_index, y_index]

        return None

    def join(self):
        e = "🌽"

        s = "".join([e for _ in range(11)]) + "\n"
        for row in self.list:
            s += f"{e}"
            for item in row:
                s += f"{item[0]}"
            s += f"{e} \n"
        s += "".join([e for _ in range(11)])

        return s