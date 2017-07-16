import random


class PositionStrategy(object):
    def __init__(self, board, options):
        self.board = board
        self.options = options
        self.init()

    def positions(self):
        raise NotImplementedError()

    def option(self, name, default=None):
        if name in self.options:
            return self.options[name]
        else:
            return default

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

        seed = self.option('seed')
        if seed:
            self.rg.seed(seed)

    def positions(self):
        while True:
            yield (
                random.randint(0, self.board.width - 1),
                random.randint(0, self.board.height - 1)
            )
