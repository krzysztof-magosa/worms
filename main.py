import random
import collections
import helpers as h
from Tkinter import Tk, Canvas, PhotoImage  # , mainloop

#

WIDTH, HEIGHT = 640, 480

#


class Board(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.fields = [[None for _y in range(height)] for _x in range(width)]
        self.ops = collections.deque()
        self.worms = []

    def within_borders(self, pos):
        x, y = pos

        if x < 0 or y < 0:
            return False

        if x >= self.width or y >= self.height:
            return False

        return True

    def random_position(self):
        return (
            random.randint(0, self.width-1),
            random.randint(0, self.height-1)
        )

    def born(self, num):
        for _n in range(num):
            while True:
                pos = self.random_position()

                if self.is_free(pos):
                    worm = Worm(board=self)
                    worm.place(pos)
                    self.worms.append(worm)
                    break

    def at(self, pos):
        x, y = pos
        return self.fields[x][y]

    def put(self, pos, worm):
        x, y = pos
        self.fields[x][y] = worm
        self.ops.append((pos, worm.species))

    def free(self, pos):
        x, y = pos
        self.fields[x][y] = None
        self.ops.append((pos, "#000000"))

    def is_free(self, pos):
        x, y = pos

        if not self.within_borders(pos):
            return False

        return self.fields[x][y] is None


class Worm(object):
    MOVES = [
        # x,  y
        (-1, -1),  # left, up
        (-1,  0),  # left,
        (-1,  1),  # left, down
        ( 1, -1),  # right, up
        ( 1,  0),  # right
        ( 1,  1),  # right, down
        ( 0, -1),  # up
        ( 0,  1),  # down
    ]

    GENDERS = [
        "female",
        "male"
    ]

    SPECIES = [
        "#b71c1c",
        "#0D47A1",
        "#558B2F",
        "#FF8F00",
        "#795548",
        "#78909C",
        "#dddddd",
        "#FF4081"
    ]

    def __init__(self, board, genes=None):
        self.board = board
        self.genes = genes if genes else h.generate_bin(20)

    @property
    def gender(self):
        return h.decode_dict(self.genes[0:0+1], self.GENDERS)

    @property
    def species(self):
        return h.decode_dict(self.genes[1:3+1], self.SPECIES)

    def place(self, pos):
        assert(self.board.is_free(pos))
        self.position = pos
        self.board.put(self.position, self)

    def move(self):
        m = random.choice(self.MOVES)
        target = (
            self.position[0] + m[0],
            self.position[1] + m[1]
        )

        if self.board.is_free(target):
            self.board.free(self.position)
            self.position = target
            self.board.put(self.position, self)
        else:
            print("XXX")


board = Board(width=WIDTH, height=HEIGHT)
board.born(50)


window = Tk()
canvas = Canvas(window, width=WIDTH, height=HEIGHT, bg="#000000")
canvas.pack()
img = PhotoImage(width=WIDTH, height=HEIGHT)
canvas.create_image((WIDTH/2, HEIGHT/2), image=img, state="normal")

n = 0
while True:
    for worm in board.worms:
        worm.move()

    n += 1
    if n % 1 == 0:
        for op in board.ops:
            pos, color = op
            img.put(color, pos)

        window.update_idletasks()
        window.update()
