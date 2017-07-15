import random
import helpers as h
import pygame
import multiprocessing as mp

#

WIDTH, HEIGHT = 100, 100

#


class Board(object):
    def __init__(self, width, height, queue):
        self.width = width
        self.height = height
        self.fields = [[None for _y in range(height)] for _x in range(width)]
#        self.ops = collections.deque()
        self.worms = []
        self.ops_queue = queue

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
#        self.ops.append((pos, worm.species))
        self.ops_queue.put((pos, worm.species))
#        print(self.ops_queue.full())

    def free(self, pos):
        x, y = pos
        self.fields[x][y] = None
#        self.ops.append((pos, (0, 0, 0)))
        self.ops_queue.put((pos, (0, 0, 0)))

    def is_free(self, pos):
        x, y = pos
        return self.fields[x][y] is None

    def after_turn(self):
        garbages = [x for x in self.worms if x.garbage]

        for garbage in garbages:
            self.worms.remove(garbage)


class Worm(object):
    GENES_NUM = 28
    GENES_GENDER = slice(0, 1)  # 0
    GENES_SPECIES = slice(1, 4)  # 1-3 (3)
    GENES_AGGRESSION = slice(4, 10)  # 4-9 (5)
    GENES_HEALTH = slice(10, 16)  # 10-15 (5)
    GENES_STRENGTH = slice(16, 22)  # 16-21 (5)
    GENES_TEMPERAMENT = slice(22, 28)  # 22-27 (5)

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
        self.genes = genes if genes else h.generate_bin(self.GENES_NUM)
        self.health = h.decode_bin(self.genes[self.GENES_HEALTH])
        self.energy = 1.0
        self.turn_energy = 0.05
        self.starvation_impact = 0.20 * self.health
        self.garbage = False
        self.strength = h.decode_bin(self.genes[self.GENES_STRENGTH])
        self.temperament = h.decode_bin(self.genes[self.GENES_TEMPERAMENT])
        self.aggression = h.decode_bin(self.genes[self.GENES_AGGRESSION])

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
    def surrounding_targets(self):
        result = []
        for m in self.MOVES:
            result.append(
                (
                    self.position[0] + m[0],
                    self.position[1] + m[1]
                )
            )

        return result

    @property
    def possible_targets(self):
        return [x for x in self.surrounding_targets if self.board.is_correct_position(x)]

    @property
    def available_targets(self):
        return [x for x in self.surrounding_targets if self.board.is_correct_position(x) and self.board.is_free(x)]

    @property
    def possible_nonfree(self):
        return [x for x in self.surrounding_targets if self.board.is_correct_position(x) and not self.board.is_free(x)]

    @property
    def possible_food(self):
        return [x for x in self.possible_nonfree if not self.board.at(x).alive]

    @property
    def possible_partners(self):
        return [x for x in self.possible_nonfree if self.board.at(x).alive and self.board.at(x).species == self.species]

    @property
    def possible_victims(self):
        return [x for x in self.possible_nonfree if self.board.at(x).alive and self.board.at(x).species != self.species]

    @property
    def want_food(self):
        return self.energy <= 0.2

    @property
    def want_procreation(self):
        targets = self.available_targets
        return len(targets) >= 2 and h.probability(self.temperament)

    @property
    def want_attack(self):
        return h.probability(self.aggression)

    def attack(self, pos):
        neighbor = self.board.at(pos)
        impact = neighbor.health * self.strength
        neighbor.health = max(neighbor.health - impact, 0.0)

    def procreate(self, pos):
        neighbor = self.board.at(pos)
        targets = self.available_targets
        random.shuffle(targets)
        # @TODO maybe random.choices() to be used with python 3

        a, b = h.crossover(self.genes, neighbor.genes)

        for i, x in enumerate([a, b]):
            c = Worm(board=self.board, genes=x)
            self.board.worms.append(c)
            c.place(targets[i])

    def eat(self, pos):
        neighbor = self.board.at(pos)
        self.energy += (neighbor.energy + 0.5)
        neighbor.destroy()

    def turn(self):
        if not self.alive:
            return

        # each move consumes energy
        self.energy = max(self.energy - self.turn_energy, 0.0)

        # being hungry kills ;-)
        if self.energy == 0:
            self.health = max(self.health - self.starvation_impact, 0.0)

        food = self.possible_food
        if food and self.want_food:
            self.eat(random.choice(food))
            return

        victims = self.possible_victims
        if victims and self.want_attack:
            self.attack(random.choice(victims))
            return

        partners = self.possible_partners
        if partners and self.want_procreation:
            self.procreate(random.choice(partners))
            return

        targets = self.available_targets
        if targets:
            self.move(random.choice(targets))


def logic(q):
    board = Board(width=WIDTH, height=HEIGHT, queue=q)
    board.born(100)

    while True:
        for worm in board.worms:
            worm.turn()

        board.after_turn()

        print("Total:  {}".format(len(board.worms)))
        print("Alive:  {}".format(sum([1 for x in board.worms if x.alive])))
        print("Dead:   {}".format(sum([1 for x in board.worms if not x.alive])))
        print("Hungry: {}".format(sum([1 for x in board.worms if x.energy == 0.0])))


screen = pygame.display.set_mode((WIDTH, HEIGHT))

q = mp.Queue()

lp = mp.Process(target=logic, args=(q,))
lp.start()

cycle = 10
while True:
    if q.full():
        cycle += 10
        print(cycle)

    for x in range(cycle):
#        print(cycle)
        op = q.get()
        pos, color = op
        screen.set_at(pos, color)

    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

lp.join()
