import random
import collections
import helpers as h
import pygame
# from multiprocessing import Process, Queue, SimpleQueue

#

WIDTH, HEIGHT = 50, 50

#


class Board(object):
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.fields = [[None for _y in range(height)] for _x in range(width)]
        self.ops = collections.deque()
        self.worms = []
#        self.ops_queue = SimpleQueue()

    def is_correct_position(self, pos):
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
#        self.ops_queue.put((pos, worm.species))

    def free(self, pos):
        x, y = pos
        self.fields[x][y] = None
        self.ops.append((pos, (0, 0, 0)))
#        self.ops_queue.put((pos, (0, 0, 0)))

    def is_free(self, pos):
        x, y = pos
        return self.fields[x][y] is None

    def after_turn(self):
        garbages = [x for x in self.worms if x.garbage]

        for garbage in garbages:
            self.worms.remove(garbage)


class Worm(object):
    GENES_NUM = 20
    GENES_GENDER = slice(0, 1)  # 0
    GENES_SPECIES = slice(1, 4)  # 1-3
    GENES_AGGRESSION = slice(4, 7)  # 4-6
    GENES_HEALTH = slice(7, 10)  # 7-9
    GENES_STRENGTH = slice(10, 13)  # 10-12

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
        (255, 255, 255),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
        (120, 0, 120)
    ]

    def __init__(self, board, genes=None):
        self.board = board
        self.genes = genes if genes else h.generate_bin(20)
        self.health = h.decode_bin(self.genes[self.GENES_HEALTH])
        self.energy = 1.0
        self.turn_energy = 0.002
        self.starvation_impact = 0.01 * self.health
        self.garbage = False

    def destroy(self):
#        print("TO BE DESTROYED")
        self.garbage = True

    @property
    def gender(self):
        return h.decode_dict(self.genes[self.GENES_GENDER], self.GENDERS)

    @property
    def species(self):
        return h.decode_dict(self.genes[self.GENES_SPECIES], self.SPECIES)

    @property
    def wants_attack(self):
        p = h.decode_bin(self.genes[self.GENES_AGGRESSION])
        return h.probability(p)

    @property
    def strength(self):
        return h.decode_bin(self.genes[self.GENES_STRENGTH])

    @property
    def alive(self):
        return self.health > 0.0

    def place(self, pos):
        assert(self.board.is_free(pos))
        self.position = pos
        self.board.put(self.position, self)

    def move(self, target):
        self.board.free(self.position)
        self.position = target
        self.board.put(self.position, self)

    @property
    def available_targets(self):
        return [x for x in self.MOVES if self.board.is_correct_position(x) and self.board.is_free(x)]

    def turn(self):
        if not self.alive:
            return

        # each move consumes energy
        self.energy = max(self.energy - self.turn_energy, 0.0)

        # being hungry kills ;-)
        if self.energy == 0:
            self.health = max(self.health - self.starvation_impact, 0.0)

        m = random.choice(self.MOVES)
        target = (
            self.position[0] + m[0],
            self.position[1] + m[1]
        )

        if not self.board.is_correct_position(target):
            # print("INCORRECT POSITION")
            return

        if self.board.is_free(target):
            self.move(target)
        else:
            neighbor = self.board.at(target)

            if neighbor.alive:
                if neighbor.species == self.species:
                    targets = self.available_targets

                    if len(targets) >= 2:
                        a, b = h.crossover(self.genes, neighbor.genes)

                        for i, x in enumerate([a, b]):
                            c = Worm(board=self.board, genes=x)
                            self.board.worms.append(c)
                            c.place(targets[i])
                            print("BEBOK")

                else:
                    if self.wants_attack:
                        impact = neighbor.health * self.strength
                        neighbor.health = max(neighbor.health - impact, 0.0)
            else:
                self.energy += (neighbor.energy + 0.5)
#                print(self.energy)
                neighbor.destroy()


board = Board(width=WIDTH, height=HEIGHT)
board.born(50)

screen = pygame.display.set_mode((WIDTH, HEIGHT))

n = 0
running = True
while running:
#    print("TURA")
    for worm in board.worms:
        worm.turn()

    board.after_turn()

    n += 1
    if n % 1 == 0:
        print("Total:  {}".format(len(board.worms)))
        print("Alive:  {}".format(sum([1 for x in board.worms if x.alive])))
        print("Dead:   {}".format(sum([1 for x in board.worms if not x.alive])))
        print("Hungry: {}".format(sum([1 for x in board.worms if x.energy == 0.0])))

        for op in board.ops:
            pos, color = op
            screen.set_at(pos, color)

        pygame.display.flip()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
