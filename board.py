class Board(object):
    def __init__(self, options, ui_queue):
        self.width = options.get("width")
        self.height = options.get("height")
        self.ui_queue = ui_queue
        self.creatures = []
        self.fields = [
            [None for y in range(self.height)] for x in range(self.width)
        ]

    def is_correct_position(self, position):
        """Checks if position is placed on board."""

        x, y = position

        if x < 0 or y < 0:
            return False

        if x >= self.width or y >= self.height:
            return False

        return True

    def is_free(self, position):
        """Checks if specified position does not contain any creature."""

        x, y = position
        return (
            self.is_correct_position(position) and
            self.fields[x][y] is None
        )

    def at(self, position):
        """Returns creature at position."""
        x, y = position
        return self.fields[x][y]

    def put(self, creature, position):
        """Puts new creature on board."""

        x, y = position
        creature.position = position
        creature.board = self
        self.creatures.append(creature)
        self.fields[x][y] = creature
        self.ui_queue.put(
            (
                creature.position,
                creature.color
            )
        )

    def remove(self, position):
        """Removes creature from board."""

        x, y = position
        self.creatures.remove(self.fields[x][y])
        self.fields[x][y] = None
        self.ui_queue.put((position, (0, 0, 0)))

    def check_out(self, creature):
        """Clears current position of creature on board."""

        x, y = creature.position
        self.fields[x][y] = creature
        self.ui_queue.put((creature.position, (0, 0, 0)))

    def check_in(self, creature):
        """Paints current position of creature on board."""

        x, y = creature.position
        self.fields[x][y] = creature
        self.ui_queue.put((creature.position, creature.color))
