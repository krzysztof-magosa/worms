    def born(self, num, feed=False):
        center = self.random_position()
        r = 30.0

        p = ps.RandomPositionStrategy(board=self, options=dict())
        pr = p.positions()
        for _n in range(num):
            while True:
                pos = next(pr)
                #pos = self.random_position()

                #offset = self.rand_circle()
                #pos = (
                    #center[0] + int(offset[0] * r),
                    #center[1] + int(offset[1] * r)
                    #)

                if self.is_correct_position(pos) and self.is_free(pos):
                #if self.is_free(pos):
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

    def after_turn(self):
        garbages = [x for x in self.worms if x.garbage]

        for garbage in garbages:
            self.worms.remove(garbage)

        # TODO maybe every N turns for better perf
        random.shuffle(self.worms)
