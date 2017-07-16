import yaml
import pygame
import multiprocessing as mp
import importlib
from creatures import Worm, Dupa

from board import Board
from genome import GenomeHandler
import helpers as h


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
            ps_def = self.options["position_strategies"][item["position"]["strategy"]]
            mod = importlib.import_module(ps_def["module"])
            obj_class = getattr(mod, ps_def["class"])
            obj = obj_class(board=self.board, options=item["position"])
            positions = obj.positions()

            for n in range(item["count"]):
                while True:
                    position = next(positions)
                    if self.board.is_free(position):
                        worm = Worm()
                        self.board.put(worm, position)
                        break

    def logic(self):
        self.init_board()
        self.init_population()

        while True:
            for creature in self.board.creatures:
                creature.turn()

    def run(self):
        """Entrypoint of application."""
        self.logic_process = mp.Process(target=self.logic)
        self.logic_process.start()

        self.init_ui()
        while True:
            self.draw_ui()

    def init_ui(self):
        self.ui = pygame.display.set_mode(
            (
                self.options["board"]["width"],
                self.options["board"]["height"],
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
