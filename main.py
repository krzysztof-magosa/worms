import random
import helpers as h
import pygame
import multiprocessing as mp
import yaml
import itertools

#

WIDTH, HEIGHT = 200, 200

#


class Board(object):
    def __init__(self, width, height, queue):
        self.width = width
        self.height = height
        self.fields = [[None for _y in range(height)] for _x in range(width)]
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

    def rand_circle(self):
        t = 2.0*math.pi*random.random()
        u = random.random()+random.random()
        r = 2.0-u if u > 1 else u
        return (r*math.cos(t), r*math.sin(t))

    def born(self, num, feed=False):
        for _n in range(num):
            while True:
                pos = self.random_position()

                if self.is_free(pos):
                    worm = Worm(board=self)

                    if feed:
                        worm.max_age = 1
                        worm.aggression = 0.0
                        worm.mobility = 0.0
                        worm.health = 0.0
                        worm.energy = 0.0

                    worm.place(pos)
                    self.worms.append(worm)
                    break

    def at(self, pos):
        x, y = pos
        return self.fields[x][y]

    def put(self, pos, worm):
        x, y = pos
        self.fields[x][y] = worm
        self.ops_queue.put((pos, worm.species))

    def free(self, pos):
        x, y = pos
        self.fields[x][y] = None
        self.ops_queue.put((pos, (0, 0, 0)))

    def is_free(self, pos):
        x, y = pos
        return self.fields[x][y] is None

    def after_turn(self):
        garbages = [x for x in self.worms if x.garbage]

        for garbage in garbages:
            self.worms.remove(garbage)

        # TODO maybe every N turns for better perf
        random.shuffle(self.worms)


class Worm(object):
    GENES_NUM = 47
    GENES_GENDER = slice(0, 1)  # 0 (1)
    GENES_SPECIES = slice(1, 4)  # 1-3 (3)
    GENES_AGGRESSION = slice(4, 10)  # 4-9 (6)
    GENES_HEALTH = slice(10, 16)  # 10-15 (6)
    GENES_STRENGTH = slice(16, 22)  # 16-21 (6)
    GENES_TEMPERAMENT = slice(22, 28)  # 22-27 (6)
    GENES_LONGEVITY = slice(28, 34)  # 28-33 (6)
    GENES_MOBILITY = slice(34, 40)  # 34-39 (6)
    GENES_ENERGY = slice(40, 46)  # 40-45 (6)
    GENES_EATS_OWN_CARRION = slice(46, 47)  # 46-46 (1)

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
        (244, 67, 54),
        (233, 30, 99),
        (156, 39, 176),
        (63, 81, 181),
        (33, 150, 243),
        (0, 150, 136),
        (205, 220, 57),
        (255, 193, 7)
    ]

    def __init__(self, board, genes=None):
        self.board = board
        self.genes = genes if genes else h.generate_bin(self.GENES_NUM)
        self.max_health = max(h.decode_bin(self.genes[self.GENES_HEALTH]), 0.01)
        self.health = self.max_health
        self.max_energy = max(h.decode_bin(self.genes[self.GENES_ENERGY]), 0.01)
        self.energy = self.max_energy
        self.turn_energy_impact = 0.1 * self.max_energy
        self.starvation_impact = 0.333 * self.max_health
        self.garbage = False
        self.strength = max(h.decode_bin(self.genes[self.GENES_STRENGTH]), 0.01)
        self.temperament = max(h.decode_bin(self.genes[self.GENES_TEMPERAMENT]), 0.01)
        self.aggression = max(h.decode_bin(self.genes[self.GENES_AGGRESSION]), 0.01)
        self.age = 0
        self.max_age = int(h.decode_bin(self.genes[self.GENES_LONGEVITY], base=30.0))
        self.mobility = max(h.decode_bin(self.genes[self.GENES_MOBILITY]), 0.01)
        self.died = False
        self.fear = 0.0
        self.last = ''
        self.eats_own_carrion = h.decode_bin(self.genes[self.GENES_EATS_OWN_CARRION]) == 1.0
        self.rg = random.Random()
        self.rg.seed(random.random())

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
        return self.health > 0.0 or self.age < self.max_age

    @property
    def young(self):
        return self.age <= self.max_age * 0.13

    @property
    def procreation_able(self):
        return (self.age >= self.max_age * 0.18) and (self.age <= self.max_age * 0.65)

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
        food = [x for x in self.possible_nonfree if not self.board.at(x).alive]

        if not self.eats_own_carrion:
            food = [x for x in food if self.board.at(x).species != self.species]

        return food

    @property
    def possible_partners(self):
        return [x for x in self.possible_nonfree if self.board.at(x).alive and self.board.at(x).species == self.species and self.board.at(x).want_partner and self.board.at(x).gender != self.gender]

    @property
    def possible_victims(self):
        ms = self.species.index(max(self.species))
        #return [x for x in self.possible_nonfree if self.board.at(x).alive and self.board.at(x).species != self.species]
        return [x for x in self.possible_nonfree if self.board.at(x).alive and ms != self.board.at(x).species.index(max(self.board.at(x).species))]

    @property
    def want_food(self):
        return self.energy < (0.3 * self.max_energy)

    @property
    def want_procreation(self):
        targets = self.available_targets
        return self.procreation_able and len(targets) >= 2 and h.probability(self.temperament) and not self.want_food

    @property
    def want_partner(self):
        return self.procreation_able and h.probability(self.temperament)

    @property
    def want_move(self):
        return h.probability(self.mobility) and self.energy > 0.0

    @property
    def want_attack(self):
        if self.young:
            return False

        if h.probability(self.aggression):
            return True

        if h.probability(self.fear):
            return True

        if self.want_food:
            return True

        return False

#    def is_ally(self, neighbor):

    def attack(self, pos):
        neighbor = self.board.at(pos)

        offensive = self.strength * (self.health / self.max_health)
        defensive = neighbor.strength * (neighbor.health / neighbor.max_health)

        if offensive > defensive or neighbor.young:
            impact = offensive
            if not neighbor.young:
                impact -= defensive

            impact = max(0.0, impact)
            neighbor.health = max(0.0, neighbor.health - (neighbor.max_health * impact))
        else:
            neighbor.energy = max(neighbor.energy - (3 * neighbor.turn_energy_impact), 0.0)
#            print(neighbor.energy)

    def procreate(self, pos):
        neighbor = self.board.at(pos)

        if not neighbor.want_partner:
#            print("NIE CHCEM")
            return

        targets = self.available_targets
        random.shuffle(targets)
        # @TODO maybe random.choices() to be used with python 3

        for i, x in enumerate(h.crossover(self.genes, neighbor.genes)):
            x = h.mutate_bin(x)
            c = Worm(board=self.board, genes=x)
            self.board.worms.append(c)
            c.place(targets[i])

    def eat(self, pos):
        neighbor = self.board.at(pos)
        self.energy = min(self.max_energy, self.energy + neighbor.energy + 0.05)
        neighbor.destroy()
        #self.move(neighbor.position)  # ???

    def die(self):
        if not self.died:
            self.died = True
#            print("TRUP")
            self.board.ops_queue.put((self.position, (80, 80, 80)))

    def turn(self):
        self.age += 1
        self.fear = max(self.fear - 0.1, 0.0)

        # regeneration
        if self.energy > 0:
            self.health = min(self.max_health, self.health * 1.05)

        # being hungry kills ;-)
        if self.energy == 0:
            self.health = max(self.health - self.starvation_impact, 0.0)

        if not self.alive:
            self.die()
            return

        food = self.possible_food
        if food and self.want_food:
#            print("EAT")
            self.eat(random.choice(food))
            self.energy = max(self.energy - self.turn_energy_impact, 0.0)
            self.last = 'eat'
            return

        partners = self.possible_partners
        if partners and self.want_procreation:
#            print("PROCREATE")
            self.procreate(random.choice(partners))
            self.energy = max(self.energy - self.turn_energy_impact, 0.0)
            self.last = 'procreate'
            return

        victims = self.possible_victims
        if victims and self.want_attack:
#            print("ATTACK")
            self.attack(random.choice(victims))
            self.energy = max(self.energy - self.turn_energy_impact, 0.0)
            self.last = 'attack'
            return

        targets = self.available_targets
        if targets and self.want_move:
            self.move(self.rg.choice(targets))
            self.energy = max(self.energy - self.turn_energy_impact, 0.0)
            return


def logic(q):
    config = yaml.load(open('config.yaml'))
    print(config)

    board = Board(width=WIDTH, height=HEIGHT, queue=q)
#    board.born(500)
    board.born(int(WIDTH * HEIGHT * 0.1))
    board.born(int(WIDTH * HEIGHT * 0.2), feed=True)

    n = 0
    while True:
        for worm in board.worms:
            worm.turn()

        board.after_turn()

        print("Total:  {}".format(len(board.worms)))
        print("Alive:  {}".format(sum([1 for x in board.worms if x.alive])))
        print("Dead:   {}".format(sum([1 for x in board.worms if not x.alive])))
        print("Hungry: {}".format(sum([1 for x in board.worms if x.want_food and x.alive])))
        print("Hungry0:{}".format(sum([1 for x in board.worms if x.energy == 0.0 and x.alive])))
        print("Eat:    {}".format(sum([1 for x in board.worms if x.last == 'eat' and x.alive])))
        print("Procre: {}".format(sum([1 for x in board.worms if x.last == 'procreate' and x.alive])))
        print("Atack:  {}".format(sum([1 for x in board.worms if x.last == 'attack' and x.alive])))
        print("Carrion:{}".format(sum([1 for x in board.worms if x.eats_own_carrion and x.alive])))
        print("Turn:   {}".format(n))
        print("")

        for worm in board.worms:
            worm.last = ''

        n += 1


screen = pygame.display.set_mode((WIDTH, HEIGHT))

q = mp.Queue(128)

lp = mp.Process(target=logic, args=(q,))
lp.start()

cycle = 50
while True:
    if q.full() and cycle < (WIDTH * HEIGHT):
        cycle += 50

    for x in range(cycle):
        if q.empty():
            break

        op = q.get()
        pos, color = op
        screen.set_at(pos, color)

    pygame.display.flip()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

lp.join()
