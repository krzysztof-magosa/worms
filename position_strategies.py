import random

# https://stackoverflow.com/questions/5837572/generate-a-random-point-within-a-circle-uniformly
#    def rand_circle(self):
#        t = 2.0*math.pi*random.random()
#        u = random.random()+random.random()
#        r = 2.0-u if u > 1 else u
#        return (r*math.cos(t), r*math.sin(t))


class PositionStrategy(object):
    def __init__(self, board, options):
        self.board = board
        self.options = options
        self.init()

    def positions(self):
        raise NotImplementedError()

    def init(self):
        pass


class HorizontalPositionStrategy(PositionStrategy):
    def positions(self):
        for y in range(self.board.height):
            for x in range(self.board.width):
                yield (x, y)


class VerticalPositionStrategy(PositionStrategy):
    def positions(self):
        for x in range(self.board.width):
            for y in range(self.board.height):
                yield (x, y)


class RandomPositionStrategy(PositionStrategy):
    def init(self):
        self.rg = random.Random()

        seed = self.options.get('seed', None)
        if seed:
            self.rg.seed(seed)

    def positions(self):
        while True:
            yield (
                random.randint(0, self.board.width - 1),
                random.randint(0, self.board.height - 1)
            )
