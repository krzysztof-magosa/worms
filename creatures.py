import helpers as h
from genome import GenomeHandler
import random


class Creature(object):
    MOVES = [
        # x, y
        (-1, -1),  # left, up
        (-1, 0),  # left,
        (-1, 1),  # left, down
        (1, -1),  # right, up
        (1, 0),  # right
        (1, 1),  # right, down
        (0, -1),  # up
        (0, 1),  # down
    ]

    @property
    def color(self):
        raise NotImplementedError()

    @classmethod
    def genes_description(cls):
        raise NotImplementedError()

    @classmethod
    def gh(cls):
        if not hasattr(cls, "gh_cache"):
            cls.gh_cache = GenomeHandler(cls.genes_description())

        return cls.gh_cache

    def __init__(self, genes=[], statics=[]):
        self.genes = genes if genes else self.gh().generate(statics=statics)
        self.data = self.gh().decode(self.genes)
#        print(self.data)
        self.init()

    def move(self, destination):
        """Moves creature to destination on board."""
        self.board.check_out(self)
        self.position = destination
        self.board.check_in(self)

    @property
    def any_destinations(self):
        for m in self.MOVES:
            yield (
                self.position[0] + m[0],
                self.position[1] + m[1]
            )

    @property
    def possible_destinations(self):
        return filter(
            lambda x: self.board.is_correct_position(x),
            self.any_destinations
        )

    @property
    def possible_free_destinations(self):
        return filter(
            lambda x: self.board.is_free(x),
            self.possible_destinations
        )

    @property
    def possible_nonfree_destinations(self):
        return filter(
            lambda x: not self.board.is_free(x),
            self.possible_destinations
        )

    def turn(self):
        raise NotImplementedError()


class Worm(Creature):
    @property
    def color(self):
        return self.species if self.alive else (50, 50, 50)

    @classmethod
    def genes_description(cls):
        return [
            dict(
                name="gender",
                count=1,
                choices=["male", "female"]
            ),
            dict(
                name="species",
                count=3,
                choices=[
                    (244, 67, 54),
                    (233, 30, 99),
                    (156, 39, 176),
                    (63, 81, 181),
                    (33, 150, 243),
                    (0, 150, 136),
                    (205, 220, 57),
                    (255, 193, 7)
                ]
            ),
            dict(
                name="aggression",
                count=8
            ),
            dict(
                name="max_health",
                count=8
            ),
            dict(
                name="strength",
                count=8
            ),
            dict(
                name="temperament",
                count=8
            ),
            dict(
                name="max_age",
                count=8
            ),
            dict(
                name="mobility",
                count=8
            ),
            dict(
                name="max_energy",
                count=8
            ),
            dict(
                name="eats_own_carrion",
                count=1,
                choices=[True, False]
            )
        ]

    def init(self):
        self.health = self.max_health
        self.energy = self.max_energy
        self.turn_energy_impact = 0.05 * self.max_energy
        self.starvation_impact = 0.05 * self.max_health

        self.age = 0
        self.fear = 0.0
        self.died = False

        self.last = ''

    @property
    def gender(self):
        return self.data["gender"]

    @property
    def species(self):
        return self.data["species"]

    @property
    def max_health(self):
        return self.data["max_health"]

    @property
    def max_energy(self):
        return self.data["max_energy"]

    @property
    def strength(self):
        return self.data["strength"]

    @property
    def temperament(self):
        return self.data["temperament"]

    @property
    def aggression(self):
        return self.data["aggression"]

    @property
    def max_age(self):
        return int(self.data["max_age"] * 100.0)

    @property
    def mobility(self):
        return self.data["mobility"]

    @property
    def eats_own_carrion(self):
        return self.data["eats_own_carrion"]

    @property
    def alive(self):
        return self.health > 0.0 and self.age < self.max_age

    @property
    def young(self):
        return self.age <= self.max_age * 0.13

    @property
    def procreation_able(self):
        return (self.age >= (self.max_age * 0.18)) and (self.age <= (self.max_age * 0.45)) and self.fear == 0.0

    @property
    def possible_food(self):
        food = [x for x in self.possible_nonfree_destinations if not self.board.at(x).alive]

        if not self.eats_own_carrion:
            food = [x for x in food if self.board.at(x).species != self.species]

        return food

    @property
    def possible_partners(self):
        return [x for x in self.possible_nonfree_destinations if self.board.at(x).alive and self.board.at(x).species == self.species and self.board.at(x).want_partner and self.board.at(x).gender != self.gender]

    @property
    def possible_victims(self):
        victims = [x for x in self.possible_nonfree_destinations if self.board.at(x).alive]
        victims = filter(lambda x: self.board.at(x).species != self.species, victims)

        return victims

    @property
    def want_food(self):
        return self.energy < (0.4 * self.max_energy) or len(self.possible_free_destinations) == 0

    @property
    def want_procreation(self):
        targets = self.possible_free_destinations
        return self.procreation_able and len(targets) >= 2 and h.probability(self.temperament) and not self.want_food

    @property
    def want_partner(self):
        return self.procreation_able and h.probability(self.temperament)

    @property
    def want_move(self):
        return h.probability(self.mobility) # and self.energy > 0.0

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
            neighbor.fear = min(neighbor.fear + 0.3, 1.0)
        else:
            neighbor.energy = max(neighbor.energy - (3 * neighbor.turn_energy_impact), 0.0)
#            print(neighbor.energy)

    def procreate(self, pos):
        neighbor = self.board.at(pos)

        if not neighbor.want_partner:
#            print("NIE CHCEM")
            return

        targets = self.possible_free_destinations
        random.shuffle(targets)
        # @TODO maybe random.choices() to be used with python 3

        for i, x in enumerate(h.crossover(self.genes, neighbor.genes)):
            x = h.mutate_bin(x)
            c = Worm(genes=x)
            self.board.put(c, targets[i])

    def eat(self, pos):
        neighbor = self.board.at(pos)
        self.energy = min(self.max_energy, self.energy + neighbor.energy + 0.5)
        self.board.remove(pos)
        # self.move(neighbor.position)  # ???

    def die(self):
        if not self.died:
#            print("TRUP")
            self.died = True
            self.board.check_in(self)
#            print("TRUP")
#            self.board.ops_queue.put((self.position, (80, 80, 80)))

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
        if partners and self.want_procreation and not self.want_food:
#            print("PROCREATE")
#            print(self.age)
#            print(self.max_age)
#            print(self.max_age * 0.18)
            self.procreate(random.choice(partners))
            self.energy = max(self.energy - (self.turn_energy_impact * 5), 0.0)
            self.last = 'procreate'
            return

        victims = self.possible_victims
        if victims and self.want_attack:
#            print("ATTACK")
            self.attack(random.choice(victims))
            self.energy = max(self.energy - self.turn_energy_impact, 0.0)
            self.last = 'attack'
            return

        targets = self.possible_free_destinations
        if targets and self.want_move:
            self.move(random.choice(targets))
            self.energy = max(self.energy - self.turn_energy_impact, 0.0)
            return
