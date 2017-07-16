import yaml
import pygame
import multiprocessing as mp
from creatures import Worm

from board import Board


class Application(object):
    def __init__(self, config_path):
        self.options = yaml.load(open(config_path))
        self.ui_queue = mp.Queue(4096)

    def init_board(self):
        self.board = Board(
            options=self.options["board"],
            ui_queue=self.ui_queue
        )

    def init_population(self):
        for item in self.options.get("initial_populations"):
            print(item)

    def logic(self):
        for x in range(10):
            for y in range(10):
                worm = Worm()
                self.board.put(worm, (x, y))

        while True:
            for creature in self.board.creatures:
                creature.turn()

    def run(self):
        """Entrypoint of application."""
        self.init_board()

        self.logic_process = mp.Process(target=self.logic)
        self.logic_process.start()

        self.init_ui()
        while True:
            self.draw_ui()

    def init_ui(self):
        self.ui = pygame.display.set_mode(
            (
                self.board.width,
                self.board.height
            )
        )

    def draw_ui(self):
        for _ in range(100):
            if self.ui_queue.empty():
                break

            operation = self.ui_queue.get()
            pos, color = operation
            self.ui.set_at(pos, color)

        pygame.display.flip()
        for event in pygame.event.get():
            pass
#            if event.type == pygame.QUIT:
#                running = False
